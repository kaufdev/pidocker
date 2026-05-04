---
name: pidocker-task-09
description: "Pidocker MVP task 9: Zwykłe `pidocker` odpala interaktywne Pi. Use when implementing, testing, or reviewing this specific pidocker task."
---

# Task 9: Zwykłe `pidocker` odpala interaktywne Pi

Before using this task skill, load the shared workflow if it is not already in context:

```text
/skill:pidocker-task-flow
```

## 9. Zwykłe `pidocker` odpala interaktywne Pi

- [x] Zrobione

### Wymaganie

Uruchomienie bez argumentów:

```bash
pidocker
```

odpala interaktywne `pi` w kontenerze.

### Dowód spełnienia

Użytkownik widzi interfejs Pi i może wpisać komendę/slash-command.

### Test automatyczny

Automatycznie sprawdzamy tylko techniczne minimum:

- obraz zawiera `pi`,
- wrapper uruchamia kontener z właściwym entrypointem/commandem,
- test statyczny potwierdza, że domyślną komendą jest `pi`.

Pełny interaktywny test zostaje ręczny.

### Ręczny test właściciela

```bash
pidocker
```

Oczekiwane: otwiera się Pi działające w kontenerze.

---

