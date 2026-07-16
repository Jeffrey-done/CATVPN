"""Discover public GitHub files that contain valid Clash/Mihomo proxy lists."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aggregate import decode_payload, parse_proxies  # noqa: E402


API_ROOT = "https://api.github.com"
API_VERSION = "2022-11-28"
FILE_TERMS = ("clash", "mihomo", "proxy", "proxies", "node", "subscribe", "sub")
FILE_SUFFIXES = (".yaml", ".yml", ".txt")


class GithubApiError(RuntimeError):
    pass


class GithubClient:
    def __init__(self, token: str | None, delay: float) -> None:
        self.token = token
        self.delay = delay

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        query = f"?{urllib.parse.urlencode(params)}" if params else ""
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "catvpn-source-discovery/0.1",
            "X-GitHub-Api-Version": API_VERSION,
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(f"{API_ROOT}{path}{query}", headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 429):
                raise GithubApiError("GitHub API rate limit reached") from exc
            raise GithubApiError(f"GitHub API returned HTTP {exc.code}") from exc
        finally:
            time.sleep(self.delay)
        return result


def candidate_path(path: str) -> bool:
    lower = path.lower()
    if not lower.endswith(FILE_SUFFIXES) or lower.endswith((".lock", ".min.yml")):
        return False
    if any(part in lower for part in ("/.github/", "/vendor/", "/node_modules/")):
        return False
    return any(term in lower for term in FILE_TERMS)


def raw_url(full_name: str, branch: str, path: str) -> str:
    return "https://raw.githubusercontent.com/{}/{}/{}".format(
        full_name,
        urllib.parse.quote(branch, safe=""),
        urllib.parse.quote(path, safe="/"),
    )


def discover(config: dict[str, Any], token: str | None) -> dict[str, Any]:
    delay = float(config.get("request_delay_seconds", 0.25))
    max_repositories = int(config.get("max_repositories", 30))
    max_files = int(config.get("max_files_per_repository", 20))
    max_bytes = int(config.get("max_file_bytes", 1_000_000))
    client = GithubClient(token, delay)
    repositories: dict[str, dict[str, Any]] = {}
    for query in config.get("queries", []):
        result = client.get("/search/repositories", {"q": query, "sort": "updated", "per_page": min(max_repositories, 30)})
        for repo in result.get("items", []):
            repositories.setdefault(repo["full_name"], repo)
            if len(repositories) >= max_repositories:
                break
        if len(repositories) >= max_repositories:
            break

    sources: dict[str, dict[str, Any]] = {}
    errors: list[dict[str, str]] = []
    for repo in repositories.values():
        if len(sources) >= max_repositories * max_files:
            break
        try:
            tree = client.get(f"/repos/{repo['full_name']}/git/trees/{urllib.parse.quote(repo.get('default_branch', 'main'), safe='')}", {"recursive": "1"})
            files = [item for item in tree.get("tree", []) if item.get("type") == "blob" and candidate_path(item.get("path", ""))]
            for item in files[:max_files]:
                if item.get("size", 0) > max_bytes:
                    continue
                url = raw_url(repo["full_name"], repo.get("default_branch", "main"), item["path"])
                try:
                    payload = decode_payload(fetch_raw(url))
                    proxies = parse_proxies(payload)
                except (OSError, urllib.error.URLError, UnicodeError):
                    continue
                if not proxies:
                    continue
                sources[url] = {
                    "name": f"github:{repo['full_name']}:{item['path']}",
                    "url": url,
                    "repository": repo["full_name"],
                    "path": item["path"],
                    "proxy_count": len(proxies),
                }
        except GithubApiError as exc:
            errors.append({"repository": repo["full_name"], "error": str(exc)})

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": sorted(sources.values(), key=lambda source: source["name"]),
        "repositories_checked": len(repositories),
        "errors": errors,
    }


def fetch_raw(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "catvpn-source-discovery/0.1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("discovery.yaml"))
    parser.add_argument("--output", type=Path, default=Path("discovered_sources.yaml"))
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"))
    args = parser.parse_args()
    result = discover(yaml.safe_load(args.config.read_text(encoding="utf-8")) or {}, args.token)
    args.output.write_text(yaml.safe_dump(result, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("repositories_checked", "sources", "errors")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
