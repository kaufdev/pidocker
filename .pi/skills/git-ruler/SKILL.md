---
name: git-ruler
description: Commit timing and commit message rules. Use before creating commits or when deciding commit names.
---

# Git Ruler

## Commit timing

- Commit the coherent change before test/debug loops.
- After failing tests, fix implementation/config/docs; do not weaken tests unless requirements changed.
- Amend the commit for direct fixes, or add a follow-up commit for a separate change.

## Commit naming

Use concise Conventional-style names:

```bash
feature(scope): summary
fix(scope): summary
docs(scope): summary
chore(scope): summary
```

Examples:

```bash
feature(repo-argument): adding repo argument
docs(task-flow): formalize pidocker workflow
```
