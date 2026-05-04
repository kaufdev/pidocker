import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PIDOCKER = REPO_ROOT / "bin" / "pidocker"
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
FORBIDDEN_DOCKER_FLAGS = [
    "--privileged",
    "--pid=host",
    "--network=host",
]


def test_pidocker_help_is_available_from_repo_script():
    assert PIDOCKER.exists()
    assert os.access(PIDOCKER, os.X_OK)

    result = subprocess.run(
        [str(PIDOCKER), "--help"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "pidocker - run Pi inside a Docker container" in result.stdout
    assert "Usage:" in result.stdout


def test_pidocker_adds_app_label_to_docker_run(tmp_path):
    docker_log = tmp_path / "docker.log"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_docker = fake_bin / "docker"
    fake_docker.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' \"$*\" >> \"$PIDOCKER_DOCKER_LOG\"\n"
        "exit 0\n"
    )
    fake_docker.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["PIDOCKER_DOCKER_LOG"] = str(docker_log)

    result = subprocess.run(
        [str(PIDOCKER)],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    docker_calls = docker_log.read_text().splitlines()
    docker_run_calls = [call.split() for call in docker_calls if call.startswith("run ")]

    assert docker_run_calls, docker_calls
    docker_run_call = docker_run_calls[-1]
    assert "--label" in docker_run_call
    assert "app=pidocker" in docker_run_call


def test_pidocker_mounts_named_home_and_workspace_volumes(tmp_path):
    docker_log = tmp_path / "docker.log"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_docker = fake_bin / "docker"
    fake_docker.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' \"$*\" >> \"$PIDOCKER_DOCKER_LOG\"\n"
        "exit 0\n"
    )
    fake_docker.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["PIDOCKER_DOCKER_LOG"] = str(docker_log)
    env["PIDOCKER_VOLUME_PREFIX"] = "pidocker-test"

    result = subprocess.run(
        [str(PIDOCKER)],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    docker_calls = docker_log.read_text().splitlines()
    docker_run_calls = [call.split() for call in docker_calls if call.startswith("run ")]

    assert docker_run_calls, docker_calls
    docker_run_call = docker_run_calls[-1]
    assert "--mount" in docker_run_call
    assert "type=volume,source=pidocker-test-home,target=/home/pi" in docker_run_call
    assert "type=volume,source=pidocker-test-workspace,target=/workspace" in docker_run_call


def test_pidocker_script_does_not_contain_forbidden_docker_flags_or_mounts():
    script = PIDOCKER.read_text()

    for forbidden_flag in FORBIDDEN_DOCKER_FLAGS:
        assert forbidden_flag not in script
    for forbidden_path in ["/var/run/docker.sock", "/Users/kaufdev"]:
        assert forbidden_path not in script


def test_pidocker_does_not_use_forbidden_docker_flags_or_mount_private_host_paths(tmp_path):
    docker_log = tmp_path / "docker.log"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_docker = fake_bin / "docker"
    fake_docker.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' \"$*\" >> \"$PIDOCKER_DOCKER_LOG\"\n"
        "exit 0\n"
    )
    fake_docker.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["PIDOCKER_DOCKER_LOG"] = str(docker_log)

    result = subprocess.run(
        [str(PIDOCKER)],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    docker_calls = docker_log.read_text().splitlines()
    docker_run_calls = [call for call in docker_calls if call.startswith("run ")]

    assert docker_run_calls, docker_calls
    docker_run_call = docker_run_calls[-1]
    for forbidden_flag in FORBIDDEN_DOCKER_FLAGS:
        assert forbidden_flag not in docker_run_call
    for forbidden_path in FORBIDDEN_HOST_PATHS:
        assert forbidden_path not in docker_run_call
