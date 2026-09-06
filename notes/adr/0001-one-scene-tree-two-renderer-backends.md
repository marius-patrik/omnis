# ADR-0001 — One scene tree, two renderer backends

- **Status**: Accepted · **Date**: 2026-09-06 · **Narrows**: D8
- **Supersedes**: `VISION.md` §6's two-renderer switch

## Context

The transcript proposes two renderers — `dom-flexbox` and `terminal-cell-grid` — selected by a
setting, and never describes a representation both consume. That means every pane, dialog, editor,
and settings screen is implemented twice.

The maintainer then set two requirements the transcript does not cover: a *single* renderer
responsible for browser rendering and terminal alike, extended to 3D, shaders, and particles; and a
TUI surface that genuinely runs in a terminal rather than merely looking like one. Those are only
contradictory while "renderer" is one concept.

## Decision

One **scene tree**. Cell-grid layout, widget layout, web content, and 3D are **sources** that emit
into it. Two **renderer backends** consume it: `omnis-render` (GPU compositor, desktop window) and
`omnis-tui` (ANSI, a real terminal, local or over SSH).

Five primitive classes only — quad, glyph run, texture, path, material layer. Adding a source must
not add a primitive class. **Every primitive declares a terminal fallback**, enforced at the type
level; a primitive without one cannot enter the scene tree.

## Alternatives rejected

- **Two renderers with no shared representation** (the transcript). Every surface built twice,
  features drift, and the second renderer becomes a second product.
- **One GPU renderer only.** Cannot run over SSH, in `tmux`, or headless. Fails a stated requirement.
- **TUI as a degraded mode of the GPU renderer** — software-rasterise, downsample to cells. Inverts
  the abstraction, still needs a GPU stack, and produces pixel mush instead of text: no selection,
  no copy, no screen reader.
- **DOM as the second backend.** Reintroduces a browser engine inside the product UI, with the
  styling, performance, and parity problems that motivated leaving it.

## Consequences

Owning the renderer means owning text shaping, hit-testing, IME, and **accessibility** — a custom
renderer publishes no native accessibility tree unless built to, so UIA/AX/AT-SPI belongs in E3's
acceptance criteria. The scene tree must land before either backend. Adding a primitive class is a
two-backend change, deliberately expensive. The material layer has no terminal equivalent and
renders a static fallback.

## What this forecloses

Any feature that cannot be expressed as scene-tree primitives with a working terminal fallback. That
is the intended constraint: a feature that cannot degrade is a scene-tree design problem, fixed by
extending the scene tree, never by branching on the backend.
