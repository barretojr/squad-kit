## What and why

<!-- The problem this solves and the change in a few lines. Link the issue if there is one. -->

## How it was tested

<!-- Commands run and their result, e.g. `python -m unittest discover -s tests -v` → OK -->

## Checklist

- [ ] `python -m unittest discover -s tests -v` passes locally
- [ ] New or changed MCP checks have a positive and a negative test
- [ ] Own files are in English (translations go in `*.<lang>.md`)
- [ ] No business niche added to the core skill, agents or rules (use a domain pack)
- [ ] Third-party folders untouched, or updated following their `UPSTREAM.md`
- [ ] `CHANGELOG.md` updated for user-visible changes
- [ ] Breaking contract change (`.squad/` paths, headings, statuses, MCP arguments)? If yes, agents, templates, tests and `SERVER_VERSION` were updated together
