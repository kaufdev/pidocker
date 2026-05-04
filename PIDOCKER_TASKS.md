# pidocker MVP — zadania i flow pracy

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

# Zadania MVP

## 0. Setup projektu i test harness

- [x] Zrobione

### Wymaganie

Repo ma minimalną strukturę pod implementację i testy:

```text
bin/pidocker
docker/Dockerfile
tests/
README.md
PIDOCKER_MVP.md
PIDOCKER_TASKS.md
```

Testy są odpalane z hosta, nie z wnętrza kontenera.

### Dowód spełnienia

```bash
pytest tests/
```

przechodzi.

### Test automatyczny

Minimalny test sanity sprawdza, że wymagane pliki istnieją.

### Ręczny test właściciela

```bash
pytest tests/
pidocker --help
```

---

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

## 2. Kontener pidocker da się znaleźć i wejść do niego ręcznie

- [x] Zrobione

### Wymaganie

Kontener uruchomiony przez `pidocker` ma label:

```text
app=pidocker
```

Dzięki temu właściciel może znaleźć działający kontener i wejść do niego przez `docker exec -it <CONTAINER_ID> bash`.

Nie dodajemy trybu `pidocker --exec`.

### Dowód spełnienia

Po uruchomieniu:

```bash
pidocker
```

w drugim terminalu działa:

```bash
docker ps --filter "label=app=pidocker"
```

i pokazuje kontener pidocker.

### Test automatyczny

Test sprawdza, że komenda uruchamiająca Dockera w wrapperze dodaje label `app=pidocker`.

Może to być test statyczny skryptu albo test przez `docker inspect` na krótkotrwałym kontenerze testowym.

### Ręczny test właściciela

Terminal 1:

```bash
pidocker
```

Terminal 2:

```bash
docker ps --filter "label=app=pidocker" --format "table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}"
docker exec -it <CONTAINER_ID> bash
whoami
exit
```

Oczekiwane: da się wejść do kontenera, a `whoami` zwraca użytkownika kontenerowego.

---

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

## 6. Kontener nie widzi prywatnych plików hosta

- [ ] Zrobione

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

## 7. `pidocker` nie używa niebezpiecznych flag Dockera

- [ ] Zrobione

### Wymaganie

Wrapper nie może uruchamiać Dockera z flagami:

```text
--privileged
--pid=host
--network=host
-v /var/run/docker.sock:/var/run/docker.sock
-v /Users/kaufdev:/host
```

### Dowód spełnienia

Działający kontener nie jest privileged, nie używa host PID namespace, nie używa host network i nie ma zamontowanego Docker socketa ani katalogu `/Users/kaufdev`.

### Test automatyczny

Test sprawdza skrypt `bin/pidocker` statycznie oraz/lub używa `docker inspect` na uruchomionym kontenerze testowym.

### Ręczny test właściciela

1. Uruchom `pidocker`.
2. W drugim terminalu znajdź kontener:

```bash
docker ps --filter "label=app=pidocker"
```

3. Sprawdź konfigurację:

```bash
docker inspect <CONTAINER_ID> --format 'Privileged={{.HostConfig.Privileged}} PidMode={{.HostConfig.PidMode}} NetworkMode={{.HostConfig.NetworkMode}}'
docker inspect <CONTAINER_ID> --format '{{json .Mounts}}'
```

Oczekiwane:

- `Privileged=false`,
- `PidMode` nie jest `host`,
- `NetworkMode` nie jest `host`,
- mounty nie zawierają `/var/run/docker.sock`,
- mounty nie zawierają `/Users/kaufdev`.

---

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

## 9. Zwykłe `pidocker` odpala interaktywne Pi

- [ ] Zrobione

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

## 12. Dedykowany SSH key dla pidocker

- [ ] Zrobione

### Wymaganie

W kontenerze można utworzyć dedykowany klucz:

```text
/home/pi/.ssh/id_ed25519_pidocker
/home/pi/.ssh/id_ed25519_pidocker.pub
```

Nie używamy hostowego `~/.ssh`.

### Dowód spełnienia

Klucz istnieje w `/home/pi/.ssh` w kontenerze i zostaje po restarcie `pidocker`.

### Test automatyczny

Test sprawdza, że:

- `/home/pi/.ssh` może powstać,
- można wygenerować klucz w testowym volume,
- klucz zostaje po ponownym uruchomieniu,
- hostowe `~/.ssh` nie jest montowane.

### Ręczny test właściciela

1. Uruchom `pidocker`.
2. Wejdź do kontenera.
3. W środku wykonaj:

```bash
mkdir -p /home/pi/.ssh
ssh-keygen -t ed25519 -f /home/pi/.ssh/id_ed25519_pidocker -N ""
ls -la /home/pi/.ssh
cat /home/pi/.ssh/id_ed25519_pidocker.pub
```

4. Dodaj publiczny klucz ręcznie w Azure DevOps.
5. Zamknij i uruchom ponownie `pidocker`, wejdź do kontenera i sprawdź, że klucz nadal istnieje.

---

## 13. Git clone do `/workspace/repos`

- [ ] Zrobione

### Wymaganie

Repozytoria są klonowane do:

```text
/workspace/repos
```

Nie kopiujemy lokalnych repo z hosta.

### Dowód spełnienia

Repo po sklonowaniu istnieje w:

```text
/workspace/repos/<repo>/.git
```

### Test automatyczny

Test podstawowy może klonować małe publiczne repo albo używać lokalnego bare repo przygotowanego przez test harness.

Test wymagający internetu oznaczamy jako integration.

### Ręczny test właściciela

1. Uruchom `pidocker`.
2. Wejdź do kontenera.
3. W środku wykonaj:

```bash
git clone https://github.com/octocat/Hello-World.git /workspace/repos/manual-hello-world
ls -la /workspace/repos/manual-hello-world/.git
```

4. Zamknij i uruchom ponownie `pidocker`.
5. Wejdź do kontenera i sprawdź:

```bash
ls -la /workspace/repos/manual-hello-world/.git
```

---

## 14. Git clone z Azure DevOps przez dedykowany SSH key

- [ ] Zrobione

### Wymaganie

Po dodaniu publicznego klucza do Azure DevOps kontener może wykonać:

```bash
git clone git@ssh.dev.azure.com:v3/org/project/repo /workspace/repos/repo
```

### Dowód spełnienia

Repo z Azure DevOps istnieje w:

```text
/workspace/repos/<repo>/.git
```

### Test automatyczny

Test automatyczny oznaczony jako integration, bo wymaga:

- sieci,
- dostępu do Azure DevOps,
- skonfigurowanego SSH key.

### Ręczny test właściciela

1. Upewnij się, że publiczny klucz z `/home/pi/.ssh/id_ed25519_pidocker.pub` jest dodany w Azure DevOps.
2. Uruchom `pidocker`.
3. Wejdź do kontenera.
4. W środku wykonaj:

```bash
ssh -T git@ssh.dev.azure.com || true
git clone git@ssh.dev.azure.com:v3/<org>/<project>/<repo> /workspace/repos/<repo>
ls -la /workspace/repos/<repo>/.git
```

---

## 15. Git push działa bez force push

- [ ] Zrobione

### Wymaganie

Agent może używać:

```text
git push
```

ale nie może używać:

```text
git push --force
git push --force-with-lease
git push --mirror
git push origin :branch
```

Lokalna blokada w wrapperze/hooku jest pomocnicza. Główna ochrona powinna być też ustawiona po stronie Azure DevOps/GitHub.

### Dowód spełnienia

Zakazane komendy kończą się błędem, np.:

```text
pidocker: force push is disabled
```

Zwykły push działa.

### Test automatyczny

Test na repo testowym sprawdza:

- `git push --force` kończy się exit code != 0,
- `git push --force-with-lease` kończy się exit code != 0,
- `git push --mirror` kończy się exit code != 0,
- `git push origin :some-branch` kończy się exit code != 0,
- zwykły `git push origin HEAD:test-branch` działa.

### Ręczny test właściciela

1. Uruchom `pidocker`.
2. Wejdź do kontenera.
3. Przejdź do testowego repo:

```bash
cd /workspace/repos/<repo>
```

4. Sprawdź zakazany push:

```bash
git push --force
```

Oczekiwane: komenda jest zablokowana.

5. Sprawdź zwykły push na testowy branch:

```bash
git push origin HEAD:test-pidocker-branch
```

Oczekiwane: zwykły push działa.

---

## 16. Notion secret path jest sandboxowy i persystentny

- [ ] Zrobione

### Wymaganie

Notion API key może być zapisany w:

```text
/home/pi/.pidocker/secrets/notion.env
```

Token jest dedykowany dla `pidocker`, ograniczony i łatwy do odwołania.

### Dowód spełnienia

Plik `/home/pi/.pidocker/secrets/notion.env` istnieje w kontenerze i zostaje po restarcie `pidocker`.

### Test automatyczny

Test sprawdza persystencję pliku w `/home/pi/.pidocker/secrets` na testowym volume.

Prawdziwe wywołanie Notion API jest testem integracyjnym/ręcznym.

### Ręczny test właściciela

1. Uruchom `pidocker`.
2. Wejdź do kontenera.
3. W środku wykonaj:

```bash
mkdir -p /home/pi/.pidocker/secrets
echo NOTION_API_KEY=test > /home/pi/.pidocker/secrets/notion.env
cat /home/pi/.pidocker/secrets/notion.env
```

4. Zamknij i uruchom ponownie `pidocker`.
5. Wejdź do kontenera i sprawdź:

```bash
cat /home/pi/.pidocker/secrets/notion.env
```

Oczekiwane: zwraca `NOTION_API_KEY=test`.

---

## 17. Web/search tooling dostępne w kontenerze

- [ ] Zrobione

### Wymaganie

W kontenerze działa obecny zestaw Pi:

```text
pi-web-access
web_search
code_search
fetch_content
get_search_content
skill librarian
```

Narzędzia działają wewnątrz kontenera, nie na hoście.

### Dowód spełnienia

Manualnie: w Pi wykonujemy zapytanie używające web/search tooling.

Technicznie, po wejściu do kontenera, można sprawdzić pakiety/pliki zależnie od sposobu instalacji.

### Test automatyczny

Test sprawdza, że wymagane pakiety/pliki są dostępne w obrazie.

Pełne użycie `web_search` może być oznaczone jako integration, bo wymaga sieci/API/auth.

### Ręczny test właściciela

Preferowany test:

```bash
pidocker
```

Następnie poproś Pi o użycie web search albo code search i potwierdź, że działa.

Jeżeli trzeba sprawdzić technicznie, wejdź do kontenera i wykonaj odpowiedni check instalacji, np. zależnie od implementacji:

```bash
npm list -g --depth=0 | grep pi-web-access
```

---

## 18. README opisuje użycie i bezpieczeństwo

- [ ] Zrobione

### Wymaganie

`README.md` opisuje:

- jak zbudować obraz,
- jak zainstalować/aktualizować komendę `pidocker`,
- jak uruchomić `pidocker`,
- jak ręcznie wejść do działającego kontenera,
- jak wykonać `/login`,
- jak wygenerować SSH key,
- gdzie dodać publiczny key w Azure DevOps,
- gdzie zapisać Notion token,
- jak działają volumes,
- jak zresetować volumes,
- czego kontener nie widzi z hosta,
- że force push ma być zablokowany lokalnie i po stronie providera.

### Dowód spełnienia

Nowy użytkownik może przejść README od zera i uruchomić MVP.

### Test automatyczny

Test sprawdza, że README zawiera wymagane frazy/sekcje:

```text
pidocker
/login
pidocker-home
pidocker-workspace
Azure DevOps
Notion
force push
/Users/kaufdev
/var/run/docker.sock
docker exec
app=pidocker
```

### Ręczny test właściciela

Przejść README krok po kroku na świeżych volumes, używając zainstalowanej komendy:

```bash
pidocker
```

---

# Definicja ukończenia MVP

MVP uznajemy za ukończone, jeśli wszystkie poniższe punkty są zaznaczone:

- [ ] `pidocker` odpala interaktywne `pi` w kontenerze.
- [ ] `/login` działa i zostaje między uruchomieniami.
- [ ] Agent może sklonować repo z Azure DevOps przez osobny SSH key.
- [ ] Agent może zrobić commit i push bez force push.
- [ ] Agent może użyć Notion API key z sandboxowego secreta.
- [ ] Agent nie widzi `/Users/kaufdev` ani lokalnych repo.
- [ ] Sesje Pi działają przez `/resume` między uruchomieniami.
- [ ] Repozytoria zostają w `/workspace/repos` między uruchomieniami.
