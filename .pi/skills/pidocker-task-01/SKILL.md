---
name: pidocker-task-01
description: "Pidocker MVP task 1: Komenda `pidocker` jest dostępna z hosta. Use when implementing, testing, or reviewing this specific pidocker task."
---

# Task 1: Komenda `pidocker` jest dostępna z hosta

Before using this task skill, load the shared workflow if it is not already in context:

```text
/skill:pidocker-task-flow
```

## 1. Komenda `pidocker` jest dostępna z hosta

- [x] Zrobione

### Wymaganie

Istnieje wykonywalny plik projektu:

```text
bin/pidocker
```

oraz jest dostępna docelowa komenda z hosta:

```bash
pidocker
```

W testach automatycznych można używać `./bin/pidocker`, żeby testować wersję z repo bez instalacji globalnej.

W testach ręcznych właściciel używa zainstalowanej komendy `pidocker`.

### Dowód spełnienia

```bash
pidocker --help
```

zwraca opis użycia i exit code `0`.

### Test automatyczny

Test sprawdza, że:

- `bin/pidocker` istnieje,
- jest wykonywalny,
- `./bin/pidocker --help` kończy się sukcesem.

### Ręczny test właściciela

```bash
which pidocker
pidocker --help
```

---

