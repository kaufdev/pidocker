import json
import os
import subprocess
import uuid
from pathlib import Path

import pytest


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


def test_docker_image_contains_pi_web_access_tooling_and_librarian_skill():
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
            "set -euo pipefail && "
            "npm list -g --depth=0 pi-web-access >/dev/null && "
            "node -e 'const pkg=require(\"/usr/local/lib/node_modules/pi-web-access/package.json\"); "
            "if (!pkg.pi || !pkg.pi.extensions || !pkg.pi.extensions.includes(\"./index.ts\")) process.exit(1)' && "
            "grep -q 'npm:pi-web-access' /home/pi/.pi/agent/settings.json && "
            "test -f /usr/local/lib/node_modules/pi-web-access/skills/librarian/SKILL.md && "
            "grep -q 'web_search' /usr/local/lib/node_modules/pi-web-access/index.ts && "
            "grep -q 'code_search' /usr/local/lib/node_modules/pi-web-access/index.ts && "
            "grep -q 'fetch_content' /usr/local/lib/node_modules/pi-web-access/index.ts && "
            "grep -q 'get_search_content' /usr/local/lib/node_modules/pi-web-access/index.ts",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert result.returncode == 0


def test_pi_web_access_package_setting_persists_in_home_volume():
    volume_prefix = f"pidocker-test-{uuid.uuid4().hex}"
    home_volume = f"{volume_prefix}-home"
    workspace_volume = f"{volume_prefix}-workspace"

    subprocess.run(
        ["docker", "build", "-t", TEST_IMAGE, str(DOCKER_CONTEXT)],
        cwd=REPO_ROOT,
        check=True,
    )

    seed_settings = (
        "settings_file=/home/pi/.pi/agent/settings.json && "
        "mkdir -p /home/pi/.pi/agent && "
        "PI_SETTINGS_FILE=\"${settings_file}\" node <<'NODE'\n"
        "const fs = require(\"fs\");\n"
        "const settingsFile = process.env.PI_SETTINGS_FILE;\n"
        "let settings = {};\n"
        "try { settings = JSON.parse(fs.readFileSync(settingsFile, \"utf8\")); } catch (_) {}\n"
        "if (!Array.isArray(settings.packages)) settings.packages = [];\n"
        "if (!settings.packages.includes(\"npm:pi-web-access\")) settings.packages.push(\"npm:pi-web-access\");\n"
        "fs.writeFileSync(settingsFile, `${JSON.stringify(settings, null, 2)}\\n`);\n"
        "NODE"
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
                seed_settings,
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
                "grep -q 'npm:pi-web-access' /home/pi/.pi/agent/settings.json && cat /home/pi/.pi/agent/settings.json",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        assert "npm:pi-web-access" in result.stdout
    finally:
        remove_docker_volumes(home_volume, workspace_volume)


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


def test_docker_image_starts_in_workspace_repos():
    volume_prefix = f"pidocker-test-{uuid.uuid4().hex}"
    home_volume = f"{volume_prefix}-home"
    workspace_volume = f"{volume_prefix}-workspace"

    subprocess.run(
        ["docker", "build", "-t", TEST_IMAGE, str(DOCKER_CONTEXT)],
        cwd=REPO_ROOT,
        check=True,
    )

    try:
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
                "pwd",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        assert result.stdout.strip() == "/workspace/repos"
    finally:
        remove_docker_volumes(home_volume, workspace_volume)


def test_git_can_clone_repo_into_workspace_repos_and_persist_it():
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
                "git init --bare /workspace/source.git && "
                "git clone /workspace/source.git /workspace/repos/cloned-repo",
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
                "test -d /workspace/repos/cloned-repo/.git && "
                "test ! -e /Users/kaufdev/projects && "
                "git -C /workspace/repos/cloned-repo rev-parse --git-dir",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        assert result.stdout.strip() == ".git"
    finally:
        remove_docker_volumes(home_volume, workspace_volume)


def test_pi_auth_file_persists_in_home_volume_between_container_runs():
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
                "mkdir -p /home/pi/.pi/agent && echo '{\"loggedIn\":true}' > /home/pi/.pi/agent/auth.json",
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
                "test -f /home/pi/.pi/agent/auth.json && cat /home/pi/.pi/agent/auth.json",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        assert json.loads(result.stdout) == {"loggedIn": True}
    finally:
        remove_docker_volumes(home_volume, workspace_volume)


def test_notion_secret_path_is_sandboxed_and_persists_in_home_volume_between_container_runs():
    volume_prefix = f"pidocker-test-{uuid.uuid4().hex}"
    home_volume = f"{volume_prefix}-home"
    workspace_volume = f"{volume_prefix}-workspace"
    notion_secret_file = "/home/pi/.pidocker/secrets/notion.env"

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
                f"test -d /home/pi/.pidocker/secrets && "
                f"test ! -e /Users/kaufdev/.config && "
                f"echo NOTION_API_KEY=test > {notion_secret_file}",
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
                f"test -f {notion_secret_file} && "
                f"test ! -e /Users/kaufdev/.config && "
                f"cat {notion_secret_file}",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        assert result.stdout.strip() == "NOTION_API_KEY=test"
    finally:
        remove_docker_volumes(home_volume, workspace_volume)


def test_pidocker_secrets_set_stores_notion_secret_in_home_volume():
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
                "-i",
                "--env",
                "PIDOCKER_SECRET_KEY=NOTION_API_KEY",
                "--volume",
                f"{home_volume}:/home/pi",
                "--volume",
                f"{workspace_volume}:/workspace",
                TEST_IMAGE,
                "bash",
                "-lc",
                "key=\"${PIDOCKER_SECRET_KEY}\" && value=\"$(cat)\" && "
                "umask 077 && mkdir -p /home/pi/.pidocker/secrets && "
                "printf \"%s=%s\\n\" \"$key\" \"$value\" > /home/pi/.pidocker/secrets/env && "
                "printf \"%s=%s\\n\" \"$key\" \"$value\" > /home/pi/.pidocker/secrets/notion.env && "
                "chmod 600 /home/pi/.pidocker/secrets/env /home/pi/.pidocker/secrets/notion.env",
            ],
            cwd=REPO_ROOT,
            input="secret-from-stdin",
            text=True,
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
                "cat /home/pi/.pidocker/secrets/env && cat /home/pi/.pidocker/secrets/notion.env",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        assert result.stdout.splitlines() == [
            "NOTION_API_KEY=secret-from-stdin",
            "NOTION_API_KEY=secret-from-stdin",
        ]
    finally:
        remove_docker_volumes(home_volume, workspace_volume)


def test_pi_resume_sessions_persist_in_home_volume_between_container_runs():
    volume_prefix = f"pidocker-test-{uuid.uuid4().hex}"
    home_volume = f"{volume_prefix}-home"
    workspace_volume = f"{volume_prefix}-workspace"
    session_file = "/home/pi/.pi/agent/sessions/session-persistence-test.jsonl"

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
                f"mkdir -p /home/pi/.pi/agent/sessions && echo session-ok > {session_file}",
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
                f"test -f {session_file} && cat {session_file}",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        assert result.stdout.strip() == "session-ok"
    finally:
        remove_docker_volumes(home_volume, workspace_volume)


def test_pidocker_ssh_setup_command_creates_dedicated_key_config_and_is_idempotent():
    volume_prefix = f"pidocker-test-{uuid.uuid4().hex}"
    home_volume = f"{volume_prefix}-home"
    workspace_volume = f"{volume_prefix}-workspace"

    subprocess.run(
        ["docker", "build", "-t", TEST_IMAGE, str(DOCKER_CONTEXT)],
        cwd=REPO_ROOT,
        check=True,
    )

    try:
        first_result = subprocess.run(
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
                "pidocker-ssh-setup",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        assert "Created dedicated pidocker GitHub SSH key" in first_result.stdout
        assert "Created dedicated pidocker Azure DevOps SSH key" in first_result.stdout
        assert "Public key to add in Azure DevOps:" in first_result.stdout
        assert "Public key to add in GitHub:" in first_result.stdout
        assert "ssh-rsa " in first_result.stdout
        assert "ssh-ed25519 " in first_result.stdout

        second_result = subprocess.run(
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
                "pidocker-ssh-setup && "
                "test -f /home/pi/.ssh/id_ed25519_pidocker_github && "
                "test -f /home/pi/.ssh/id_ed25519_pidocker_github.pub && "
                "test -f /home/pi/.ssh/id_rsa_pidocker_azure && "
                "test -f /home/pi/.ssh/id_rsa_pidocker_azure.pub && "
                "test -f /home/pi/.ssh/config && "
                "grep -q 'Host ssh.dev.azure.com' /home/pi/.ssh/config && "
                "grep -q 'IdentityFile /home/pi/.ssh/id_rsa_pidocker_azure' /home/pi/.ssh/config && "
                "grep -q 'Host github.com' /home/pi/.ssh/config && "
                "grep -q 'IdentityFile /home/pi/.ssh/id_ed25519_pidocker_github' /home/pi/.ssh/config && "
                "grep -q 'StrictHostKeyChecking accept-new' /home/pi/.ssh/config && "
                "test ! -e /Users/kaufdev/.ssh",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        assert "already exists" in second_result.stdout
        assert "Updated SSH config" in second_result.stdout
    finally:
        remove_docker_volumes(home_volume, workspace_volume)


def test_pidocker_ssh_setup_updates_legacy_managed_config_without_removing_custom_hosts():
    volume_prefix = f"pidocker-test-{uuid.uuid4().hex}"
    home_volume = f"{volume_prefix}-home"
    workspace_volume = f"{volume_prefix}-workspace"

    subprocess.run(
        ["docker", "build", "-t", TEST_IMAGE, str(DOCKER_CONTEXT)],
        cwd=REPO_ROOT,
        check=True,
    )

    try:
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
                "mkdir -p /home/pi/.ssh && "
                "ssh-keygen -t ed25519 -f /home/pi/.ssh/id_ed25519_pidocker -N '' >/dev/null && "
                "cat > /home/pi/.ssh/config <<'EOF'\n"
                "Host ssh.dev.azure.com\n"
                "  IdentityFile /home/pi/.ssh/id_ed25519_pidocker\n"
                "  IdentitiesOnly yes\n"
                "\n"
                "Host internal.example.com\n"
                "  User custom\n"
                "\n"
                "Host github.com\n"
                "  IdentityFile /home/pi/.ssh/id_ed25519_pidocker\n"
                "  IdentitiesOnly yes\n"
                "EOF\n"
                "pidocker-ssh-setup >/dev/null && cat /home/pi/.ssh/config",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        config = result.stdout
        assert "Host internal.example.com" in config
        assert "User custom" in config
        assert "IdentityFile /home/pi/.ssh/id_rsa_pidocker_azure" in config
        assert "IdentityFile /home/pi/.ssh/id_ed25519_pidocker_github" in config
        assert "  IdentityFile /home/pi/.ssh/id_ed25519_pidocker\n" not in config
    finally:
        remove_docker_volumes(home_volume, workspace_volume)


def test_dedicated_pidocker_ssh_key_can_be_generated_and_persists_in_home_volume():
    volume_prefix = f"pidocker-test-{uuid.uuid4().hex}"
    home_volume = f"{volume_prefix}-home"
    workspace_volume = f"{volume_prefix}-workspace"
    key_path = "/home/pi/.ssh/id_ed25519_pidocker"

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
                f"mkdir -p /home/pi/.ssh && ssh-keygen -t ed25519 -f {key_path} -N ''",
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
                f"test -f {key_path} && test -f {key_path}.pub && test ! -e /Users/kaufdev/.ssh && cat {key_path}.pub",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        assert result.stdout.startswith("ssh-ed25519 ")
    finally:
        remove_docker_volumes(home_volume, workspace_volume)


@pytest.mark.integration
def test_azure_devops_clone_uses_dedicated_pidocker_ssh_key_and_workspace_repo_path():
    azure_repo_url = os.environ.get("PIDOCKER_AZURE_DEVOPS_SSH_URL")
    if not azure_repo_url:
        pytest.skip("set PIDOCKER_AZURE_DEVOPS_SSH_URL=git@ssh.dev.azure.com:v3/org/project/repo")

    repo_name = os.environ.get("PIDOCKER_AZURE_DEVOPS_REPO_NAME") or azure_repo_url.rstrip("/").split("/")[-1]
    volume_prefix = f"pidocker-test-{uuid.uuid4().hex}"
    home_volume = f"{volume_prefix}-home"
    workspace_volume = f"{volume_prefix}-workspace"
    clone_path = f"/workspace/repos/{repo_name}"

    subprocess.run(
        ["docker", "build", "-t", TEST_IMAGE, str(DOCKER_CONTEXT)],
        cwd=REPO_ROOT,
        check=True,
    )

    try:
        setup_result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--volume",
                f"{home_volume}:/home/pi",
                "--volume",
                f"{workspace_volume}:/workspace",
                TEST_IMAGE,
                "pidocker-ssh-setup",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        assert "Public key to add in Azure DevOps:" in setup_result.stdout
        assert "ssh-rsa " in setup_result.stdout

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
                "git",
                "clone",
                azure_repo_url,
                clone_path,
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
                f"test -d {clone_path}/.git && git -C {clone_path} remote get-url origin",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        assert result.stdout.strip() == azure_repo_url
    finally:
        remove_docker_volumes(home_volume, workspace_volume)


def test_git_push_wrapper_blocks_destructive_pushes_but_allows_normal_push():
    volume_prefix = f"pidocker-test-{uuid.uuid4().hex}"
    home_volume = f"{volume_prefix}-home"
    workspace_volume = f"{volume_prefix}-workspace"

    subprocess.run(
        ["docker", "build", "-t", TEST_IMAGE, str(DOCKER_CONTEXT)],
        cwd=REPO_ROOT,
        check=True,
    )

    try:
        setup_script = (
            "set -euo pipefail && "
            "git init --bare /workspace/origin.git && "
            "git clone /workspace/origin.git /workspace/repos/push-test && "
            "cd /workspace/repos/push-test && "
            "git config user.email pi@example.invalid && "
            "git config user.name pidocker && "
            "echo ok > README.md && "
            "git add README.md && "
            "git commit -m initial"
        )
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
                setup_script,
            ],
            cwd=REPO_ROOT,
            check=True,
        )

        forbidden_pushes = [
            "git push --force origin HEAD:test-force",
            "git push --force-with-lease origin HEAD:test-force-with-lease",
            "git push --mirror origin",
            "git push origin :some-branch",
        ]
        for command in forbidden_pushes:
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
                    f"cd /workspace/repos/push-test && {command}",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            assert result.returncode != 0, command
            assert "pidocker: force push is disabled" in result.stderr

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
                "cd /workspace/repos/push-test && git push origin HEAD:test-branch",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        assert "test-branch" in result.stderr
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
