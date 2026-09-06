# ADR-0017 — The TUI is dropped as a surface

- **Status**: Accepted · **Date**: 2026-09-06
- **Supersedes**: the two-backend model in [ADR-0001](0001-one-scene-tree-two-renderer-backends.md)
- **Closes**: D15

## Context

ADR-0001 established two renderer backends over one scene tree: the GPU compositor, and `omnis-tui`
rendering the same scene tree as ANSI escape sequences in a real terminal. The second backend brought
a parity contract (§9.4), a degradation ladder per primitive, terminal capability detection, kitty
and SGR input decoding, a terminal capability floor to decide (D15), and an epic to build it (E22).

Two things changed since. Remote access is now a **web surface over Tailscale** (ADR-0015), which
covers the case the TUI was mostly wanted for — reaching the workspace from elsewhere. And the
compositor targets WebGPU, so the browser already hosts the real interface rather than a reduced one.

That leaves the TUI carrying a large, permanent tax for a shrinking benefit.

## Decision

**There is one renderer backend: the GPU compositor.** It targets a desktop window natively and a
browser canvas over WebGPU. `omnis-tui` is not built.

What this does **not** remove:

- **`cell-grid` presentation mode stays.** The terminal *aesthetic* — fixed advance, ANSI palettes,
  pane-grid keyboard navigation, command-palette-first interaction — is a layout mode the GPU
  compositor draws, and was always separate from running in a terminal. The Zed-style look survives
  intact.
- **The CLI stays a surface.** `omnis` with `--json` on every command is unaffected; it is not a
  renderer.
- **The scene tree stays.** It remains the single input to the renderer and the abstraction feature
  code targets. One backend does not make it optional — it is what keeps sources from reaching into
  rendering.

What this removes: the `omnis-tui` crate, the parity contract, per-primitive terminal fallbacks (P7),
terminal capability detection, D15, and E22.

## Alternatives rejected

- **Keep both backends** (ADR-0001 as written). Honest, and expensive: every primitive needs a
  declared terminal fallback forever, the material layer can never render, and every new source pays
  a degradation tax. Justified when the TUI was the remote story; not justified once the web surface
  is.
- **Keep a reduced TUI** — a status view rather than a full surface. Sounds cheap and is not: it
  still needs a renderer, capability detection, and input decoding, and it sets an expectation of
  parity it does not meet. A CLI with good output serves that need without pretending to be a UI.
- **Drop the scene tree too**, since there is one backend. That would let sources reach into
  rendering, which is the coupling ADR-0001 existed to prevent. The abstraction earns its place with
  one backend.

## Consequences

- **A machine with no display and no browser gets the CLI only.** This is the real loss and it should
  be named rather than discovered: SSH into a headless box and there is no interactive Omnis, only
  `omnis` commands. If that becomes intolerable, this ADR is what gets superseded.
- **Accessibility gets more important, not less.** The TUI was one path to text-addressable output;
  with it gone, the compositor's published accessibility tree (UIA/AX/AT-SPI) is the *only* path.
  That work moves from important to non-negotiable.
- The roadmap loses E22 and shrinks E3's acceptance criteria. The parity clauses come out of the
  architecture.
- ADR-0001's core claim — sources are not renderers, and everything meets in one scene tree — is
  unaffected. Only its second backend is.
