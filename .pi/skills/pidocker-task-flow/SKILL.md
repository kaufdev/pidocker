---
name: pidocker-task-flow
description: "Workflow, release checklist, manual testing rules, and instructions for entering a running pidocker container."
---

# Pidocker Task Flow

Use this checklist when preparing a release or handing changes over for manual testing.

## Manual testing rule

Do not add or use a `pidocker --exec` interface. Manual testing should use the installed command:

```bash
pidocker
```

If you need to inspect files or run commands inside the container, start `pidocker` normally and then enter the running container with Docker.

## Enter a running pidocker container

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

If no container is found with label `app=pidocker`, the installed command is not starting the expected container.

## Change workflow

1. Make the code/configuration change.
2. Run automated tests.
3. Commit the change.
4. If the change should reach Homebrew users, run the Homebrew release workflow below.
5. Install or update the local `pidocker` command to point at the tested commit or released Homebrew formula.
6. Run the manual test with the installed `pidocker` command.

Before handing off a manual test, record:

- commit hash,
- release tag, if published,
- Homebrew tap commit hash, if published,
- how the local `pidocker` command was installed or updated,
- whether the image or volumes need to be rebuilt/reset.

## Homebrew release workflow

Use this when a committed pidocker change should be available after `brew update` and `brew upgrade pidocker`.

1. Confirm the pidocker working tree is clean and tests have passed.
2. Create the next version tag in `kaufdev/pidocker`, for example `v0.1.2`.
3. Push both `main` and the tag.
4. Download the GitHub tag tarball and calculate its SHA-256.
5. Update `kaufdev/homebrew-pidocker` formula:
   - change `url` to the new tag tarball,
   - change `sha256` to the calculated digest,
   - keep the formula's versioned image tag behavior so upgrades build a fresh image, for example `pidocker:v#{version}`.
6. Commit and push the Homebrew tap update.
7. Tell the user to run `brew update` and `brew upgrade pidocker`. `brew update` refreshes the tap, but `brew upgrade pidocker` installs the updated formula.

Useful release commands:

```bash
# pidocker repo
git status --short
git rev-parse --short HEAD
git tag v0.1.2
git push origin main
git push origin v0.1.2

# calculate formula sha256
tmp=$(mktemp)
curl -LfsS -o "$tmp" https://github.com/kaufdev/pidocker/archive/refs/tags/v0.1.2.tar.gz
sha256sum "$tmp"
rm "$tmp"

# homebrew-pidocker repo
git status --short
git diff -- Formula/pidocker.rb
git diff --check
git add Formula/pidocker.rb
git commit -m "Update pidocker to v0.1.2"
git push origin main
```

Useful manual-test commands:

```bash
git rev-parse --short HEAD
which pidocker
pidocker --help
brew update
brew upgrade pidocker
pidocker
```
