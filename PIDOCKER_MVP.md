# pidocker MVP

## Cel

Jedna komenda:

```bash
pidocker
```

Uruchamia normalne `pi`, ale **całe pi działa wewnątrz kontenera Dockera**. Agent pracuje na repozytoriach sklonowanych w kontenerze, nie na plikach hosta.

## Główny flow

1. Użytkownik wpisuje:

   ```bash
   pidocker
   ```

2. Otwiera się interaktywne `pi` w kontenerze.
3. Użytkownik podaje repozytoria w rozmowie, np. Azure DevOps / GitHub URL.
4. Agent robi `git clone` do `/workspace/repos`.
5. Agent pracuje na swojej kopii repo.
6. Zmiany wychodzą przez `git commit` i `git push`.
7. Brak kopiowania lokalnych repo z hosta.

## Architektura

- `pi` działa w Dockerze.
- Built-in tools `bash/read/write/edit/grep/find/ls` działają w Dockerze.
- Agent nie dostaje hostowego shella.
- Kontener jest jednorazowy i może być usuwany po wyjściu.
- Stan trzymany jest w Docker volumes.

## Docker volumes

### `pidocker-home`

Montowany jako:

```text
/home/pi
```

Przechowuje:

```text
/home/pi/.pi/agent/auth.json
/home/pi/.pi/agent/settings.json
/home/pi/.pi/agent/sessions/
/home/pi/.ssh/
/home/pi/.gitconfig
/home/pi/.pidocker/secrets/
```

Czyli:

- login do Pi,
- ustawienia Pi,
- sesje `/resume`,
- SSH key do Azure DevOps,
- Notion API key,
- inne sandboxowe configi.

### `pidocker-workspace`

Montowany jako:

```text
/workspace
```

Przechowuje:

```text
/workspace/repos/...
```

Czyli:

- sklonowane repozytoria,
- lokalne branche,
- lokalne commity,
- niezacommitowane zmiany.

## Co agent widzi z hosta

Domyślnie: nic z prywatnych plików hosta.

Nie montujemy:

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

Agent widzi tylko:

```text
/home/pi
/workspace
/tmp
system plików kontenera
internet
```

## Zasady bezpieczeństwa kontenera

Nie używać:

```text
--privileged
--pid=host
--network=host
-v /var/run/docker.sock:/var/run/docker.sock
-v /Users/kaufdev:/host
```

Kontener powinien działać jako zwykły user, nie root.

## Sekrety MVP

### 1. Pi `/login`

- Login robiony wewnątrz kontenera.
- Token zapisuje się w `pidocker-home`:

```text
/home/pi/.pi/agent/auth.json
```

Konsekwencja: agent może potencjalnie odczytać ten plik, bo działa w tym samym środowisku.

### 2. SSH do Azure DevOps

Używamy osobnego SSH key tylko dla `pidocker`.

Przykładowe pliki:

```text
/home/pi/.ssh/id_ed25519_pidocker
/home/pi/.ssh/id_ed25519_pidocker.pub
```

Publiczny klucz dodawany ręcznie w Azure DevOps.

Agent może robić:

```bash
git clone git@ssh.dev.azure.com:v3/org/project/repo
git push
```

Nie używamy hostowego `~/.ssh`.

### 3. Notion API key

Na MVP Notion API key może być zapisany w kontenerowym volume, np.:

```text
/home/pi/.pidocker/secrets/notion.env
```

Wymaganie:

- dedykowany token dla `pidocker`,
- ograniczony dostęp tylko do potrzebnych stron/baz,
- łatwy do odwołania.

## Git policy

Agent może:

```text
git clone
git checkout -b ...
git commit
git push
```

Agent nie może używać:

```text
git push --force
git push --force-with-lease
git push --mirror
git push origin :branch
```

Blokada lokalna przez wrapper/hook jest dobra, ale główna ochrona powinna być po stronie Azure DevOps/GitHub:

- branch protection,
- brak uprawnień do force push,
- brak admin permissions.

## Web/search tooling

W kontenerze ma działać obecny zestaw Pi:

- `pi-web-access`,
- `web_search`,
- `code_search`,
- `fetch_content`,
- `get_search_content`,
- skill `librarian`.

Te narzędzia muszą działać wewnątrz kontenera, nie na hoście.

## Out of scope dla MVP

Na MVP nie robimy:

- hostowego Pi z dockerowymi toolami,
- proxy dla Notion API key,
- proxy dla Pi/model auth,
- kopiowania lokalnych repo z hosta,
- mountowania katalogów projektowych hosta,
- mountowania hostowego `~/.ssh`,
- automatycznego PR flow,
- trybu jednorazowego `pidocker "prompt"`.

## Minimalne komendy MVP

Wymagana:

```bash
pidocker
```

Opcjonalne później:

```bash
pidocker-reset
pidocker-shell
pidocker-volumes
```

## Definicja sukcesu MVP

MVP działa, jeśli:

1. `pidocker` odpala interaktywne `pi` w kontenerze.
2. `/login` działa i zostaje między uruchomieniami.
3. Agent może sklonować repo z Azure DevOps przez osobny SSH key.
4. Agent może zrobić commit i push bez force push.
5. Agent może użyć Notion API key z sandboxowego secreta.
6. Agent nie widzi `/Users/kaufdev` ani lokalnych repo.
7. Sesje Pi działają przez `/resume` między uruchomieniami.
8. Repozytoria zostają w `/workspace/repos` między uruchomieniami.
