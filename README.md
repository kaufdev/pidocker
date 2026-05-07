# pidocker

`pidocker` runs Pi inside an isolated Docker container. The container uses only the named volumes `pidocker-home` and `pidocker-workspace`; it does not mount private host directories or the Docker socket.

## Requirements

- Docker installed and available on the host.
- Network access for installing Pi and related packages during the image build.

## Install

Install with Homebrew:

```bash
brew tap kaufdev/pidocker
brew install pidocker
```

Docker Desktop, OrbStack, Colima, or another Docker daemon must be running before starting `pidocker`.

Verify the installed command:

```bash
which pidocker
pidocker --help
```

## Build the image

The first `pidocker` run builds the Docker image automatically if `pidocker:local` does not exist. The Docker build output is expected on first run and is useful for troubleshooting.

To build manually from the repository root:

```bash
docker build -t pidocker:local docker
```

Override the image name with `PIDOCKER_IMAGE` if needed.

## Local development install

For development, symlink the repository script into a directory on your `PATH`:

```bash
mkdir -p ~/.local/bin
ln -sf "$(pwd)/bin/pidocker" ~/.local/bin/pidocker
```

To update a local development install, pull the latest repository changes and rebuild the image:

```bash
git pull
docker build -t pidocker:local docker
```

## Run Pi

Start an interactive Pi session:

```bash
pidocker
```

By default the wrapper starts a container with the label `app=pidocker`, mounts the named volumes, starts in `/workspace/repos`, and runs `pi`.

Start directly inside an existing repository so Pi loads that repository's `AGENTS.md` and skills:

```bash
pidocker monorepo
```

This starts Pi in `/workspace/repos/monorepo`.

Clone a new GitHub or Azure DevOps repository into `/workspace/repos` and start Pi there:

```bash
pidocker git@ssh.dev.azure.com:v3/ORG/PROJECT/REPO
pidocker git@github.com:ORG/REPO.git
```

If the repository directory already exists, `pidocker` reuses it instead of cloning again.

Inside Pi, log in with:

```text
/login
```

Pi authentication files and `/resume` sessions are stored in `pidocker-home`, so they survive container restarts.

## Azure CLI context

The image includes the Azure CLI (`az`) so Pi can inspect and manage Azure resources from inside the container.

```bash
az --version
az login
```

Azure CLI configuration and login state under `/home/pi/.azure` are stored in `pidocker-home`, so the Azure context survives container restarts.

## Enter the running container manually

Terminal 1:

```bash
pidocker
```

Terminal 2:

```bash
docker ps --filter "label=app=pidocker" --format "table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}"
docker exec -it <CONTAINER_ID> bash
```

Useful checks inside the container:

```bash
whoami
pwd
ls -la /home/pi
ls -la /workspace
```

## SSH keys for Git and Azure DevOps

Generate dedicated keys inside `pidocker-home`:

```bash
pidocker setupssh
```

The command creates a dedicated Azure DevOps key at `/home/pi/.ssh/id_rsa_pidocker_azure` and prints the public key. Add that public key in Azure DevOps:

```text
User settings -> SSH public keys -> New Key
```

Then clone repositories into `/workspace/repos` with `pidocker GIT_URL`:

```bash
pidocker git@ssh.dev.azure.com:v3/ORG/PROJECT/REPO
```

You can also clone manually from inside the container:

```bash
git clone git@ssh.dev.azure.com:v3/ORG/PROJECT/REPO /workspace/repos/REPO
```

## Shell completion

`pidocker` can print shell completion that suggests command names and existing directories under `/workspace/repos`.

Bash:

```bash
eval "$(pidocker completion bash)"
```

Zsh:

```bash
pidocker completion zsh > ~/.zfunc/_pidocker
```

Make sure `~/.zfunc` is on your `fpath`.

## Notion token

Store a Notion token with the installed `pidocker` command:

```bash
pidocker secrets set NOTION_API_KEY
```

The secret is stored in the sandboxed `pidocker-home` volume at `/home/pi/.pidocker/secrets/env` and `/home/pi/.pidocker/secrets/notion.env`. On startup, `pidocker` loads those values as environment variables for Pi.

## Volumes and reset

`pidocker` uses two named volumes:

- `pidocker-home` -> `/home/pi`: Pi auth, sessions, SSH keys, secrets, and configuration.
- `pidocker-workspace` -> `/workspace`: repositories and working files, including `/workspace/repos`.

Reset the environment by removing both volumes:

```bash
docker volume rm -f pidocker-home pidocker-workspace
```

After a reset, run `/login`, `pidocker setupssh`, and secret setup again.

## Host isolation and security

The container must not see private host paths such as the user's home directory, local project directories, `~/.ssh`, `~/.aws`, `~/.kube`, package-manager credentials, or `/var/run/docker.sock`. The wrapper must not use `--privileged`, `--pid=host`, or `--network=host`.

Do not mount private host files into the container. Store persistent data only in `pidocker-home` or `pidocker-workspace`.

## Git push and force push

A local `git` wrapper inside the container blocks destructive pushes such as `force push`, `--force-with-lease`, `--mirror`, and remote ref deletion. Force push should also be blocked by the Git provider, for example with branch policies or protected branches in Azure DevOps or GitHub.

A normal push is allowed:

```bash
git push origin HEAD:your-branch
```

## Development

Install development dependencies and run tests from the host:

```bash
python -m pip install -r requirements-dev.txt
pytest tests/
```
