---
name: pidocker-task-03
description: "Pidocker MVP task 3: Dockerfile tworzy usera non-root. Use when implementing, testing, or reviewing this specific pidocker task."
---

# Task 3: Dockerfile tworzy usera non-root

Before using this task skill, load the shared workflow if it is not already in context:

```text
/skill:pidocker-task-flow
```

## 3. Dockerfile tworzy usera non-root

- [x] Zrobione

### Wymaganie

Kontener działa jako zwykły user `pi`, nie jako `root`.

W kontenerze istnieją katalogi:

```text
/home/pi
/workspace
/workspace/repos
```

### Dowód spełnienia

Po wejściu do działającego kontenera:

```bash
id -u
whoami
test -d /home/pi
test -d /workspace/repos
```

`whoami` zwraca `pi`, a `id -u` nie zwraca `0`.

### Test automatyczny

Test buduje obraz i odpala krótką komendę przez `docker run`, sprawdzając:

```bash
id -u
whoami
test -d /home/pi
test -d /workspace/repos
```

### Ręczny test właściciela

Terminal 1:

```bash
pidocker
```

Terminal 2, po wejściu do kontenera:

```bash
id
whoami
ls -ld /home/pi /workspace /workspace/repos
```

---

