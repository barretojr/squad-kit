# Market discovery (before the interview)

Goal: before asking about the stack, learn **what already exists** that solves the request, fully or in part, so the interview offers informed choices (build, integrate or adapt) and the plan does not reinvent what is already a product, library or API.

Owner: `@PM` (in `lite`, the Architect). Output: `.squad/product/discovery.md`, written in the user's language. Target length: short; this is reconnaissance, not a market study.

## When to run

- Always in greenfield with a "build/create…" request.
- In brownfield, only for the new feature requested (not the whole product).
- Skip it if the user explicitly says "don't research" or if `.squad/product/discovery.md` already exists and covers the request.
- Without web access: record "discovery pending: no web access", never invent products or URLs, and go to the interview.

## What to gather (primary sources, direct URL and access date)

1. **Equivalent products (3 to 5):** who already does this, for whom, pricing model, what they do well and what users complain about (only with a public source). Used for scope cuts and differentiation, not for copying.
2. **Reusable building blocks:** for each core capability of the request, what already exists:
   - official API/service (e.g. a messaging channel, a payment provider, a data source);
   - maintained open-source library/SDK (license, latest release; stars alone are not a criterion);
   - official template/starter of the likely stack.
3. **Constraints that change the architecture:** terms of use, platform policies, account approvals, usage-based costs, rate limits, opt-in/consent requirements, bans on unofficial automation. See `references/integrations.md`.
4. **Dependency risks:** unofficial API, service without SLA, pricing that scales with usage, lock-in.

## Build × integrate × adapt

Record one row per core capability:

| Capability | Options found | Recommendation | Reason | Cost/risk |
|---|---|---|---|---|
| [e.g. sending messages] | [official API X; unofficial library Y] | integrate X | [policy, stability] | [cost per message; account approval] |

Rules:

- Prefer the **official API** over unofficial automation; if the only viable option is unofficial, mark it high risk and bring it to the interview.
- **Integrate** when the block is not the product's differentiator; **build** what is.
- Never recommend working around terms of use, CAPTCHAs, paywalls or technical blocks.

## How it feeds the interview

Bring at most **two** discovery questions into the interview block, only when the answer changes the architecture. Example formats:

- "For [capability], the official path is [X] (requires [approval/cost]). Use X, use [alternative] accepting the risk, or leave it out of the MVP?"
- "[Product] already does [part]. Integrate with it or build our own?"

Show the user a 3–5 line discovery summary together with the questions.

## Template for `.squad/product/discovery.md`

```markdown
# Discovery — [request in one sentence]

- **Date:** [YYYY-MM-DD] · **Web access:** [yes/no]

## Equivalent products
| Product | For whom | Price | Strengths | Observed gaps | Source (URL, date) |
|---|---|---|---|---|---|

## Building blocks and decision
| Capability | Options | Recommendation | Reason | Cost/risk |
|---|---|---|---|---|

## Constraints affecting the architecture
- [policy/limit/approval — source]

## Proposed differentiator
- [what this product does that the equivalents do not, or "none: it is an in-house version"]

## Questions brought to the interview
1. [...]
```

Keep facts, inferences and recommendations apart. No market numbers without a source.
