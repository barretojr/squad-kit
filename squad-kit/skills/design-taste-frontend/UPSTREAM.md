# Upstream attribution

This folder vendors the skill **design-taste-frontend** from [leonxlnx/taste-skill](https://github.com/leonxlnx/taste-skill) (upstream folder `skills/taste-skill`, install name `design-taste-frontend`).

- **License:** MIT, Copyright (c) 2026 Leonxlnx. The full text is in [`LICENSE`](LICENSE) in this folder and must stay with any copy of it.
- **Reviewed:** license and repository checked on 2026-11-27.

## What is upstream and what is local

| Path | Origin |
|---|---|
| `references/`, `scripts/`, `assets/`, `library/` | Copied from upstream (not edited in this repository) |
| `UPSTREAM_SKILL.md` | Copy of the upstream `SKILL.md` (kept for reference) |
| `SKILL.md` | **Local adaptation** for the Squad (shorter workflow, Squad paths, MCP `audit_frontend_taste`) |
| `UPSTREAM.md` | Local (this file) |
| `LICENSE` | Upstream license text |

Until 2026-11-27 this repository carried two copies of the upstream suite (`taste-skill/` and `design-taste-frontend/`). They were merged into this folder; `library/` (palettes and type pairings that `scripts/start.mjs` reads) came from the old `taste-skill/` copy, which was the only one that had it.

## Third-party media inside the assets

Photographs, icons and fonts referenced by the assets are **not** covered by the MIT license above; they keep their own licenses (upstream sources them from open archives such as Wikimedia Commons and Unsplash, and fonts from Google Fonts). Their credits ship with the assets and must be kept:

- `assets/layout/img/credits.json`
- `assets/moments/_demo/credits.json`
- `assets/scenes/_demo/credits.json`
- `assets/icons/demo/icons-credits.json`
- `assets/ui/icons/icons-credits.json`

When a generated page uses one of these photographs, keep the credit line that the upstream scripts produce (`scripts/photos.mjs credits`). Never ship a brand logo from the icon set as if it were the product's own mark.

## Updating from upstream

Replace `references/`, `scripts/`, `assets/`, `library/`, `UPSTREAM_SKILL.md` and `LICENSE` with the upstream versions, keep the local `SKILL.md`, then update the review date above.
