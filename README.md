# pidocker

`pidocker` runs Pi inside an isolated Docker container. The container uses only the named volumes `pidocker-home` and `pidocker-workspace`; it does not mount private host directories or the Docker socket.

## Requirements

- Docker installed and available on the host.
- Network access for installing Pi and related packages during the image build.

## Build the image

From the repository root:

```bash
docker build -t pidocker:local docker
```

The `pidocker` wrapper also builds the image automatically if `pidocker:local` does not exist. Override the image name with `PIDOCKER_IMAGE` if needed.

## Install or update the `pidocker` command

For a local installation, symlink the repository script into a directory on your `PATH`:

```bash
mkdir -p ~/.local/bin
ln -sf "$(pwd)/bin/pidocker" ~/.local/bin/pidocker
```

Verify the installed command:

```bash
which pidocker
pidocker --help
```

To update, pull the latest repository changes and rebuild the image:

```bash
git pull
docker build -t pidocker:local docker
```

If you install `pidocker` somewhere else, update that file or symlink so it points to the version you want to run.

## Run Pi

Start an interactive Pi session:

```bash
pidocker
```

By default the wrapper starts a container with the label `app=pidocker`, mounts the named volumes, starts in `/workspace/repos`, and runs `pi`.

Inside Pi, log in with:

```text
/login
```

Pi authentication files and `/resume` sessions are stored in `pidocker-home`, so they survive container restarts.

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

Then clone repositories into `/workspace/repos`, for example from inside the container:

```bash
git clone git@ssh.dev.azure.com:v3/ORG/PROJECT/REPO /workspace/repos/REPO
```

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
