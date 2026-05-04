---
name: pidocker-task-00
description: "Pidocker MVP task 0: Setup projektu i test harness. Use when implementing, testing, or reviewing this specific pidocker task."
---

# Task 0: Setup projektu i test harness

Before using this task skill, load the shared workflow if it is not already in context:

```text
/skill:pidocker-task-flow
```

## 0. Setup projektu i test harness

- [x] Zrobione

### Wymaganie

Repo ma minimalną strukturę pod implementację i testy:

```text
bin/pidocker
docker/Dockerfile
tests/
README.md
PIDOCKER_MVP.md
PIDOCKER_TASKS.md
```

Testy są odpalane z hosta, nie z wnętrza kontenera.

### Dowód spełnienia

```bash
pytest tests/
```

przechodzi.

### Test automatyczny

Minimalny test sanity sprawdza, że wymagane pliki istnieją.

### Ręczny test właściciela

```bash
pytest tests/
pidocker --help
```

---

