---
name: pidocker-mvp-completion
description: "Pidocker MVP completion checklist. Use when assessing whether the overall pidocker MVP is complete."
---

# Pidocker MVP Completion

# Definicja ukończenia MVP

MVP uznajemy za ukończone, jeśli wszystkie poniższe punkty są zaznaczone:

- [ ] `pidocker` odpala interaktywne `pi` w kontenerze.
- [ ] `/login` działa i zostaje między uruchomieniami.
- [ ] Agent może sklonować repo z Azure DevOps przez osobny SSH key.
- [ ] Agent może zrobić commit i push bez force push.
- [ ] Agent może użyć Notion API key z sandboxowego secreta.
- [ ] Agent nie widzi `/Users/kaufdev` ani lokalnych repo.
- [ ] Sesje Pi działają przez `/resume` między uruchomieniami.
- [ ] Repozytoria zostają w `/workspace/repos` między uruchomieniami.
