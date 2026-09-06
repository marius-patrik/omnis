# ADR-0018 — Services are backends of domain subsystems

- **Status**: Accepted · **Date**: 2026-09-06
- **Depends on**: ADR-0001, ADR-0011, ADR-0013 · **Applies**: P2, P10

## Context

A power user's day runs through services they do not own: ChatGPT, DeepSeek, Google, YouTube,
Netflix, and a hundred others. Each has its own interface, its own conventions, and no relationship
to any of the others. Omnis should be able to present them through interfaces we control, and to
present *several* of them through **one** interface — a single streaming view over YouTube, Netflix,
and whatever else, the way a single VCS view already spans Git and Sapling.

The temptation is to treat this as a new subsystem class with new machinery. It is not. Almost all of
it is two abstractions that already exist, which is why it is worth writing down before anyone builds
a third.

## Decision

**A service is a backend of a domain subsystem.** YouTube is to `streaming` what `git` is to `vcs`.

```
domain: streaming            one interface, one schema
  backends:
    youtube    → api adapter          official API where one exists
    plex       → declared adapter     a mapping, no code
    <anything> → browser source       works immediately, no integration
```

Three parts, each landing on an existing mechanism:

| Concern | Mechanism |
|---|---|
| **Presentation** — how the service appears | A **source** emitting scene-tree primitives (ADR-0001) |
| **Action** — doing something to it | A **capability** over the bus, brokered and escrow-gated (§7) |
| **Aggregation** — several services, one interface | A **domain schema** every backend maps onto |

Only the third is new. Presentation and action are the scene tree and the bus, unchanged.

### The universal translator already exists

`omnis-web-source`'s semantic mode — AXTree to layout to primitives — *is* the "show anything"
translator. Any service with a web interface is renderable today, as real primitives rather than a
rectangle of pixels: keyboard-navigable, themeable, and legible to an agent. No new machinery.

### Progressive, with no cliff

| Tier | What it is | Cost |
|---|---|---|
| 0 | Raster — screencast into a texture | Nothing; always works |
| 1 | **Semantic translation** — AXTree to primitives | Nothing; the default |
| 2 | **Declared adapter** — a mapping from the service to the domain schema | Data, not code (P10) |
| 3 | **API adapter** — the service's own API | An adapter subsystem, and credentials |

Everything starts usable at tier 1 and is upgraded in place. Nothing waits on an adapter, and writing
one is a declaration change — which also means a service that breaks its DOM is fixed by editing
data, not by shipping a release.

### Domain schemas are small and explicit

A domain names its entities, its actions, and — importantly — which capabilities a backend may
**decline**. Not every provider supports every action, and a schema that assumes they all do produces
an interface full of controls that silently fail.

## Alternatives rejected

- **A bespoke integration per service.** Where every comparable product ends up: N integrations, no
  composition, and each one rotting independently. It also cannot deliver the thing actually asked
  for — *one* interface over several providers.
- **Iframes and webviews, unstyled.** Cheap and it is not an interface; it is a browser with extra
  steps, and nothing aggregates.
- **A new "service" subsystem class with its own machinery.** Duplicates the backend pattern that
  already governs VCS, task runners, and agent harnesses, and would drift from it.
- **Scraping everything at tier 2 with no tier 1.** Makes every service a project before it is usable
  at all, and guarantees a long tail that never gets done.

## Consequences

- Adding a service is a declaration; removing one removes it completely, integration included
  (ADR-0013).
- Tier-2 adapters break when services change their markup. That is inherent, and the mitigation is
  that a fix is data — not that breakage is avoidable.
- Credentials go through the vault (ADR-0010): referenced by name, injected, never in agent context.
- **Terms of service is a decision, not a technical question.** Re-presenting some services through
  our own interface is contractually restricted regardless of feasibility, and which services we ship
  adapters for needs the same treatment as trade dress (D3).
- **DRM playback cannot be a source.** Protected content cannot be composited into a scene tree we
  own. It is delegated instead — see ADR-0019 — and the schema must therefore let a backend decline
  the playback capability while still supplying search, metadata, and queue.
