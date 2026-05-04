---
name: pidocker-task-18
description: "Pidocker MVP task 18: README opisuje użycie i bezpieczeństwo. Use when implementing, testing, or reviewing this specific pidocker task."
---

# Task 18: README opisuje użycie i bezpieczeństwo

Before using this task skill, load the shared workflow if it is not already in context:

```text
/skill:pidocker-task-flow
```

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

