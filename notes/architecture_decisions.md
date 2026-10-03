# Architecture decisions — process

`ARCHITECTURE.md` is the normative system architecture. Supporting specifications under `docs/`
refine implementation contracts. ADRs record architectural choices, supersessions, and the reasoning
behind them. Historical source material in `notes/transcript.md` is never normative on its own.

ADR-0023 is the architecture reset that establishes OmnisOS, OmnisManager, OmnisAgent, OmnisControl,
the shared multidimensional graph, and the Agent worldline. Earlier ADRs remain binding only where
they do not conflict with ADR-0023 or the current normative architecture.

## When an ADR is required

- A change would alter a normative invariant in `ARCHITECTURE.md` or a supporting subsystem spec.
- A cross-component protocol or graph ownership rule changes.
- A previously accepted ADR must be superseded or narrowed.
- Historical/source material is intentionally promoted into normative architecture.

Pure implementation choices that preserve the normative contracts do not need ADRs.

## Status values

| Status | Meaning |
|---|---|
| `Proposed` | Written, awaiting maintainer approval; non-binding. |
| `Accepted` | Binding unless superseded by a later ADR or normative architecture reset. |
| `Superseded by ADR-NNNN` | Historical reasoning only; no longer binds implementation. |

Records remain append-only in substance: a changed decision gets a new ADR. Updating an older
record's status to point at its superseding ADR is allowed and expected.

## Specification sequence

```text
ARCHITECTURE.md
  -> supporting specs in docs/
  -> ADRs for unresolved architectural choices
  -> ROADMAP.md
  -> tracked implementation issues/plans
  -> code
```

Issues should track settled implementation work, not become the place where the architecture is
invented.

## Writing an ADR

Create `notes/adr/NNNN-kebab-case-title.md` with the next free number. Every ADR must contain:

- a parseable `# ADR-NNNN — Title` heading;
- a `**Status**:` line;
- `## Context`;
- `## Decision`;
- `## Alternatives rejected`;
- `## Consequences`.

The documentation site discovers ADRs automatically; do not maintain a second static index.
