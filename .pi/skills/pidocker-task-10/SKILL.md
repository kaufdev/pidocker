---
name: pidocker-task-10
description: "Pidocker MVP task 10: `/login` zapisuje auth w `pidocker-home`. Use when implementing, testing, or reviewing this specific pidocker task."
---

# Task 10: `/login` zapisuje auth w `pidocker-home`

Before using this task skill, load the shared workflow if it is not already in context:

```text
/skill:pidocker-task-flow
```

## 10. `/login` zapisuje auth w `pidocker-home`

- [ ] Zrobione

### Wymaganie

Login do Pi wykonywany jest wewnątrz kontenera.

Auth zapisuje się w:

```text
/home/pi/.pi/agent/auth.json
```

Plik zostaje między uruchomieniami, bo `/home/pi` jest volume.

### Dowód spełnienia

Po wykonaniu `/login` plik istnieje w kontenerze:

```text
/home/pi/.pi/agent/auth.json
```

### Test automatyczny

Test techniczny bez prawdziwego loginu:

1. tworzy `/home/pi/.pi/agent/auth.json` w testowym volume,
2. restartuje kontener,
3. sprawdza, że plik istnieje.

Prawdziwy `/login` jest testem ręcznym/integracyjnym.

### Ręczny test właściciela

1. Uruchom:

```bash
pidocker
```

2. W Pi wykonaj:

```text
/login
```

3. Po zalogowaniu wejdź do kontenera i sprawdź:

```bash
ls -la /home/pi/.pi/agent/auth.json
```

4. Zamknij `pidocker`, uruchom ponownie `pidocker` i potwierdź, że nie trzeba logować się od nowa.

---

