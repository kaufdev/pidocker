---
name: pidocker-task-15
description: "Pidocker MVP task 15: Git push działa bez force push. Use when implementing, testing, or reviewing this specific pidocker task."
---

# Task 15: Git push działa bez force push

Before using this task skill, load the shared workflow if it is not already in context:

```text
/skill:pidocker-task-flow
```

## 15. Git push działa bez force push

- [x] Zrobione

### Wymaganie

Agent może używać:

```text
git push
```

ale nie może używać:

```text
git push --force
git push --force-with-lease
git push --mirror
git push origin :branch
```

Lokalna blokada w wrapperze/hooku jest pomocnicza. Główna ochrona powinna być też ustawiona po stronie Azure DevOps/GitHub.

### Dowód spełnienia

Zakazane komendy kończą się błędem, np.:

```text
pidocker: force push is disabled
```

Zwykły push działa.

### Test automatyczny

Test na repo testowym sprawdza:

- `git push --force` kończy się exit code != 0,
- `git push --force-with-lease` kończy się exit code != 0,
- `git push --mirror` kończy się exit code != 0,
- `git push origin :some-branch` kończy się exit code != 0,
- zwykły `git push origin HEAD:test-branch` działa.

### Ręczny test właściciela

1. Uruchom `pidocker`.
2. Wejdź do kontenera.
3. Przejdź do testowego repo:

```bash
cd /workspace/repos/<repo>
```

4. Sprawdź zakazany push:

```bash
git push --force
```

Oczekiwane: komenda jest zablokowana.

5. Sprawdź zwykły push na testowy branch:

```bash
git push origin HEAD:test-pidocker-branch
```

Oczekiwane: zwykły push działa.

---

