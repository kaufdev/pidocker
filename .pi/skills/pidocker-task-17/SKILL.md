---
name: pidocker-task-17
description: "Pidocker MVP task 17: Web/search tooling dostępne w kontenerze. Use when implementing, testing, or reviewing this specific pidocker task."
---

# Task 17: Web/search tooling dostępne w kontenerze

Before using this task skill, load the shared workflow if it is not already in context:

```text
/skill:pidocker-task-flow
```

## 17. Web/search tooling dostępne w kontenerze

- [x] Zrobione

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

