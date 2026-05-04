---
name: pidocker-task-16
description: "Pidocker MVP task 16: Notion secret path jest sandboxowy i persystentny. Use when implementing, testing, or reviewing this specific pidocker task."
---

# Task 16: Notion secret path jest sandboxowy i persystentny

Before using this task skill, load the shared workflow if it is not already in context:

```text
/skill:pidocker-task-flow
```

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

