# Architecture Decision Records

Numbered, append-only. An ADR is added when an open decision from `ARCHITECTURE.md` §7 is resolved,
or when any deviation from `ARCHITECTURE.md` is approved (rule 3 in `AGENTS.md`).

Each record states the decision, the alternatives that were rejected and why, and what the decision
forecloses. "We chose X because it is better" is not an ADR.

Template:

```markdown
## ADR-000N — <title>

- **Status**: Proposed | Accepted | Superseded by ADR-000M
- **Date**: YYYY-MM-DD
- **Resolves**: D<n> (ARCHITECTURE.md §7) — or: deviation from ARCHITECTURE.md §<section>
- **Issue**: #<decision issue>

### Context
What forced the decision. Constraints, measurements, deadlines.

### Decision
The choice, stated so that code can be checked against it.

### Alternatives rejected
Each with the reason, not just the name.

### Consequences
What this makes easy, what it makes hard, and what it rules out permanently.
```

---

*No decisions recorded yet. D1–D8 in `ARCHITECTURE.md` §7 are all open.*
