---
name: pidocker-task-06
description: "Pidocker MVP task 6: Kontener nie widzi prywatnych plików hosta. Use when implementing, testing, or reviewing this specific pidocker task."
---

# Task 6: Kontener nie widzi prywatnych plików hosta

Before using this task skill, load the shared workflow if it is not already in context:

```text
/skill:pidocker-task-flow
```

## 6. Kontener nie widzi prywatnych plików hosta

- [x] Zrobione

### Wymaganie

Kontener domyślnie nie ma dostępu do:

```text
/Users/kaufdev
/Users/kaufdev/projects
/Users/kaufdev/.ssh
/Users/kaufdev/.aws
/Users/kaufdev/.kube
/Users/kaufdev/.config
/Users/kaufdev/.npmrc
/Users/kaufdev/.m2
/var/run/docker.sock
```

### Dowód spełnienia

Po wejściu do kontenera poniższe komendy przechodzą:

```bash
test ! -e /Users/kaufdev
test ! -S /var/run/docker.sock
```

### Test automatyczny

Test sprawdza przez `docker run`/`docker inspect`, że zabronione ścieżki nie są montowane.

Dodatkowo test może sprawdzić mounty działającego kontenera i upewnić się, że zawierają tylko oczekiwane volumes.

### Ręczny test właściciela

1. Uruchom `pidocker`.
2. Wejdź do kontenera.
3. W środku wykonaj:

```bash
ls -la /Users || true
test ! -e /Users/kaufdev
test ! -e /Users/kaufdev/projects
test ! -e /Users/kaufdev/.ssh
test ! -S /var/run/docker.sock
```

Oczekiwane: testy kończą się sukcesem.

---

