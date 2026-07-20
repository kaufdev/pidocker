from pathlib import Path


REQUIRED_PATHS = [
    ".dockerignore",
    "bin/pidocker",
    "docker/Dockerfile",
    "docker/pidocker-AGENTS.md",
    "docker/pidocker-resume-repo.ts",
    "tests",
    "README.md",
]


def test_required_project_paths_exist():
    repo_root = Path(__file__).resolve().parents[1]

    missing = [path for path in REQUIRED_PATHS if not (repo_root / path).exists()]

    assert missing == []


def test_docker_build_context_uses_an_allowlist():
    repo_root = Path(__file__).resolve().parents[1]
    patterns = (repo_root / ".dockerignore").read_text().splitlines()

    assert patterns[0] == "**"
    assert {"!.dockerignore", "!README.md", "!docker/", "!docker/**"} <= set(patterns)
