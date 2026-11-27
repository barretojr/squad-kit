# Contributing to Squad

Thanks for helping! Issues and pull requests are welcome in English or Portuguese; the repository's own files are written in English.

## Good first contributions

- **Domain packs** — niche knowledge kept outside the core skill (see `squad-kit/skills/squad/references/domain-packs.md`).
- **Stack profiles** — a new row in `references/stacks.md` and `references/stack-translation.md`, with build/test commands that `run_checks` can detect.
- **MCP heuristics** — a new check in `squad-kit/mcp/server.py` **with a test** that shows a positive and a negative case.
- **Translations** of the READMEs (`README.<lang>.md`, linked from the language selector at the top of `README.md`).

## Ground rules

1. **No dependencies** in the MCP server or the installers: Python 3.10+ standard library only.
2. **Contract stability:** paths under `.squad/`, required `##` headings, status keywords and MCP tool names/arguments are a contract with the agents. Changing them is a breaking change: update the agents, templates, tests and `CHANGELOG.md` together and bump `SERVER_VERSION`.
3. **Domain-agnostic core:** nothing in `skills/squad`, `agents/` or `rules/` may assume a business niche. Niche knowledge goes into a domain pack.
4. **Evidence over claims:** heuristics must say they are heuristics; never make a tool report something that did not run.
5. **Third-party material** (`design-md/`, `design-taste-frontend/`, `playwright-cli/`) keeps its upstream license and text. Do not edit it in place; follow the update notes in each folder's `UPSTREAM.md`/README, and keep `LICENSE` files and credits.
6. **Language:** own files in English; user-facing output follows the user's language at runtime (see "Language" in `skills/squad/SKILL.md`). The language test in `tests/test_repo.py` enforces this.

## Development

```bash
python -m py_compile squad-kit/mcp/server.py install_claude.py
python -m unittest discover -s tests -v
```

Try the installer against a scratch folder:

```bash
python install_claude.py --project /tmp/scratch-app
./install.sh /tmp/scratch-app      # Antigravity layout
```

Exercise the MCP by hand (one JSON-RPC message per line on stdin):

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python squad-kit/mcp/server.py
```

## Pull requests

- One topic per PR; describe the problem, the change and how you tested it (the PR template has a checklist).
- CI must be green (tests on Linux and Windows, Python 3.10 and 3.13, installer smoke test).
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).
- Add an entry under "Unreleased" in `CHANGELOG.md` for user-visible changes.

## Reporting security issues

Do not open a public issue for a vulnerability in the MCP server or installers. Use GitHub's private vulnerability reporting on this repository ("Security" tab → "Report a vulnerability").
