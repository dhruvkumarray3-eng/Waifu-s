---
name: Remote repository safety
description: Safe rules for bringing an external repository into an existing Replit project.
---

When syncing an external repository into an existing project, preserve the project’s Git metadata and do not delete the existing workspace root. Stage only the source and configuration that belongs in the upstream repository; keep generated scaffolding and local runtime artifacts out unless they are intentionally part of that repository.

**Why:** A broad copy with dotfile cleanup can remove the project’s Git history and mix unrelated generated artifacts into the upstream repository.

**How to apply:** Clone into a temporary directory, inspect first, copy files without removing the project root, and use an explicit staging allowlist before committing.