# Omnis — Roadmap

Authoritative list of epics and their sequencing. Every `epic`-labelled GitHub issue corresponds to
exactly one row here. Epics are containers: never implemented directly, only their child `Request`
issues are. Update this file whenever an epic is added, split, completed, or dropped
(`AGENTS.md` rule 13).

**Gate**: what must be true before the epic may leave `Backlog`.

---

## Phase 0 — Foundations

| # | Epic | Area | Gate | Scope |
|---|---|---|---|---|
| E0 | Repository, governance, autonomous pipeline | `area:ci` | — | Done. Everything else is produced by this pipeline. |
| D∗ | Architecture decisions D1–D10 | `area:docs` | — | Ten open decisions in `ARCHITECTURE.md` §7. Each is a `Request`, not code. |

## Phase 1 — The spine

| # | Epic | Area | Gate | Scope |
|---|---|---|---|---|
| E1 | Substrate Bus, daemon, process topology | `area:core` | D1, D9 | `omnis-proto` wire schema; control socket (JSON-RPC 2.0) and data socket (9-byte framed binary, opcodes `0x01`–`0x05`); additive versioning; `omnisd` conditional subsystem bootloader; the `Subsystem` trait; surface attach/detach; crash isolation. |
| E9 | Capability matrix and settings switchboard | `area:core` | E1 | Five orthogonal axes; layered resolution (`defaults → preset → user → workspace → runtime`); JSON schema; the `features` block that decides which subsystems initialize; live IPC updates; layer introspection; the lint enforcing no branching on preset names. |
| E10 | Renderer-agnostic view model | `area:core` | E9 | The scene tree: panes, focus, buffers, selections, decorations. **Must land before E3.** The abstraction that makes a second renderer affordable instead of a second product. |
| E2 | Tauri shell and window chrome engine | `area:ui` | D4 | The five pillars: frame styles, drag regions, traffic-light insets, vibrancy (`NSVisualEffectView`, Mica, Acrylic), corner radius and border metrics, menu-bar paradigms; dynamic dock/tray icon state machine. |
| E6 | Local-first persistence | `area:data` | D2 | PGlite store, schema, migrations, the config/data boundary, the sync boundary. |

## Phase 2 — The developer substrate

The subsystems that make Omnis a workspace rather than a shell. Each is independently omittable
(`ARCHITECTURE.md` §2.2) and each must pass D9's admission criteria.

| # | Epic | Area | Gate | Scope |
|---|---|---|---|---|
| E11 | Vault, SSH/GPG agent, secure process spawn | `area:core` | D4, D10, E1 | Argon2id KEK in `Zeroizing` with `mlock`; OS keychain bridging (Keychain, DPAPI, Secret Service); `omnis-ssh-agent` on `~/.omnis/ssh.sock`; `.env` injection into child memory maps, never disk and never agent context. |
| E12 | Terminals, PTY, containers | `area:core` | E1 | Native PTY manager, tmux control server, Bollard Docker pipes, resource supervisor; `PTY_STREAM` / `PTY_RESIZE` / `DOCKER_LOG` opcodes end to end. |
| E13 | Content-addressed storage and VFS | `area:data` | E6 | `omnis-cas`: FastCDC chunking, BLAKE3 keys, convergent encryption, reflink deduplication, multi-provider VFS mounts, central inotify watcher. |
| E14 | Universal VCS and stacked PRs (`ovcs`) | `area:core` | E1 | Dual Git/Sapling engine, atomic operation log, automated `absorb`, 3-way AST merge, stacked PRs across GitHub/GitLab/Forgejo, git alternates manager. |
| E15 | Task and build DAG engine | `area:core` | E13 | Manifest parsing (`package.json`, `Cargo.toml`, `Makefile`, `Taskfile.yaml`), cross-repository graph, CAS-timestamp skipping, parallel execution. |
| E16 | Packages and extensions — the binary substrate | `area:ext` | D5, E1 | The two universes kept separate: `omnis pkg` (project and system dependencies) versus `omnis ext` (client, editor, agent capabilities). Install, resolve, cache, grant. |
| E17 | LSP hub and DAP | `area:core` | E1, E12 | `omnis-lsp` multiplexer, `omnis-dap` implementation. |

## Phase 3 — The second renderer

| # | Epic | Area | Gate | Scope |
|---|---|---|---|---|
| E4 | Brand presets as pure data | `area:ui` | D3, E9 | Preset file format, token sets, asset packs, `lucide-animated` default icon set, typography and density profiles, keymap profiles, audio packs; and the proof that adding a brand requires zero code changes. |
| E3 | Terminal cell-grid renderer | `area:term` | D4, D7, D8, E10 | `omnis-term-ui`: GPU cell matrix buffer, WebGPU/WebGL blit, monospace metrics, 24-bit TrueColor with SGR attributes, 256-colour ANSI palettes, cursor shapes, pane-grid keyboard navigation, command-palette-first interaction, inline terminal inspector. |
| E7 | Terminal-grid browser bridge | `area:browser` | E3, D7 | `omnis-browser` Chromium/CDP worker; semantic mode (AXTree → styled cells with interactive coordinates and CDP navigation); pixel mode (screencast → Sixel / Unicode Braille); `auto`/`hybrid` selection and FPS budget. |

## Phase 4 — Agents, extensibility, mesh

| # | Epic | Area | Gate | Scope |
|---|---|---|---|---|
| E5 | Agent harness, audit stream, approval escrow | `area:agents` | D6, E1, E11 | Provider adapter contract; `omnis-agent` and the `@omnis/agent` MCP bridge; session supervision; immutable append-only audit stream with a one-click killswitch; escrow tickets with expiry. Decoupled from visual themes by `ARCHITECTURE.md` §3. |
| E8 | Extension host | `area:ext` | D5, E16 | `exthost-node` sandboxed runtime, plugin API surface, capability grants, VS Code compatibility shims. |
| E18 | Universal context fabric | `area:core` | E13, E1 | `ContextFragment` harvesting from code selections, terminal buffers, browser pages, and container logs; persistent sidebar shelf; `omnis://context/<id>` URIs. |
| E19 | Sync mesh and CRDT change log | `area:data` | E6, E13, D10 | Tailscale mesh sync, CRDT with hybrid logical clocks, P2P WebRTC mesh, cloud storage VFS, serialized PGlite mailbox. |

## Not scheduled

- Chat and social bridges (Matrix, iMessage). Present in the source `features` block; no gate, no
  demand, and every one is a third-party protocol commitment.
- Reproducing any third-party product's full feature set.
- Live renderer hot-swap without restart — a goal, gated behind D8 and a measured spike.
- Cloud accounts or multi-user collaboration. The mesh in E19 syncs *one user's* devices.

---

## Sequencing rationale

1. **E10 before E3.** The largest risk in the project is building the terminal renderer as a fork of
   the DOM UI. The view model must exist and be proven with one renderer before the second starts.
2. **E1 and E9 before every subsystem.** Subsystems are conditionally initialized from settings and
   speak only over the bus. Both mechanisms have to exist before there is anything to plug in, or the
   first three subsystems will hard-wire themselves to each other.
3. **D9 before Phase 2.** Seventeen subsystems is a lot of surface. Admission criteria — bus-only
   communication, independent omission, a resource budget, failure isolation — need to be a written
   gate, not a habit that erodes under deadline.
4. **E11 early.** The vault is not a feature bolted on later: terminals, VCS pushes, package
   installs, and agents all need secrets. Building them first means retrofitting secret handling into
   four subsystems.
5. **E13 before E15.** The task engine's whole caching claim rests on CAS timestamps.
6. **E9 before E4.** Presets are coordinates in the matrix; without the matrix they become the
   per-brand bolt-ons the design exists to reject.
7. **D1 is a slice, not a thesis.** The architecture already says what Omnis does. What it does not
   say is which path gets built first — and that choice determines which bus messages, which
   subsystem, and which surface come into existence first.
