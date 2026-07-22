import base64
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PIDOCKER = REPO_ROOT / "bin" / "pidocker"
PIDOCKERTEST = REPO_ROOT / "bin" / "pidockertest"
PIDOCKER_BOOTSTRAP = REPO_ROOT / "docker" / "pidocker-bootstrap.cjs"
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


def run_package_bootstrap(tmp_path, host_packages, *, pi_exit=0, npm_exit=0):
    fake_bin = tmp_path / "bootstrap-bin"
    fake_bin.mkdir(exist_ok=True)
    fake_pi = fake_bin / "pi"
    fake_pi.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "with open(os.environ['PIDOCKER_FAKE_PI_LOG'], 'a', encoding='utf8') as stream:\n"
        "    stream.write(json.dumps(sys.argv[1:]) + '\\n')\n"
        "raise SystemExit(int(os.environ.get('PIDOCKER_FAKE_PI_EXIT', '0')))\n"
    )
    fake_pi.chmod(0o755)
    fake_npm = fake_bin / "npm"
    fake_npm.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "with open(os.environ['PIDOCKER_FAKE_NPM_LOG'], 'a', encoding='utf8') as stream:\n"
        "    stream.write(json.dumps({'argv': sys.argv[1:], 'cwd': os.getcwd()}) + '\\n')\n"
        "raise SystemExit(int(os.environ.get('PIDOCKER_FAKE_NPM_EXIT', '0')))\n"
    )
    fake_npm.chmod(0o755)

    paths = {
        "settings": tmp_path / "settings.json",
        "keybindings": tmp_path / "keybindings.json",
        "reconcile": tmp_path / "package-reconcile.json",
        "pi_log": tmp_path / "pi.log",
        "npm_log": tmp_path / "npm.log",
    }
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["PI_SETTINGS_FILE"] = str(paths["settings"])
    env["PI_KEYBINDINGS_FILE"] = str(paths["keybindings"])
    env["PIDOCKER_PACKAGE_RECONCILE_FILE"] = str(paths["reconcile"])
    env["PIDOCKER_PACKAGE_SPECS_B64"] = base64.b64encode(
        "\n".join(host_packages).encode()
    ).decode()
    env["PIDOCKER_FAKE_PI_LOG"] = str(paths["pi_log"])
    env["PIDOCKER_FAKE_PI_EXIT"] = str(pi_exit)
    env["PIDOCKER_FAKE_NPM_LOG"] = str(paths["npm_log"])
    env["PIDOCKER_FAKE_NPM_EXIT"] = str(npm_exit)

    result = subprocess.run(
        ["node", str(PIDOCKER_BOOTSTRAP)],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    return result, paths


def read_fake_pi_calls(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines()]


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


def test_pidocker_builds_missing_image_from_root_context(tmp_path):
    docker_log = tmp_path / "docker.log"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_docker = fake_bin / "docker"
    fake_docker.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' \"$*\" >> \"$PIDOCKER_DOCKER_LOG\"\n"
        "if [[ \"${1:-}\" == image && \"${2:-}\" == inspect ]]; then exit 1; fi\n"
        "exit 0\n"
    )
    fake_docker.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["PIDOCKER_CONFIG_DIR"] = str(tmp_path / "config")
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
    docker_calls = [call.split() for call in docker_log.read_text().splitlines()]
    build_call = next(call for call in docker_calls if call[0] == "build")
    assert build_call == [
        "build",
        "--file",
        str(REPO_ROOT / "docker" / "Dockerfile"),
        "-t",
        "pidocker:local",
        str(REPO_ROOT),
    ]


def test_pidocker_rebuilds_image_with_incompatible_runtime_label(tmp_path):
    docker_log = tmp_path / "docker.log"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_docker = fake_bin / "docker"
    fake_docker.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' \"$*\" >> \"$PIDOCKER_DOCKER_LOG\"\n"
        "if [[ \"${1:-}\" == image && \"${2:-}\" == inspect && \" $* \" == *\" --format \"* ]]; then\n"
        "  printf '%s\\n' '0'\n"
        "fi\n"
        "exit 0\n"
    )
    fake_docker.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["PIDOCKER_CONFIG_DIR"] = str(tmp_path / "config")
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
    assert "rebuilding incompatible image" in result.stderr
    docker_calls = [call.split() for call in docker_log.read_text().splitlines()]
    assert any(call[0] == "build" for call in docker_calls)


def test_pidockertest_symlink_runs_repository_pidocker(tmp_path):
    launcher = tmp_path / "pidockertest"
    launcher.symlink_to(PIDOCKERTEST)
    env = os.environ.copy()
    env["PIDOCKER_TEST_CONFIG_DIR"] = str(tmp_path / "config")

    result = subprocess.run(
        [str(launcher), "repos", "list"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "No repository aliases configured."


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
    env["PIDOCKER_CONFIG_DIR"] = str(tmp_path / "config")
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


def test_pidocker_repos_add_list_remove_use_host_config(tmp_path):
    config_dir = tmp_path / "config"
    env = os.environ.copy()
    env["PIDOCKER_CONFIG_DIR"] = str(config_dir)

    add = subprocess.run(
        [str(PIDOCKER), "repos", "add", "monorepo", "git@github.com:company/monorepo.git"],
        cwd=REPO_ROOT, env=env, text=True, capture_output=True, check=False,
    )
    assert add.returncode == 0
    assert (config_dir / "repos" / "monorepo").read_text() == "git@github.com:company/monorepo.git\n"
    assert (config_dir / "repos" / "monorepo").stat().st_mode & 0o077 == 0

    listed = subprocess.run(
        [str(PIDOCKER), "repos", "list"],
        cwd=REPO_ROOT, env=env, text=True, capture_output=True, check=False,
    )
    assert listed.returncode == 0
    assert listed.stdout.strip() == "monorepo"

    removed = subprocess.run(
        [str(PIDOCKER), "repos", "remove", "monorepo"],
        cwd=REPO_ROOT, env=env, text=True, capture_output=True, check=False,
    )
    assert removed.returncode == 0
    assert not (config_dir / "repos" / "monorepo").exists()


def test_pidocker_repos_reject_reserved_alias_and_invalid_url(tmp_path):
    env = os.environ.copy()
    env["PIDOCKER_CONFIG_DIR"] = str(tmp_path / "config")

    reserved = subprocess.run(
        [str(PIDOCKER), "repos", "add", "tools", "https://example.com/repo.git"],
        cwd=REPO_ROOT, env=env, text=True, capture_output=True, check=False,
    )
    invalid_url = subprocess.run(
        [str(PIDOCKER), "repos", "add", "repo", "https://example.com/repo.git\nssh://other/repo.git"],
        cwd=REPO_ROOT, env=env, text=True, capture_output=True, check=False,
    )
    assert reserved.returncode == 2
    assert "reserved" in reserved.stderr
    assert invalid_url.returncode == 2
    assert "without whitespace" in invalid_url.stderr


def test_pidocker_alias_uses_isolated_instance_resources(tmp_path):
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
    env["PIDOCKER_CONFIG_DIR"] = str(tmp_path / "config")
    subprocess.run(
        [str(PIDOCKER), "repos", "add", "monorepo", "git@github.com:company/monorepo.git"],
        cwd=REPO_ROOT, env=env, text=True, capture_output=True, check=True,
    )

    first = subprocess.run([str(PIDOCKER), "monorepo"], cwd=REPO_ROOT, env=env, text=True, capture_output=True, check=False)
    second = subprocess.run([str(PIDOCKER), "monorepo"], cwd=REPO_ROOT, env=env, text=True, capture_output=True, check=False)
    assert first.returncode == second.returncode == 0
    calls = [line for line in docker_log.read_text().splitlines() if line.startswith("run ")]
    interactive_calls = [call for call in calls if " -it " in f" {call} "]
    assert len(interactive_calls) == 2
    for call in interactive_calls:
        assert "PIDOCKER_REPO_ARG=git@github.com:company/monorepo.git" in call
        assert "PIDOCKER_REPO_ALIAS=monorepo" in call
        assert "PIDOCKER_RESUME_REQUEST_DIR=/home/pi/.pidocker/resume-requests" in call
        assert re.search(r"PIDOCKER_RESUME_LAUNCH_ID=[0-9a-f]{32}", call)
        assert "type=volume,source=pidocker-home,target=/home/pi" in call
    instances = [
        re.search(r"PIDOCKER_INSTANCE_ID=(monorepo-[0-9a-f]{12})", call).group(1)
        for call in interactive_calls
    ]
    assert instances[0] != instances[1]
    assert f"--name pidocker-{instances[0]}" in interactive_calls[0]
    assert f"--name pidocker-{instances[1]}" in interactive_calls[1]
    assert f"source=pidocker-{instances[0]}-workspace,target=/workspace" in interactive_calls[0]
    assert f"source=pidocker-{instances[1]}-workspace,target=/workspace" in interactive_calls[1]
    assert f"PI_CODING_AGENT_SESSION_DIR=/home/pi/.pi/agent/instance-sessions/{instances[0]}" in interactive_calls[0]


def test_pidocker_resume_request_relaunches_selected_workspace_and_session(tmp_path):
    docker_log = tmp_path / "docker.log"
    helper_count = tmp_path / "helper-count"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_docker = fake_bin / "docker"
    fake_docker.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' \"$*\" >> \"$PIDOCKER_DOCKER_LOG\"\n"
        "if [[ \" $* \" == *\" PIDOCKER_RESUME_LAUNCH_ID=\"* && \" $* \" != *\" -it \"* ]]; then\n"
        "  count=0\n"
        "  if [ -f \"$PIDOCKER_HELPER_COUNT\" ]; then count=$(cat \"$PIDOCKER_HELPER_COUNT\"); fi\n"
        "  count=$((count + 1))\n"
        "  printf '%s\\n' \"$count\" > \"$PIDOCKER_HELPER_COUNT\"\n"
        "  if [ \"$count\" -eq 1 ]; then\n"
        "    printf '%s\\n' 'monorepo-aaaaaaaaaaaa' '2026-07-18T12-00-00-000Z_session.jsonl'\n"
        "  fi\n"
        "fi\n"
        "exit 0\n"
    )
    fake_docker.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["PIDOCKER_DOCKER_LOG"] = str(docker_log)
    env["PIDOCKER_HELPER_COUNT"] = str(helper_count)
    env["PIDOCKER_CONFIG_DIR"] = str(tmp_path / "config")
    subprocess.run(
        [str(PIDOCKER), "repos", "add", "monorepo", "git@github.com:company/monorepo.git"],
        cwd=REPO_ROOT, env=env, text=True, capture_output=True, check=True,
    )

    result = subprocess.run(
        [str(PIDOCKER), "monorepo"],
        cwd=REPO_ROOT, env=env, text=True, capture_output=True, check=False,
    )

    assert result.returncode == 0
    calls = [line for line in docker_log.read_text().splitlines() if line.startswith("run ")]
    interactive_calls = [call for call in calls if " -it " in f" {call} "]
    assert len(interactive_calls) == 2
    resumed = interactive_calls[1]
    target = "monorepo-aaaaaaaaaaaa"
    session = "2026-07-18T12-00-00-000Z_session.jsonl"
    assert f"--name pidocker-{target}" in resumed
    assert f"source=pidocker-{target}-workspace,target=/workspace" in resumed
    assert f"PI_CODING_AGENT_SESSION_DIR=/home/pi/.pi/agent/instance-sessions/{target}" in resumed
    assert f"PIDOCKER_SESSION_PATH=/home/pi/.pi/agent/instance-sessions/{target}/{session}" in resumed
    assert helper_count.read_text().strip() == "2"


def test_pidocker_resume_request_rejects_another_repository_alias(tmp_path):
    docker_log = tmp_path / "docker.log"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_docker = fake_bin / "docker"
    fake_docker.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' \"$*\" >> \"$PIDOCKER_DOCKER_LOG\"\n"
        "if [[ \" $* \" == *\" PIDOCKER_RESUME_LAUNCH_ID=\"* && \" $* \" != *\" -it \"* ]]; then\n"
        "  printf '%s\\n' 'other-aaaaaaaaaaaa' 'session.jsonl'\n"
        "fi\n"
        "exit 0\n"
    )
    fake_docker.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["PIDOCKER_DOCKER_LOG"] = str(docker_log)
    env["PIDOCKER_CONFIG_DIR"] = str(tmp_path / "config")
    subprocess.run(
        [str(PIDOCKER), "repos", "add", "monorepo", "git@github.com:company/monorepo.git"],
        cwd=REPO_ROOT, env=env, text=True, capture_output=True, check=True,
    )

    result = subprocess.run(
        [str(PIDOCKER), "monorepo"],
        cwd=REPO_ROOT, env=env, text=True, capture_output=True, check=False,
    )

    assert result.returncode == 2
    assert "malformed repository resume request" in result.stderr
    calls = [line for line in docker_log.read_text().splitlines() if line.startswith("run ")]
    interactive_calls = [call for call in calls if " -it " in f" {call} "]
    assert len(interactive_calls) == 1


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


def test_pidocker_packages_add_replaces_same_git_repo_across_url_forms(tmp_path):
    config_dir = tmp_path / "config"
    env = os.environ.copy()
    env["PIDOCKER_CONFIG_DIR"] = str(config_dir)
    old_source = "git:git@github.com:client/pi-tools.git@v1.0.0"
    new_source = "git:https://github.com/client/pi-tools@v2.0.0"

    subprocess.run(
        [str(PIDOCKER), "packages", "add", old_source],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        [str(PIDOCKER), "packages", "add", new_source],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )

    packages_file = config_dir / "packages.json"
    assert json.loads(packages_file.read_text()) == {"packages": [new_source]}

    subprocess.run(
        [str(PIDOCKER), "packages", "remove", "git:github.com/client/pi-tools"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
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
    unpinned_ssh_result = subprocess.run(
        [
            str(PIDOCKER),
            "packages",
            "add",
            "git:ssh://git@github.com/client/pi-tools",
        ],
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
    assert unpinned_ssh_result.returncode == 2
    assert "must include a pinned ref" in unpinned_ssh_result.stderr


def test_package_bootstrap_replaces_refs_deduplicates_and_preserves_filters(tmp_path):
    desired_git = "git:github.com/kaufdev/notion-agent-manager@v0.1.4"
    desired_npm = "npm:@client/pi-tools@2.0.0"
    settings = {
        "theme": "dark",
        "packages": [
            "../../../../workspace/repos/notion-agent-manager",
            "npm:unrelated@9.9.9",
            {
                "source": "git:git@github.com:kaufdev/notion-agent-manager.git@v0.1.3",
                "autoload": False,
                "extensions": ["extensions/*.ts"],
            },
            "git:https://github.com/kaufdev/notion-agent-manager.git@v0.1.2",
            {
                "source": "npm:@client/pi-tools@1.0.0",
                "skills": [],
            },
            "npm:@client/pi-tools@0.9.0",
            {"source": "../../local-extension", "extensions": []},
        ],
    }
    (tmp_path / "settings.json").write_text(json.dumps(settings))

    result, paths = run_package_bootstrap(
        tmp_path, [desired_git, desired_npm]
    )

    assert result.returncode == 0, result.stderr
    updated = json.loads(paths["settings"].read_text())
    assert updated["theme"] == "dark"
    assert updated["packages"] == [
        "../../../../workspace/repos/notion-agent-manager",
        "npm:unrelated@9.9.9",
        {
            "source": desired_git,
            "autoload": False,
            "extensions": ["extensions/*.ts"],
        },
        {"source": desired_npm, "skills": []},
        {"source": "../../local-extension", "extensions": []},
        "npm:pi-web-access",
        "npm:@tifan/pi-fixed-editor",
    ]
    assert read_fake_pi_calls(paths["pi_log"]) == [
        ["install", desired_git, "--no-approve"]
    ]
    assert json.loads(paths["reconcile"].read_text()) == {
        "version": 1,
        "managed": {
            "git:github.com/kaufdev/notion-agent-manager": desired_git,
            "npm:@client/pi-tools": desired_npm,
        },
        "pendingGit": {},
        "pendingRemove": {},
    }

    second_result, _ = run_package_bootstrap(
        tmp_path, [desired_git, desired_npm]
    )

    assert second_result.returncode == 0, second_result.stderr
    assert read_fake_pi_calls(paths["pi_log"]) == [
        ["install", desired_git, "--no-approve"]
    ]


def test_package_bootstrap_retries_git_reconcile_after_failure(tmp_path):
    old_git = "git:github.com/kaufdev/notion-agent-manager@v0.1.3"
    desired_git = "git:github.com/kaufdev/notion-agent-manager@v0.1.4"
    identity = "git:github.com/kaufdev/notion-agent-manager"
    (tmp_path / "settings.json").write_text(
        json.dumps({"packages": [old_git]})
    )
    (tmp_path / "package-reconcile.json").write_text(
        json.dumps({"version": 1, "pendingGit": {identity: old_git}})
    )

    failed, paths = run_package_bootstrap(
        tmp_path, [desired_git], pi_exit=17
    )

    assert failed.returncode == 1
    assert "pi install failed" in failed.stderr
    assert json.loads(paths["settings"].read_text())["packages"][0] == desired_git
    assert json.loads(paths["reconcile"].read_text()) == {
        "version": 1,
        "managed": {identity: desired_git},
        "pendingGit": {identity: desired_git},
        "pendingRemove": {},
    }
    assert read_fake_pi_calls(paths["pi_log"]) == [
        ["install", desired_git, "--no-approve"]
    ]

    succeeded, _ = run_package_bootstrap(tmp_path, [desired_git])
    final, _ = run_package_bootstrap(tmp_path, [desired_git])

    assert succeeded.returncode == 0, succeeded.stderr
    assert final.returncode == 0, final.stderr
    assert read_fake_pi_calls(paths["pi_log"]) == [
        ["install", desired_git, "--no-approve"],
        ["install", desired_git, "--no-approve"],
    ]
    assert json.loads(paths["reconcile"].read_text()) == {
        "version": 1,
        "managed": {identity: desired_git},
        "pendingGit": {},
        "pendingRemove": {},
    }


def test_package_bootstrap_removes_packages_deleted_from_host_config(tmp_path):
    managed_git = "git:github.com/client/git-tools@v1.0.0"
    managed_npm = "npm:@client/pi-tools@1.0.0"
    git_identity = "git:github.com/client/git-tools"
    npm_identity = "npm:@client/pi-tools"
    local_package = "../../../../workspace/repos/local-tools"
    (tmp_path / "settings.json").write_text(
        json.dumps(
            {
                "packages": [
                    managed_git,
                    managed_npm,
                    "npm:unrelated@9.9.9",
                    local_package,
                ]
            }
        )
    )
    (tmp_path / "package-reconcile.json").write_text(
        json.dumps(
            {
                "version": 1,
                "managed": {
                    git_identity: managed_git,
                    npm_identity: managed_npm,
                },
                "pendingGit": {},
                "pendingRemove": {},
            }
        )
    )

    result, paths = run_package_bootstrap(tmp_path, [])

    assert result.returncode == 0, result.stderr
    assert json.loads(paths["settings"].read_text())["packages"] == [
        "npm:unrelated@9.9.9",
        local_package,
        "npm:pi-web-access",
        "npm:@tifan/pi-fixed-editor",
    ]
    assert read_fake_pi_calls(paths["pi_log"]) == []
    assert json.loads(paths["reconcile"].read_text()) == {
        "version": 1,
        "managed": {},
        "pendingGit": {},
        "pendingRemove": {},
    }

    second, _ = run_package_bootstrap(tmp_path, [])
    assert second.returncode == 0, second.stderr
    assert len(read_fake_pi_calls(paths["pi_log"])) == 0


def test_package_bootstrap_retries_incomplete_git_dependencies(tmp_path):
    old_git = "git:github.com/client/pi-tools@v1.0.0"
    desired_git = "git:github.com/client/pi-tools@v2.0.0"
    identity = "git:github.com/client/pi-tools"
    install_dir = tmp_path / "git" / "github.com" / "client" / "pi-tools"
    install_dir.mkdir(parents=True)
    (install_dir / "package.json").write_text('{"name":"pi-tools"}\n')
    (tmp_path / "settings.json").write_text(
        json.dumps({"packages": [old_git]})
    )

    failed, paths = run_package_bootstrap(
        tmp_path, [desired_git], npm_exit=23
    )

    assert failed.returncode == 1
    assert "dependency install failed" in failed.stderr
    assert read_fake_pi_calls(paths["pi_log"]) == [
        ["install", desired_git, "--no-approve"]
    ]
    assert read_fake_pi_calls(paths["npm_log"]) == [
        {"argv": ["install", "--omit=dev"], "cwd": str(install_dir)}
    ]
    assert json.loads(paths["reconcile"].read_text())["pendingGit"] == {
        identity: desired_git
    }

    succeeded, _ = run_package_bootstrap(tmp_path, [desired_git])

    assert succeeded.returncode == 0, succeeded.stderr
    assert read_fake_pi_calls(paths["pi_log"]) == [
        ["install", desired_git, "--no-approve"],
        ["install", desired_git, "--no-approve"],
    ]
    assert len(read_fake_pi_calls(paths["npm_log"])) == 2
    assert json.loads(paths["reconcile"].read_text())["pendingGit"] == {}


def test_package_bootstrap_passes_git_source_as_one_argv_value(tmp_path):
    source = "git:github.com/client/pi-tools@v1;echo-owned"

    result, paths = run_package_bootstrap(tmp_path, [source])

    assert result.returncode == 0, result.stderr
    assert read_fake_pi_calls(paths["pi_log"]) == [
        ["install", source, "--no-approve"]
    ]


def test_pidocker_tools_add_list_and_remove_use_host_config(tmp_path):
    config_dir = tmp_path / "config"
    env = os.environ.copy()
    env["PIDOCKER_CONFIG_DIR"] = str(config_dir)

    add_result = subprocess.run(
        [str(PIDOCKER), "tools", "add", "apt:binutils"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert add_result.returncode == 0
    tools_file = config_dir / "tools.json"
    assert json.loads(tools_file.read_text()) == {"tools": ["apt:binutils"]}
    assert "pidocker:local-tools" in add_result.stdout

    list_result = subprocess.run(
        [str(PIDOCKER), "tools", "list"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert list_result.returncode == 0
    assert list_result.stdout.strip() == "apt:binutils"

    remove_result = subprocess.run(
        [str(PIDOCKER), "tools", "remove", "apt:binutils"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert remove_result.returncode == 0
    assert json.loads(tools_file.read_text()) == {"tools": []}


def test_pidocker_tools_add_rejects_non_apt_or_invalid_tools(tmp_path):
    env = os.environ.copy()
    env["PIDOCKER_CONFIG_DIR"] = str(tmp_path / "config")

    non_apt_result = subprocess.run(
        [str(PIDOCKER), "tools", "add", "npm:readelf"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    invalid_result = subprocess.run(
        [str(PIDOCKER), "tools", "add", "apt:../binutils"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert non_apt_result.returncode == 2
    assert "tool must start with apt:" in non_apt_result.stderr
    assert invalid_result.returncode == 2
    assert "apt tools must look like apt:binutils" in invalid_result.stderr


def test_pidocker_tools_build_generates_derived_image_dockerfile(tmp_path):
    docker_log = tmp_path / "docker.log"
    docker_stdin = tmp_path / "Dockerfile.generated"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_docker = fake_bin / "docker"
    fake_docker.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' \"$*\" >> \"$PIDOCKER_DOCKER_LOG\"\n"
        "if [ \"${1:-}\" = image ] && [ \"${2:-}\" = inspect ]; then\n"
        "  if [ \"${3:-}\" = pidocker:local ]; then\n"
        "    if [ \"${4:-}\" = --format ]; then printf '%s\\n' 'sha256:base-image'; fi\n"
        "    exit 0\n"
        "  fi\n"
        "  exit 1\n"
        "fi\n"
        "if [ \"${1:-}\" = build ]; then cat > \"$PIDOCKER_DOCKER_STDIN\"; fi\n"
        "exit 0\n"
    )
    fake_docker.chmod(0o755)

    config_dir = tmp_path / "config"
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["PIDOCKER_DOCKER_LOG"] = str(docker_log)
    env["PIDOCKER_DOCKER_STDIN"] = str(docker_stdin)
    env["PIDOCKER_CONFIG_DIR"] = str(config_dir)

    add_result = subprocess.run(
        [str(PIDOCKER), "tools", "add", "apt:binutils"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    build_result = subprocess.run(
        [str(PIDOCKER), "tools", "build"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert add_result.returncode == 0
    assert build_result.returncode == 0
    docker_calls = docker_log.read_text().splitlines()
    assert "build -t pidocker:local-tools -" in docker_calls
    generated = docker_stdin.read_text()
    assert "FROM pidocker:local" in generated
    expected_hash = hashlib.sha256(b"sha256:base-image\napt:binutils\n").hexdigest()
    assert f'LABEL org.pidocker.tools.sha="{expected_hash}"' in generated
    assert "apt-get install -y --no-install-recommends" in generated
    assert "binutils" in generated
    assert "USER pi" in generated
    assert str(config_dir) not in " ".join(docker_calls)


def test_pidocker_runs_tools_image_when_tools_are_configured(tmp_path):
    docker_log = tmp_path / "docker.log"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_docker = fake_bin / "docker"
    fake_docker.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' \"$*\" >> \"$PIDOCKER_DOCKER_LOG\"\n"
        "if [ \"${1:-}\" = image ] && [ \"${2:-}\" = inspect ]; then\n"
        "  if [ \"${3:-}\" = pidocker:local ]; then exit 0; fi\n"
        "  exit 1\n"
        "fi\n"
        "if [ \"${1:-}\" = build ]; then cat >/dev/null; fi\n"
        "exit 0\n"
    )
    fake_docker.chmod(0o755)

    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "tools.json").write_text(
        '{\n'
        '  "tools": [\n'
        '    "apt:binutils"\n'
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
    assert "pidocker:local-tools" in docker_run_call
    assert str(config_dir) not in " ".join(docker_run_call)


def test_pidocker_agents_sync_streams_host_agents_without_mounting_host_dir(tmp_path):
    docker_log = tmp_path / "docker.log"
    docker_stdin = tmp_path / "docker-stdin.tar"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_docker = fake_bin / "docker"
    fake_docker.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' \"$*\" >> \"$PIDOCKER_DOCKER_LOG\"\n"
        "if [ \"${1:-}\" = run ]; then cat > \"$PIDOCKER_DOCKER_STDIN\"; fi\n"
        "exit 0\n"
    )
    fake_docker.chmod(0o755)

    host_agents = tmp_path / "agents"
    host_agents.mkdir()
    (host_agents / "reviewer.md").write_text("---\nname: reviewer\n---\nReview.\n")

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["PIDOCKER_DOCKER_LOG"] = str(docker_log)
    env["PIDOCKER_DOCKER_STDIN"] = str(docker_stdin)
    env["PIDOCKER_HOST_AGENTS_DIR"] = str(host_agents)

    result = subprocess.run(
        [str(PIDOCKER), "agents", "sync", "--delete"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Synced 1 host agent" in result.stdout
    docker_calls = docker_log.read_text().splitlines()
    docker_run_call = next(call for call in docker_calls if call.startswith("run "))
    assert "PIDOCKER_AGENTS_DELETE=1" in docker_run_call
    assert "pidocker-home" in docker_run_call
    assert str(host_agents) not in docker_run_call

    import tarfile

    with tarfile.open(docker_stdin) as archive:
        names = archive.getnames()
    assert "./reviewer.md" in names


def test_pidocker_agents_list_shows_host_and_container_agents(tmp_path):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_docker = fake_bin / "docker"
    fake_docker.write_text(
        "#!/usr/bin/env bash\n"
        "if [ \"${1:-}\" = run ]; then printf '%s\\n' '  container-reviewer.md'; fi\n"
        "exit 0\n"
    )
    fake_docker.chmod(0o755)

    host_agents = tmp_path / "agents"
    host_agents.mkdir()
    (host_agents / "host-reviewer.md").write_text("---\nname: host-reviewer\n---\n")

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["PIDOCKER_HOST_AGENTS_DIR"] = str(host_agents)

    result = subprocess.run(
        [str(PIDOCKER), "agents", "list"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Host agents" in result.stdout
    assert "  host-reviewer.md" in result.stdout
    assert "Pidocker agents" in result.stdout
    assert "  container-reviewer.md" in result.stdout


def test_pidocker_skills_sync_streams_host_skills_without_mounting_host_dir(tmp_path):
    docker_log = tmp_path / "docker.log"
    docker_stdin = tmp_path / "docker-stdin.tar"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_docker = fake_bin / "docker"
    fake_docker.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' \"$*\" >> \"$PIDOCKER_DOCKER_LOG\"\n"
        "if [ \"${1:-}\" = run ]; then cat > \"$PIDOCKER_DOCKER_STDIN\"; fi\n"
        "exit 0\n"
    )
    fake_docker.chmod(0o755)

    host_skills = tmp_path / "skills"
    skill_dir = host_skills / "two-pass-review"
    script_dir = skill_dir / "scripts"
    script_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: two-pass-review\ndescription: Test skill.\n---\n"
    )
    (script_dir / "helper.sh").write_text("#!/bin/sh\n")

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["PIDOCKER_DOCKER_LOG"] = str(docker_log)
    env["PIDOCKER_DOCKER_STDIN"] = str(docker_stdin)
    env["PIDOCKER_HOST_SKILLS_DIR"] = str(host_skills)

    result = subprocess.run(
        [str(PIDOCKER), "skills", "sync", "--delete"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Synced 1 host skill" in result.stdout
    docker_calls = docker_log.read_text().splitlines()
    docker_run_call = next(call for call in docker_calls if call.startswith("run "))
    assert "PIDOCKER_SKILLS_DELETE=1" in docker_run_call
    assert "pidocker-home" in docker_run_call
    assert str(host_skills) not in docker_run_call

    import tarfile

    with tarfile.open(docker_stdin) as archive:
        names = archive.getnames()
    assert "./two-pass-review/SKILL.md" in names
    assert "./two-pass-review/scripts/helper.sh" in names


def test_pidocker_skills_list_shows_host_and_container_skills(tmp_path):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_docker = fake_bin / "docker"
    fake_docker.write_text(
        "#!/usr/bin/env bash\n"
        "if [ \"${1:-}\" = run ]; then printf '%s\\n' '  container-skill/SKILL.md'; fi\n"
        "exit 0\n"
    )
    fake_docker.chmod(0o755)

    host_skills = tmp_path / "skills"
    skill_dir = host_skills / "host-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: host-skill\ndescription: Test skill.\n---\n"
    )

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["PIDOCKER_HOST_SKILLS_DIR"] = str(host_skills)

    result = subprocess.run(
        [str(PIDOCKER), "skills", "list"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Host skills" in result.stdout
    assert "  host-skill/SKILL.md" in result.stdout
    assert "Pidocker skills" in result.stdout
    assert "  container-skill/SKILL.md" in result.stdout


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


def test_pidocker_bootstraps_packages_in_home_volume_before_running_pi():
    script = PIDOCKER.read_text()
    bootstrap = PIDOCKER_BOOTSTRAP.read_text()

    assert "/home/pi/.pi/agent/settings.json" in script
    assert "/home/pi/.pidocker/package-reconcile.json" in script
    assert "flock -x 9" in script
    assert "node /usr/local/share/pidocker/pidocker-bootstrap.cjs" in script
    assert "npm:pi-web-access" in bootstrap
    assert "npm:@tifan/pi-fixed-editor" in bootstrap
    assert 'runPiPackageCommand("install", source)' in bootstrap
    assert '[action, source, "--no-approve"]' in bootstrap
    assert script.index("secrets_file=") < script.index("pidocker-bootstrap.cjs")
    assert script.index("pidocker-bootstrap.cjs") < script.index("exec pi")


def test_pidocker_configures_multiline_keybinding_before_running_pi():
    script = PIDOCKER.read_text()
    bootstrap = PIDOCKER_BOOTSTRAP.read_text()
    dockerfile = (REPO_ROOT / "docker" / "Dockerfile").read_text()

    assert "/home/pi/.pi/agent/keybindings.json" in script
    assert "tui.input.newLine" in bootstrap
    assert "ctrl+j" in bootstrap
    assert script.index("pidocker-bootstrap.cjs") < script.index("exec pi")
    assert '"tui.input.newLine":["shift+enter","ctrl+j"]' in dockerfile


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
