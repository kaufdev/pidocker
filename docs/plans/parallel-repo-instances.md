# Plan: równoległe instancje pidockera dla jednego repo

## Cel

Wielokrotne wykonanie:

```bash
pidocker monorepo
pidocker monorepo
```

ma uruchomić dwa równoległe kontenery z dwoma niezależnymi clone'ami tego samego skonfigurowanego repo.

Każda instancja dostaje:

- osobny workspace volume,
- świeży clone z własnym `.git`,
- osobny katalog sesji Pi.

Instancje celowo współdzielą istniejący `pidocker-home`, czyli auth, settings, SSH keys, sekrety, agents, skills i packages. Hostowe `packages.json` i `tools.json` nadal są stosowane przez obecny kod.

To jest wyłącznie izolacja równoległych checkoutów. Nie przenosimy Pi na hosta i nie budujemy task managera.

## UX

Alias repo konfigurujemy raz:

```bash
pidocker repos add monorepo git@github.com:company/monorepo.git
```

Każde późniejsze:

```bash
pidocker monorepo
```

generuje nową instancję i przed uruchomieniem Pi wypisuje na przykład:

```text
pidocker: instance monorepo-a13f42198b7c
pidocker: workspace volume pidocker-monorepo-a13f42198b7c-workspace
```

## Minimalny projekt

### 1. Hostowa konfiguracja aliasów

Dodać katalog:

```text
${PIDOCKER_CONFIG_DIR}/repos/
```

Każdy alias jest osobnym plikiem, np.:

```text
~/.config/pidocker/repos/monorepo
```

Plik zawiera jeden Git URL. Osobny plik jest prostszy i bezpieczniejszy od dokładania kolejnego ręcznego parsera JSON do `bin/pidocker` i nie wymaga `jq`, Node ani Pythona na hoście.

Dodać tylko:

```bash
pidocker repos add ALIAS GIT_URL
pidocker repos list
pidocker repos remove ALIAS
```

Walidacja `repos add`:

- alias pasuje do `[A-Za-z0-9][A-Za-z0-9_-]{0,39}`,
- alias nie jest istniejącą komendą CLI (`setupssh`, `secrets`, `packages`, `tools`, `agents`, `skills`, `completion`, `repos`) ani opcją,
- URL jest jednym niepustym wierszem bez whitespace,
- URL używa formatu już obsługiwanego przez clone: `https://`, `http://`, `ssh://`, `git://` albo `git@HOST:PATH`,
- plik jest zapisywany atomowo z prywatnymi uprawnieniami,
- pliku nigdy nie wykonujemy przez `source`.

Nie dodawać refów, profili ani per-repo settings. Clone startuje z remote default branch.

### 2. Zachowanie starego CLI

Dla `pidocker ARG`:

1. Jeśli `${PIDOCKER_CONFIG_DIR}/repos/ARG` istnieje, uruchomić nową instancję.
2. Jeśli alias nie istnieje, zachować obecne `pidocker REPO|GIT_URL` bez zmian.

Zmiana jest opt-in. Bezpośrednie Git URL i istniejące repo ze współdzielonego workspace zachowują obecną semantykę.

Bash/zsh completion ma nadal sugerować istniejące repo ze starego workspace, a dodatkowo komendę `repos` i aliasy z hostowego katalogu config.

### 3. Instancja

Dla aliasu wygenerować 12-znakowy losowy token szesnastkowy, np.:

```text
a13f42198b7c
```

Z niego zbudować:

```text
instance:         monorepo-a13f42198b7c
workspace volume: ${PIDOCKER_VOLUME_PREFIX}-monorepo-a13f42198b7c-workspace
session dir:      /home/pi/.pi/agent/instance-sessions/monorepo-a13f42198b7c
```

Token jest praktycznie unikalny; nie dodajemy rejestru, retry state machine ani metadata store do obsługi teoretycznej kolizji.

Nie potrzebujemy jawnych nazw kontenerów ani nowych labels. Każdy `docker run` już tworzy osobny kontener, a istniejący label `app=pidocker` wystarcza do ich znalezienia.

### 4. Osobny workspace, wspólny home

Dla aliasu zmienia się wyłącznie workspace mount:

```text
${PIDOCKER_VOLUME_PREFIX}-home                         -> /home/pi
${PIDOCKER_VOLUME_PREFIX}-monorepo-<token>-workspace  -> /workspace
```

Nie parametryzujemy ani nie kopiujemy home. Nie dodajemy profile/overlay volumes.

Nowa ścieżka musi przejść przez ten sam istniejący wybór obrazu co zwykłe uruchomienie:

- bazowy `PIDOCKER_IMAGE`, albo
- `PIDOCKER_TOOLS_IMAGE`, jeśli skonfigurowano tools.

Musi również przekazać ten sam `PIDOCKER_PACKAGE_SPECS_B64`.

### 5. Clone i sesja

Do istniejącego `run_container` przekazać dla aliasu:

```text
PIDOCKER_REPO_ARG=<URL z configu>
PIDOCKER_INSTANCE_ID=monorepo-a13f42198b7c
PI_CODING_AGENT_SESSION_DIR=/home/pi/.pi/agent/instance-sessions/monorepo-a13f42198b7c
```

Unikalny workspace volume jest pusty, więc istniejąca ścieżka `git clone` tworzy świeży clone na domyślnym branchu repo.

Nie zmieniamy brancha automatycznie. Po wejściu do Pi użytkownik może pracować na `master`/`main` albo samodzielnie przełączyć się na dowolny branch. Rozdzielenie instancji zapewniają osobne workspace volumes i osobne katalogi `.git`, nie branch tworzony przez pidocker.

Zakładamy normalne, niepuste repo z poprawnym remote default branch. Nie obsługujemy w tej zmianie empty repositories, detached refs, submodules ani Git LFS.

### 6. Współbieżny zapis wspólnego home

Obecny startup bezwarunkowo przepisuje `settings.json` i `keybindings.json`. Przy równoległym starcie dwóch kontenerów zwiększa to ryzyko nadpisania zmiany wykonanej przez drugą instancję.

Chirurgiczna poprawka: inline Node zapisuje plik tylko wtedy, gdy wynikowy JSON faktycznie różni się od istniejącej zawartości. Nie dodajemy lock managera ani pełnej synchronizacji `/settings`.

### 7. Retencja workspace

Kontener nadal działa z `--rm`, ale nazwany workspace volume pozostaje po wyjściu, żeby nie usuwać niezacommitowanych zmian.

Wrapper wypisuje nazwę volume przed uruchomieniem. Nie dodajemy managera instancji, resume, garbage collectora ani automatycznego cleanupu. Standardowe polecenia Dockera wystarczą do odzyskania lub usunięcia volume.

## Zmiany w plikach

### `bin/pidocker`

Dodać wyłącznie:

- `PIDOCKER_REPOS_DIR`,
- `repos add/list/remove`,
- walidację aliasu, zarezerwowanych nazw i Git URL,
- lookup aliasu przed dotychczasowym fallbackiem `REPO|GIT_URL`,
- generowanie tokenu instancji,
- wybór unikalnego workspace volume dla aliasu,
- env instancji i katalog sesji,
- zapis settings/keybindings tylko przy rzeczywistej zmianie,
- aliasy i `repos` w completion.

Nie refaktoryzować packages, tools, agents, skills, secrets ani pozostałego CLI.

### `tests/test_pidocker_wrapper.py`

Dodać fake-Docker/testy host config dla:

- `repos add/list/remove`,
- odrzucenia niebezpiecznego i zarezerwowanego aliasu,
- odrzucenia pustego, wieloliniowego i nieobsługiwanego URL,
- dwóch wywołań aliasu z różnymi workspace volume i session directories,
- wspólnego `${PIDOCKER_VOLUME_PREFIX}-home`,
- zachowania `PIDOCKER_VOLUME_PREFIX`,
- clone URL przed `exec pi`,
- braku automatycznej zmiany brancha w ścieżce aliasowej i starej ścieżce,
- użycia tools image i przekazania package specs przez ścieżkę aliasu,
- completion zawierającego stare repo, `repos` i hostowe aliasy.

Nie dodawać osobnego testu, który ręcznie klonuje repo do dwóch volumes z pominięciem wrappera — nie testowałby nowej logiki.

### `README.md`

Dodać krótką sekcję opisującą:

- konfigurację aliasu,
- wielokrotne `pidocker monorepo`,
- wspólny home i niezależne workspace,
- pozostawienie workspace volume po wyjściu.

`docker/Dockerfile` nie wymaga zmian.

## Szybko weryfikowalne zadania

### Zadanie A: aliasy i completion

Zakres:

- `repos add/list/remove`,
- walidacja,
- lookup aliasu,
- completion,
- bez zmiany uruchamiania kontenera.

Automatycznie:

```bash
./.venv/bin/pytest tests/test_pidocker_wrapper.py -k 'repos or completion'
```

Manualnie:

```bash
~/.local/bin/pidocker-dev repos add monorepo git@github.com:company/monorepo.git
~/.local/bin/pidocker-dev repos list
~/.local/bin/pidocker-dev repos remove monorepo
```

### Zadanie B: unikalna instancja per wywołanie

Zakres:

- token instancji,
- osobny workspace volume i session directory,
- świeży clone na domyślnym branchu,
- idempotentny zapis settings/keybindings,
- zachowanie tools image i packages.

Automatycznie:

```bash
./.venv/bin/pytest tests/test_pidocker_wrapper.py -k 'instance or alias or tools'
```

Manualnie w dwóch terminalach:

```bash
~/.local/bin/pidocker-dev monorepo
~/.local/bin/pidocker-dev monorepo
```

W pierwszej instancji:

```text
Utwórz instance.txt z treścią A i pokaż git branch --show-current. Nie przełączaj brancha.
```

W drugiej:

```text
Utwórz instance.txt z treścią B i pokaż git branch --show-current. Nie przełączaj brancha.
```

Oczekiwane:

- niezależne clone'y na tym samym domyślnym branchu i różne zawartości pliku,
- oba kontenery działają równolegle,
- ten sam home volume,
- różne workspace volumes.

### Zadanie C: dokumentacja i pełna regresja

Zakres:

- README,
- pełny szybki zestaw testów,
- manualny test dwóch prawdziwych clone'ów.

Automatycznie:

```bash
./.venv/bin/pytest tests/test_pidocker_wrapper.py tests/test_project_structure.py tests/test_readme.py
```

Przed handoffem uruchomić pełny zestaw Docker tests raz, zgodnie z workflow projektu.

## Kryteria ukończenia

1. Dwa równoległe `pidocker monorepo` używają różnych workspace volumes, clone'ów i session directories; branch jest kontrolowany przez użytkownika.
2. Obie instancje używają tego samego `${PIDOCKER_VOLUME_PREFIX}-home` i hostowej konfiguracji packages/tools.
3. Zmiana pliku lub Git metadata w jednej instancji nie wpływa na drugą.
4. Nieskonfigurowane `pidocker REPO` i bezpośrednie `pidocker GIT_URL` zachowują dotychczasowe działanie.
5. Alias nadal korzysta z tools image, package specs i istniejących zabezpieczeń mountów.
6. Nie powstaje task manager, daemon, hostowy router Pi, profile system ani ogólny refaktor wrappera.

## Świadome ograniczenia

- Wspólny `pidocker-home` oznacza izolację checkoutów, nie sekretów ani `/settings`.
- Każdy start wykonuje pełny clone i zużywa osobny named volume.
- Workspace volume pozostaje po wyjściu i wymaga ręcznego usunięcia.
- Obie instancje mogą celowo pracować na tym samym branchu; konsekwencje równoległego pushowania są po stronie użytkownika.
- Źródłem jest URL z hostowego configu; nie kopiujemy dirty state z istniejącego clone'a.

## Poza zakresem

Nie realizować w tej zmianie:

- hostowego Pi i routingu tools,
- per-instance home/auth/secrets,
- desktop runnera,
- subagentów,
- task create/open/list/resume/prune,
- automatycznego cleanupu,
- clone cache/mirror,
- dirty snapshots,
- refów per alias,
- submodules/Git LFS,
- nowych polityk sieci i resource limits,
- refaktoryzacji wrappera poza koniecznymi miejscami.

## Szacunek

Po zawężeniu planu: 1–2 dni implementacji, testów wrappera i manualnej weryfikacji dwóch równoległych instancji.
