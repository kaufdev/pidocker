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
4. Install or update the local `pidocker` command to point at the tested commit.
5. Run the manual test with the installed `pidocker` command.

Before handing off a manual test, record:

- commit hash,
- how the local `pidocker` command was installed or updated,
- whether the image or volumes need to be rebuilt/reset.

Useful commands:

```bash
git rev-parse --short HEAD
which pidocker
pidocker --help
```
