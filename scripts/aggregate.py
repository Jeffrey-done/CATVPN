"""Fetch, normalize, validate and publish Clash/Mihomo subscriptions."""

from __future__ import annotations

import argparse
import base64
import concurrent.futures
import hashlib
import json
import socket
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

import yaml


USER_AGENT = "catvpn-subscription-aggregator/0.1"


def load_config(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    sources = list(data.get("sources", []))
    discovered_path = path.with_name("discovered_sources.yaml")
    if discovered_path.exists():
        discovered = yaml.safe_load(discovered_path.read_text(encoding="utf-8")) or {}
        sources.extend(discovered.get("sources", []))
    return sources, data.get("settings", {})


def fetch(url: str, timeout: float) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def decode_payload(raw: bytes) -> str:
    text = raw.decode("utf-8-sig", errors="replace").strip()
    if "proxies:" in text or text.startswith("---"):
        return text
    try:
        decoded = base64.b64decode("".join(text.split()), validate=True)
        candidate = decoded.decode("utf-8", errors="replace").strip()
        if candidate:
            return candidate
    except (ValueError, UnicodeDecodeError):
        pass
    return text


def parse_proxies(payload: str) -> list[dict[str, Any]]:
    try:
        data = yaml.safe_load(payload)
    except yaml.YAMLError:
        return []
    if not isinstance(data, dict) or not isinstance(data.get("proxies"), list):
        return []
    return [proxy for proxy in data["proxies"] if isinstance(proxy, dict) and proxy.get("server") and proxy.get("port")]


def proxy_key(proxy: dict[str, Any]) -> str:
    stable = {
        key: proxy.get(key)
        for key in ("type", "server", "port", "username", "uuid", "password", "cipher", "tls", "network", "ws-opts")
    }
    return hashlib.sha256(json.dumps(stable, sort_keys=True, default=str).encode()).hexdigest()


def measure_latency(proxy: dict[str, Any], timeout: float) -> float | None:
    started = time.perf_counter()
    try:
        with socket.create_connection((str(proxy["server"]), int(proxy["port"])), timeout=timeout):
            return round((time.perf_counter() - started) * 1000, 1)
    except (OSError, TypeError, ValueError):
        return None


def collect(source: dict[str, Any], timeout: float) -> tuple[str, list[dict[str, Any]], str | None]:
    try:
        payload = decode_payload(fetch(source["url"], timeout))
        return source["name"], parse_proxies(payload), None
    except Exception as exc:  # A single stale source must not stop publication.
        return source["name"], [], f"{type(exc).__name__}: {exc}"


def build_config(proxies: list[dict[str, Any]]) -> dict[str, Any]:
    clean_proxies = [{key: value for key, value in proxy.items() if key != "catvpn-latency"} for proxy in proxies]
    names = [str(proxy["name"]) for proxy in clean_proxies]
    return {
        "mixed-port": 7890,
        "allow-lan": False,
        "mode": "rule",
        "log-level": "info",
        "proxies": clean_proxies,
        "proxy-groups": [
            {"name": "AUTO", "type": "url-test", "url": "https://www.gstatic.com/generate_204", "interval": 300, "proxies": names},
            {"name": "PROXY", "type": "select", "proxies": ["AUTO", "DIRECT"]},
        ],
        "rules": ["MATCH,PROXY"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("sources.yaml"))
    parser.add_argument("--output", type=Path, default=Path("public"))
    parser.add_argument("--no-check", action="store_true", help="Skip TCP reachability checks for local dry runs")
    args = parser.parse_args()

    sources, settings = load_config(args.config)
    timeout = float(settings.get("connect_timeout", 2.5))
    max_workers = int(settings.get("max_workers", 32))
    max_proxies = int(settings.get("max_proxies", 300))

    results: list[tuple[str, list[dict[str, Any]], str | None]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(collect, source, timeout) for source in sources]
        for future in futures:
            results.append(future.result())

    unique: dict[str, dict[str, Any]] = {}
    report = {"sources": [], "total_before_check": 0, "total_after_check": 0}
    for name, proxies, error in results:
        report["sources"].append({"name": name, "count": len(proxies), "error": error})
        for proxy in proxies:
            proxy.setdefault("name", f"{proxy.get('server')}:{proxy.get('port')}")
            unique.setdefault(proxy_key(proxy), proxy)

    candidates = list(unique.values())
    report["total_before_check"] = len(candidates)
    if not args.no_check:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
            latencies = pool.map(lambda item: measure_latency(item, timeout), candidates)
            checked = []
            for proxy, latency in zip(candidates, latencies):
                if latency is not None:
                    proxy["catvpn-latency"] = latency
                    checked.append(proxy)
            candidates = sorted(checked, key=lambda item: item["catvpn-latency"])
    else:
        for proxy in candidates:
            proxy.pop("catvpn-latency", None)
    candidates = candidates[:max_proxies]
    report["total_after_check"] = len(candidates)

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "clash.yaml").write_text(yaml.safe_dump(build_config(candidates), allow_unicode=True, sort_keys=False), encoding="utf-8")
    (args.output / "status.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if candidates or args.no_check else 1


if __name__ == "__main__":
    sys.exit(main())
