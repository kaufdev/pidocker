---
name: pidocker-task-04
description: "Pidocker MVP task 4: Volume `pidocker-home` persystuje `/home/pi`. Use when implementing, testing, or reviewing this specific pidocker task."
---

# Task 4: Volume `pidocker-home` persystuje `/home/pi`

Before using this task skill, load the shared workflow if it is not already in context:

```text
/skill:pidocker-task-flow
```

## 4. Volume `pidocker-home` persystuje `/home/pi`

- [x] Zrobione

### Wymaganie

Dane zapisane w `/home/pi` zostają między uruchomieniami kontenera.

Volume:

```text
pidocker-home -> /home/pi
```

### Dowód spełnienia

Po zapisaniu pliku w `/home/pi`, zamknięciu `pidocker` i ponownym uruchomieniu, plik nadal istnieje.

### Test automatyczny

Test:

1. używa testowego prefixu volume, np. `PIDOCKER_VOLUME_PREFIX=pidocker-test`,
2. zapisuje plik w `/home/pi` przez krótkotrwały kontener testowy,
3. uruchamia kontener ponownie,
4. sprawdza, że plik istnieje.

### Ręczny test właściciela

Pierwsze uruchomienie:

1. Uruchom `pidocker`.
2. Wejdź do kontenera.
3. W środku wykonaj:

```bash
date > /home/pi/manual-home-test.txt
cat /home/pi/manual-home-test.txt
```

4. Wyjdź z kontenera i zamknij `pidocker`.

Drugie uruchomienie:

1. Uruchom ponownie `pidocker`.
2. Wejdź do kontenera.
3. W środku wykonaj:

```bash
cat /home/pi/manual-home-test.txt
```

Oczekiwane: plik istnieje i ma poprzednią zawartość.

---

