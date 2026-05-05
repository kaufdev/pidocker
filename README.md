# pidocker

`pidocker` uruchamia Pi w izolowanym kontenerze Docker. Kontener używa wyłącznie nazwanych volumes `pidocker-home` i `pidocker-workspace`; nie montuje katalogów prywatnych hosta ani socketa Dockera.

## Wymagania

- Docker dostępny na hoście.
- Dostęp do obrazu budowanego z tego repozytorium.

## Budowanie obrazu

Z katalogu repozytorium uruchom:

```bash
docker build -t pidocker:local docker
```

Wrapper `pidocker` buduje obraz automatycznie, jeśli `pidocker:local` jeszcze nie istnieje. Możesz nadpisać nazwę obrazu przez `PIDOCKER_IMAGE`.

## Instalacja i aktualizacja komendy `pidocker`

Najprostsza lokalna instalacja to symlink do skryptu z repozytorium:

```bash
mkdir -p ~/.local/bin
ln -sf "$(pwd)/bin/pidocker" ~/.local/bin/pidocker
```

Upewnij się, że `~/.local/bin` jest w `PATH`:

```bash
which pidocker
pidocker --help
```

Aktualizacja polega na pobraniu nowych zmian w repozytorium i ponownym zbudowaniu obrazu:

```bash
git pull
docker build -t pidocker:local docker
```

Jeśli używasz innej lokalizacji instalacji, podmień tam plik/symlink tak, żeby zainstalowana komenda `pidocker` wskazywała na aktualną wersję.

## Uruchamianie Pi

Uruchom interaktywnie:

```bash
pidocker
```

Domyślnie wrapper startuje kontener z labelem `app=pidocker`, montuje volumes i wykonuje `pi` w katalogu `/workspace/repos`.

W Pi wykonaj logowanie:

```text
/login
```

Auth Pi i sesje `/resume` są zapisywane w `pidocker-home`, więc zostają po restarcie kontenera.

## Ręczne wejście do działającego kontenera

Terminal 1:

```bash
pidocker
```

Terminal 2:

```bash
docker ps --filter "label=app=pidocker" --format "table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}"
docker exec -it <CONTAINER_ID> bash
```

W środku możesz sprawdzić:

```bash
whoami
pwd
ls -la /home/pi
ls -la /workspace
```

## SSH key do Git i Azure DevOps

Wygeneruj dedykowane klucze wewnątrz `pidocker-home`:

```bash
pidocker setupssh
```

Komenda tworzy m.in. klucz dla Azure DevOps (`/home/pi/.ssh/id_rsa_pidocker_azure`) i wypisuje publiczny key. Dodaj go w Azure DevOps w:

```text
User settings -> SSH public keys -> New Key
```

Potem klonuj repozytoria do `/workspace/repos`, np. wewnątrz kontenera:

```bash
git clone git@ssh.dev.azure.com:v3/ORG/PROJECT/REPO /workspace/repos/REPO
```

## Notion token

Token Notion zapisz przez zainstalowaną komendę `pidocker`:

```bash
pidocker secrets set NOTION_API_KEY
```

Sekret trafia do sandboxowego miejsca w `pidocker-home`: `/home/pi/.pidocker/secrets/env` oraz `/home/pi/.pidocker/secrets/notion.env`. Przy starcie `pidocker` ładuje te wartości jako zmienne środowiskowe dla Pi.

## Volumes i reset

`pidocker` używa dwóch nazwanych volumes:

- `pidocker-home` -> `/home/pi`: auth Pi, sesje, SSH keys, sekrety, konfiguracja.
- `pidocker-workspace` -> `/workspace`: repozytoria i pliki pracy, w tym `/workspace/repos`.

Reset świeżego środowiska usuwa oba volumes:

```bash
docker volume rm -f pidocker-home pidocker-workspace
```

Po resecie trzeba ponownie wykonać `/login`, `pidocker setupssh` i zapisać sekrety.

## Bezpieczeństwo i izolacja hosta

Kontener nie widzi prywatnych ścieżek hosta takich jak `/Users/kaufdev`, katalogów projektu hosta, `~/.ssh`, `~/.aws`, `~/.kube` ani `/var/run/docker.sock`. Wrapper nie powinien używać `--privileged`, `--pid=host` ani `--network=host`.

Nie montuj prywatnych plików hosta do kontenera. Wszystko, co ma przetrwać, zapisuj w `pidocker-home` albo `pidocker-workspace`.

## Git push i force push

W kontenerze lokalny wrapper `git` blokuje destrukcyjne operacje typu `force push`, `--force-with-lease`, `--mirror` i kasowanie zdalnych refów. Dodatkowo force push ma być zablokowany po stronie providera repozytorium, np. przez branch policies/protected branches w Azure DevOps albo GitHub.

Zwykły push jest dozwolony:

```bash
git push origin HEAD:twoja-galaz
```

## Development

Run tests from the host:

```bash
pytest tests/
```
