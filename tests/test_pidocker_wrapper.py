import base64
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PIDOCKER = REPO_ROOT / "bin" / "pidocker"
FORBIDDEN_HOST_PATHS = [
    "/Users/example-user",
    "/Users/example-user/projects",
    "/Users/example-user/.ssh",
    "/Users/example-user/.aws",
    "/Users/example-user/.kube",
    "/Users/example-user/.config",
    "/Users/example-user/.npmrc",
    "/Users/example-user/.m2",
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


def test_pidocker_setupssh_runs_ssh_setup_command_in_container(tmp_path):
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
        [str(PIDOCKER), "setupssh"],
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
    assert "-it" not in docker_run_call
    assert "type=volume,source=pidocker-test-home,target=/home/pi" in docker_run_call
    assert "type=volume,source=pidocker-test-workspace,target=/workspace" in docker_run_call
    assert docker_run_call[-1] == "pidocker-ssh-setup"


def test_pidocker_secrets_set_reads_value_from_stdin_without_value_argument(tmp_path):
    docker_log = tmp_path / "docker.log"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_docker = fake_bin / "docker"
    fake_docker.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' \"$*\" >> \"$PIDOCKER_DOCKER_LOG\"\n"
        "if [ \"${1:-}\" = run ]; then cat >/dev/null; fi\n"
        "exit 0\n"
    )
    fake_docker.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["PIDOCKER_DOCKER_LOG"] = str(docker_log)
    env["PIDOCKER_VOLUME_PREFIX"] = "pidocker-test"

    result = subprocess.run(
        [str(PIDOCKER), "secrets", "set", "NOTION_API_KEY"],
        cwd=REPO_ROOT,
        env=env,
        input="secret-value\n",
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Stored secret NOTION_API_KEY" in result.stdout
    docker_calls = docker_log.read_text().splitlines()
    docker_run_calls = [call.split() for call in docker_calls if call.startswith("run ")]

    assert docker_run_calls, docker_calls
    docker_run_call = docker_run_calls[-1]
    assert "-i" in docker_run_call
    assert "--env" in docker_run_call
    assert "PIDOCKER_SECRET_KEY=NOTION_API_KEY" in docker_run_call
    assert "secret-value" not in " ".join(docker_run_call)
    assert "type=volume,source=pidocker-test-home,target=/home/pi" in docker_run_call
    assert "type=volume,source=pidocker-test-workspace,target=/workspace" in docker_run_call


def test_pidocker_secrets_set_rejects_empty_value(tmp_path):
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
        [str(PIDOCKER), "secrets", "set", "NOTION_API_KEY"],
        cwd=REPO_ROOT,
        env=env,
        input="\n",
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "pidocker: secret value must not be empty" in result.stderr
    docker_calls = docker_log.read_text().splitlines()
    assert not any(call.startswith("run ") for call in docker_calls)


def test_pidocker_accepts_repository_name_as_start_directory(tmp_path):
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
        [str(PIDOCKER), "monorepo"],
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
    assert "--env" in docker_run_call
    assert "PIDOCKER_REPO_ARG=monorepo" in docker_run_call


def test_pidocker_can_print_shell_completion():
    result = subprocess.run(
        [str(PIDOCKER), "completion", "bash"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "complete -F _pidocker_complete pidocker" in result.stdout
    assert "/workspace/repos" in result.stdout


def test_pidocker_packages_add_list_and_remove_use_host_config(tmp_path):
    config_dir = tmp_path / "config"
    env = os.environ.copy()
    env["PIDOCKER_CONFIG_DIR"] = str(config_dir)

    add_result = subprocess.run(
        [str(PIDOCKER), "packages", "add", "npm:@client/pi-tools@1.2.3"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert add_result.returncode == 0
    packages_file = config_dir / "packages.json"
    assert json.loads(packages_file.read_text()) == {
        "packages": ["npm:@client/pi-tools@1.2.3"]
    }

    list_result = subprocess.run(
        [str(PIDOCKER), "packages", "list"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert list_result.returncode == 0
    assert list_result.stdout.strip() == "npm:@client/pi-tools@1.2.3"

    remove_result = subprocess.run(
        [str(PIDOCKER), "packages", "remove", "npm:@client/pi-tools"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert remove_result.returncode == 0
    assert json.loads(packages_file.read_text()) == {"packages": []}


def test_pidocker_packages_add_rejects_unpinned_or_local_packages(tmp_path):
    env = os.environ.copy()
    env["PIDOCKER_CONFIG_DIR"] = str(tmp_path / "config")

    unpinned_result = subprocess.run(
        [str(PIDOCKER), "packages", "add", "npm:@client/pi-tools"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    local_result = subprocess.run(
        [str(PIDOCKER), "packages", "add", "git:../pi-tools@v1"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert unpinned_result.returncode == 2
    assert "npm packages must be pinned" in unpinned_result.stderr
    assert local_result.returncode == 2
    assert "not a local path" in local_result.stderr


def test_pidocker_passes_host_packages_without_mounting_host_config(tmp_path):
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

    config_dir = tmp_path / "config"
    packages_file = config_dir / "packages.json"
    config_dir.mkdir()
    packages_file.write_text(
        '{\n'
        '  "packages": [\n'
        '    "npm:@client/pi-tools@1.2.3"\n'
        '  ]\n'
        '}\n'
    )

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["PIDOCKER_DOCKER_LOG"] = str(docker_log)
    env["PIDOCKER_CONFIG_DIR"] = str(config_dir)

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
    package_env = next(
        arg for arg in docker_run_call if arg.startswith("PIDOCKER_PACKAGE_SPECS_B64=")
    )
    encoded_packages = package_env.split("=", 1)[1]
    assert base64.b64decode(encoded_packages).decode() == "npm:@client/pi-tools@1.2.3"
    assert str(config_dir) not in " ".join(docker_run_call)
    assert str(packages_file) not in " ".join(docker_run_call)


def test_pidocker_script_clones_git_url_and_changes_to_repo_before_pi():
    script = PIDOCKER.read_text()

    assert "PIDOCKER_REPO_ARG" in script
    assert "git clone \"${repo_arg}\" \"${workdir}\"" in script
    assert "cd \"${workdir}\"" in script
    assert script.index("cd \"${workdir}\"") < script.index("exec pi")


def test_pidocker_runs_pi_by_default(tmp_path):
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
    assert docker_run_call[-2:] == ["bash", "-lc"]


def test_pidocker_loads_pidocker_secrets_before_running_pi():
    script = PIDOCKER.read_text()

    assert "/home/pi/.pidocker/secrets/env" in script
    assert "export \"${key}=${value}\"" in script
    assert "exec pi" in script


def test_pidocker_persists_pi_web_access_package_in_home_volume_before_running_pi():
    script = PIDOCKER.read_text()

    assert "/home/pi/.pi/agent/settings.json" in script
    assert "npm:pi-web-access" in script
    assert "settings.packages.push" in script
    assert script.index("npm:pi-web-access") < script.index("exec pi")


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
    for forbidden_path in ["/var/run/docker.sock", "/Users/example-user"]:
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
