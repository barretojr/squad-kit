# Domain packs

The `squad` skill holds no niche knowledge. When a business type keeps coming back, create a separate **domain pack** (e.g. `skills/<domain-name>/SKILL.md`) and let the squad just point to it.

A domain pack contains only what is specific to the niche:

- glossary and main business flows;
- starting data model (entities and relations);
- typical integrations, with official links and usage constraints;
- business rules and known pitfalls (platform policies, consent, limits);
- suggested vertical slices and extra interview questions;
- (optional) scaffold snippets.

How the squad uses it:

1. If the user names a domain pack (or it is installed and the request clearly belongs to that niche), read it after the generic interview and **add** its extra questions to the same block.
2. Decisions are still recorded in `.squad/stack.md` and the roadmap.
3. Without a pack, `@PM` researches the domain from the user's description. Never assume a niche.

Hygiene rule: if a squad rule, template or tool mentions a specific niche, it is in the wrong place; move it to a pack.

Contributions: domain packs are a good first PR. Use the "Domain pack" issue template and follow `CONTRIBUTING.md`.
