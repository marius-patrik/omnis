# Omnis — Architecture

**Status: NORMATIVE.** This is the single source of truth for process topology, crate boundaries,
IPC contracts, and renderer separation. `VISION.md` is reference material and never overrides this
document. Changes to this file require an ADR in `notes/architecture_decisions.md`.

---

## 1. Product thesis

Omnis is a local-first desktop workspace whose entire presentation layer — renderer, layout
topology, input routing, keymap, chrome, and iconography — is a **configuration state of one engine**
rather than a set of alternative implementations.

A "theme" in Omnis is a named preset over an orthogonal capability matrix. The engine exposes every
axis independently; presets merely pick coordinates on those axes. If a visual target can only be
reached by adding code specific to that target, the engine is wrong, not the target.

**Non-goal:** Omnis is not a reimplementation of VS Code, Zed, or any chat client. It borrows their
*interaction shapes* as configuration presets.

---

## 2. Process topology

Omnis runs as several cooperating processes so that a crash or reload in one never takes down the
others.

```
                       ┌──────────────────────────────────────┐
   SURFACES            │  omnis-gui (Tauri)  │  omnis (CLI)   │  external harnesses
                       └─────────┬───────────┴────────┬───────┴──────────┬─────────┘
                                 │                    │                  │
                                 └────────── Substrate Bus ──────────────┘
                                                │
                       ┌────────────────────────┴────────────────────────┐
   DAEMON              │                     omnisd                      │
                       │  session state · scheduling · persistence · I/O │
                       └───┬──────────────┬──────────────┬───────────────┘
                           │              │              │
   WORKERS          ┌──────┴─────┐ ┌──────┴──────┐ ┌─────┴────────┐
                    │ pty/lang   │ │ omnis-      │ │ extension    │
                    │ multiplexer│ │ browser     │ │ host         │
                    └────────────┘ └─────────────┘ └──────────────┘
```

### 2.1 Process responsibilities

| Process | Owns | Never does |
|---|---|---|
| `omnisd` | Session state, scheduling, persistence, all blocking I/O, agent supervision | Render anything; depend on a GUI being attached |
| `omnis-gui` | Window, renderer, input capture, presentation state | Own durable state; block on I/O |
| `omnis` (CLI) | Scriptable surface over the same bus; `--json` on every command | Reimplement daemon logic |
| Browser worker | Chromium/CDP lifecycle, page capture | Touch the GUI process directly |
| Extension host | Untrusted third-party code, sandboxed | Share an address space with `omnisd` |

### 2.2 Substrate Bus

The IPC fabric. Two sockets with different guarantees:

- **Control socket** — request/response, ordered, typed, versioned. Configuration, commands, queries.
- **Stream socket** — high-volume unidirectional frames. Terminal output, screencast frames, agent
  token streams, log tails.

Contract rules:
- The wire schema is versioned and additive. A surface built against version *N* must run against
  daemon version *N+k*.
- Every message is serializable to JSON for the CLI and for debugging, whatever the binary encoding.
- Surfaces are stateless with respect to the daemon: any surface may attach, detach, or crash at any
  point without data loss.

---

## 3. The capability matrix

The core of the design. Five orthogonal axes; a preset is a point in this space.

| Axis | Setting | Values |
|---|---|---|
| Renderer engine | `workbench.renderer` | `dom-flexbox` · `terminal-cell-grid` |
| Layout topology | `workbench.layout.paradigm` | `chat-centric` · `ide-split` · `terminal-grid` · `vcs-dag` |
| Input routing | `workbench.inputBar.mode` | `global-hud` · `per-pane` · `hybrid` |
| Keymap | `workbench.keybindings` | `default` · `vscode` · `zed` · `vim` · `emacs` |
| Chrome & tokens | `workbench.window.*`, `workbench.theme.*` | see §5 |

**Invariant:** no product feature may branch on the *preset name*. Features branch on axis values,
or on capability queries, never on `if (theme === 'brand-claude')`. This invariant is testable and
must be covered by a lint.

A **brand preset** is therefore a data file — a set of axis values plus token values plus assets —
and nothing else. Adding a brand must require zero code changes.

---

## 4. Renderer separation

Two renderers, one view model.

```
                 ┌───────────────────────────────┐
                 │        View Model (Rust)      │   panes, focus, buffers,
                 │  renderer-agnostic scene tree │   selections, decorations
                 └───────────┬───────────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
   ┌────────────────────┐        ┌──────────────────────┐
   │  dom-flexbox       │        │  terminal-cell-grid  │
   │  React + Dockview  │        │  GPU cell matrix     │
   └────────────────────┘        └──────────────────────┘
```

**The rule that makes two renderers affordable:** feature code targets the view model, never a
renderer. A feature that cannot be expressed in the renderer-agnostic scene tree does not ship until
the scene tree grows to express it. Any feature implemented twice is a design defect.

- The scene tree is the abstraction boundary and must exist **before** the second renderer starts.
  Building `terminal-cell-grid` first as a fork of the DOM UI is the failure mode this repository
  exists to avoid.
- Renderer switching is a **restart-tolerant** operation in v1. Live hot-swap without restart is a
  goal, gated behind a measured spike, not an assumption.

---

## 5. Configuration

`settings.json` is the user-facing switchboard, JSON-with-comments, schema-validated, layered:

```
defaults  →  brand preset  →  user settings  →  workspace settings  →  runtime overrides
```

Later layers win. Every layer is inspectable; the settings UI must be able to answer "which layer
set this value?" for any key.

Presets live in versioned files, not in a database. **The database stores user data; configuration
stores configuration.** The `pgTable` sketches in `VISION.md` are explicitly rejected for appearance
presets.

---

## 6. Crate & package layout (target)

```
crates/
  omnis-core/          capability matrix, settings resolution, scene tree types
  omnis-proto/         Substrate Bus wire schema + codegen
  omnisd/              daemon: state, scheduling, supervision, persistence
  omnis-cli/           `omnis` binary
  omnis-term-ui/       cell-grid renderer (GPU cell matrix buffer)
  omnis-browser/       Chromium/CDP worker
  omnis-term-browser/  AXTree→cells and screencast→sixel/braille bridges
  omnis-ext-host/      sandboxed extension host
apps/
  desktop/             Tauri shell + React DOM renderer
packages/
  ui/                  renderer-agnostic view-model bindings for the DOM renderer
  presets/             brand presets (data only — no code)
```

Nothing in this tree exists yet. It is the target shape that epics build toward, and the reason
`ci.yml` already contains guarded Rust and web jobs.

---

## 7. Open decisions

Blocking decisions. Each must be resolved by an ADR before its dependent epic leaves `Backlog`.

| # | Decision | Blocks |
|---|---|---|
| D1 | Day-one user workflow — what does someone *do* with Omnis before any theming exists? | Everything; sequencing of E1 |
| D2 | Storage engine and shape for local-first user data (rejecting Postgres for config; undecided for data) | E6 |
| D3 | Trade-dress policy: which third-party names, marks, and icons may ship, and under what attribution | E4 |
| D4 | Target platform matrix and the primary platform for v1 | E2, E3 |
| D5 | Extension host compatibility target — VS Code API emulation vs. a native-first API | E8 |
| D6 | Agent provider adapter contract | E5 |
| D7 | Performance budgets: frame time, redraw latency, cold start, memory ceiling | E3, E7 |
| D8 | Renderer hot-swap: restart-tolerant only, or live | E3 |

---

## 8. Repository automation

The development pipeline is itself part of the architecture and is documented in `AGENTS.md`
(rules), `.github/workflows/` (enforcement), and `.github/scripts/` (implementation). The pipeline is
Python; that is deliberate and independent of the product stack.
