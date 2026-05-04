import json
import subprocess
import uuid
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCKER_CONTEXT = REPO_ROOT / "docker"
TEST_IMAGE = "pidocker:test-non-root-user"
FORBIDDEN_HOST_PATHS = [
    "/Users/kaufdev",
    "/Users/kaufdev/projects",
    "/Users/kaufdev/.ssh",
    "/Users/kaufdev/.aws",
    "/Users/kaufdev/.kube",
    "/Users/kaufdev/.config",
    "/Users/kaufdev/.npmrc",
    "/Users/kaufdev/.m2",
    "/var/run/docker.sock",
]


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


def test_docker_image_uses_pi_as_default_command():
    subprocess.run(
        ["docker", "build", "-t", TEST_IMAGE, str(DOCKER_CONTEXT)],
        cwd=REPO_ROOT,
        check=True,
    )

    result = subprocess.run(
        [
            "docker",
            "image",
            "inspect",
            TEST_IMAGE,
            "--format",
            "{{json .Config.Cmd}}",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert json.loads(result.stdout) == ["pi"]


def test_docker_image_contains_pi_command():
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
            "command -v pi && pi --version || true",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert result.stdout.splitlines()[0].endswith("/pi")


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


def test_workspace_volume_persists_repos_between_container_runs():
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
                "mkdir -p /workspace/repos/test-repo && echo ok > /workspace/repos/test-repo/workspace-persistence-test.txt",
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
                "cat /workspace/repos/test-repo/workspace-persistence-test.txt",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        assert result.stdout.strip() == "ok"
    finally:
        remove_docker_volumes(home_volume, workspace_volume)


def test_container_mounts_only_pidocker_volumes_and_cannot_see_private_host_paths():
    volume_prefix = f"pidocker-test-{uuid.uuid4().hex}"
    home_volume = f"{volume_prefix}-home"
    workspace_volume = f"{volume_prefix}-workspace"
    container_id = None

    subprocess.run(
        ["docker", "build", "-t", TEST_IMAGE, str(DOCKER_CONTEXT)],
        cwd=REPO_ROOT,
        check=True,
    )

    try:
        run_result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--detach",
                "--label",
                "app=pidocker",
                "--mount",
                f"type=volume,source={home_volume},target=/home/pi",
                "--mount",
                f"type=volume,source={workspace_volume},target=/workspace",
                TEST_IMAGE,
                "sleep",
                "300",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        container_id = run_result.stdout.strip()

        subprocess.run(
            [
                "docker",
                "exec",
                container_id,
                "bash",
                "-lc",
                "test ! -e /Users/kaufdev && "
                "test ! -e /Users/kaufdev/projects && "
                "test ! -e /Users/kaufdev/.ssh && "
                "test ! -e /Users/kaufdev/.aws && "
                "test ! -e /Users/kaufdev/.kube && "
                "test ! -e /Users/kaufdev/.config && "
                "test ! -e /Users/kaufdev/.npmrc && "
                "test ! -e /Users/kaufdev/.m2 && "
                "test ! -S /var/run/docker.sock",
            ],
            cwd=REPO_ROOT,
            check=True,
        )

        config_result = subprocess.run(
            [
                "docker",
                "inspect",
                container_id,
                "--format",
                "{{json .HostConfig}}",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        host_config = json.loads(config_result.stdout)

        assert host_config["Privileged"] is False
        assert host_config["PidMode"] != "host"
        assert host_config["NetworkMode"] != "host"

        inspect_result = subprocess.run(
            ["docker", "inspect", container_id, "--format", "{{json .Mounts}}"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        mounts = json.loads(inspect_result.stdout)

        assert {mount["Destination"] for mount in mounts} == {"/home/pi", "/workspace"}
        assert {mount["Type"] for mount in mounts} == {"volume"}
        assert {mount["Name"] for mount in mounts} == {home_volume, workspace_volume}

        mount_sources = [mount.get("Source", "") for mount in mounts]
        mount_destinations = [mount.get("Destination", "") for mount in mounts]
        for forbidden_path in FORBIDDEN_HOST_PATHS:
            assert all(forbidden_path not in source for source in mount_sources)
            assert all(forbidden_path not in destination for destination in mount_destinations)
    finally:
        if container_id:
            subprocess.run(
                ["docker", "stop", container_id],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        remove_docker_volumes(home_volume, workspace_volume)
