import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PIDOCKER = REPO_ROOT / "bin" / "pidocker"


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
