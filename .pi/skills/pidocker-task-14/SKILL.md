---
name: pidocker-task-14
description: "Pidocker MVP task 14: Git clone z Azure DevOps przez dedykowany SSH key. Use when implementing, testing, or reviewing this specific pidocker task."
---

# Task 14: Git clone z Azure DevOps przez dedykowany SSH key

Before using this task skill, load the shared workflow if it is not already in context:

```text
/skill:pidocker-task-flow
```

## 14. Git clone z Azure DevOps przez dedykowany SSH key

- [ ] Zrobione

### Wymaganie

Po dodaniu publicznego klucza do Azure DevOps kontener może wykonać:

```bash
git clone git@ssh.dev.azure.com:v3/org/project/repo /workspace/repos/repo
```

### Dowód spełnienia

Repo z Azure DevOps istnieje w:

```text
/workspace/repos/<repo>/.git
```

### Test automatyczny

Test automatyczny oznaczony jako integration, bo wymaga:

- sieci,
- dostępu do Azure DevOps,
- skonfigurowanego SSH key.

### Ręczny test właściciela

1. Upewnij się, że publiczny klucz z `/home/pi/.ssh/id_ed25519_pidocker.pub` jest dodany w Azure DevOps.
2. Uruchom `pidocker`.
3. Wejdź do kontenera.
4. W środku wykonaj:

```bash
ssh -T git@ssh.dev.azure.com || true
git clone git@ssh.dev.azure.com:v3/<org>/<project>/<repo> /workspace/repos/<repo>
ls -la /workspace/repos/<repo>/.git
```

---

