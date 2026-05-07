---
name: pidocker-task-flow
description: Pidocker development, test handoff, and Homebrew release workflow. Use for pidocker code changes, local manual testing, and brew deployment.
---

# Pidocker Task Flow

## Rules

- No `pidocker --exec`; manual tests use installed commands.
- Do not edit shell rc/config for local testing. Prefer `pidocker-dev`.
- If anything outside the repo is changed, record it and revert it before release.
- Fix failing implementation; do not weaken tests unless requirements changed.

## Change workflow

1. Clarify the requirement enough to implement.
2. Change project files.
3. Commit the coherent change before test/debug loops.
4. Run automated tests.
5. If tests fail, fix code/config/docs, then amend or add a follow-up commit.
6. Prepare local manual test command:

```bash
docker build -t pidocker:local docker
mkdir -p ~/.local/bin
ln -sf "$PWD/bin/pidocker" ~/.local/bin/pidocker-dev
pidocker-dev --help
```

7. Ask user to test with `pidocker-dev ...`.
8. After approval, push the default branch (`main` in this repo) and run Homebrew release.

## Homebrew release

1. Ensure pidocker tree is clean and tests passed.
2. Tag next version, e.g. `v0.1.3`.
3. Push default branch and tag.
4. Download tag tarball and calculate SHA-256.
5. Update `kaufdev/homebrew-pidocker/Formula/pidocker.rb`:
   - `url` -> new tag tarball,
   - `sha256` -> new digest,
   - keep `pidocker:v#{version}` image behavior.
6. Run `brew audit --strict --online kaufdev/pidocker/pidocker` and `brew fetch`.
7. Commit and push the tap.
8. Tell user: `brew update && brew upgrade pidocker`.

## Useful commands

```bash
./.venv/bin/pytest tests/
git status --short
git rev-parse --short HEAD
git tag v0.1.3
git push origin main && git push origin v0.1.3

tmp=$(mktemp)
curl -LfsS -o "$tmp" https://github.com/kaufdev/pidocker/archive/refs/tags/v0.1.3.tar.gz
shasum -a 256 "$tmp"
rm "$tmp"
```

## Inspect running container

```bash
docker ps --filter "label=app=pidocker" --format "table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}"
docker exec -it <CONTAINER_ID> bash
```
