# Omnis — Roadmap

Authoritative list of epics and their sequencing. Every `epic`-labelled GitHub issue corresponds to
exactly one row here. Epics are containers: they are never implemented directly, only their child
`Request` issues are. Update this file whenever an epic is added, split, completed, or dropped
(rule 13 in `AGENTS.md`).

Legend — **Gate**: what must be true before the epic may leave `Backlog`.

---

## Phase 0 — Foundations

| # | Epic | Area | Gate | Why it is first |
|---|---|---|---|---|
| E0 | Repository, governance, and autonomous pipeline | `area:ci` | — | Everything else is produced by this pipeline. |
| D∗ | Architecture decisions D1–D8 | `area:docs` | — | Eight open decisions in `ARCHITECTURE.md` §7 block later epics. Each is a `Request`, not code. |

## Phase 1 — The spine

| # | Epic | Area | Gate | Scope |
|---|---|---|---|---|
| E1 | Substrate Bus & process topology | `area:core` | D1 | `omnis-proto` wire schema, dual-socket transport, versioning rules, `omnisd` skeleton, surface attach/detach, crash isolation. |
| E2 | Tauri shell & window chrome engine | `area:ui` | D4 | Frameless/native/transparent frame styles, drag regions, traffic-light insets, vibrancy (mica/acrylic/sidebar/hud), corner radius, shadow elevation, dynamic dock/tray icon with state machine. |
| E6 | Local-first persistence | `area:data` | D2 | Storage engine choice, schema, migrations, sync boundary, what is config vs. what is data. |

## Phase 2 — The matrix

| # | Epic | Area | Gate | Scope |
|---|---|---|---|---|
| E9 | Capability matrix & settings switchboard | `area:core` | E1 | Five orthogonal axes, layered settings resolution (`defaults → preset → user → workspace → runtime`), JSON schema, live IPC updates, "which layer set this?" introspection, and the lint enforcing *no branching on preset name*. |
| E10 | Renderer-agnostic view model | `area:core` | E9 | Scene tree: panes, focus, buffers, selections, decorations. **Must land before E3.** The abstraction that makes two renderers affordable instead of two products. |
| E4 | Brand presets as pure data | `area:ui` | D3, E9 | Preset file format, token sets, asset packs, `lucide-animated` default icon set, and the proof that adding a brand requires zero code changes. |

## Phase 3 — The second renderer

| # | Epic | Area | Gate | Scope |
|---|---|---|---|---|
| E3 | Terminal cell-grid renderer | `area:term` | D4, D7, D8, E10 | GPU cell matrix buffer, WebGPU/WebGL blit pipeline, monospace metrics, 24-bit TrueColor + SGR attributes, 256-colour ANSI palettes, cursor shapes, pane-grid keyboard navigation, command-palette-first interaction, inline terminal inspector. |
| E7 | Terminal-grid browser bridge | `area:browser` | E3, D7 | `omnis-browser` Chromium/CDP worker; semantic mode (AXTree → styled cells with interactive cell coordinates and CDP navigation); pixel mode (screencast → Sixel / Unicode Braille); `auto`/`hybrid` mode selection and FPS budget. |

## Phase 4 — Extensibility & agents

| # | Epic | Area | Gate | Scope |
|---|---|---|---|---|
| E5 | Agent harness orchestration | `area:agents` | D6, E1 | Provider adapter contract, session supervision, approval gates, streaming, persona configuration. Explicitly **decoupled** from visual themes — see the review note in `VISION.md` §5. |
| E8 | Extension host | `area:ext` | D5, E1 | Sandboxed host process, plugin API surface, capability grants, compatibility shims. |

---

## Sequencing rationale

1. **E10 before E3.** The single largest risk in this project is building the terminal renderer as a
   fork of the DOM UI. The view model must exist and be proven with one renderer before the second
   one starts.
2. **D-decisions before their dependents.** Eight questions in `ARCHITECTURE.md` §7 are unanswered by
   the source material. Each is filed as a `Request` so it gets the same interpretation and
   confirmation gate as code work.
3. **E9 before E4.** Presets are coordinates in the matrix; the matrix has to exist first, or presets
   become the very bolt-ons the whole design rejects.
4. **D1 gates E1.** Until there is a day-one user workflow, "which messages does the bus carry" has
   no answer that is not guesswork.

## Not scheduled

- Reproducing any third-party product's full feature set.
- Live renderer hot-swap without restart (goal, gated behind D8 and a measured spike).
- Cloud sync, accounts, or multi-user collaboration.
