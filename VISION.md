# Omnis — Vision (Reference Only)

> **Status: NON-NORMATIVE.** This document is a captured transcript-derived record of the scoping
> conversation that produced the Omnis concept. It is raw source material. It is **not** a
> specification, it is **not** a commitment, and it does **not** override `ARCHITECTURE.md`.
> Where this file and `ARCHITECTURE.md` disagree, `ARCHITECTURE.md` wins.
>
> **Provenance:** Google Gemini conversation "App Scoping Technical Specifications Discussion"
> (`gemini.google.com/app/545cf54445afcd33`), captured 2026-09-06 via browser automation.
>
> **Capture is incomplete.** The browser extension disconnected partway through extraction. Turns
> 0–13 are captured substantially in full; the master compilation (turns 15–19, roughly 45,000
> characters) is only partially captured. Every gap is marked inline with a
> `> **[GAP]**` callout. Do not treat an absent section as an absent requirement.

---

## Table of contents

1. [What Omnis is](#1-what-omnis-is)
2. [Brand parity and dynamic appearance subsystem](#2-brand-parity-and-dynamic-appearance-subsystem)
3. [Native window styling](#3-native-window-styling)
4. [Typography, audio, icon state machines](#4-typography-audio-icon-state-machines)
5. [System personality packages](#5-system-personality-packages)
6. [The terminal-native UI engine](#6-the-terminal-native-ui-engine)
7. [The settings switchboard](#7-the-settings-switchboard)
8. [Terminal-grid web browser](#8-terminal-grid-web-browser)
9. [Master specification (partial)](#9-master-specification-partial)
10. [Open questions the transcript never answers](#10-open-questions-the-transcript-never-answers)

---

## 1. What Omnis is

> Universal Developer Workspace & Local-First Personal Data Operating System.

Omnis is a desktop application that can *completely change its identity* — visual aesthetic, window
chrome, layout topology, keybindings, input model, rendering engine, and agent persona — to match
the native experience of a target tool (Claude, VS Code, GitHub, Zed, DeepSeek, Kimi, Codex), and
that does so through **first-class configuration of one core engine**, never through per-theme
bolt-ons.

The user's framing, verbatim, across the conversation:

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

**The load-bearing principle**, stated three separate ways by the user and echoed by the model:
a "theme" is not a stylesheet. A theme is a *named preset over a matrix of native engine
capabilities*. Every visual target must be reachable by toggling settings that exist independently
of any brand.

---

## 2. Brand parity and dynamic appearance subsystem

Namespace: `omnis.appearance`. Called the **Dynamic Brand Skinning Engine**.

### 2.1 Dynamic app icon & window chrome engine

- **Tauri native dock/tray integration** — the main application icon (Dock on macOS, Taskbar/Tray on
  Windows/Linux) hot-swaps vectors or animated frames via Rust native bindings
  (`tauri::AppHandle::set_icon`).
- **Default state** — powered by `lucide-animated`: interactive, micro-animated SVG vector
  components reacting to workspace events, sync status, and agent activity.
- **Universal asset support** — static SVGs, animated web components, or `.icns`/`.ico` binary icon
  packs.

### 2.2 Brand theme presets (`appearanceProfiles`)

Each preset overrides global CSS custom properties:

| Preset | Character |
|---|---|
| `brand-default` | Developer dark/light, Lucide-animated iconography, high-contrast glassmorphism |
| `brand-claude` | Warm parchment/charcoal palettes, terracotta/amber accent glows (`#CC785C`), humanist typography, restrained minimalism |
| `brand-github` | Classic GitHub dark/dimmed/light schemes, electric purple/blue interactive states (`#2f81f7`), dense technical layouts |
| `brand-deepseek` | Deep midnight-navy backdrops, neon cyan/teal accents (`#00E5FF`), high-tech telemetry readouts |
| `brand-kimi` | Soft violet/indigo gradients, playful rounded geometry, airy spacing |
| `brand-codex` / `brand-vscode` | Editor-first chrome, high-density explorer trees, classic blue/orange accents |
| `brand-zed` | Terminal cell-grid renderer (see §6) |

### 2.3 Proposed persistence (Drizzle / Postgres)

```ts
export const brandAppearanceProfiles = pgTable('brand_appearance_profiles', {
  id: text('id').primaryKey(),          // 'default','claude','github','deepseek','kimi','vscode'
  displayName: text('display_name'),
  colorTokens: jsonb('color_tokens').$type<{
    background: string;
    foreground: string;
    primaryAccent: string;
    secondaryAccent: string;
    border: string;
    sidebarBackground: string;
    titlebarStyle: 'native' | 'integrated' | 'hidden';
    borderRadius: string;
  }>().notNull(),
  customCssOverrides: text('custom_css_overrides'),
  updatedAt: timestamp('updated_at', { withTimezone: true }).defaultNow(),
});
```

> **[REVIEW]** A Postgres table for local desktop appearance presets is almost certainly the wrong
> store. See `ARCHITECTURE.md` — presets belong in versioned config files, with the database
> reserved for user data. Recorded here only because the transcript proposed it.

---

## 3. Native window styling

The model's framing: window styling *"dictates how the physical application window sits on your OS
desktop"* — structural chrome, frames, and OS-level integration, not colour tokens.

### 3.1 Frame architecture & titlebar mechanics (Pillar 1)

- **Borderless / frameless canvas** — the OS titlebar is removed entirely (`decorations: false` in
  Tauri). The header region is rendered in HTML/CSS with `data-tauri-drag-region`, permitting a
  Claude-style minimalist floating header or a VS Code-style integrated command center.
- **Native integrated titlebar** — for targets that prefer standard OS buttons while keeping custom
  styling: native OS titlebar embedding with a translucent background.

> **[GAP]** Pillars 2–5 of "The 5 Pillars of Native Brand Window Styling" were lost during capture
> (approximately 1,500 characters). From the schema below they appear to cover traffic-light
> positioning, vibrancy materials, corner radius/shadow elevation, and native window control
> visibility — but this is inference, not transcript.

### 3.2 Window styling schema (captured)

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

colorThemeVariables: jsonb('color_theme_variables').$type<{
  background: string;
  foreground: string;
  primaryAccent: string;
  secondaryAccent: string;
  border: string;
  sidebarBackground: string;
}>().notNull(),
```

---

## 4. Typography, audio, icon state machines

Prompted by the user's *"I still dont think its enough"*.

### 4.1 Typography engines & font-stack metrics

Native apps use proprietary font stacks and optical sizing rules that define their visual voice:

- **Claude profile** — humanist, warm sans-serif stacks, generous line-height ratios, slightly
  heavier body weights (Inter Display, custom serif headers).
- **VS Code profile** — high-density crisp monospace (Fira Code, JetBrains Mono) paired with compact
  UI font metrics (Segoe UI / San Francisco at 11–12px density).
- **DeepSeek profile** — sharp, technical, geometric.

> **[GAP]** The remainder of the DeepSeek/Kimi/GitHub typography entries and the whole of section 2
> ("layout density") were lost during capture (~400 characters). The surviving fragment of section 2
> ends: *"…and zero wasted vertical pixels."*

### 4.2 Brand-specific sound & haptic cues

- Claude / DeepSeek — subtle low-frequency haptic clicks or quiet audio ticks when agents finish
  reasoning blocks, stream tool outputs, or require approvals.
- VS Code / GitHub — crisp mechanical keyboard ticks, clean commit-success chimes.
- Setting: `workbench.audioFeedback: "brand-native" | "muted" | "subtle"`.

### 4.3 App icon state machines (dynamic icon badges)

The dock/tray icon reflects background daemon state in real time:

| State | Behaviour |
|---|---|
| Idle | Brand default icon |
| Agent running / thinking | Icon pulses, spins, or animates internal vectors |
| CI failure / error | Brand accent ring shifts to a warning red glow |
| Action required (approval pending) | Badge count, or amber flash |

### 4.4 Native context menus

> **[GAP]** Section 5, "Native Context M…", was lost during capture (~1,000 characters).

### 4.5 `BrandProfileSpecification` (captured)

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

  typography: {
    uiFontFamily: string;
    /* [GAP] remaining typography fields lost in capture */
  };

  audio: {
    enabled: boolean;
    soundPack: 'claude-soft' | 'vscode-mech' | 'minimal' | 'muted';
  };

  tokens: {
    background: string;
    foreground: string;
    primaryAccent: string;
    secondaryAccent: string;
    border: string;
    sidebarBackground: string;
    cardBackground: string;
  };
}
```

---

## 5. System personality packages

Prompted by the user's *"still not enough"*. The model escalated from "brand profile" to
**System Personality Package** — switching a theme shifts *"the editor's core cognitive engine,
input mappings, layout rules, and agent behaviors"*.

```ts
export interface SystemPersonalityPackage {
  id: string;               // 'claude'|'vscode'|'github'|'deepseek'|'kimi'|'default'

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

  extensionHostCompatibility: {
    emulateVsCodeApi: boolean;
    injectNativeShims: boolean;
  };
}
```

> **[GAP]** The opening ~2,000 characters of this turn (the prose introducing the five override
> categories) were lost during capture. The interface above is complete as captured.

> **[REVIEW]** `aiPersona` binding a *visual* theme to a *model provider and reasoning effort* is a
> coupling the user never asked for and that will surprise people. Flagged for a decision;
> see `ARCHITECTURE.md` §Open Decisions.

---

## 6. The terminal-native UI engine

User: *"a zed theme that basically draws the entire ui as terminal - all of this should be supported
by native features not boltons per theme"*.

The response is the single most consequential idea in the transcript: `brand-zed` is not a skin, it
is a **second renderer**.

### 6.1 The cell-grid UI engine (`omnis-term-ui`)

When `brand-zed` is active, Omnis bypasses HTML DOM layout trees and CSS flexbox for its chrome,
replacing them with a **GPU-accelerated Cell Matrix Buffer** that treats every UI element — sidebar
borders, status bars, tab headers, buttons, input prompts — as styled terminal cells rendered via
WebGL/WebGPU directly inside the Tauri window.

- **Unified cell buffer rendering** — the entire window (editors, panels, sidebars, dialogs) shares
  one text-grid coordinate space.
- **Zero DOM overhead** — UI components are pure data structures mapped to character cells holding
  Unicode glyphs, 24-bit foreground/background RGB, and SGR attribute flags (bold, dim, italic,
  underline, reverse).
- **GPU blitting** — an optimized WebGPU/WebGL shader pipeline running inside `omnisd`, targeting
  sub-millisecond full-screen redraws and zero layout thrashing.

### 6.2 Native Zed-style interaction paradigms

- **Command palette first** (`Cmd/Ctrl + Shift + P`) — no heavy floating menus or nested settings
  trees; everything from configuration to Docker containers to PR review is driven through a
  fuzzy-searched terminal command palette overlay.
- **Pane-grid keyboard navigation** — zero-latency multi-pane splitting and resizing governed by
  vim-like motions or Zed chords (`Ctrl + K`, then directional).
- **Inline terminal inspector** — diagnostics, compiler errors, git status, and agent thoughts render
  as collapsible colour-coded terminal strips inline with code buffers, not as separate cards.

### 6.3 The native rendering switchboard (`omnis-core`)

| HTML / DOM engine | Cell-grid terminal engine (`omnis-term-ui`) |
|---|---|
| Used by Claude, VS Code, GitHub, Default | Used by `brand-zed` |
| React / DOM layout trees | GPU cell matrix buffer |
| CSS Flexbox & Tailwind | Monospace font metrics · TrueColor 24-bit ANSI themes |
| DOM event listeners | Direct PTY / canvas blit · modal Vi/Emacs keymaps · zero DOM layout thrashing |

### 6.4 Schema extension

```ts
export interface SystemPersonalityPackage {
  id: string;               // 'zed'|'claude'|'vscode'|'github'|'deepseek'|'kimi'|'default'
  displayName: string;

  rendererEngine: 'dom-flexbox' | 'terminal-cell-grid';   // native core switch

  terminalGridConfig?: {
    fontFamily: string;
    fontSize: number;
    lineHeight: number;
    cursorShape: 'block' | 'bar' | 'underline';
    ansiPalette: {
      black: string; red: string; green: string; yellow: string;
      blue: string; magenta: string; cyan: string; white: string;
      brightBlack: string;
      // … up to 256 ANSI colours + TrueColor RGB background/foreground
    };
  };

  domThemeConfig?: BrandProfileSpecification;

  keybindings: 'zed' | 'vscode' | 'cursor-claude' | 'vim' | 'emacs';
  runtimeBehavior: {
    primaryWorkspaceParadigm: 'terminal-split-grid' | 'chat-artifacts' | 'file-tree-editor';
    commandPaletteStyle: 'zed-fuzzy' | 'vscode-palette' | 'claude-spotlight';
  };
}
```

### 6.5 Claimed outcomes

- Rendering the interface as a terminal grid uses a fraction of the RAM and CPU of a DOM app.
- True Zed fidelity — text-driven, keyboard-first, crisp TrueColor ANSI palettes.
- Users toggle between DOM and terminal-native renderers instantly in `settings.json`, with the core
  daemon and Substrate Bus completely unchanged.

> **[REVIEW]** "Instantly, without restart" for a renderer swap is an unvalidated performance claim.
> Treated in `ARCHITECTURE.md` as a goal requiring a spike, not a given.

---

## 7. The settings switchboard

User: *"by the support I meant … there should be a setting for global input bar or per chat input
bar and a chat centric or ide layout setting … that the settings just toggle to achieve their target
style get it?"*

Settings function as a **declarative switchboard**. `settings.json` is a master layout matrix;
toggling options reconfigures the core renderer, input routing, and view topology on the fly.

```jsonc
{
  "$schema": "https://omnis.dev/schemas/settings.v1.json",

  // 1. Core visual brand personality
  "workbench.brandTheme": "brand-zed",
  //   'brand-zed' | 'brand-claude' | 'brand-vscode' | 'brand-github' | 'brand-default'

  // 2. Input bar routing paradigm
  "workbench.inputBar.mode": "global-hud",
  //   'global-hud' (omni-bar spotlight) | 'per-pane' (anchored in active chat/terminal) | 'hybrid'

  // 3. Workspace layout topology
  "workbench.layout.paradigm": "terminal-grid",
  //   'terminal-grid' (Zed) | 'chat-centric' (Claude) | 'ide-split' (VS Code) | 'vcs-dag'

  // 4. Window frame & native integration physics
  "workbench.window.frameStyle": "frameless-custom",
  "workbench.window.vibrancy": "mica",

  // 5. Keybinding & interaction model
  "workbench.keybindings": "zed",
  //   'zed' | 'vscode' | 'cursor-claude' | 'vim'

  // 6. AI agent persona alignment
  "ai.personaAlignment": "brand-native"
}
```

Three independent axes are read at startup and on live IPC updates, assembling the UI framework
without reloading the background daemon:

| Input paradigm | Layout topology | Renderer engine |
|---|---|---|
| `global-hud` — omni-bar handles all chat/terminal input globally | `terminal-grid` — Zed-style split panes, command-palette focus | `terminal-cell-grid` — WebGL cell matrix buffer |
| `per-pane` — attached input boxes per view | `chat-centric` — minimalist card/artifact stream | `dom-flexbox` — React/Tailwind Dockview layout |
| `hybrid` | `ide-split`, `vcs-dag` | |

- Setting `workbench.inputBar.mode: "per-pane"` unmounts the floating omni-bar and injects anchored
  input fields at the bottom of chat panels and terminal buffers; `global-hud` restores the global
  spotlight overlay (`Cmd/Ctrl + K`).
- Setting `workbench.layout.paradigm: "chat-centric"` reorganizes Dockview to prioritize a
  conversation canvas with floating artifact cards; `ide-split` locks into a multi-root file
  explorer with strict grid lines.
- **Zero bloat** — every target style is a native configuration state of the core engine. Users mix
  and match inputs, layouts, and themes freely; brands are merely named presets over this matrix.

---

## 8. Terminal-grid web browser

User: *"for the terminal based renderer we need to actually support the full app including web
browser"*.

`omnis-term-browser` is a **dual-mode rendering bridge**. When the terminal-native UI is active, the
embedded Chromium engine (`omnis-browser`) does not display raw DOM nodes; it renders pages through
two conversion pipelines fed by headless CDP.

### 8.1 Semantic text mode (AXTree → cells)

For documentation, repositories, blogs, and text-heavy pages:

- Strips DOM overhead into a semantic text tree; headings, paragraphs, and lists render as clean
  monospaced blocks with ANSI colour weights matching the active theme.
- Links and input fields are assigned interactive cell coordinates; tabbing or clicking highlights
  the cell range and triggers CDP navigation events.
- Consumes near-zero GPU memory relative to a full browser frame; scrolls instantly via keyboard
  motions.

### 8.2 Pixel blit mode (Sixel / Unicode Braille)

For rich web apps, interactive charts, embedded editors, or video:

- Headless screencast stream — Chromium captures the viewport via CDP at 30/60 FPS.
- In-terminal rasterization — `omnis-term-browser` downsamples pixel buffers into TrueColor ANSI
  Sixel graphics or high-density Unicode Braille matrices (`⣿⣾⣽⣻⢿⡿⣟⣯⣷`), letting full-colour
  graphical web apps render inside character-cell panes.

### 8.3 Settings integration

```jsonc
{
  "workbench.brandTheme": "brand-zed",
  "workbench.layout.paradigm": "terminal-grid",
  "browser.terminalRenderer.mode": "auto",
  //   'semantic-text' (AXTree) | 'pixel-sixel' (Braille/graphics) | 'hybrid'
  "browser.terminalRenderer.fps": 30
}
```

- When `terminal-grid` is active, opening a browser tab instantiates the `omnis-term-browser`
  supervisor; the tab header renders in a terminal tab bar and content is blitted into the cell grid.
- When `dom-flexbox` is active, the browser tab switches to a standard sandboxed Chromium `<iframe>`
  view.
- The entire application — code editor, terminal, settings, multi-agent chat, and web browser —
  operates across both rendering engines with no bolted-on extensions.

---

## 9. Master specification (partial)

User: *"incorporate everything new we scopped and audit gaps and think hard about adressing them
incorporate that and compile master"*.

### 9.1 Process topology, binary sharding & dual-socket IPC

> Omnis is engineered as a decoupled, multi-process operating system. The persistent background
> daemon, Tauri GUI presentation layer, language multiplexers, browser engine, and extension
> execution hosts run independently. This guarantees zero window crashes on UI reloads, unblocked
> I/O streams, and full harness agnosticism.

**Surface layer** (as captured):

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                                   SURFACE LAYER                                    │
│                                                                                    │
│  ┌────────────────────────────┐ ┌──────────────────────────┐ ┌──────────────────┐  │
│  │ Omnis GUI (Tauri Desktop)  │ │ Omnis CLI (`omnis`)      │ │ External Harness │  │
│  │ DOM-Flex / Cell-Grid       │ │ Shell orchestration tool │ │ Claude Code,     │  │
│  │ Cordis Microkernel Root    │ │ Pretty & `--json` output │ │ Codex CLI, Aider,│  │
│  │                            │ │                          │ │ Cursor, Scripts  │  │
│  └─────────────┬──────────────┘ └────────────┬─────────────┘ └────────┬─────────┘  │
└────────────────┼─────────────────────────────┼────────────────────────┼────────────┘
                 │                             │                        │
                 ▼                             ▼                        ▼
                        (Substrate Bus — dual-socket IPC)
```

Named components appearing across the transcript:

| Name | Role |
|---|---|
| `omnisd` | Persistent background daemon; owns state, I/O, GPU blitting |
| `cordis` | Microkernel / context runtime rooted in the GUI process |
| Substrate Bus | Dual-socket IPC fabric between surfaces and daemon |
| `omnis-core` | Native rendering switchboard and configuration engine |
| `omnis-term-ui` | Cell-grid terminal renderer |
| `omnis-browser` | Embedded Chromium engine |
| `omnis-term-browser` | AXTree/Sixel bridge from Chromium into the cell grid |
| `omnis` (CLI) | Shell orchestration surface with `--json` output |

> **[GAP — MAJOR]** The remainder of the master compilation was not captured: approximately 17,000
> characters of turn 15, plus turns 16–19 (a follow-up question, a 6,500-character answer, a second
> question, and a 19,000-character final compilation). Based on the surviving heading —
> "1. Process Topology, Binary Sharding & Dual-Socket IPC" — the lost material is the numbered
> sections 2..n of the master spec. **Recapture is required before this document can be considered
> a complete record.** See `notes/vision_capture.md` for how to resume the capture.

---

## 10. Open questions the transcript never answers

These are gaps in the *source material*, not in the capture. They are carried into
`ARCHITECTURE.md` as decisions that must be made before the corresponding epics start.

1. **What does Omnis actually do for a user on day one?** Every captured turn describes *how it
   looks and how it is configured*. No captured turn describes a workflow a user completes. The
   product thesis is undefined.
2. **Why Postgres/Drizzle in a local-first desktop app?** The transcript reaches for `pgTable` for
   appearance presets. Local-first and a server RDBMS are in tension.
3. **Is trade-dress imitation acceptable?** "Match their native apps as close as possible" for
   Claude, GitHub, VS Code, Zed, DeepSeek, and Kimi involves third-party names, marks, icons, and
   distinctive visual identity. Bundling and shipping those is a legal question, not a technical one.
4. **Is a second renderer affordable?** `dom-flexbox` and `terminal-cell-grid` means every UI
   surface — settings, dialogs, browser, editor, chat — is implemented twice, or implemented once
   against an abstraction that does not exist yet.
5. **What is the extension host actually compatible with?** `emulateVsCodeApi` is a multi-year
   commitment stated as a boolean.
6. **Which agent providers, and through what interface?** `aiPersona.defaultProvider` is a string
   with no adapter contract behind it.
7. **What are the performance budgets?** "Sub-millisecond full-screen redraws" and "instant"
   renderer switching are asserted, never bounded or measured.
8. **What is the target platform matrix?** macOS vibrancy, Windows Mica/Acrylic, and Linux are all
   named; none is declared primary.
