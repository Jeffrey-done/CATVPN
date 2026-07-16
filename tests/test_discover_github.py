import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from discover_github import candidate_path, raw_url  # noqa: E402


def test_candidate_path_filters_to_subscription_like_files():
    assert candidate_path("configs/clash.yaml")
    assert candidate_path("mihomo/sub.txt")
    assert not candidate_path("README.md")
    assert not candidate_path("src/proxy.js")


def test_raw_url_quotes_branch_and_path():
    assert raw_url("owner/repo", "feature/x", "configs/my file.yaml") == "https://raw.githubusercontent.com/owner/repo/feature%2Fx/configs/my%20file.yaml"
