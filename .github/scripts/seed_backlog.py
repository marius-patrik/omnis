"""Seeds the epic and decision issues that decompose the roadmap, and puts them on the board.

`ROADMAP.md` and `ARCHITECTURE.md` §7 are the source of truth; this script turns them into tracked,
addressable issues so the pipeline has something to work against. It is idempotent: an issue whose
title already exists is updated in place rather than duplicated.

Usage::

    python .github/scripts/seed_backlog.py --plan
    python .github/scripts/seed_backlog.py --apply
"""

import argparse
import json
import subprocess
import sys
from typing import Dict, List, Optional, Sequence, Tuple

OWNER = "marius-patrik"
REPO = "omnis"
SLUG = f"{OWNER}/{REPO}"
PROJECT_NUMBER = 15

#: (roadmap id, title, area label, entry gate, scope, acceptance criteria).
EPICS: List[Tuple[str, str, str, str, str, List[str]]] = [
    (
        "E1",
        "Substrate Bus and process topology",
        "area:core",
        "Blocked by D1 (first vertical slice) and D9 (subsystem admission criteria).",
        "The `omnis-proto` wire schema, dual-socket transport (control: ordered typed "
        "request/response; stream: high-volume unidirectional frames), the additive versioning "
        "rule, an `omnisd` skeleton, surface attach/detach, and crash isolation between surfaces "
        "and daemon.",
        [
            "A surface built against schema version N runs unchanged against daemon version N+1",
            "Killing any surface leaves the daemon and every other surface running",
            "Every message round-trips through JSON for the CLI and for debugging",
            "Reconnecting a surface loses no durable state",
        ],
    ),
    (
        "E2",
        "Tauri shell and window chrome engine",
        "area:ui",
        "Blocked by D4 (platform matrix).",
        "Frame styles (`frameless-custom`, `native-integrated`, `transparent-overlay`), drag "
        "regions, traffic-light insets, vibrancy materials (mica, acrylic, sidebar, hud), corner "
        "radius, shadow elevation, and the dynamic dock/tray icon with its idle / thinking / error "
        "/ approval-pending state machine.",
        [
            "Every chrome property is reachable from settings without brand-specific code",
            "The icon state machine reflects daemon state within one frame of the transition",
            "Each frame style is verified on every platform declared primary by D4",
        ],
    ),
    (
        "E3",
        "Unified GPU compositor (`omnis-render`)",
        "area:term",
        "Blocked by D4 (platforms), D7 (performance budgets), D11 (graphics baseline), "
        "D12 (text stack), and E10 (scene tree). Building any source before the compositor "
        "produces a private renderer with a different name.",
        "**The** renderer. Frame graph; batched instanced primitives (quad, glyph run, texture, "
        "path, material layer); shared glyph atlas and shaping; damage tracking; device-loss "
        "handling; and the material-layer pass that 3D and particles ride on. Terminal, widget, "
        "browser, and 3D are sources that emit into this crate - they are not renderers.",
        [
            "Terminal cells and UI labels share one glyph atlas and one pipeline",
            "Adding a source adds no new primitive class",
            "A terminal pane, a video, and a particle field composite in one frame within the "
            "D7 budget, measured in CI",
            "The accessibility tree is published to the platform (UIA / AX / AT-SPI) - a custom "
            "renderer that ships without one is unusable with a screen reader",
            "GPU device loss recovers without losing application state",
        ],
    ),
    (
        "E4",
        "Brand presets as pure data",
        "area:ui",
        "Blocked by D3 (trade-dress policy), E9 (capability matrix), and E20 (layout modes).",
        "Preset file format, token sets, asset packs, the `lucide-animated` default icon set, and "
        "the proof that adding a brand requires zero code changes.",
        [
            "Adding a new preset touches only data files - no source file changes",
            "A lint fails any code that branches on a preset name",
            "Third-party marks shipped, if any, comply with the policy set by D3",
        ],
    ),
    (
        "E5",
        "Agent harness orchestration",
        "area:agents",
        "Blocked by D6 (provider adapter contract) and E1 (bus).",
        "Provider adapter contract, session supervision, approval gates, streaming, and persona "
        "configuration. Explicitly decoupled from visual themes: selecting a look must not select "
        "a model.",
        [
            "A new provider is added by implementing the adapter, with no core changes",
            "Every side-effectful agent action passes an approval gate",
            "Theme selection has no effect on which provider or model is used",
        ],
    ),
    (
        "E6",
        "Local-first persistence",
        "area:data",
        "Blocked by D2 (the configuration/data boundary).",
        "The PGlite store, schema, migrations, the configuration/data boundary, and the sync "
        "boundary.",
        [
            "Configuration never lives in the database",
            "Migrations run forward on a populated store without data loss",
            "The application starts and works with no network available",
        ],
    ),
    (
        "E7",
        "Browser as a source",
        "area:browser",
        "Blocked by E3 (compositor), E20 (layout modes), D7 (performance budgets), and "
        "D13 (webview compositing).",
        "The `omnis-browser` Chromium/CDP worker and `omnis-web-source`: semantic mode "
        "(AXTree to layout to primitives, keyboard-navigable) and raster mode (screencast to "
        "texture), `auto`/`hybrid` selection, an FPS budget, and webview compositing per D13. "
        "A browser is a content source, not a rendering engine.",
        [
            "A documentation page is readable and navigable in semantic mode by keyboard alone",
            "Raster mode holds the configured FPS without starving the daemon",
            "Crashing the browser worker does not affect the daemon or other surfaces",
            "Third-party webviews reach the frame without a full readback per frame",
        ],
    ),
    (
        "E8",
        "Extension host",
        "area:ext",
        "Blocked by D5 (compatibility target) and E1 (bus).",
        "Sandboxed host process, plugin API surface, capability grants, and compatibility shims.",
        [
            "A misbehaving extension cannot crash or block the daemon",
            "Capability grants are explicit, auditable, and revocable",
            "The compatibility target chosen in D5 is met for a named reference extension",
        ],
    ),
    (
        "E9",
        "Capability matrix and settings switchboard",
        "area:core",
        "Blocked by E1 (bus).",
        "The five orthogonal axes, layered settings resolution "
        "(`defaults -> preset -> user -> workspace -> runtime`), JSON schema, live IPC updates, "
        "layer introspection, and the lint that enforces no branching on preset names.",
        [
            "Every axis is settable independently; no combination is rejected by construction",
            "The settings UI can name which layer set any given key",
            "A settings change propagates without restarting the daemon",
        ],
    ),
    (
        "E10",
        "Scene tree - the renderer-agnostic view model",
        "area:core",
        "Blocked by E9 (capability matrix). Must land before E3.",
        "Panes, focus, buffers, selections, decorations, and the primitive vocabulary of "
        "ARCHITECTURE.md section 4.2. The single input to the single renderer.",
        [
            "Every source emits scene-tree primitives and nothing else",
            "No feature code references a renderer directly",
            "A feature that cannot be expressed in the scene tree is rejected, not special-cased",
        ],
    ),
    (
        "E11",
        "Vault, SSH/GPG agent, and secure process spawn",
        "area:core",
        "Blocked by D4 (platforms), D10 (threat model), and E1 (bus).",
        "Argon2id-derived KEK held in a `Zeroizing` buffer with `mlock`; OS keychain bridging "
        "(Apple Keychain, DPAPI, Secret Service); `omnis-ssh-agent` on `~/.omnis/ssh.sock`; "
        "`.env` injection into child process memory maps, never to disk and never into agent "
        "context windows.",
        [
            "No plaintext secret is ever written to disk or into an agent's context",
            "A spawned process receives its secrets; a sibling process cannot read them",
            "Locking the vault revokes in-flight access, not just future access",
        ],
    ),
    (
        "E12",
        "Terminals, PTY, and containers",
        "area:core",
        "Blocked by E1 (bus).",
        "Native PTY manager, tmux control server, Bollard Docker pipes, resource supervisor, and "
        "the `PTY_STREAM` / `PTY_RESIZE` / `DOCKER_LOG` data-socket opcodes end to end.",
        [
            "A terminal survives the GUI reloading or crashing",
            "Resize is in-band and never loses buffered output",
            "The resource supervisor bounds a runaway process without killing the daemon",
        ],
    ),
    (
        "E13",
        "Content-addressed storage and VFS",
        "area:data",
        "Blocked by E6 (persistence).",
        "`omnis-cas`: FastCDC chunking, BLAKE3 keys, convergent encryption, reflink deduplication, "
        "multi-provider VFS mounts, and the central inotify watcher.",
        [
            "Identical content stored twice occupies one copy",
            "Convergent keys never leak plaintext across encryption boundaries",
            "The watcher scales to a large workspace without exhausting handles",
        ],
    ),
    (
        "E14",
        "Universal VCS and stacked PRs (`ovcs`)",
        "area:core",
        "Blocked by E1 (bus).",
        "Dual Git/Sapling engine, atomic operation log (`vcs_op_log`), automated `absorb`, 3-way "
        "AST merge editor, stacked PR management across GitHub/GitLab/Forgejo, git alternates "
        "manager.",
        [
            "Every mutating operation is undoable from the operation log",
            "The same workflow works against Git and Sapling repositories",
            "A stack rebases without the user reconstructing it by hand",
        ],
    ),
    (
        "E15",
        "Task and build DAG engine",
        "area:core",
        "Blocked by E13 (CAS). The caching claim rests on CAS timestamps.",
        "Manifest parsing (`package.json`, `Cargo.toml`, `Makefile`, `Taskfile.yaml`), a "
        "cross-repository dependency graph, CAS-timestamp skipping of unchanged targets, and "
        "parallel execution.",
        [
            "An unchanged target is skipped, and the skip is explainable",
            "A dependency cycle is reported with the cycle, not just detected",
            "Parallel execution respects the resource supervisor's bounds",
        ],
    ),
    (
        "E16",
        "Packages and extensions - the binary substrate",
        "area:ext",
        "Blocked by D5 (compatibility target) and E1 (bus).",
        "The two universes kept deliberately separate: `omnis pkg` (project and system "
        "dependencies) versus `omnis ext` (client, editor, and agent capabilities). Install, "
        "resolve, cache, and grant.",
        [
            "A project dependency can never be installed as a client extension, or vice versa",
            "Extension capability grants are explicit and auditable",
            "The FastCDC cache is shared across workspaces without cross-contamination",
        ],
    ),
    (
        "E17",
        "LSP hub and DAP",
        "area:core",
        "Blocked by E1 (bus) and E12 (PTY and process supervision).",
        "`omnis-lsp` multiplexer hub and the `omnis-dap` Debug Adapter Protocol implementation.",
        [
            "One language server instance serves every surface and every pane",
            "A crashing language server is restarted without losing editor state",
            "Debug sessions survive a GUI reload",
        ],
    ),
    (
        "E18",
        "Universal context fabric",
        "area:core",
        "Blocked by E13 (CAS) and E1 (bus).",
        "`ContextFragment` harvesting from code selections, terminal buffers, browser pages, and "
        "container logs; a persistent sidebar shelf; and `omnis://context/<id>` URIs.",
        [
            "A fragment resolves to the same content after a restart",
            "Fragments from every listed origin share one normal form",
            "An agent can consume a fragment by URI without a bespoke adapter",
        ],
    ),
    (
        "E20",
        "Layout modes - cell-grid and widget",
        "area:term",
        "Blocked by E3 (compositor) and E10 (scene tree).",
        "`omnis-layout`: the cell-grid mode (fixed advance, 24-bit TrueColor with SGR attributes, "
        "256-colour ANSI palettes, cursor shapes, pane-grid keyboard navigation, "
        "command-palette-first interaction, inline inspector strips) and the widget mode, both "
        "emitting scene-tree primitives. `hybrid` mixes them per pane.",
        [
            "A cell-grid editor and a widget settings panel coexist in one window",
            "Switching presentation mode is a layout change, requiring no renderer restart",
            "Neither mode owns a primitive the other cannot use",
        ],
    ),
    (
        "E21",
        "3D, shaders, and particles",
        "area:ui",
        "Blocked by E3 (compositor), D11 (graphics baseline), and D14 (shader exposure). "
        "D14 sizes this epic by an order of magnitude.",
        "The material-layer pass in anger: a scene layer with its own camera and depth buffer, "
        "GPU-instanced particle systems, and custom shader materials with declared inputs. If D14 "
        "opens authoring to users and extensions: sandboxing, resource limits, and GPU-hang "
        "recovery.",
        [
            "A material layer composites correctly behind and between glyph runs in cell-grid mode",
            "A particle field runs without pushing the frame past the D7 budget",
            "If exposed per D14, a hostile or careless shader cannot wedge the GPU or the daemon",
        ],
    ),
    (
        "E19",
        "Sync mesh and CRDT change log",
        "area:data",
        "Blocked by E6 (persistence), E13 (CAS), and D10 (threat model).",
        "Tailscale mesh sync, a CRDT change log with hybrid logical clocks, P2P WebRTC mesh, "
        "cloud storage VFS, and the serialized PGlite mailbox. Syncs one user's devices - not "
        "multi-user collaboration.",
        [
            "Two devices edited offline converge without losing either side's work",
            "Clock skew between devices does not reorder causally related changes",
            "Sync is opt-in per workspace and the application works fully without it",
        ],
    ),
]

#: (decision id, question, what it blocks).
DECISIONS: List[Tuple[str, str, str]] = [
    (
        "D1",
        "Which single path through the substrate is built first, end to end, to prove the bus, "
        "the daemon lifecycle, and one surface? "
        "This is a sequencing choice, not a product thesis - the architecture is the "
        "specification, and the subsystems compose rather than enumerate.",
        "E1, and the ordering of everything after it",
    ),
    (
        "D2",
        "Which entities are configuration in versioned files, and which are data in the PGlite "
        "store, and where does the sync boundary fall? "
        "The engine itself is settled: the daemon's 'Serialized PGlite Mailbox' is embedded "
        "Postgres, so Drizzle is consistent with local-first.",
        "E6",
    ),
    (
        "D3",
        "Which third-party names, marks, and icons may ship, and under what attribution? "
        "'Match their native apps as close as possible' is a legal question before a technical one.",
        "E4",
    ),
    (
        "D4",
        "What is the target platform matrix, and which platform is primary for v1? "
        "Vibrancy, Mica/Acrylic, traffic-light insets, and `mlock` all diverge by platform.",
        "E2, E3, E11",
    ),
    (
        "D5",
        "Is the extension host compatible with the VS Code API, or is it a native-first API? "
        "`emulateVsCodeApi` is a multi-year commitment stated as a boolean.",
        "E8",
    ),
    (
        "D6",
        "What is the agent provider adapter contract?",
        "E5",
    ),
    (
        "D7",
        "What are the performance budgets: frame time, redraw latency, cold start, memory ceiling? "
        "'Sub-millisecond redraws' is currently asserted, never bounded or measured.",
        "E3, E7",
    ),
    (
        "D8",
        "Are graphics device loss and adapter switching handled transparently, or surfaced to the "
        "user? Narrowed from 'renderer hot-swap': with one renderer there is no renderer to swap, "
        "and switching presentation mode is a layout change.",
        "E3",
    ),
    (
        "D9",
        "What must a subsystem satisfy to be admitted into `omnisd` - bus-only communication, "
        "independent omission, a resource budget, failure isolation? "
        "The subsystem list is long enough that this has to be a written gate, not a habit.",
        "E1, and every subsystem epic in Phase 2",
    ),
    (
        "D10",
        "What does the vault threat model actually defend against, and what does it not? "
        "`mlock`, the Argon2id parameters, and injecting secrets into child process environments "
        "each carry real exposure that needs stating before it is built.",
        "E11, E19",
    ),
    (
        "D11",
        "Which graphics API, what minimum GPU capability, and what happens below it - software "
        "fallback, degraded mode, or refusal? One renderer makes this a hard floor for the whole "
        "application rather than a per-feature concern.",
        "E3, E21",
    ),
    (
        "D12",
        "What is the text stack: shaping engine, glyph atlas strategy, subpixel and hinting "
        "policy, bidi and complex-script support, IME integration? Owning the renderer means "
        "owning all of it.",
        "E3",
    ),
    (
        "D13",
        "How do out-of-process third-party webviews reach the frame - shared-texture zero-copy, "
        "readback, or a native subsurface? This decides whether VS Code extension UIs are usable "
        "or merely present.",
        "E3, E7, E8",
    ),
    (
        "D14",
        "Is the material layer authored only by Omnis and its presets, or also by users and "
        "extensions? Exposure demands sandboxing, resource limits, and GPU-hang recovery, since a "
        "careless shader can wedge a GPU.",
        "E21",
    ),
]


def run(cmd: List[str], apply: bool, capture: bool = True) -> Optional[str]:
    """Runs a command, or prints it in plan mode.

    Args:
        cmd: Command and arguments.
        apply: Execute when ``True``.
        capture: Capture and return stdout.

    Returns:
        Stripped stdout, or ``None``.
    """
    if not apply:
        print(f"  would run: {' '.join(cmd)}")
        return None
    result = subprocess.run(cmd, capture_output=capture, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip().splitlines()
        print(f"  FAILED: {' '.join(cmd[:4])} -> {detail[0] if detail else '?'}", file=sys.stderr)
        return None
    return (result.stdout or "").strip()


def existing_issues() -> Dict[str, int]:
    """Maps existing issue titles to their numbers.

    Returns:
        Title-to-number mapping for every issue in the repository.
    """
    raw = subprocess.run(
        [
            "gh",
            "issue",
            "list",
            "--repo",
            SLUG,
            "--state",
            "all",
            "--limit",
            "300",
            "--json",
            "number,title",
        ],
        capture_output=True,
        text=True,
    )
    if raw.returncode != 0:
        return {}
    return {entry["title"]: entry["number"] for entry in json.loads(raw.stdout)}


def upsert_issue(
    title: str, body: str, labels: Sequence[str], apply: bool, known: Dict[str, int]
) -> Optional[int]:
    """Creates the issue, or updates it when one with the same title already exists.

    Args:
        title: Issue title.
        body: Issue body in markdown.
        labels: Labels to apply.
        apply: Execute when ``True``.
        known: Title-to-number mapping of existing issues.

    Returns:
        The issue number, or ``None`` in plan mode or on failure.
    """
    label_args: List[str] = []
    for label in labels:
        label_args += ["--label", label]

    if title in known:
        number = known[title]
        print(f"  #{number} exists: {title}")
        run(
            ["gh", "issue", "edit", str(number), "--repo", SLUG, "--body", body] + label_args, apply
        )
        return number

    url = run(
        ["gh", "issue", "create", "--repo", SLUG, "--title", title, "--body", body] + label_args,
        apply,
    )
    if not url:
        return None
    number = int(url.rstrip("/").rsplit("/", 1)[-1])
    print(f"  #{number} created: {title}")
    return number


def add_to_board(issue_number: int, apply: bool) -> None:
    """Adds an issue to the project board.

    The board status is then set by the project automation workflow from the issue's labels, so this
    only has to place the item.

    Args:
        issue_number: Issue number.
        apply: Execute when ``True``.
    """
    run(
        [
            "gh",
            "project",
            "item-add",
            str(PROJECT_NUMBER),
            "--owner",
            OWNER,
            "--url",
            f"https://github.com/{SLUG}/issues/{issue_number}",
        ],
        apply,
    )


def epic_body(roadmap_id: str, gate: str, scope: str, acceptance: Sequence[str]) -> str:
    """Renders an epic issue body.

    Args:
        roadmap_id: Identifier from `ROADMAP.md`.
        gate: Entry gate text.
        scope: Scope text.
        acceptance: Acceptance criteria.

    Returns:
        Markdown body.
    """
    criteria = "\n".join(f"- [ ] {item}" for item in acceptance)
    return f"""**Roadmap ID:** `{roadmap_id}` — see [ROADMAP.md](../blob/main/ROADMAP.md)

### Scope
{scope}

### Entry Gate
{gate}

### Acceptance Criteria
{criteria}

### Child Requests
_None yet. File them with the Request template and link them here._

---
Epics are containers and are never implemented directly (`AGENTS.md` rule 13). Work happens in child
`Request` issues, each of which gets its own interpretation gate, `Plan` issue, and approval.
"""


def decision_body(decision_id: str, question: str, blocks: str) -> str:
    """Renders a decision issue body.

    Args:
        decision_id: Identifier from `ARCHITECTURE.md` §7.
        question: The question to answer.
        blocks: What stays blocked until it is answered.

    Returns:
        Markdown body.
    """
    return f"""**Decision ID:** `{decision_id}` — see
[ARCHITECTURE.md §7](../blob/main/ARCHITECTURE.md#7-open-decisions)

### The Question
{question}

### What This Blocks
{blocks}

### Options Under Consideration
_To be filled in. Each option with its cost, its risk, and what it forecloses._

### Constraints & Evidence
_To be filled in. Distinguish measured facts from assumptions._

---
Closing this issue requires a numbered ADR in
[`notes/architecture_decisions.md`](../blob/main/notes/architecture_decisions.md), and an update to
`ARCHITECTURE.md` where the decision changes the normative architecture.
"""


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description="Seed Omnis epics and decisions")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--apply", action="store_true", help="Create or update the issues")
    mode.add_argument("--plan", action="store_true", help="Print without changing anything")
    args = parser.parse_args()
    apply = args.apply

    known = existing_issues() if apply else {}

    print("== Decisions ==")
    for decision_id, question, blocks in DECISIONS:
        title = f"Decision: {decision_id} — {question.split('?')[0].strip()}?"
        number = upsert_issue(
            title,
            decision_body(decision_id, question, blocks),
            ["decision", "area:docs", "Backlog"],
            apply,
            known,
        )
        if number:
            add_to_board(number, apply)

    print("\n== Epics ==")
    for roadmap_id, name, area, gate, scope, acceptance in EPICS:
        title = f"Epic: {roadmap_id} — {name}"
        number = upsert_issue(
            title,
            epic_body(roadmap_id, gate, scope, acceptance),
            ["epic", area, "Backlog"],
            apply,
            known,
        )
        if number:
            add_to_board(number, apply)

    print("\nDone.")


if __name__ == "__main__":
    main()
