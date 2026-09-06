# ADR-0020 — Documentation is generated from the option schema and lives in the product

- **Status**: Accepted · **Date**: 2026-09-06
- **Depends on**: ADR-0012 · **Establishes**: P9

## Context

The system is defined by a declaration (ADR-0012), which is only usable if you can discover what you
may declare. Three consumers need that knowledge and normally get it three separate ways: the
settings UI has hand-built forms, the documentation is hand-written prose, and an agent gets nothing
and guesses.

Three sources for one truth is three ways to be wrong, and the failure is asymmetric — the settings
UI is exercised constantly and stays right, while the documentation quietly rots and the agent
produces plausible configuration that does not evaluate.

## Decision

**One option schema, three consumers.** Every option carries a type, a default, a description, an
example, and whether changing it applies live or needs a restart. From that single definition:

1. **The settings UI** is generated from the types. Forms are not hand-built per option.
2. **The documentation** is generated — both the published site and the in-product surface.
3. **The agent's vocabulary** is the same schema: what it may set, to what values, and what each
   means.

**Documentation is a surface inside the product**, not a website beside it. In the GUI, editing the
declaration shows the documentation for the option under the cursor, alongside the architecture and
the decision records. Declaring the system and reading about it are one activity.

**The agent reads what you read.** When it proposes a declaration change, the documentation for every
option it touched is shown beside the diff, so approval happens with the reasoning present rather
than from a bare patch.

An option without a description is an incomplete option, and CI can say so.

## Alternatives rejected

- **Hand-written documentation beside generated settings.** The status quo everywhere, and it drifts
  in one direction only: the code changes, the prose does not, and nobody notices until a user is
  misled.
- **Generated documentation, hand-built settings forms.** Halves the problem and keeps the expensive
  half — every new option still needs UI work, which is what makes people avoid adding options.
- **Documentation as a website only.** Forces a context switch out of the product at exactly the
  moment attention is scarcest, and gives the agent nothing at all.
- **Letting the agent read the published site.** Scraping our own documentation to recover structure
  we had and discarded.

## Consequences

- Every option needs a real description before it ships; a schema is only as good as its prose.
- The generated settings UI constrains what an option *can* be — an option whose type the generator
  cannot render either needs a new type or a different design. That constraint is deliberate.
- The published site and the in-product surface must render the same schema without diverging, which
  argues for the site being a thin consumer rather than a separate implementation.
- Documentation becomes part of the definition of done for a subsystem, not a follow-up task.
