# Omnis — Architecture

**Status: NORMATIVE, and the only normative document.** Vision and architecture are one file: what
Omnis is, why, and how it is built. The scoping transcript that started it is kept as source material
in [`notes/transcript.md`](notes/transcript.md) and specifies nothing.

Changes require a decision record in [`notes/adr/`](notes/adr/).

---

## 1. What Omnis is

**An AI-first operating system for a power user's machine.**

*AI-first* here is a structural claim, not a description of a feature. An agent is a **first-class
operator** of this system: it calls the same API as the user (P5), reads the same option schema the
settings UI is generated from (P9), addresses the same objects by the same URIs (§10.3), and is bound
by the same approval gate and audit trail (§7.1). It is not a panel bolted into an editor.

That is only safe because of what §4.1 and §7.1 provide: every change an agent makes is a generation
with an author and a diff, gated before it takes effect and reversible after. Giving an agent real
power over a machine is defensible exactly to the degree that its actions are reviewable and
undoable — so the accountability machinery is not a constraint on the AI-first goal, it is the thing
that makes it achievable.

Omnis is a headless daemon that owns nothing you could get elsewhere, and everything that makes those
things compose. Version control, packages, tasks, terminals, containers, language servers,
debuggers, a browser, agents, secrets, and storage are all **bound, not built** — `git`, `sl`, Nix,
podman, libvirt, Chromium, Tailscale, the coding-agent CLIs. What Omnis owns is the seams: one bus,
one scene tree, one declaration, one modification surface, one audit trail.

Four properties follow, and they are the whole design:

**The system is declared, not configured.** One file describes the machine — subsystems, packages,
guest operating systems, where each process runs, how it looks. Applying it produces a *generation*
with a parent, a diff, and an author. Rollback is one operation. Removing something removes it
entirely: the processes, the packages, the files, and everything it contributed to the rest of the
system.

**Everything is modifiable, by anyone authorised.** The user, the built-in agent, and an external
agent all change the system through the same API, pass the same approval gate, and land in the same
audit trail. There is no privileged surface and no trusted caller.

**The documentation is part of the product.** The option schema that defines the declaration also
generates the documentation, so you read about the system in the same window you are declaring it in
— and so does the agent proposing the change.

**The interface is a configuration state, not an implementation.** Renderer output, layout, input
routing, keymap, and chrome are orthogonal axes. A *profile* is a named point in that space; a
*theme* is colours in the VS Code format, so the existing ecosystem loads unmodified.

**We do not enumerate workflows.** The subsystems compose: a task graph that reads a Cargo manifest,
a terminal whose secrets came from the vault, a browser page harvested into a context fragment, an
agent whose every action lands in the audit stream and whose risky ones wait in escrow. The
capability surface is the specification; workflows are what a user assembles from it.

**Non-goals.** Reimplementing anything on the bound list. Reproducing another product's feature set.
Cloud accounts, multi-user collaboration, or anything that requires a network service to start.

---

## 2. Principles

Each is enforced somewhere — a lint, a test, a type, or a process boundary. A principle that is only
a paragraph erodes on the first deadline.

| | Principle | Enforced by |
|---|---|---|
| P1 | **Bind, don't reimplement.** If it exists, bind it. If binding exposes it raw, write the adapter — not the tool. | Review against ADR-0011's list of owned abstractions |
| P2 | **An abstraction exists to make its backend swappable and removable**, never to replace it. | Two backends before an abstraction is called done |
| P3 | **Declared, not imperative.** State goes in the declaration; changes converge. | Runtime mutations write the declaration (§4.2) |
| P4 | **Removal is complete**, including system integration. | Integration is brokered, never self-registered (§5.3) |
| P5 | **No privileged caller.** The GUI has no capability the CLI or an external agent lacks. | One API, one validation path, one escrow (§7) |
| P6 | **No branching on a profile or theme name.** Features branch on axis values or capability queries. | Lint |
| P7 | **Every primitive degrades to a terminal.** A feature that cannot is a scene-tree problem. | Type-level: no fallback, no primitive (§9.4) |
| P8 | **Subsystems cannot couple.** The bus is the only ABI. | Separate processes (§5.1) |
| P9 | **One schema, three consumers.** Option definitions drive the settings UI, the documentation, and the agent's vocabulary. | Generated, never hand-written (§6) |
| P10 | **Adding a thing is declaring a thing.** Panes, sources, subsystems, environments, profiles, and themes are instances of shared abstractions, never bespoke implementations. | A new instance touches data and declaration, not core code |

---

## 3. Topology

Four layers. Nothing runs inside the core.

```
SURFACES      gui · tui · cli · web (over Tailscale) · external harnesses
                                    ▲
NEXT TO       vcs · terminals · lsp · dap · browser · cas · tasks · agent · docs · automation · exthost
              environments: containers · VMs · compat
              supervised peers — separate processes, the bus is the only ABI
                                    ▲
CORE          omnisd — bus router · registry · capability broker · convergence & generations
                                    ▲
BELOW         host OS · container runtime · Nix store · systemd · Tailscale · OS keychain
              bound, never owned
```

**Below** is infrastructure that pre-exists. The core binds it and never assumes exclusive ownership.
**Next to** are peers the core supervises but does not contain. **The core is small** — routing,
registry, brokering, convergence.

### 3.1 Responsibilities

| Process | Owns | Never does |
|---|---|---|
| `omnisd` | Bus routing, subsystem registry, capability brokering, convergence, generations | Render; contain a subsystem; depend on a surface being attached |
| Subsystems | One domain each, behind an adapter | Talk to each other except over the bus; self-register integration |
| `omnis-gui` | Window, renderer, input capture | Own durable state; block on I/O |
| `omnis-tui` | A full interactive surface in a real terminal, local or over SSH | Assume a GPU, a window, or a display server |
| `omnis` (CLI) | Scriptable surface, `--json` on every command | Reimplement daemon logic |
| Environments | A guest userland or machine | Nest inside the core |

### 3.2 The Substrate Bus

**Control** (`omnis-control.sock`, `\\.\pipe\omnis-control`) — JSON-RPC 2.0. Capability checks,
declaration reads and writes, generation transitions, escrow tickets, registry and schema queries.

**Data** (`omnis-data.sock`, `\\.\pipe\omnis-data`) — binary multiplexer, uniform 9-byte header:

```
[StreamID: u32][Opcode: u8][PayloadLength: u32]

0x01 PTY_STREAM   raw terminal stdout/stdin
0x02 PTY_RESIZE   [Cols: u16][Rows: u16]
0x03 DOCKER_LOG   demultiplexed container logs
0x04 CAS_CHUNK    decrypted content-addressed payloads
0x05 CDP_BINARY   browser screencast frames, guest window frames
```

Contract rules:

- The wire schema is **versioned and additive**. A surface built against version *N* runs against
  daemon version *N+k*. New opcodes are appended, never renumbered.
- Every control message is expressible as JSON, whatever the encoding on the wire.
- Surfaces are **stateless with respect to the daemon**. Any surface may attach, detach, or crash at
  any point without data loss — which is why a surface on another machine is legal (§8).
- **Tracing is part of the bus from the first message.** With every subsystem out of process, one
  stack trace becomes several processes and a correlation id. Retrofitting that is far more expensive
  than carrying it from the start.

---

## 4. The declaration

**One file defines the system.** Not settings the daemon reads — the definition it converges toward.
See [`examples/omnis.nix`](examples/omnis.nix) for the reference declaration.

It is a **Nix module**. Not a format of our own that compiles to Nix: that means owning a language, a
parser, a type system, an error-reporting story, and a compiler, to arrive where the Nix module
system already is. We get typed options, merge semantics, `mkDefault`/`mkForce`, imports, and
nixpkgs for nothing (P1).

It declares hosts and placement, subsystems and their backends, guest environments, presentation,
remote access, and secret *references* — never secret values.

### 4.1 Generations

Applying a declaration produces a **generation**: a parent, a diff, an author, and a resulting system.
Generations are listable, diffable, and roll back.

This is the mechanism behind two guarantees that would otherwise be aspirations:

- **Reversibility.** "Any change an agent makes can be rolled back" becomes one operation, identical
  for a typo, a bad profile, and a misbehaving agent.
- **Attribution.** A generation has an author. An agent reconfiguring your machine produces a
  reviewable change with a parent, not an untraceable mutation.

Audit answers *what happened*; generations answer *what the system now is, and who made it so*.

### 4.2 Runtime changes write the declaration

A change made through the modification surface is **staged into the declaration** and applied by
convergence. It is not an overlay and not a side channel. Overlays guarantee drift: the running
system stops matching the declaration exactly when you need the declaration to be true.

Resolution layers, later winning:

```
defaults → profile → user → workspace → runtime
```

Every layer is inspectable: the settings surface can name which layer set any value.

### 4.3 What this costs

Nix is a hard dependency with a real learning curve. Users who never open the file are served by the
GUI writing typed options for them; users who do open it meet Nix. Convergence is also not instant —
some changes apply live, others need a subsystem restart, and the option schema must say which, or
the interface will lie about when a change took effect.

---

## 5. Subsystems

A subsystem is **a separate process that speaks the bus**. That is the whole contract.

### 5.1 Why out of process

"Every subsystem must be independently omittable" as a *rule* erodes: with seventeen subsystems in
one address space, the first deadline produces a direct call between two of them and nothing fails to
signal it. With separate processes and only a versioned wire schema between them, two subsystems
**cannot** couple. The property becomes structural (P8).

It also makes P1 mechanical: binding `git` is a thin adapter process, not a module inside the daemon,
and a subsystem may be written in any language.

### 5.2 Supervision is not ours

Restart policy, resource limits, ordering, health checks, and **socket activation** are systemd's.
Socket activation matters specifically: a subsystem starts on its first bus message, which answers
both the memory cost of many processes and the cold-start cost of starting them.

### 5.3 Removal is complete

Disabling a subsystem removes the processes, the packages, the installed files, **and everything it
contributed to the rest of the system** — commands, keybindings, menu entries, file associations,
protocol handlers, shell completions, credential helpers, settings surfaces. Remove the Git backend
and nothing of Git remains anywhere. "Disabled" and "not installed" are not different states.

**This forces a constraint.** Integration points are **declared and brokered by the core registry**,
never registered imperatively by a subsystem. A subsystem that could install a shim, a menu entry, or
a `PATH` entry on its own would be one whose removal could never be complete. Declaring integration
is the only way the guarantee holds (P4).

### 5.4 Backends are swappable

Where a subsystem fronts more than one implementation — `git` and `sl`, several task runners, several
agent CLIs — the abstraction exists so they are **interchangeable and removable** (P2), not so either
is reimplemented. Omnis owns the operation log, the cross-repository graph, and the harness registry.
The tools stay the tools.

---

## 6. Documentation is part of the system

A declaration is only usable if you can discover what you may declare. So documentation is not a
website beside the product — it is a **surface inside it**.

### 6.1 One schema, three consumers

Every option carries a type, a default, a description, and an example. That single schema drives:

1. **The settings UI** — forms generated from types, not hand-built per option.
2. **The documentation** — in-product and published, generated from the same definitions.
3. **The agent's vocabulary** — what an agent may set, with what values, and what each means.

There is no second place to update, and therefore no way for the three to disagree (P9). An option
without a description is an incomplete option, and CI can say so.

### 6.2 Live while you declare

In the GUI and the TUI, editing the declaration shows the documentation for the option under the
cursor: what it does, its type, its default, what it interacts with, and whether changing it applies
live or needs a restart. **Declaring the system and reading about it are one activity**, not a
context switch to a browser.

The same pane carries the architecture and decision records, so "why is it like this" is answerable
without leaving the workspace.

### 6.3 The agent reads what you read

When an agent proposes a change to the declaration it is working from the option schema, and its
proposal cites the options it sets. An agent that must guess at option names produces
plausible-looking configuration that does not evaluate — the failure mode this design removes.

Combined with §7, the sequence is: the agent proposes a declaration change, the documentation for
every option it touched is shown beside the diff, and you approve or reject with the reasoning in
front of you.

### 6.4 It degrades

A documentation pane is text, so it satisfies the parity contract completely (§9.4). The TUI gets the
same documentation, searchable, with no loss.

---

## 7. The modification surface

**Everything configurable is modifiable at runtime — by the user, the built-in agent, and external
agents — through one API.**

- **No privileged surface.** The GUI is a control-socket client like any other. If a setting can be
  changed by clicking, it can be changed by `omnis` and by an agent over MCP, using the same
  operation (P5).
- **Introspectable, not guessable.** Clients enumerate the option schema, the axes and their legal
  values, installed profiles, themes, keymaps, environments, and subsystems (§6.1).
- **One validation path, one approval path.** Side-effectful mutations pass the same escrow whoever
  sent them. There is no trusted-caller shortcut: identity is not a security boundary when both the
  built-in and external agents run arbitrary model output. The gate is on the *action*.
- **Attributed.** Every mutation records who made it. An unattributable change is indistinguishable
  from a compromise.
- **Reversible**, via generations (§4.1).

### 7.1 Agent accountability

Every side-effectful agent action is **recorded before it takes effect** in an append-only audit
stream — actor, action category, parameters, outcome — and **gated by an escrow ticket** that
expires. An expired ticket is a denial, never a silent grant. A killswitch revokes in-flight
execution, not merely future execution. Actions that cannot be recorded cannot be executed.

Audit without escrow is a perfect record of damage already done. Escrow without audit is approvals
with no history. They are one invariant.

### 7.2 Self-optimisation

The system observes itself — which subsystems are used, latency and memory per process, cache hit
rates, which placements are slow — and **proposes changes to its own declaration**: disable a
subsystem nothing has called in a month, resize a cache, move a process to a host that is not
saturated, prefetch what is always fetched.

**Self-optimisation is not a new mechanism.** It is the system acting as an agent against itself, and
it goes through exactly the path in §7 and §7.1: a proposed generation, with a diff, an author, and
the measurements that motivated it, passing the same escrow. Approving it is the same action as
approving anything else, and rolling it back is the same operation.

**It is never silent.** A system that reconfigures itself without a reviewable generation is
precisely the unattributable change §7 rejects, and "the computer decided" is not an acceptable
answer to "why is my machine different today". Whether a class of optimisation may be auto-approved
is a policy in the declaration — off by default, and never for anything that removes or relocates.

The honest limit: this is only as good as the telemetry, and telemetry that answers "is this
subsystem worth keeping" is a design problem in its own right, not a side effect of logging.

### 7.3 Automation

Goal loops, workflow graphs, one-shot tasks, and scheduled jobs are **one abstraction**, not four
features (P10).

An **automation** is a declared graph of steps with:

| Part | What it is |
|---|---|
| **Trigger** | Manual, a schedule, a bus event, or a goal becoming unsatisfied |
| **Steps** | A graph — sequential, parallel, or conditional — of actions, each addressable (§10.3) |
| **Gates** | Escrow points where a human approves before the graph continues (§7.1) |
| **Checkpoints** | Durable progress, so an interrupted run resumes rather than restarts |
| **Termination** | An explicit stop condition. A goal loop without one is not a loop, it is a leak |

Every automation is declared (P3), every step is attributed and audited (§7.1), and a failed or
blocked run checkpoints and reports rather than dying silently.

**A goal loop is a graph with a satisfaction condition** rather than a distinct mechanism: it runs,
checks whether the goal holds, and either stops or re-enters. Self-optimisation (§7.2) is a goal loop
whose action is proposing a generation. Scheduled jobs are graphs with a time trigger. The task graph
(§11) is the execution engine underneath, not a parallel system.

**The proof this abstraction is right is that it already exists.** The pipeline that builds Omnis —
request, interpretation gate, plan, approval gate, implement, self-review loop, merge gate, with
checkpoint-and-resume on quota exhaustion — *is* a goal loop with human gates and durable
checkpoints. It is currently GitHub Actions and Python because the product does not exist yet. When
it does, that pipeline should be an Omnis automation, and the fact that it was built by hand first
means the abstraction is validated against a real workload rather than an imagined one.

**Not built yet.** This section specifies the shape; no automation engine exists. Its position in the
roadmap is deliberate — an automation abstraction is only worth building once the bus, the
declaration, and the escrow it depends on are real.

---

## 8. Hosts and placement

A **host** is a named execution target backed by a runtime: `native`, `docker`, `wsl`, `podman`,
`nspawn`, or `remote` (another personal machine over the tailnet). The container runtime is itself an
abstraction — pinning one would exclude users to save a thin dispatch.

Each core process — **daemon, CLI, GUI, TUI, web** — is **placed on a host** in the declaration.
Placement is a property of the system, not an installation detail: daemon on the workstation,
interface on the laptop, is a configuration rather than a special build.

Processes carry constraints, checked at evaluation time:

| Process | Requires |
|---|---|
| `daemon` | The workspace filesystem; durable storage |
| `gui` | A display, a GPU, the platform window system — effectively `native` |
| `tui` | A TTY |
| `cli` | Nothing; attaches to a daemon wherever it is |
| `web` | Reachability on the tailnet |

**Resolution failure is a configuration error with a reason**, reported when the generation is
evaluated — not a runtime crash. The GUI constraint is load-bearing: a GPU compositor in a container
without passthrough is crippled, and passthrough on macOS and Windows ranges from fragile to
unavailable. **The GUI runs natively; the daemon is what gets containerised.**

### 8.1 Remote access

Remote access is a **web surface served over Tailscale** at the device's HTTPS name
(`https://<device>.<tailnet>.ts.net`). Transport, naming, and certificates are Tailscale's; caller
identity comes from the tailnet, which is what makes attribution satisfiable for a remote caller.

It is **optional**. The daemon starts, runs, and is fully usable with no network at all.

The web surface is a surface, not a renderer backend: the compositor is wgpu-based and wgpu targets
WebGPU, so a browser hosts the *same* backend in a canvas.

### 8.2 What splitting costs

A remote daemon means remote filesystem access, so the VFS and content-addressed store stop being
optimisations and become load-bearing for correctness and latency. Input-to-frame latency crosses a
network in split configurations. And the tested combinations must be named explicitly, or "it works
on my placement" becomes the standard bug report.

---

## 9. Rendering

**Sources are not renderers.** Cell-grid layout, widget layout, web content, guest windows, and 3D
all emit primitives into one scene tree. Two **backends** consume it.

| Backend | Crate | Target | Output |
|---|---|---|---|
| GPU compositor | `omnis-render` | Desktop window, and a browser canvas via WebGPU | Batched GPU primitives |
| ANSI/TUI | `omnis-tui` | A real terminal, local or over SSH | Escape sequences on stdout |

The split is not aesthetic. `cell-grid` presentation is a terminal *look* the GPU compositor draws in
a window; the TUI backend is Omnis genuinely *running in a terminal* — no window, no GPU, works over
SSH, survives in `tmux`. Different problems, different code, identical features.

### 9.1 Why one scene tree

A terminal cell is a glyph run with fixed advance; a UI label is a glyph run with shaped advance —
same atlas, same pipeline. A browser is a content source, not a rendering engine. Effects that live
in only one backend become the per-profile bolt-on the whole design rejects. And compositing a
terminal pane, a video, and a particle field in one frame is a scheduling problem with one answer.

### 9.2 Primitives

| Primitive | Used by |
|---|---|
| Quad — solid, gradient, rounded, bordered, shadowed | backgrounds, panels, cell backgrounds, chrome |
| Glyph run — shared atlas, fixed or shaped advance | terminal cells, labels, code, semantic web text |
| Texture | screencast rasters, guest windows, icons, render targets |
| Path — SDF or tessellated | vector icons, graphs, DAG edges |
| Material layer — custom shader with declared inputs | 3D scenes, particle fields, backdrops, transitions |

**Adding a source must not add a primitive class.** If it would, that is a design conversation, not a
patch.

### 9.3 3D, shaders, particles

The material layer is a first-class primitive, not an effects add-on, available in every presentation
mode — including behind and between glyph runs in the cell grid. Two uses, deliberately not
conflated: **chrome** (backdrops, transitions, agent-activity fields) authored by Omnis and profiles,
and **content** (shader playgrounds, model preview, GPU-accelerated visualisation) supplied by a user
or extension. The engine supports both; exposing authoring demands sandboxing, resource limits, and
GPU-hang recovery, and is gated on D14.

### 9.4 The parity contract

| Primitive | In a terminal | Fidelity |
|---|---|---|
| Glyph run | Text cells | Full |
| Quad — fill, border | Background colour and box-drawing characters | Full when cell-aligned |
| Quad — rounded, shadow, gradient | Nearest box-drawing corner; shadows dropped | Approximate |
| Path | Braille or box-drawing rasterisation, else its label | Approximate |
| Texture | Terminal graphics protocol where present, else half-block or Braille, else declared alt text | Terminal-dependent |
| Material layer | **Cannot execute**; renders its static fallback | None |

1. **Every primitive declares a terminal fallback.** No fallback, no primitive — enforced at the type
   level, not by convention (P7).
2. **Nothing is silently dropped.** Degradation is visible — alt text, a placeholder — never a blank
   region that hides the fact content exists.
3. **Feature parity, not pixel parity.** Every command, pane, view, and workflow is reachable in the
   TUI. Visual fidelity is explicitly not promised.
4. **No feature is TUI-only or GPU-only.** A feature that cannot degrade is a scene-tree design
   problem, fixed by extending the scene tree — never by branching on the backend.

Terminal capability is **detected, not assumed**: truecolor versus 256-colour, kitty keyboard
protocol versus legacy escapes, SGR mouse reporting, graphics-protocol support.

### 9.5 What owning the renderer costs

Text shaping, hit-testing, IME, and **accessibility**. A custom-rendered UI publishes no native
accessibility tree unless built to, so UIA/AX/AT-SPI belongs in the compositor's acceptance criteria
rather than a later epic. The web surface makes this sharper, not softer: a browser is where users
most expect assistive technology to work.

---

## 10. Presentation

### 10.1 Themes and profiles

**A theme is colours**, in the **VS Code colour-theme format** — `colors`, `tokenColors`,
`semanticTokenColors`, `type`. Existing themes load unmodified, and the format already carries
`terminal.ansi*`, so the sixteen ANSI colours both the cell grid and `omnis-tui` need come free. Icon
themes use the VS Code icon-theme format for the same reason.

**A profile bundles** a theme, an icon theme, the axis values below, window chrome, the app icon and
its state animations, typography and density, an audio pack, material-layer backdrops, and settings
overrides.

**Agent persona is not part of a profile.** A profile may *suggest* one; it never sets a provider,
model, or reasoning effort behind the user's back.

### 10.2 The capability matrix

| Axis | Option | Values |
|---|---|---|
| Presentation mode | `presentation` | `cell-grid` · `widget` · `hybrid` |
| Layout topology | `layout` | `chat-centric` · `ide-split` · `terminal-grid` · `vcs-dag` |
| Input routing | `inputBar` | `global-hud` · `per-pane` · `hybrid` |
| Keymap | `keybindings` | `default` · `vscode` · `zed` · `cursor-claude` · `vim` · `emacs` |
| Chrome & tokens | `window.*`, `theme` | §10.1 |

Which *backend* runs is not an axis and not a preference: it follows from the surface. `hybrid` mixes
presentation modes per pane, so a cell-grid editor beside a widget settings panel is legal rather
than a special case.

Themes and profiles are **data files** and nothing else. Adding either requires zero code changes (P6).

### 10.3 One input bar, one navigation model

**There is one input bar.** Not a chat box, a search field, a terminal prompt, a command palette, and
a browser address bar — one input, bound to whatever has focus. A chat, a quick search, a terminal, a
web page, a settings filter, and a documentation query all reach the user through the same control.

Panes do not ship their own input widgets. A pane declares an **input contract** — what it accepts,
where completions come from, what history it draws on, and what submitting means — and the input bar
renders and routes accordingly. That is P10 applied to the most duplicated widget in every
comparable product.

This clarifies the `inputBar` axis (§10.2): `global-hud` and `per-pane` are not two implementations,
they are two *placements* of the same bar — floating and centred, or anchored into the focused pane.
`hybrid` mixes them.

**Everything is addressable.** Panes, files, settings pages, documentation, chats, repositories,
tasks, context fragments, and guest environments all have an `omnis://` address. Addressability is
what makes the rest of this work: it is what the input bar navigates to, what the CLI takes as an
argument, what an agent cites in a proposal, and what a link in the documentation points at.

**Navigation is global.** Because everything is addressed, **back, forward, and reload** are system
controls rather than browser controls, over one history stack across every surface. Reload means
*re-materialise this view from its source* — re-read the file, re-query the schema, re-fetch the page
— and never *re-execute*: reloading a task view must not run the task. Confusing those two is how a
navigation control becomes destructive.

---

## 11. Data

**Configuration lives in files; user data lives in PGlite** — embedded Postgres, not a server.

The test: *would a user want this in version control, or be alarmed to find it there?* Themes,
profiles, keymaps, layouts, feature flags, placement, and environments are the first. Workspaces,
tabs, chat threads, audit entries, CAS metadata, VCS state, context fragments, and escrow tickets are
the second.

- **Content-addressed storage** — content-defined chunking, BLAKE3 keys, convergent encryption keyed
  by a per-user master secret, reflink deduplication. Convergent encryption leaks equality *within*
  one user's store: an attacker with store access who can guess a plaintext can confirm its presence.
  A bounded, accepted property, not an oversight.
- **Context fragments** — everything captured normalises to one envelope regardless of origin (code
  selection, terminal buffer, browser page, container log), addressable as `omnis://context/<id>`,
  payload in the CAS. Per-origin formats would mean an adapter per origin per consumer.
- **The VCS operation log** — every mutating operation appends an entry carrying enough state to
  invert it. Undo is a first-class operation over that log, not reconstruction from git internals,
  and it holds identically for Git and Sapling because the log is Omnis's. Operations that are not
  losslessly invertible must capture the discarded state into the CAS first, or refuse.
- **Task identity is the hash of its inputs** — source content, dependency output hashes, the command
  line, the declared environment. Not a timestamp: `mtime` changes on checkout and fails to change on
  same-second writes, and is meaningless across machines or a sync mesh. Undeclared inputs produce
  wrong cache hits, so detecting them is part of the work, not an extra.

---

## 12. Security

- **The vault.** Master key via Argon2id; the key-encryption key in a zeroising buffer with `mlock`,
  never serialised. Device secrets bridge to the OS keychain.
- **Secrets reach child processes by injection at spawn time** — never written to disk, never to a
  file the child reads.
- **Secrets never enter agent context.** An agent may reference a secret by name and cause it to be
  injected; it may not read the value. Otherwise every secret reaches a model provider's logs and any
  transcript the user later shares.
- **Git, forge, and SSH authentication** go through a local agent socket, so private keys are
  decrypted on demand and never handed out.

The structure is fixed; the **threat model is D10** and may constrain it.

---

## 13. Crate and package layout

```
crates/
  omnis-core/          bus contracts, option schema, scene tree types, capability matrix
  omnisd/              the core: routing, registry, brokering, convergence, generations
  omnis-cli/           `omnis`, `--json` on every command
  omnis-gui/           desktop host and window manager
  omnis-tui/           ANSI backend: scene tree to cells, capability detection, input decoding
  omnis-render/        GPU compositor: frame graph, primitives, glyph atlas, material passes
  omnis-layout/        cell-grid and widget layout modes
  omnis-browser/       Chromium supervisor and CDP bridge
  omnis-web-source/    AXTree→layout and screencast→texture bridges
  omnis-cas/           chunking, convergent encryption, VFS
  omnis-agent/         harness registry, session supervision, MCP bridge
  omnis-docs/          option schema → documentation, search index, in-product docs surface
subsystems/            one adapter binary per bound tool — vcs, terminals, lsp, dap, tasks, …
packages/
  frontend/            web surface shell
  profiles/            profiles and themes — data only, no code
nix/                   modules defining the declaration's option schema
examples/
  omnis.nix            the reference declaration
```

Nothing here exists yet. It is the target shape, and the reason `ci.yml` already carries guarded Rust
and web jobs.

---

## 14. Open decisions

Resolved decisions link to their record; see [the decision log](notes/adr/).

| # | Decision | Blocks |
|---|---|---|
| D1 | **First vertical slice** — which single path through the substrate is built first, end to end. A sequencing choice, not a product thesis. | E1, and the ordering of everything after |
| ~~D2~~ | Config/data boundary — resolved by [ADR-0005](notes/adr/0005-configuration-lives-in-files-data-lives-in-pglite.md) and [ADR-0012](notes/adr/0012-the-system-is-one-declarative-configuration-applied-as-generations.md) | ~~E6~~ |
| D3 | **Trade-dress policy** — which third-party names, marks, and icons may ship, and under what attribution | E4 |
| D4 | **Host backends and tested placements per platform** — reshaped by [ADR-0016](notes/adr/0016-hosts-are-declared-execution-targets-and-processes-are-placed-on-them.md) from "which platforms" to "which backends, and which placements do we test" | E2, E3, E11 |
| D5 | **Extension host compatibility target** — VS Code API emulation, or native-first with shims | E8 |
| D6 | **Agent provider adapter contract** | E5 |
| D7 | **Performance budgets** — frame time, redraw latency, cold start, memory ceiling, and input-to-frame across a network | E3, E7 |
| ~~D8~~ | Renderer hot-swap — dissolved by [ADR-0001](notes/adr/0001-one-scene-tree-two-renderer-backends.md); what remains is graphics device loss and adapter switching | E3 |
| D9 | **Subsystem admission criteria** — what a subsystem must satisfy to enter the "next to" layer | Every subsystem |
| D10 | **Vault threat model** — what `mlock`, the Argon2id parameters, and spawn-time injection actually defend against | E11, E19 |
| D11 | **Graphics baseline** — API, minimum GPU capability, and what happens below it | E3, E21 |
| D12 | **Text stack** — shaping, atlas strategy, subpixel policy, bidi, IME | E3 |
| D13 | **Webview compositing** — shared-texture, readback, or native subsurface | E3, E7, E8 |
| D14 | **Shader and 3D exposure** — Omnis and profiles only, or users and extensions | E21 |
| D15 | **Terminal capability floor** for `omnis-tui` | E22 |

---

## 15. Repository automation

The development pipeline is part of the architecture: [`AGENTS.md`](AGENTS.md) states the rules,
[`notes/pipeline.md`](notes/pipeline.md) explains how it works and how releases are cut,
`.github/workflows/` enforces it, and `.github/scripts/` implements it. The pipeline is Python; that
is deliberate and independent of the product stack.
