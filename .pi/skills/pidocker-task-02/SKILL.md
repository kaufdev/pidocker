---
name: pidocker-task-02
description: "Pidocker MVP task 2: Kontener pidocker da się znaleźć i wejść do niego ręcznie. Use when implementing, testing, or reviewing this specific pidocker task."
---

# Task 2: Kontener pidocker da się znaleźć i wejść do niego ręcznie

Before using this task skill, load the shared workflow if it is not already in context:

```text
/skill:pidocker-task-flow
```

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

