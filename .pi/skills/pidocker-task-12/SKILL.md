---
name: pidocker-task-12
description: "Pidocker MVP task 12: Dedykowany SSH key dla pidocker. Use when implementing, testing, or reviewing this specific pidocker task."
---

# Task 12: Dedykowany SSH key dla pidocker

Before using this task skill, load the shared workflow if it is not already in context:

```text
/skill:pidocker-task-flow
```

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

