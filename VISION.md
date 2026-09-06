# Omnis — Vision (Reference Only)

> **Status: NON-NORMATIVE.** This is a transcript-derived record of the scoping conversation that
> produced Omnis. It is source material. It is **not** a specification and does **not** override
> `ARCHITECTURE.md`. Where the two disagree, `ARCHITECTURE.md` wins.
>
> **Provenance:** Google Gemini conversation "App Scoping Technical Specifications Discussion"
> (`gemini.google.com/app/545cf54445afcd33`). First captured 2026-09-06 (partial); **completed
> 2026-09-06** — all 20 turns, 79,181 characters. No gaps remain. See
> [notes/vision_capture.md](notes/vision_capture.md) for provenance detail.

---

## Table of contents

1. [What Omnis is](#1-what-omnis-is)
2. [Brand parity and dynamic appearance](#2-brand-parity-and-dynamic-appearance)
3. [Native window styling: the five pillars](#3-native-window-styling-the-five-pillars)
4. [Typography, density, audio, icon state machines](#4-typography-density-audio-icon-state-machines)
5. [System personality packages: behavioural forking](#5-system-personality-packages-behavioural-forking)
6. [The terminal-native UI engine](#6-the-terminal-native-ui-engine)
7. [The settings switchboard](#7-the-settings-switchboard)
8. [Terminal-grid web browser](#8-terminal-grid-web-browser)
9. [Master specification](#9-master-specification)
10. [Reference implementation sketches](#10-reference-implementation-sketches)
11. [Review notes](#11-review-notes)

---

## 1. What Omnis is

> Universal Developer Workspace & Local-First Personal Data Operating System.

Two ideas run through the whole conversation, and they are not independent.

**The substrate.** Omnis is a headless daemon that owns everything durable — version control,
packages, tasks, terminals, containers, language servers, debuggers, an embedded browser, an agent
runtime, a secrets vault, content-addressed storage, and a sync mesh — with thin, interchangeable
surfaces attached over IPC. The surfaces are a Tauri desktop app, a CLI, and any external harness
(Claude Code, Codex CLI, Aider, Cursor). Nothing important lives in the window.

**The switchboard.** Because the substrate owns behaviour rather than the UI, the entire
presentation layer — renderer, layout, input routing, keymap, chrome, iconography, and even agent
persona — becomes a *configuration state of one engine*. A "theme" is a named point in an orthogonal
capability matrix, never a fork.

The user's framing, verbatim:

- *"should be able to configure main app icon with us defaul using a lucide-animated icon but
  support anything - I want vscode icon github icon and agent icons - claude, kimi, codex,
  deepseek, -- these should come with themes that make the app actually match their native apps as
  close as possible"*
- *"a zed theme that basically draws the entire ui as terminal - all of this should be supported by
  native features not boltons per theme"*
- *"there should be a setting for global input bar or per chat input bar and a chat centric or ide
  layout setting or something like that and so on that the settings just toggle to achieve their
  target style"*
- *"for the terminal based renderer we need to actually support the full app including web browser"*
- *"incorporate everything new we scopped and audit gaps"* / *"definitely not complete"* /
  *"whats wrong we need the full master spec"*

**The load-bearing principle**: every visual target must be reachable by toggling settings that
exist independently of any brand. If a look needs code specific to that look, the engine is wrong.

---

## 2. Brand parity and dynamic appearance

Namespace: `omnis.appearance`. Called the **Dynamic Brand Skinning Engine**.

### 2.1 Dynamic app icon and window chrome engine

- **Tauri native dock/tray integration** — the app icon (Dock on macOS, Taskbar/Tray on
  Windows/Linux) hot-swaps vectors or animated frames via `tauri::AppHandle::set_icon`.
- **Default state** — `lucide-animated`: micro-animated SVG components reacting to workspace events,
  sync status, and agent activity.
- **Universal asset support** — static SVGs, animated web components, or `.icns`/`.ico` packs.

### 2.2 Brand theme presets

| Preset | Character |
|---|---|
| `brand-default` | Developer dark/light, Lucide-animated iconography, high-contrast glassmorphism |
| `brand-claude` | Warm parchment/charcoal, terracotta/amber accent glows (`#CC785C`), humanist typography, restrained minimalism |
| `brand-github` | GitHub dark/dimmed/light, electric purple/blue interactive states (`#2f81f7`), dense technical layouts |
| `brand-deepseek` | Midnight-navy backdrops, neon cyan/teal accents (`#00E5FF`), telemetry readouts |
| `brand-kimi` | Soft violet/indigo gradients, playful rounded geometry, airy spacing |
| `brand-codex` / `brand-vscode` | Editor-first chrome, high-density explorer trees, blue/orange accents |
| `brand-zed` | Terminal cell-grid renderer (§6) |

---

## 3. Native window styling: the five pillars

Window styling *"dictates how the physical application window sits on your OS desktop"* — structural
chrome and OS integration, not colour tokens.

**1. Frame architecture and titlebar mechanics.** Frameless canvas with the OS titlebar removed
(`decorations: false`), header rendered in HTML/CSS with `data-tauri-drag-region` — enabling either
Claude's minimalist floating header or VS Code's integrated command center. Alternatively a native
integrated titlebar with translucent background mixing, for targets that keep standard OS buttons.

**2. Traffic lights and window control positioning.** On macOS the red/yellow/green lights float
inside the sidebar or header at custom offsets (`titleBarStyle: "transparent"`, custom inset margins)
rather than pinned top-left. On Windows and Linux, custom-rendered minimize/maximize/close buttons
styled to the active palette — sharp geometric for DeepSeek, rounded soft for Kimi.

**3. OS-level vibrancy and frosted glass.** macOS `NSVisualEffectView` materials (`hudWindow`,
`sidebar`, `underWindowBackground`); Windows 11 Mica and Acrylic, so backdrops tint and blur against
the desktop wallpaper.

**4. Geometry, corner radius, border metrics.** Window corner radii matched programmatically to the
active OS standard or brand profile. Border widths and outer shadow layers — VS Code's sharp 1px
high-contrast borders versus Claude's borderless soft-shadow elevation.

**5. Menu bar paradigms.** Minimalist header menus replacing OS drop-downs with icon triggers or a
command palette embedded in the titlebar; or traditional native application menus, toggled
dynamically when switching to editor-heavy themes.

### Window styling schema

```ts
windowStyling: jsonb('window_styling').$type<{
  frameStyle: 'frameless-custom' | 'native-integrated' | 'transparent-overlay';
  titlebarHeightPx: number;
  trafficLightsPosition: { x: number; y: number };
  windowCornerRadius: string;
  vibrancyMaterial: 'none' | 'sidebar' | 'hud' | 'mica' | 'acrylic';
  borderGlowColor: string;
  shadowElevation: 'flat' | 'subtle' | 'deep' | 'floating';
  hideNativeWindowControls: boolean;
}>().notNull(),
```

---

## 4. Typography, density, audio, icon state machines

**1. Typography engines and font-stack metrics.** Native apps use proprietary stacks and optical
sizing rules that define their visual voice. Claude: humanist warm sans-serif, generous line-height,
slightly heavier body weights (Inter Display, custom serif headers). VS Code: high-density monospace
(Fira Code, JetBrains Mono) with compact UI font metrics (Segoe UI / San Francisco at 11–12px).
DeepSeek: sharp geometric typography with monospace data accents and high-contrast tabular numerals.

**2. Layout psychology and information density.** Branding is how space is partitioned. The
Claude/Kimi aesthetic: generous padding, floating rounded cards, soft drop shadows, center-aligned
conversational focus, minimal structural lines. The VS Code/GitHub aesthetic: dense multi-split
grids, razor-sharp 1px bounding borders, strict hierarchical tree indentation, zero wasted vertical
pixels.

**3. Brand-specific sound and haptic cues.** Claude/DeepSeek: subtle low-frequency haptic clicks or
quiet ticks when agents finish reasoning blocks, stream tool output, or require approvals. VS
Code/GitHub: crisp mechanical keyboard ticks, clean commit-success chimes. Setting:
`workbench.audioFeedback: "brand-native" | "muted" | "subtle"`.

**4. App icon state machines.**

| State | Behaviour |
|---|---|
| Idle | Brand default icon |
| Agent running / thinking | Icon pulses, spins, or animates internal vectors |
| CI failure / error | Brand accent ring shifts to a warning red glow |
| Action required (escrow pending) | Badge count, or amber flash |

**5. Native context menus and command palette styling.** Right-click menus and the Omni-Bar
(`Cmd/Ctrl + K`) match the brand: Claude-themed menus use rounded pill-shaped hover states with soft
icon alignment; VS Code-themed menus render sharp high-density rectangular rows with keybindings
right-aligned.

### `BrandProfileSpecification`

```ts
export interface BrandProfileSpecification {
  id: string;               // 'claude'|'github'|'vscode'|'deepseek'|'kimi'|'default'
  displayName: string;

  appIcon: {
    vectorSvg: string;
    isAnimatedLucide: boolean;
    stateAnimations: {
      thinking: 'pulse' | 'spin' | 'glow' | 'morph';
      error: string;
      pendingApproval: string;
    };
  };

  windowStyling: {
    frameStyle: 'frameless-custom' | 'native-integrated' | 'transparent-overlay';
    trafficLightsInset: { top: number; left: number };
    cornerRadius: string;
    vibrancy: 'none' | 'sidebar' | 'hud' | 'mica' | 'acrylic';
    shadowElevation: 'flat' | 'subtle' | 'deep' | 'floating';
  };

  typography: { uiFontFamily: string; /* … */ };

  audio: {
    enabled: boolean;
    soundPack: 'claude-soft' | 'vscode-mech' | 'minimal' | 'muted';
  };

  tokens: {
    background: string; foreground: string;
    primaryAccent: string; secondaryAccent: string;
    border: string; sidebarBackground: string; cardBackground: string;
  };
}
```

---

## 5. System personality packages: behavioural forking

The pivotal turn. The model's own framing:

> If "still not enough" means skinning layout tokens and window frames isn't capturing the soul of
> these applications, it is because a brand theme in Omnis must fundamentally alter how the
> operating system behaves, not just how it looks.

**1. Brand-specific interaction paradigms.**

- *Claude / Kimi*: chat-centric and artifact-driven. Clicking agent-generated code does not open an
  editor tab — it renders an interactive, live-executing Artifact card that floats or splits
  dynamically. Navigation is minimalist and search-first; no heavy file trees unless summoned.
- *VS Code / Codex*: file-system and workspace-centric. Instant multi-root explorer tree, strict
  split grids, inline diagnostics, persistent terminal panes, command-palette mastery.
- *GitHub / DeepSeek*: PR, issue, and telemetry-centric. The primary view is a live Smartlog DAG or
  git graph wired to issue streams and real-time GPU/CPU readouts.

**2. Native input and keybinding schema swapping.** *"A true VS Code theme is useless if your muscle
memory expects `Cmd/Ctrl + P` to do quick-open and it triggers something else."* Selecting a profile
swaps the entire keybinding engine — VS Code mode (`Cmd/Ctrl+P` quick open, `Cmd/Ctrl+Shift+P`
palette, `Ctrl+Tab` MRU), Claude/Cursor mode (`Cmd/Ctrl+I` inline edit, `Cmd/Ctrl+L` chat focus,
`Cmd/Ctrl+K` agent prompt), and brand-agnostic Vim/Emacs modal keymaps embedded in Monaco and the
Omni-Bar.

**3. Agent persona and cognitive voice sync.** `brand-claude` aliases the default agent to
Anthropic's system prompt architecture and tone; `brand-deepseek` tunes reasoning tokens and
math-optimized prompts; `brand-github` biases agents toward PRs, conventional commits, and CI
compliance.

**4. Extension API emulation layers.** When a `vscode:full` extension runs inside `brand-claude`,
Omnis injects compatibility shims mapping expected VS Code UI elements into native chat artifacts or
sidebar panels without uncaught exceptions.

```ts
export interface SystemPersonalityPackage {
  id: string;
  chrome: BrandProfileSpecification;

  runtimeBehavior: {
    primaryWorkspaceParadigm:
      'chat-artifacts' | 'file-tree-editor' | 'vcs-dag-hud' | 'infinite-canvas';
    defaultDockviewLayout: SerializedDockviewLayout;
    allowMultipleEditors: boolean;
    artifactFocusMode: boolean;
  };

  keybindings: 'vscode' | 'cursor-claude' | 'sublime' | 'vim' | 'emacs';

  aiPersona: {
    defaultProvider: string;
    defaultModel: string;
    systemPromptModifier: string;
    reasoningEffort: 'low' | 'medium' | 'high' | 'max';
  };

  extensionHostCompatibility: { emulateVsCodeApi: boolean; injectNativeShims: boolean };
}
```

---

## 6. The terminal-native UI engine

`brand-zed` is not a skin. It is a **second renderer**.

### 6.1 The cell-grid UI engine (`omnis-term-ui`)

Omnis bypasses HTML DOM layout trees and CSS flexbox for its chrome, replacing them with a
**GPU-accelerated Cell Matrix Buffer**. Every UI element — sidebar borders, status bars, tab headers,
buttons, input prompts — is a styled terminal cell rendered via WebGL/WebGPU inside the Tauri window.

- **Unified cell buffer** — the whole window shares one text-grid coordinate space.
- **Zero DOM overhead** — components are data structures mapped to cells holding Unicode glyphs,
  24-bit RGB foreground/background, and SGR attribute flags (bold, dim, italic, underline, reverse).
- **GPU blitting** — an optimized WebGPU/WebGL shader pipeline inside `omnisd`, targeting
  sub-millisecond full-screen redraws and zero layout thrashing.

### 6.2 Interaction paradigms

- **Command palette first** (`Cmd/Ctrl+Shift+P`) — no floating menus or nested settings trees;
  everything from configuration to Docker containers to PR review runs through a fuzzy-searched
  terminal overlay.
- **Pane-grid keyboard navigation** — zero-latency splitting and resizing via vim-like motions or Zed
  chords (`Ctrl+K`, then directional).
- **Inline terminal inspector** — diagnostics, compiler errors, git status, and agent thoughts render
  as collapsible colour-coded strips inline with code buffers.

### 6.3 The native rendering switchboard

| HTML / DOM engine | Cell-grid terminal engine (`omnis-term-ui`) |
|---|---|
| Claude, VS Code, GitHub, Default | `brand-zed` |
| React / DOM layout trees | GPU cell matrix buffer |
| CSS Flexbox & Tailwind | Monospace metrics · TrueColor 24-bit ANSI |
| DOM event listeners | Direct PTY / canvas blit · modal Vi/Emacs keymaps · zero layout thrashing |

```ts
rendererEngine: 'dom-flexbox' | 'terminal-cell-grid';

terminalGridConfig?: {
  fontFamily: string;
  fontSize: number;
  lineHeight: number;
  cursorShape: 'block' | 'bar' | 'underline';
  ansiPalette: { /* 16 named + up to 256 ANSI + TrueColor RGB */ };
};
```

---

## 7. The settings switchboard

Settings are a **declarative switchboard**: `settings.json` is a master layout matrix, and toggling
options reconfigures the renderer, input routing, and view topology on the fly.

Three independent axes, read at startup and on live IPC updates, assembling the UI without reloading
the daemon:

| Input paradigm | Layout topology | Renderer engine |
|---|---|---|
| `global-hud` — omni-bar handles all input globally | `terminal-grid` — Zed-style split panes, palette focus | `terminal-cell-grid` — WebGL cell matrix |
| `per-pane` — anchored input boxes per view | `chat-centric` — minimalist card/artifact stream | `dom-flexbox` — React/Tailwind Dockview |
| `hybrid` | `ide-split`, `vcs-dag` | |

Setting `workbench.inputBar.mode: "per-pane"` unmounts the floating omni-bar and injects anchored
inputs at the bottom of chat panels and terminal buffers; `global-hud` restores the spotlight overlay
(`Cmd/Ctrl+K`). Setting `workbench.layout.paradigm: "chat-centric"` reorganizes Dockview around a
conversation canvas with floating artifact cards; `ide-split` locks into a multi-root explorer with
strict grid lines.

**Zero bloat**: every target style is a native configuration state of the core engine.

---

## 8. Terminal-grid web browser

`omnis-term-browser` is a **dual-mode rendering bridge**. Under the terminal renderer the embedded
Chromium engine (`omnis-browser`) does not display DOM nodes; it renders pages through two
conversion pipelines fed by headless CDP.

**Semantic text mode (AXTree → cells).** For documentation, repositories, blogs, and text-heavy
pages: DOM overhead is stripped into a semantic text tree; headings, paragraphs, and lists render as
monospaced blocks with ANSI colour weights. Links and inputs get interactive cell coordinates;
tabbing or clicking highlights the cell range and triggers CDP navigation. Near-zero GPU memory,
instant keyboard scrolling.

**Pixel blit mode (Sixel / Unicode Braille).** For rich apps, charts, embedded editors, or video:
Chromium screencasts the viewport over CDP at 30/60 FPS, and `omnis-term-browser` downsamples pixel
buffers into TrueColor ANSI Sixel graphics or high-density Braille matrices (`⣿⣾⣽⣻⢿⡿⣟⣯⣷`).

```jsonc
"browser.terminalRenderer.mode": "auto",   // 'semantic-text' | 'pixel-sixel' | 'hybrid'
"browser.terminalRenderer.fps": 30
```

Under `dom-flexbox` the browser tab switches to a standard sandboxed Chromium `<iframe>` view. The
whole application — editor, terminal, settings, multi-agent chat, and browser — operates across both
renderers with no bolted-on extensions.

---

## 9. Master specification

The compilation the user pushed for three times. This is the substrate the appearance layer sits on.

### 9.1 Process topology and dual-socket IPC

> Omnis isolates the persistent background daemon, GUI presentation layer, language servers, browser
> runtimes, and extension execution hosts into strictly decoupled processes. This guarantees zero
> process termination on UI reloads, unblocked I/O streaming, and complete harness agnosticism.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              SURFACE LAYER                                   │
│  ┌────────────────────────┐ ┌──────────────────────┐ ┌────────────────────┐  │
│  │ Omnis GUI (Tauri)      │ │ Omnis CLI (`omnis`)  │ │ Any External       │  │
│  │ DOM-Flex / Cell-Grid   │ │ Shell orchestration  │ │ Harness: Claude    │  │
│  │ Cordis Microkernel Root│ │ Pretty & `--json`    │ │ Code, Codex, Aider │  │
│  └───────────┬────────────┘ └──────────┬───────────┘ └─────────┬──────────┘  │
└──────────────┼─────────────────────────┼───────────────────────┼─────────────┘
               │   DUAL IPC TRANSPORT                            │ MCP / Stdio
               │   • Control: JSON-RPC 2.0 (omnis-control.sock)  ▼
               │   • Data: framed binary  (omnis-data.sock)  ┌──────────────────┐
               │                                            │ `@omnis/agent`   │
               ▼                                            │ SDK & MCP bridge │
┌────────────────────────────────────────────────────────┐  └──────────────────┘
│ HEADLESS DAEMON (`omnisd`)                             │
│           OMNIS SUBSTRATE BUS (OSB ROUTER)             │
│ ┌──────────────────┬──────────────────┬──────────────┐ │
│ │ Core Engine/Sync │ Background       │ Storage &    │ │
│ │                  │ Runtimes         │ DB Fabric    │ │
│ ├──────────────────┼──────────────────┼──────────────┤ │
│ │ Tailscale Mesh   │ Tmux Control Srv │ PGlite       │ │
│ │ CRDT HLC Log     │ Native PTY Mgr   │  Mailbox     │ │
│ │ Approval Escrow  │ Bollard Docker   │ FastCDC CAS  │ │
│ │ Git Alternates   │ Resource Superv. │ VFS Mounts   │ │
│ │                  │                  │ Inotify      │ │
│ └──────────────────┴──────────────────┴──────────────┘ │
│ Modular subsystems (conditionally initialized):        │
│  LSP Hub · DAP (`omnis-dap`) · P2P WebRTC Mesh         │
│  Browser (`omnis-browser` + `omnis-term-browser`)      │
│  SSH/GPG Agent · Task DAG Engine · Audit Stream        │
│  Context Harvester · VCS & Forge · Cloud VFS · Chat    │
└────────────────────────────────────────────────────────┘
```

**Control socket** (`omnis-control.sock` / `\\.\pipe\omnis-control`) — strict JSON-RPC 2.0 framing
carrying capability checks, layout persistence, escrow ticket transitions, extension registrations,
database queries, and context shelf modifications.

**Data socket** (`omnis-data.sock` / `\\.\pipe\omnis-data`) — high-throughput binary multiplexer with
a uniform 9-byte header:

```
[StreamID: u32][Opcode: u8][PayloadLength: u32]

0x01 PTY_STREAM   raw terminal stdout/stdin bytes
0x02 PTY_RESIZE   in-band dimension updates [Cols: u16][Rows: u16]
0x03 DOCKER_LOG   demultiplexed container logs
0x04 CAS_CHUNK    decrypted FastCDC blob payloads
0x05 CDP_BINARY   CDP screencast frames and Sixel terminal rasters
```

### 9.2 Workspace layout

```
omnis/
├── Cargo.toml                  # virtual workspace root
├── crates/
│   ├── omnis-core/             # shared RPC models, schemas, OSB contracts
│   ├── omnisd/                 # headless daemon binary
│   │   └── src/
│   │       ├── main.rs         # conditional subsystem bootloader
│   │       └── subsystems/     # modular domain implementations
│   ├── omnis-cli/              # `omnis` executable
│   ├── omnis-gui/              # Tauri desktop host & window manager
│   ├── omnis-agent/            # agent engine & MCP server binary
│   ├── omnis-lsp/              # LSP multiplexer hub
│   ├── omnis-dap/              # Debug Adapter Protocol implementation
│   ├── omnis-browser/          # Chromium supervisor, CDP bridge, adblock
│   └── omnis-cas/              # FastCDC chunking, convergent encryption, VFS
└── packages/
    ├── core/                   # Cordis microkernel, context defs, dsh-compat
    ├── agent-sdk/              # npm package `@omnis/agent`
    ├── exthost-node/           # isolated Node.js runtime for VS Code extensions
    └── frontend/               # webview shell (Dockview, shadcn/ui)
```

### 9.3 The binary substrate model

Two distinct installable universes, deliberately not merged:

| **Packages** (`omnis pkg` / `ctx.packages`) | **Extensions** (`omnis ext` / `ctx.extensions`) |
|---|---|
| *"What my project runs on"* | *"What my workspace and agents run on"* |
| Target: the codebase repo or host OS | Target: Omnis client, Monaco, Cordis, agents |
| Code deps: Bun, pnpm, npm, Cargo, uv, Poetry, Go modules, Deno | Editor & tools: VS Code extensions (Open VSX/VSIX), web extensions, LSPs |
| System deps: Homebrew, Pacman, APT | Runtime modules: native `dsh` extensions, Cordis forks, V8 worker realms, Shadow-DOM slots |
| Task runners: `package.json` scripts, Cargo targets, task DAGs | Agent capabilities: MCP servers, Claude Code skills, Codex playbooks |
| Local cache: FastCDC reflink deduplication across workspaces | Visual skins: VS Code themes, file icon themes, product icon packs |

### 9.4 Security, vault, and process injection

- **Zero-knowledge vault** — master key derived via Argon2id (64 MB, 3 iterations, 4 parallelism).
  The KEK is held in a `Zeroizing<[u8; 32]>` buffer with `mlock()` protection. Device secrets bridge
  to OS keychains (Apple Keychain, DPAPI, Secret Service).
- **Secure process injection** — `omnisd` intercepts child spawns (`omnis.terminal`,
  `omnis.pkg.exec`) and injects decrypted `.env` secrets directly into the child's memory map,
  without writing plaintext credentials to disk *or into agent context windows*.
- **Integrated SSH/GPG agent** (`omnis-ssh-agent`) — a native Unix socket (`~/.omnis/ssh.sock`)
  managed by the daemon, decrypting private keys from the vault on demand to authenticate git pushes,
  forge operations, and SSH tunnels.

### 9.5 Advanced runtimes and subsystems

- **Agent behavioural audit stream** — immutable append-only log of every tool call, file
  modification, SQL query, and network request an autonomous agent executes, with a one-click sandbox
  execution killswitch.
- **Unified task & build DAG engine** (`omnis task`) — parses `package.json`, `Cargo.toml`,
  `Makefile`, `Taskfile.yaml` into a cross-repository dependency graph, using CAS timestamps to skip
  unchanged targets and parallelize builds.
- **Universal context fabric** (`omnis-context`) — harvests normal-form `ContextFragment` envelopes
  from code selections, terminal buffers, browser pages, and Docker logs; pins them to a persistent
  sidebar shelf; exposes them as `omnis://context/<id>` URIs.
- **Universal VCS & stacked PRs** (`ovcs`) — dual Git/Sapling engine with an atomic operation log
  (`vcs_op_log`), automated `absorb`, a 3-way AST merge editor, and stacked PR management across
  GitHub, GitLab, and Forgejo.

### 9.6 Master schema

Eighteen tables across eight groups, expressed in Drizzle against **PGlite** (embedded Postgres, per
the daemon's "Serialized PGlite Mailbox"):

| Group | Tables |
|---|---|
| Workspaces & layouts | `workspaces`, `workspaceWindows`, `workspaceTabs` |
| Appearance | `brandAppearanceProfiles` |
| Extensions | `installedExtensions` |
| Vault & identity | `userAccounts`, `vaultSecrets` |
| CAS & virtual files | `casBlobs` (BLAKE3-keyed), `virtualFiles` |
| Chat, agents, audit | `chatThreads`, `chatMessages`, `agentAuditStream`, `approvalEscrowTickets` |
| Tasks & VCS | `taskDagCache`, `vcsRepositories`, `vcsStackedPrs` |
| Context & browser | `contextFragments`, `browserTabs` |

```ts
export const brandAppearanceProfiles = pgTable('brand_appearance_profiles', {
  id: text('id').primaryKey(),          // 'brand-zed', 'brand-claude', 'brand-vscode', …
  displayName: text('display_name').notNull(),
  rendererEngine: text('renderer_engine').notNull().default('dom-flexbox'),
  appIconConfig: jsonb('app_icon_config').$type<{
    vectorSvg: string; isAnimatedLucide: boolean;
    stateAnimations: { thinking: string; error: string; pending: string };
  }>().notNull(),
  windowStyling: jsonb('window_styling').$type<{
    frameStyle: string; vibrancy: string; cornerRadius: string;
    trafficLightsInset: { top: number; left: number };
  }>().notNull(),
  typography: jsonb('typography')
    .$type<{ uiFont: string; codeFont: string; density: string }>().notNull(),
  colorTokens: jsonb('color_tokens').$type<Record<string, string>>().notNull(),
  terminalGridConfig: jsonb('terminal_grid_config')
    .$type<{ ansiPalette: Record<string, string> }>(),
  updatedAt: timestamp('updated_at', { withTimezone: true }).defaultNow(),
});

export const agentAuditStream = pgTable('agent_audit_stream', {
  id: uuid('id').primaryKey().defaultRandom(),
  agentId: text('agent_id').notNull(),
  threadId: uuid('thread_id').references(() => chatThreads.id),
  actionCategory: text('action_category').notNull(),  // fs_write|shell_exec|sql_query|net_request
  payloadSummary: jsonb('payload_summary').notNull(),
  isSandboxBlocked: boolean('is_sandbox_blocked').default(false),
  executedAt: timestamp('executed_at', { withTimezone: true }).defaultNow(),
});

export const approvalEscrowTickets = pgTable('approval_escrow_tickets', {
  id: uuid('id').primaryKey().defaultRandom(),
  callId: text('call_id').notNull().unique(),
  subsystem: text('subsystem').notNull(),
  action: text('action').notNull(),
  parameters: jsonb('parameters').notNull(),
  status: text('status').default('pending'),
  expiresAt: timestamp('expires_at', { withTimezone: true }).notNull(),
});
```

### 9.7 Master configuration reference

```jsonc
{
  "$schema": "https://omnis.dev/schemas/settings.v1.json",
  "daemon.autoStartOnLogin": true,
  "daemon.controlSocketPath": "default",
  "daemon.dataSocketPath": "default",

  "workbench.brandTheme": "brand-zed",
  "workbench.rendererEngine": "terminal-cell-grid",
  "workbench.inputBar.mode": "global-hud",
  "workbench.layout.paradigm": "terminal-grid",
  "workbench.window.frameStyle": "frameless-custom",
  "workbench.window.vibrancy": "mica",
  "workbench.keybindings": "zed",

  "features": {
    "vcs":          { "git": true, "sapling": true },
    "forges":       { "github": true, "forgejo": false },
    "cloudStorage": { "icloud": false, "onedrive": false },
    "chatBridges":  { "matrix": true, "imessage": false },
    "runtimes":     { "docker": true, "tmux": true, "browser": true, "dap": true }
  },

  "browser.terminalRenderer.mode": "auto",
  "tasks.dag.cacheEnabled": true,
  "security.vault.processInjection": true,
  "security.sshAgent.enabled": true,
  "ai.defaultProvider": "anthropic",
  "ai.defaultModel": "claude-3-5-sonnet"
}
```

The `features` block is the load-bearing part: subsystems are **conditionally initialized** from
settings, so the daemon a user runs contains only what they enabled.

---

## 10. Reference implementation sketches

The transcript's final technical turn supplied Rust skeletons. They are illustrative, not reviewed —
several have acknowledged defects (the task DAG sort returns the unsorted input; the cell grid writes
characters without touching colour). Treat them as shape, not as code to copy.

- `crates/omnis-core/src/bus.rs` — `Subsystem` async trait (`name`/`initialize`/`shutdown`) and a
  `SubstrateBus` over a `tokio::sync::broadcast` channel carrying `BusMessage { id, topic, payload }`.
- `crates/omnisd/src/ipc.rs` — `UnixListener` control socket, per-connection `tokio::spawn`, JSON-RPC
  2.0 request/response.
- `crates/omnisd/src/security/process.rs` — `SecureProcessSpawner::spawn_with_vault_env`, injecting
  `Zeroizing<String>` secrets into the child environment only.
- `crates/omnis-cas/src/chunker.rs` — `ConvergentFastCDC` with min/avg/max chunk sizes and a
  BLAKE3 keyed convergent key derivation.
- `crates/omnis-browser/src/term_ui.rs` — `Cell { character, fg_color, bg_color, flags }` and
  `CellGridBuffer { cols, rows, grid: Vec<Cell> }`.
- `crates/omnisd/src/tasks/dag.rs` — Kahn topological sort over `TaskNode { name, dependencies,
  input_hash }` with cycle detection.

---

## 11. Review notes

Points where the source material is internally inconsistent, or where following it literally would
be a mistake. Each is a decision to make deliberately, not a defect to fix silently.

1. **The two-renderer model is superseded.** The transcript presents `dom-flexbox` and
   `terminal-cell-grid` as a switch, and never describes a shared representation both consume —
   which would mean implementing every surface twice. `ARCHITECTURE.md` §4 replaces it with **one
   GPU compositor**: terminal, widget UI, browser content, and 3D become *sources* that emit
   primitives into a single frame graph, over the scene tree of §4.2. A terminal cell is a glyph run
   with fixed advance and a browser is a content source, so neither justifies its own renderer. This
   also extends the engine beyond anything in the transcript — shaders, 3D scenes, and particle
   systems are a first-class material-layer primitive available to every presentation mode, rather
   than effects that would exist in one renderer and not the other.

   The transcript also conflates two different things under `brand-zed`: a terminal *look*, and
   actually *running in a terminal*. Omnis separates them. `cell-grid` is a presentation mode the
   GPU compositor draws in a desktop window; `omnis-tui` is a genuine second renderer backend that
   emits ANSI to a real terminal, works over SSH, and needs no GPU. Both consume the same scene
   tree, which is what makes feature parity between them a contract rather than a hope
   (`ARCHITECTURE.md` §4.7).
2. **`aiPersona` couples appearance to model choice.** Selecting a look also selects a provider,
   model, and reasoning effort. Nobody asked for that, and it will surprise people who want Claude's
   layout with a different model. Keep the axes separate; let a preset *suggest* a persona.
3. **The schema mixes configuration with data.** `brandAppearanceProfiles` puts presets in the
   database while `settings.json` also carries appearance keys, with no stated precedence. Presets
   are versioned, diffable, shareable artifacts — they belong in files. (The store itself is fine:
   "Serialized PGlite Mailbox" means embedded Postgres, not a server, so Drizzle/`pgTable` is
   consistent with local-first.)
4. **Performance claims are unbounded.** "Sub-millisecond full-screen redraws" and instant renderer
   switching are asserted, never measured or budgeted.
5. **`emulateVsCodeApi` is a multi-year commitment stated as a boolean.** Same for `dsh-compat` and
   Sapling parity.
6. **Trade dress.** Shipping third-party names, marks, icons, and distinctive visual identity for
   Claude, GitHub, VS Code, Zed, DeepSeek, and Kimi is a legal question before a technical one.
7. **`ai.defaultModel: "claude-3-5-sonnet"` is stale.** A pinned literal in the reference config;
   model identifiers belong behind the provider adapter, resolved at runtime.
8. **Scope.** The daemon subsystem list — VCS, forges, packages, tasks, terminals, containers, LSP,
   DAP, browser, agents, vault, CAS, WebRTC mesh, Tailscale sync, cloud VFS, chat bridges — is a
   decade of work stated as a diagram. The architecture is coherent; the sequencing is the hard part,
   which is what `ROADMAP.md` exists to answer.
