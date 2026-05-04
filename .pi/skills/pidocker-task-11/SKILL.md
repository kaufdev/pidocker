---
name: pidocker-task-11
description: "Pidocker MVP task 11: Sesje Pi `/resume` są persystentne. Use when implementing, testing, or reviewing this specific pidocker task."
---

# Task 11: Sesje Pi `/resume` są persystentne

Before using this task skill, load the shared workflow if it is not already in context:

```text
/skill:pidocker-task-flow
```

## 11. Sesje Pi `/resume` są persystentne

- [ ] Zrobione

### Wymaganie

Sesje Pi są zapisywane w:

```text
/home/pi/.pi/agent/sessions/
```

i zostają między uruchomieniami.

### Dowód spełnienia

Po rozpoczęciu sesji i ponownym uruchomieniu `pidocker`, `/resume` pokazuje poprzednie sesje.

### Test automatyczny

Test techniczny:

1. tworzy plik w `/home/pi/.pi/agent/sessions/` w testowym volume,
2. restartuje kontener,
3. sprawdza, że plik istnieje.

### Ręczny test właściciela

1. Uruchom:

```bash
pidocker
```

2. Rozpocznij krótką rozmowę.
3. Wyjdź z Pi.
4. Uruchom ponownie:

```bash
pidocker
```

5. Użyj:

```text
/resume
```

Oczekiwane: poprzednia sesja jest dostępna.

---

