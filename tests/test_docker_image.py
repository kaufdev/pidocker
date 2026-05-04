import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCKER_CONTEXT = REPO_ROOT / "docker"
TEST_IMAGE = "pidocker:test-non-root-user"


def test_docker_image_runs_as_pi_non_root_with_workspace_dirs():
    subprocess.run(
        ["docker", "build", "-t", TEST_IMAGE, str(DOCKER_CONTEXT)],
        cwd=REPO_ROOT,
        check=True,
    )

    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            TEST_IMAGE,
            "bash",
            "-lc",
            "id -u && whoami && test -d /home/pi && test -d /workspace/repos",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    stdout_lines = result.stdout.splitlines()
    assert stdout_lines[0] != "0"
    assert stdout_lines[1] == "pi"
