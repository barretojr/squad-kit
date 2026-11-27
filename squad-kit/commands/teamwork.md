---
description: Shortcut to start the squad in full mode (round table) before executing roadmap items.
---

# `/teamwork` alias

User request: `$ARGUMENTS`

Route the request to `skills/squad/SKILL.md` in **`full` mode** and follow the skill's whole flow: discovery, interview, specialist fan-out, reports in `.squad/`, roadmap, and the user picking items before any implementation. Do not keep a parallel workflow here. Answer in the user's language.

At the end of execution, the independent review (critics + `appsec`) and `@Finalizer` are mandatory; the Finalizer writes `quality/finalizer.md` and approves only when `validate_completion_checklist` returns `valid: true`. Without row-by-row evidence there is no final approval; gaps become roadmap tasks.
