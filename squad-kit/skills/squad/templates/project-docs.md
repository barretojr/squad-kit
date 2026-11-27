# Product documentation layout

Create this folder at the project root, next to the `.sln`/`.slnx` or `package.json` when there is one. It holds agent reports and working context; it is not a buildable project. `initialize_squad_docs` creates it and adds `.squad/` to `.gitignore`.

Paths and `##` headings are a fixed contract in English (the MCP validators read them). Report bodies are written in the language recorded in `.squad/stack.md`.

```text
.squad/
├── README.md
├── stack.md                         # Interview decisions (stack, language, deploy, accepted risks)
├── PROJECT_MAP.md                   # Confirmed index of screens, routes, data and tests
├── product/
│   ├── discovery.md                 # PM: equivalent products and build × integrate
│   └── field-research.md            # PM: users, APIs/integrations and sources
├── coordination/
│   ├── coord.md                     # Coord: scope, contracts, integrations, decisions
│   └── roadmap.md                   # The single prioritized, traceable backlog
├── design/
│   ├── visual-direction.md          # Designer: brand/logo, UX and visual direction
│   ├── design-system.md             # Design system: report
│   └── DESIGN.md                    # Design system: visual contract for the code
├── data/dba.md                      # Model, integrity and planned/applied migrations
├── backend/backend.md               # APIs, authentication and domain rules
├── frontend/frontend.md             # Screens, consumed contracts and real integration
├── frontend/visual-review.md        # UI reviewer: browser, viewports and evidence
├── security/appsec.md               # Threats, controls and security tests
├── quality/
│   ├── qa.md                        # Criteria, test matrix and real test evidence
│   ├── blind-code-critique.md       # Blind code critic
│   ├── spec-critique.md             # Spec/roadmap critic
│   └── finalizer.md                 # Independent completion gate
├── operations/devops.md             # Environments, pipeline and operations
└── evidence/                        # run_checks.md, deploy.md, frontend screenshots
```

Each agent file contains: status and date; context/evidence; decisions and assumptions; what needs to be done; plan and dependencies; what was done (in planning: no product implementation); validation with commands and real results; open items and links to sources/roadmap IDs. The owning agent updates its own report; Coord keeps the roadmap and the index.

Never write secrets, tokens, credentials, personal payloads or unanonymized customer data in these documents. Do not duplicate long research: Coord links the PM research and records only the decisions that follow from it.

`.squad/quality/finalizer.md` is the independent completion gate. It has one checklist row per required final check and records status plus evidence. It does not replace QA, frontend review or either code critic.
