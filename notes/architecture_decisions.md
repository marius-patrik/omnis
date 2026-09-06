# Architecture Decisions — process

How decisions are made and recorded. The decisions themselves live one per file in
[`notes/adr/`](adr/), and the published index is generated from those files — never hand-maintained
(`AGENTS.md` rule 2).

## When an ADR is required

- An open decision from `ARCHITECTURE.md` §8 is resolved.
- Any deviation from `ARCHITECTURE.md` is approved (`AGENTS.md` rule 3).
- Anything in `VISION.md` is promoted into the normative architecture. The vision is non-normative
  source material; it never binds the implementation by being written down, only by being promoted
  through a record here.

## Status values

| Status | Meaning |
|---|---|
| `Proposed` | Written, awaiting the maintainer's approval. Does **not** bind the implementation. |
| `Accepted` | Binding. Code is checked against it; a contradiction is a defect in the code or a new ADR. |
| `Superseded by ADR-NNNN` | Historical. Kept for the reasoning, never deleted. |

Records are **append-only**. A decision that turns out wrong gets a new ADR that supersedes it, with
the reason. Editing history erases the argument, which is the part worth keeping.

## Writing one

Create `notes/adr/NNNN-kebab-case-title.md` with the next free number. The docs site picks it up with
no further wiring: `.github/scripts/docs_hooks.py` discovers the directory, generates the index
table from each file's title and status line, and injects the navigation entries.

```markdown
# ADR-NNNN — <title>

- **Status**: Proposed · **Date**: YYYY-MM-DD · **Resolves**: D<n>
- **Supersedes**: ADR-MMMM  ·  **Promotes**: `VISION.md` §<n>

## Context
What forced the decision. Constraints, measurements, what broke.

## Decision
The choice, stated so that code can be checked against it.

## Alternatives rejected
Each with the reason it lost, not just its name. An ADR whose alternatives are strawmen is
worthless — the real ones are the plausible options someone will propose again in six months.

## Consequences
What this makes easy, what it makes hard, what it costs. State the costs plainly; an ADR that reads
as advocacy is a decision nobody can revisit honestly.

## What this forecloses
Optional. The doors this closes permanently.
```

## Scope limits

An ADR may fix a *structure* while explicitly declining to assert something adjacent — ADR-0009 and
ADR-0010 fix storage and secret-handling shapes while leaving the threat model to D10. Say so in a
**Scope limit** section rather than implying coverage the record does not have. A later decision may
then constrain an ADR without superseding it.
