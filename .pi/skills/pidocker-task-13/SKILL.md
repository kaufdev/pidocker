---
name: pidocker-task-13
description: "Pidocker MVP task 13: Git clone do `/workspace/repos`. Use when implementing, testing, or reviewing this specific pidocker task."
---

# Task 13: Git clone do `/workspace/repos`

Before using this task skill, load the shared workflow if it is not already in context:

```text
/skill:pidocker-task-flow
```

## 13. Git clone do `/workspace/repos`

- [ ] Zrobione

### Wymaganie

Repozytoria są klonowane do:

```text
/workspace/repos
```

Nie kopiujemy lokalnych repo z hosta.

### Dowód spełnienia

Repo po sklonowaniu istnieje w:

```text
/workspace/repos/<repo>/.git
```

### Test automatyczny

Test podstawowy może klonować małe publiczne repo albo używać lokalnego bare repo przygotowanego przez test harness.

Test wymagający internetu oznaczamy jako integration.

### Ręczny test właściciela

1. Uruchom `pidocker`.
2. Wejdź do kontenera.
3. W środku wykonaj:

```bash
git clone https://github.com/octocat/Hello-World.git /workspace/repos/manual-hello-world
ls -la /workspace/repos/manual-hello-world/.git
```

4. Zamknij i uruchom ponownie `pidocker`.
5. Wejdź do kontenera i sprawdź:

```bash
ls -la /workspace/repos/manual-hello-world/.git
```

---

