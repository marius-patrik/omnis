# Omnis — Architecture

**Status: NORMATIVE.** This is the single source of truth for process topology, crate boundaries,
IPC contracts, and renderer separation. `VISION.md` is reference material and never overrides this
document. Changes require an ADR in `notes/architecture_decisions.md`.

---

## 1. Product thesis

Omnis is a **headless daemon that owns everything durable**, with thin interchangeable surfaces
attached over IPC.

The daemon owns version control, packages, tasks, terminals, containers, language servers,
debuggers, an embedded browser, an agent runtime, a secrets vault, content-addressed storage, and a
sync mesh. The surfaces — a Tauri desktop app, a CLI, and any external harness — own nothing but
presentation and input. Closing a window, reloading the UI, or crashing a surface costs nothing.

Because the daemon owns behaviour, the presentation layer collapses into **configuration**. Renderer,
layout topology, input routing, keymap, chrome, and iconography are orthogonal axes; a "theme" is a
named point in that space, never a fork.

**We do not enumerate workflows.** The subsystems compose: a task DAG that reads a Cargo manifest, a
terminal whose secrets came from the vault, a browser page harvested into a context fragment, an
agent whose every action lands in the audit stream and whose risky ones wait in escrow. The
capability surface is the specification; the workflows are what users assemble from it. Specifying
them one by one would be both endless and wrong.

**Non-goal:** reimplementing VS Code, Zed, or any chat client. Their *interaction shapes* are
configuration presets.

---

## 2. Process topology

```
                       ┌──────────────────────────────────────┐
   SURFACES            │  omnis-gui (Tauri)  │  omnis (CLI)   │  external harnesses
                       └─────────┬───────────┴────────┬───────┴──────────┬─────────┘
                                 │                    │                  │ MCP/stdio
                                 └────────── Substrate Bus ──────────────┘
                                                │
                       ┌────────────────────────┴────────────────────────┐
   DAEMON              │                     omnisd                      │
                       │      OSB router · conditional subsystems        │
                       └───┬──────────────┬──────────────┬───────────────┘
                           │              │              │
   WORKERS          ┌──────┴─────┐ ┌──────┴──────┐ ┌─────┴────────┐
                    │ pty / lsp  │ │ omnis-      │ │ extension    │
                    │ / dap      │ │ browser     │ │ host (node)  │
                    └────────────┘ └─────────────┘ └──────────────┘
```

### 2.1 Responsibilities

| Process | Owns | Never does |
|---|---|---|
| `omnisd` | Session state, scheduling, persistence, all blocking I/O, subsystem supervision | Render anything; depend on a GUI being attached |
| `omnis-gui` | Window, renderer, input capture, presentation state | Own durable state; block on I/O |
| `omnis` (CLI) | Scriptable surface over the same bus; `--json` on every command | Reimplement daemon logic |
| Browser worker | Chromium/CDP lifecycle, page capture | Touch the GUI process directly |
| Extension host | Untrusted third-party code, sandboxed | Share an address space with `omnisd` |

### 2.2 Subsystems are conditional

`omnisd` initializes subsystems from the `features` block in `settings.json`. A user who has not
enabled Docker runs a daemon with no Docker subsystem — not a disabled one. This is what keeps a
platform of this size honest: **every subsystem must be independently omittable**, which forces it to
sit behind the bus rather than reach into its neighbours.

A subsystem implements one trait — initialize, shut down, and communicate only over the bus. A
subsystem that cannot be disabled without breaking another subsystem is a design defect.

### 2.3 Substrate Bus

Two sockets with different guarantees.

**Control** (`omnis-control.sock`, `\\.\pipe\omnis-control`) — JSON-RPC 2.0. Capability checks,
layout persistence, escrow transitions, extension registration, queries, context shelf edits.

**Data** (`omnis-data.sock`, `\\.\pipe\omnis-data`) — binary multiplexer, uniform 9-byte header:

```
[StreamID: u32][Opcode: u8][PayloadLength: u32]

0x01 PTY_STREAM   raw terminal stdout/stdin
0x02 PTY_RESIZE   [Cols: u16][Rows: u16]
0x03 DOCKER_LOG   demultiplexed container logs
0x04 CAS_CHUNK    decrypted FastCDC blob payloads
0x05 CDP_BINARY   CDP screencast frames, Sixel rasters
```

Contract rules:

- The wire schema is **versioned and additive**. A surface built against version *N* runs against
  daemon version *N+k*.
- Every control message is expressible as JSON, for the CLI and for debugging, whatever the encoding.
- Surfaces are **stateless with respect to the daemon**. Any surface may attach, detach, or crash at
  any point without data loss.
- New opcodes are appended, never renumbered.

---

## 3. The capability matrix

Five orthogonal axes. A preset is a point in this space.

| Axis | Setting | Values |
|---|---|---|
| Renderer engine | `workbench.rendererEngine` | `dom-flexbox` · `terminal-cell-grid` |
| Layout topology | `workbench.layout.paradigm` | `chat-centric` · `ide-split` · `terminal-grid` · `vcs-dag` |
| Input routing | `workbench.inputBar.mode` | `global-hud` · `per-pane` · `hybrid` |
| Keymap | `workbench.keybindings` | `default` · `vscode` · `zed` · `cursor-claude` · `vim` · `emacs` |
| Chrome & tokens | `workbench.window.*`, `workbench.theme.*` | see §5 |

**Invariant:** no product code may branch on a *preset name*. Features branch on axis values or on
capability queries — never `if (theme === 'brand-claude')`. This is testable and must be covered by a
lint.

A **brand preset** is therefore a data file — axis values, token values, assets — and nothing else.
Adding a brand must require zero code changes.

**Agent persona is not an axis.** `VISION.md` §5 binds a theme to a provider, model, and reasoning
effort. Omnis does not. A preset may *suggest* a persona; it never sets one behind the user's back.

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
renderer. A feature that cannot be expressed in the scene tree does not ship until the scene tree
grows to express it. Any feature implemented twice is a design defect.

The source material describes the switch but never the shared representation. The scene tree is this
document's addition, and it is the single highest-leverage decision in the project.

- The scene tree must exist **before** `terminal-cell-grid` starts. Building it first as a fork of
  the DOM UI is the failure this repository exists to avoid.
- Renderer switching is **restart-tolerant** in v1. Live hot-swap is a goal gated behind a measured
  spike (D8).

---

## 5. Configuration

`settings.json` is the user-facing switchboard: JSON-with-comments, schema-validated, layered.

```
defaults  →  brand preset  →  user settings  →  workspace settings  →  runtime overrides
```

Later layers win. Every layer is inspectable; the settings UI must answer "which layer set this?"
for any key.

**Configuration lives in files; user data lives in the store.** Presets, keymaps, and feature flags
are versioned, diffable, shareable artifacts. The store — PGlite, embedded, per `VISION.md` §9.6 —
holds workspaces, tabs, chat, audit, CAS metadata, VCS state, and context fragments. The transcript's
`brandAppearanceProfiles` table crosses that line and is not adopted.

---

## 6. Crate and package layout

Following the source layout (`VISION.md` §9.2), with `omnis-term-ui` split out of `omnis-browser`
because a renderer and a browser supervisor have no reason to share a crate.

```
crates/
  omnis-core/          shared RPC models, schema types, OSB contracts, capability matrix,
                       settings resolution, scene tree types
  omnisd/              headless daemon; conditional subsystem bootloader
    src/subsystems/    one module per subsystem, each independently omittable
  omnis-cli/           `omnis` executable, `--json` on every command
  omnis-gui/           Tauri desktop host and window manager
  omnis-agent/         agent engine and MCP server binary
  omnis-lsp/           LSP multiplexer hub
  omnis-dap/           Debug Adapter Protocol implementation
  omnis-browser/       Chromium supervisor, CDP bridge, adblock
  omnis-term-ui/       GPU cell-matrix renderer
  omnis-term-browser/  AXTree→cells and screencast→sixel/braille bridges
  omnis-cas/           FastCDC chunking, convergent encryption, VFS
packages/
  core/                Cordis microkernel, context definitions, dsh-compat
  agent-sdk/           npm package `@omnis/agent`
  exthost-node/        isolated Node.js runtime for VS Code extensions
  frontend/            webview shell (Dockview, shadcn/ui)
  presets/             brand presets — data only, no code
```

None of this exists yet. It is the target shape epics build toward, and the reason `ci.yml` already
carries guarded Rust and web jobs.

---

## 7. Open decisions

Each must be resolved by an ADR before its dependent epic leaves `Backlog`.

| # | Decision | Blocks |
|---|---|---|
| D1 | **First vertical slice** — which single path through the substrate is built first, end to end, to prove the bus, the daemon lifecycle, and one surface. Not a product thesis: the capability surface is the spec. This is a sequencing choice. | E1, and the ordering of everything after |
| D2 | **Config/data boundary** — PGlite is the store (§5), so the engine is settled. What remains: which entities are configuration in files versus data in the store, and where the sync boundary falls. | E6 |
| D3 | **Trade-dress policy** — which third-party names, marks, and icons may ship, and under what attribution. | E4 |
| D4 | **Platform matrix** — which platforms, and which is primary for v1. Vibrancy, Mica/Acrylic, traffic lights, and `mlock` all diverge. | E2, E3, E11 |
| D5 | **Extension host compatibility target** — VS Code API emulation via `exthost-node`, or a native-first API with shims. | E8 |
| D6 | **Agent provider adapter contract.** | E5 |
| D7 | **Performance budgets** — frame time, redraw latency, cold start, memory ceiling. | E3, E7 |
| D8 | **Renderer hot-swap** — restart-tolerant only, or live. | E3 |
| D9 | **Subsystem admission criteria** — what a subsystem must satisfy to enter `omnisd` (bus-only communication, independent omission, resource budget, failure isolation). The daemon's subsystem list is long enough that this needs to be a gate, not a habit. | E1, and every subsystem epic |
| D10 | **Vault threat model** — what `mlock`, Argon2id parameters, and process injection actually defend against, and what they do not. Injecting secrets into child environments is a real exposure that needs stating before it is built. | E11 |

---

## 8. Repository automation

The development pipeline is part of the architecture: `AGENTS.md` (rules), `.github/workflows/`
(enforcement), `.github/scripts/` (implementation). The pipeline is Python; that is deliberate and
independent of the product stack.
