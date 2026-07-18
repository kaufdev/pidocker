---
name: piddocker-notion
description: Explains the exact private Notion page and database used for Piddocker, available read operations, schema, and status vocabulary.
---

# Piddocker Notion

## Exact target

The Piddocker Notion target is in:

```text
Workspace: Maciek’s Space
Connection/bot: Maciek Labs Projects Token

Parent page: Piddocker
Page URL: https://app.notion.com/p/Piddocker-3a1c950bec578015b5e8f598de0ed40f
Page ID: 3a1c950b-ec57-8015-b5e8-f598de0ed40f

Child database: New database
Database ID: 3a1c950b-ec57-80d8-a634-e049f610c14f
Data source ID: 3a1c950b-ec57-8085-9f03-000b6a647196
```

The shared URL points to the **parent page**, not directly to the database or a saved view. Do not invent a `v=` view ID. Resolve the child database first, or use the database/data-source IDs above.

## Authentication

The Notion API token is supplied only through:

```text
MACIEK_LAB_NOTION_API_KEY
```

Never print it, pass it as a CLI argument, put it in a prompt, or commit it to the repository.

Use the available Notion API/read-only integration in the current runtime. When a generic database inspection command is available, pass the database ID above rather than the parent page URL. A saved-view query requires a real view ID.

## What is available

Read-only operations currently available through the helper/API:

- check the connection identity and workspace;
- inspect the Piddocker database and data-source schema;
- read pages/tasks and their properties;
- query a saved view when its actual view ID is known;
- resolve the parent page and its child database.

The current skill is read-only by default. Do not create, update, archive, delete, or migrate Notion content unless the user explicitly requests that specific mutation and the target/property change is clear.

## Current schema

The data source currently has exactly these properties:

| Property | Type | Meaning |
|---|---|---|
| `Name` | title | Piddocker work item title |
| `Status` | status | Current workflow state |
| `Assign` | people | Assigned person |

Do not assume that this database has the Agent Queue fields such as `Priority`, `Checkpoint`, `Needs from me`, `Project`, or `Pi Session ID`. Those belong to a different schema unless they are explicitly added later.

## Statuses

Use the exact current Notion option names:

| Status | Meaning |
|---|---|
| `Not started` | Work has not begun |
| `In progress` | Work is being performed |
| `Done` | Work is finished |

Notion groups them as:

```text
To-do       -> Not started
In progress -> In progress
Complete    -> Done
```

Do not use the separate Agent Queue vocabulary (`Agent pracuje`, `Czeka na mnie`, `Zablokowane`, `Kod gotowy`, `Odpowiedź gotowa`) for this Piddocker database.

## Current snapshot

At the time this skill was created, the database contained:

```text
Name: nie mozna robic force pushy
Status: Not started
Assign: empty
```

This is only a reference. Always query Notion before reporting the current task list.

## Working rules

1. Confirm access if uncertain.
2. Use the exact Piddocker database/data-source IDs above.
3. Distinguish parent page, database, data source, and saved view in reports.
4. Resolve properties from the live schema where possible.
5. Preserve exact status names and capitalization.
6. If the API returns `404 object_not_found`, explain that the resource may not be shared with the connection.
7. If it returns `403 restricted_resource`, explain that the connection lacks permission.
8. Never invent IDs, views, properties, or statuses.
9. Keep token values out of command output, logs, commits, and responses.

## Mutation boundary

Any Piddocker task creation or status update requires an explicit user request and a separately reviewed implementation against the schema above. This skill does not authorize mutations by default.
