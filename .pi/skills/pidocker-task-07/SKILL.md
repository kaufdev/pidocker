---
name: pidocker-task-07
description: "Pidocker MVP task 7: `pidocker` nie używa niebezpiecznych flag Dockera. Use when implementing, testing, or reviewing this specific pidocker task."
---

# Task 7: `pidocker` nie używa niebezpiecznych flag Dockera

Before using this task skill, load the shared workflow if it is not already in context:

```text
/skill:pidocker-task-flow
```

## 7. `pidocker` nie używa niebezpiecznych flag Dockera

- [x] Zrobione

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

