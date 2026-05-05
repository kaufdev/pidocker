from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"
REQUIRED_README_PHRASES = [
    "pidocker",
    "/login",
    "pidocker-home",
    "pidocker-workspace",
    "Azure DevOps",
    "Notion",
    "force push",
    "/Users/kaufdev",
    "/var/run/docker.sock",
    "docker exec",
    "app=pidocker",
]


def test_readme_documents_required_usage_and_security_topics():
    readme = README.read_text()

    missing = [phrase for phrase in REQUIRED_README_PHRASES if phrase not in readme]

    assert missing == []
