from pathlib import Path


REQUIRED_PATHS = [
    "bin/pidocker",
    "docker/Dockerfile",
    "tests",
    "README.md",
]


def test_required_project_paths_exist():
    repo_root = Path(__file__).resolve().parents[1]

    missing = [path for path in REQUIRED_PATHS if not (repo_root / path).exists()]

    assert missing == []
