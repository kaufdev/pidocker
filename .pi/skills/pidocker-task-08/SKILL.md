---
name: pidocker-task-08
description: "Pidocker MVP task 8: Obraz zawiera komendę `pi`. Use when implementing, testing, or reviewing this specific pidocker task."
---

# Task 8: Obraz zawiera komendę `pi`

Before using this task skill, load the shared workflow if it is not already in context:

```text
/skill:pidocker-task-flow
```

## 8. Obraz zawiera komendę `pi`

- [ ] Zrobione

### Wymaganie

W kontenerze dostępna jest komenda:

```bash
pi
```

### Dowód spełnienia

Po wejściu do kontenera:

```bash
command -v pi
```

zwraca ścieżkę do binarki/skryptu `pi`.

### Test automatyczny

Test buduje obraz i sprawdza:

```bash
command -v pi
```

Opcjonalnie, jeśli stabilne:

```bash
pi --version
```

### Ręczny test właściciela

Preferowany test:

```bash
pidocker
```

Oczekiwane: otwiera się Pi.

Jeżeli trzeba sprawdzić technicznie:

1. Wejdź do kontenera.
2. W środku wykonaj:

```bash
command -v pi
pi --version || true
```

---

