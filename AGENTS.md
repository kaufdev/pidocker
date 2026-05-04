# Agent instructions for pi-docker

## Cel organizacji kontekstu

Nie wczytuj całego `PIDOCKER_TASKS.md` ani wszystkich tasków naraz. Ten projekt używa pi skills jako progressive disclosure, żeby trzymać mały context.

`PIDOCKER_TASKS.md` jest tylko lekkim indeksem z tytułami zadań i nazwami skilli.

## Kiedy ładować który skill

### `/skill:pidocker-task-flow`

Ładuj, gdy:

- zaczynasz pracę nad dowolnym zadaniem MVP,
- kończysz zadanie i potrzebujesz Definition of Done,
- przygotowujesz commit albo przekazanie do ręcznego testu,
- nie pamiętasz zasad ręcznego testowania `pidocker`,
- trzeba wejść ręcznie do działającego kontenera.

Ten skill zawiera wspólny workflow: zmiana → testy → commit → instalacja testowanej wersji → ręczny test właściciela → zaznaczenie checkboxa.

### `/skill:pidocker-task-XX`

Ładuj tylko skill dla konkretnego zadania, nad którym aktualnie pracujesz.

Przykłady:

- task 7 → `/skill:pidocker-task-07`
- task 8 → `/skill:pidocker-task-08`
- task 18 → `/skill:pidocker-task-18`

Skill taska zawiera wymaganie, dowód spełnienia, test automatyczny i ręczny test dla tego jednego zadania.

Nie ładuj sąsiednich tasków, jeśli nie są bezpośrednio potrzebne.

### `/skill:pidocker-mvp-completion`

Ładuj tylko wtedy, gdy oceniasz całość MVP albo użytkownik pyta, co jeszcze brakuje do ukończenia MVP.

Nie używaj go do implementacji pojedynczego zadania.

## Zalecany flow pracy nad zadaniem

1. Odczytaj `PIDOCKER_TASKS.md` tylko jako indeks.
2. Wybierz następne lub wskazane zadanie.
3. Załaduj `/skill:pidocker-task-flow`, jeśli workflow nie jest już w kontekście.
4. Załaduj tylko odpowiadający skill `/skill:pidocker-task-XX`.
5. Implementuj wyłącznie zakres tego zadania.
6. Uruchom testy wskazane w skillu.
7. Po ręcznym teście właściciela dopiero zaznacz checkbox w `PIDOCKER_TASKS.md` i w odpowiadającym skillu.

## Ważne ograniczenia

- Nie używaj ani nie dodawaj interfejsu `pidocker --exec`.
- Ręczny test ma używać zainstalowanej komendy `pidocker`, nie tylko `./bin/pidocker`.
- Nie montuj prywatnych plików hosta do kontenera.
- Nie dodawaj zmian spoza bieżącego zadania bez wyraźnej potrzeby.
