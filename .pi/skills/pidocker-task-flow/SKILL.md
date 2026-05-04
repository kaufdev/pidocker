---
name: pidocker-task-flow
description: "Pidocker MVP workflow, Definition of Done, manual testing rules, and instructions for entering the running pidocker container. Use before starting or finishing any pidocker task."
---

# Pidocker Task Flow

Ten plik jest checklistą realizacji MVP z `PIDOCKER_MVP.md`.

Każde zadanie ma:

- konkretne wymaganie,
- dowód spełnienia,
- test automatyczny / półautomatyczny,
- ręczny test końcowy.

Zadanie uznajemy za zakończone dopiero po przejściu całego flow.

---

## Ważna zasada ręcznych testów

W ręcznych testach **nie używamy** trybu typu:

```bash
pidocker --exec '...'
```

Nie chcemy takiego interfejsu w produkcie ani w ręcznej weryfikacji.

Ręczne testy robimy na jeden z dwóch sposobów:

1. **Preferowany sposób:** samo uruchomienie:

   ```bash
   pidocker
   ```

   Jeżeli odpalenie Pi wystarcza do potwierdzenia zadania, używamy tylko tego.

2. **Gdy trzeba sprawdzić system plików albo komendy w kontenerze:** uruchamiamy `pidocker`, a potem samodzielnie wchodzimy do działającego kontenera przez Dockera.

---

## Jak ręcznie wejść do kontenera pidocker

Używamy tego tylko w zadaniach, gdzie trzeba sprawdzić coś technicznego wewnątrz kontenera.

### Terminal 1

Uruchom normalnie:

```bash
pidocker
```

Zostaw ten proces uruchomiony.

### Terminal 2

Znajdź kontener:

```bash
docker ps --filter "label=app=pidocker" --format "table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}"
```

Wejdź do środka:

```bash
docker exec -it <CONTAINER_ID> bash
```

W środku możesz sprawdzać np.:

```bash
whoami
pwd
ls -la /home/pi
ls -la /workspace
```

Po skończeniu:

```bash
exit
```

Jeśli kontenera nie da się znaleźć po labelu `app=pidocker`, zadanie dotyczące uruchamiania kontenera nie jest spełnione.

---

## Flow realizacji każdego zadania

Dla każdego zadania obowiązuje taki cykl:

```text
1. Zmiana w kodzie / konfiguracji
2. Testy automatyczne
3. Commit
4. Przygotowanie i instalacja testowanej wersji pidocker
5. Ręczny test przez właściciela projektu
6. Zaznaczenie checkboxa jako zrobione
```

### 1. Zmiana

Implementujemy tylko zakres danego zadania.

Nie dokładamy przy okazji dużych zmian spoza zadania, chyba że są konieczne i jasno opisane.

### 2. Testy

Przed commitem muszą przejść testy automatyczne przypisane do zadania.

Docelowo:

```bash
pytest tests/
```

Jeśli zadanie ma test integracyjny wymagający sieci, auth albo zewnętrznego serwisu, oznaczamy go osobno, np.:

```bash
pytest -m integration
```

Testy automatyczne mogą używać `./bin/pidocker`, `docker build`, `docker run`, `docker inspect` itd. Ręczny test właściciela ma używać zainstalowanej komendy `pidocker`.

### 3. Commit

Po przejściu testów robimy commit.

Przykład:

```bash
git add .
git commit -m "Add pidocker container runner"
```

### 4. Przygotowanie i instalacja testowanej wersji

Przed ręcznym testem właściciel projektu musi mieć przygotowaną i zainstalowaną odpowiednią wersję `pidocker`.

Oznacza to, że komenda:

```bash
pidocker
```

ma wskazywać na wersję odpowiadającą commitowi, który ma być testowany ręcznie.

Przed przekazaniem zadania do ręcznego testu zapisujemy:

- commit hash,
- sposób instalacji albo aktualizacji lokalnej komendy `pidocker`,
- ewentualne wymagane czyszczenie/rebuild obrazu lub volumes.

Przykład sprawdzenia:

```bash
git rev-parse --short HEAD
which pidocker
pidocker --help
```

Jeżeli `pidocker` wskazuje na starą wersję, ręczny test jest nieważny.

### 5. Ręczny test

Po przygotowaniu i instalacji właściwej wersji właściciel projektu wykonuje ręczny test opisany przy zadaniu.

Jeżeli ręczny test nie przejdzie, zadanie wraca do etapu `Zmiana`.

### 6. Zaznaczenie zadania

Dopiero po ręcznym teście zaznaczamy checkbox:

```md
- [x] Zrobione
```

---
