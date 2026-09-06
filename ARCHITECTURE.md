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
| Presentation mode | `workbench.presentation` | `cell-grid` · `widget` · `hybrid` |
| Layout topology | `workbench.layout.paradigm` | `chat-centric` · `ide-split` · `terminal-grid` · `vcs-dag` |
| Input routing | `workbench.inputBar.mode` | `global-hud` · `per-pane` · `hybrid` |
| Keymap | `workbench.keybindings` | `default` · `vscode` · `zed` · `cursor-claude` · `vim` · `emacs` |
| Chrome & tokens | `workbench.window.*`, `workbench.theme.*` | see §5 |

The first axis is **presentation, not renderer**. There is one renderer (§4); `cell-grid` and
`widget` are layout modes that emit into it. `hybrid` mixes them per pane — a cell-grid editor beside
a widget-laid-out settings panel is a legal configuration, not a special case. The transcript's
`workbench.rendererEngine: 'dom-flexbox' | 'terminal-cell-grid'` is superseded.

**Invariant:** no product code may branch on a *preset name*. Features branch on axis values or on
capability queries — never `if (theme === 'brand-claude')`. This is testable and must be covered by a
lint.

A **brand preset** is therefore a data file — axis values, token values, assets — and nothing else.
Adding a brand must require zero code changes.

**Agent persona is not an axis.** `VISION.md` §5 binds a theme to a provider, model, and reasoning
effort. Omnis does not. A preset may *suggest* a persona; it never sets one behind the user's back.

---

## 4. The renderer — one GPU compositor

**There is one renderer.** Terminal, graphical UI, web content, and 3D are not renderers; they are
**sources** that emit primitives into a single GPU frame graph.

```
   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐
   │ Cell-grid    │ │ Widget       │ │ Browser      │ │ Browser      │ │ 3D scene   │
   │ layout       │ │ layout       │ │ (semantic)   │ │ (raster)     │ │ layer      │
   └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └─────┬──────┘
          │                │                │                │               │
          └────────────────┴────────┬───────┴────────────────┴───────────────┘
                                    ▼
                    ┌───────────────────────────────────┐
                    │   Scene tree  (renderer-agnostic) │
                    └────────────────┬──────────────────┘
                                     ▼
                    ┌───────────────────────────────────┐
                    │  omnis-render — GPU compositor    │
                    │  batched primitives · frame graph │
                    │  damage tracking · material passes│
                    └────────────────┬──────────────────┘
                                     ▼
                              wgpu → Vulkan / Metal / DX12
```

### 4.1 Why one renderer

- **Text is text.** A terminal cell is a glyph run with fixed advance; a UI label is a glyph run with
  shaped advance. Same atlas, same pipeline, same shader. Two renderers would build that twice.
- **A browser is a content source, not a rendering engine.** Whether a page arrives as a semantic
  tree we lay out ourselves or as a screencast texture, it ends up as primitives in the same frame.
- **Effects that live in only one renderer become per-theme bolt-ons** — precisely what §3's
  invariant exists to reject. Shaders and particles must be available to every presentation mode or
  they are decoration for one theme.
- **One frame, one budget.** Compositing a terminal pane, a chart, a video, and a particle field in
  one pass is a scheduling problem with one answer. Two renderers make it two answers that disagree.

### 4.2 Primitives

The compositor's vocabulary is deliberately small; every source reduces to it.

| Primitive | Used by |
|---|---|
| Quad — solid, gradient, rounded, bordered, shadowed | backgrounds, panels, cell backgrounds, chrome |
| Glyph run — from a shared atlas, fixed or shaped advance | terminal cells, labels, code, semantic web text |
| Texture — sampled image or video frame | screencast rasters, icons, webview surfaces, render targets |
| Path — SDF or tessellated | vector icons, `lucide-animated`, graphs, DAG edges |
| Material layer — custom shader with declared inputs | 3D scenes, particle fields, backdrops, transitions |

Primitives are instanced and batched by class. Adding a source must not add a primitive class; if it
would, that is a design conversation, not a patch.

### 4.3 Sources

| Source | Emits | Note |
|---|---|---|
| Cell-grid layout | glyph runs on a fixed advance grid, background quads | "Terminal UI" is a **layout mode**, not an engine |
| Widget layout | rounded quads, glyph runs, textures, paths | The graphical UI |
| Browser — semantic | AXTree → widget layout → primitives | Keyboard-navigable, cheap, diffable |
| Browser — raster | CDP screencast → texture | For content we cannot or should not re-lay-out |
| 3D scene | depth-tested draws, instanced particles, custom materials | Own camera and depth buffer, composited as a layer |

**The DOM is not a renderer here.** A real DOM is still required for third-party webviews — VS Code
extension UIs expect one. Those are hosted out-of-process and composited as textures: a *source*,
never the renderer. No Omnis product UI is implemented in DOM.

### 4.4 3D, shaders, and particles

The material layer is a first-class primitive, not an effects add-on. It carries a shader, declared
uniform inputs, and a compositing mode, and it is available to every presentation mode — including
the cell grid, where a material layer renders behind or between glyph runs.

Two distinct uses, deliberately not conflated:

- **Chrome** — backdrops, transitions, agent-activity particle fields, the icon state machine's
  animation. Authored by Omnis and by presets.
- **Content** — shader playgrounds, 3D model preview, GPU-accelerated data visualization, anything a
  user or extension supplies.

The compositor supports both identically. Whether the *product* exposes authoring to users and
extensions — and on what sandboxing terms, since a hostile shader can hang a GPU — is D14, and it
sizes the epic very differently. The engine is built for both; the exposure is gated.

### 4.5 What this costs, stated plainly

Owning the renderer means owning text shaping, layout, hit-testing, IME, and **accessibility**. A
fully custom-rendered UI has no native accessibility tree; one has to be published deliberately
(UIA, AX, AT-SPI) or the application is unusable with a screen reader. That is a real obligation, not
a footnote — it is why `accessibility` is a first-class label and why it must appear in E3's
acceptance criteria rather than being discovered late.

### 4.6 Consequences for the rest of this document

- **The scene tree becomes more load-bearing, not less.** It is now the single input to the single
  renderer. E10 still lands before E3.
- **D8 largely dissolves.** With one renderer there is no renderer to hot-swap; switching between
  cell-grid and widget presentation is a layout change. Live switching becomes cheap rather than
  needing a spike. D8 is narrowed to whether *graphics device loss and adapter switching* are handled
  transparently.
- **A new baseline decision appears.** One GPU compositor means a minimum GPU capability, a graphics
  API choice, and a software-fallback answer for machines that cannot meet it (D11).

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
  omnis-render/        THE renderer: GPU compositor, frame graph, primitive batching,
                       glyph atlas and shaping, material/shader passes, damage tracking
  omnis-layout/        cell-grid and widget layout modes; both emit scene-tree primitives
  omnis-browser/       Chromium supervisor, CDP bridge, adblock
  omnis-web-source/    AXTree→layout and screencast→texture bridges (browser as a source)
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
| D8 | **Graphics device loss and adapter switching** — handled transparently, or surfaced. Narrowed from "renderer hot-swap", which §4.6 dissolves: with one renderer, switching presentation mode is a layout change. | E3 |
| D9 | **Subsystem admission criteria** — what a subsystem must satisfy to enter `omnisd` (bus-only communication, independent omission, resource budget, failure isolation). The daemon's subsystem list is long enough that this needs to be a gate, not a habit. | E1, and every subsystem epic |
| D10 | **Vault threat model** — what `mlock`, Argon2id parameters, and process injection actually defend against, and what they do not. Injecting secrets into child environments is a real exposure that needs stating before it is built. | E11 |
| D11 | **Graphics baseline** — API (wgpu over Vulkan/Metal/DX12, or native per platform), the minimum GPU capability required, and what happens on machines below it: software fallback, degraded mode, or refusal. One renderer makes this a hard floor for the whole application, not a per-feature concern. | E3, E20 |
| D12 | **Text stack** — shaping engine, glyph atlas strategy, subpixel and hinting policy, bidi and complex-script support, IME integration. Owning the renderer means owning all of it (§4.5). | E3 |
| D13 | **Webview compositing** — how out-of-process third-party webviews reach the frame: shared-texture zero-copy, readback, or native subsurface. Determines whether VS Code extension UIs are usable or merely present. | E8, E3 |
| D14 | **Shader and 3D exposure** — is the material layer authored only by Omnis and its presets (chrome), or also by users and extensions (content)? Exposure demands sandboxing, resource limits, and a hang-recovery story, since a hostile or careless shader can wedge a GPU. Sizes E20 by an order of magnitude. | E20 |

---

## 8. Repository automation

The development pipeline is part of the architecture: `AGENTS.md` (rules), `.github/workflows/`
(enforcement), `.github/scripts/` (implementation). The pipeline is Python; that is deliberate and
independent of the product stack.
