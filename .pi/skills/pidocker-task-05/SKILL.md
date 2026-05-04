---
name: pidocker-task-05
description: "Pidocker MVP task 5: Volume `pidocker-workspace` persystuje `/workspace`. Use when implementing, testing, or reviewing this specific pidocker task."
---

# Task 5: Volume `pidocker-workspace` persystuje `/workspace`

Before using this task skill, load the shared workflow if it is not already in context:

```text
/skill:pidocker-task-flow
```

## 5. Volume `pidocker-workspace` persystuje `/workspace`

- [x] Zrobione

### Wymaganie

Dane zapisane w `/workspace/repos` zostają między uruchomieniami kontenera.

Volume:

```text
pidocker-workspace -> /workspace
```

### Dowód spełnienia

Po zapisaniu pliku w `/workspace/repos`, zamknięciu `pidocker` i ponownym uruchomieniu, plik nadal istnieje.

### Test automatyczny

Test:

1. używa testowego prefixu volume,
2. zapisuje plik w `/workspace/repos`,
3. uruchamia kontener ponownie,
4. sprawdza, że plik istnieje.

### Ręczny test właściciela

Pierwsze uruchomienie:

1. Uruchom `pidocker`.
2. Wejdź do kontenera.
3. W środku wykonaj:

```bash
mkdir -p /workspace/repos/manual
echo ok > /workspace/repos/manual/test.txt
cat /workspace/repos/manual/test.txt
```

4. Wyjdź z kontenera i zamknij `pidocker`.

Drugie uruchomienie:

1. Uruchom ponownie `pidocker`.
2. Wejdź do kontenera.
3. W środku wykonaj:

```bash
cat /workspace/repos/manual/test.txt
```

Oczekiwane: zwraca `ok`.

---

