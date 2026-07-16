import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from aggregate import build_config, decode_payload, load_config, parse_proxies, proxy_key  # noqa: E402


def test_decodes_base64_yaml():
    payload = "proxies:\n  - name: a\n    server: example.com\n    port: 443\n"
    import base64

    assert "example.com" in decode_payload(base64.b64encode(payload.encode()))


def test_parses_and_deduplicates_proxy_identity():
    data = yaml.safe_load(Path("tests/fixtures/sample.yaml").read_text())
    proxies = parse_proxies(yaml.safe_dump(data))
    assert len(proxies) == 2
    assert proxy_key(proxies[0]) == proxy_key(proxies[1])


def test_builds_selectable_auto_group():
    proxies = [{"name": "a", "type": "ss", "server": "example.com", "port": 443}]
    config = build_config(proxies)
    assert config["proxy-groups"][0]["type"] == "url-test"
    assert config["proxy-groups"][0]["proxies"] == ["a"]


def test_load_config_merges_discovered_sources(tmp_path):
    config_path = tmp_path / "sources.yaml"
    config_path.write_text("sources: [{name: fixed, url: https://example.com/fixed}]\n", encoding="utf-8")
    (tmp_path / "discovered_sources.yaml").write_text("sources: [{name: discovered, url: https://example.com/discovered}]\n", encoding="utf-8")
    sources, _ = load_config(config_path)
    assert [source["name"] for source in sources] == ["fixed", "discovered"]
