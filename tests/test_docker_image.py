import subprocess
import uuid
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCKER_CONTEXT = REPO_ROOT / "docker"
TEST_IMAGE = "pidocker:test-non-root-user"


def remove_docker_volumes(*volume_names):
    subprocess.run(
        ["docker", "volume", "rm", "-f", *volume_names],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


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


def test_home_volume_persists_between_container_runs():
    volume_prefix = f"pidocker-test-{uuid.uuid4().hex}"
    home_volume = f"{volume_prefix}-home"
    workspace_volume = f"{volume_prefix}-workspace"

    subprocess.run(
        ["docker", "build", "-t", TEST_IMAGE, str(DOCKER_CONTEXT)],
        cwd=REPO_ROOT,
        check=True,
    )

    try:
        subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--volume",
                f"{home_volume}:/home/pi",
                "--volume",
                f"{workspace_volume}:/workspace",
                TEST_IMAGE,
                "bash",
                "-lc",
                "echo ok > /home/pi/home-persistence-test.txt",
            ],
            cwd=REPO_ROOT,
            check=True,
        )

        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--volume",
                f"{home_volume}:/home/pi",
                "--volume",
                f"{workspace_volume}:/workspace",
                TEST_IMAGE,
                "bash",
                "-lc",
                "cat /home/pi/home-persistence-test.txt",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        assert result.stdout.strip() == "ok"
    finally:
        remove_docker_volumes(home_volume, workspace_volume)
