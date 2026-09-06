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
        "Blocked by D1 (day-one user workflow). Until we know what a user does, "
        "the message set is guesswork.",
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
        "Terminal cell-grid renderer",
        "area:term",
        "Blocked by D4 (platforms), D7 (performance budgets), D8 (hot-swap), and E10 (view model). "
        "Starting this before the view model exists produces a fork of the UI, not a renderer.",
        "GPU cell matrix buffer, WebGPU/WebGL blit pipeline, monospace metrics, 24-bit TrueColor "
        "with SGR attributes, 256-colour ANSI palettes, cursor shapes, pane-grid keyboard "
        "navigation, command-palette-first interaction, and the inline terminal inspector.",
        [
            "Every screen reachable in the DOM renderer is reachable here, from the same view model",
            "No feature code is written twice; the diff touches renderers, not features",
            "Frame time meets the budget set by D7, measured in CI",
        ],
    ),
    (
        "E4",
        "Brand presets as pure data",
        "area:ui",
        "Blocked by D3 (trade-dress policy) and E9 (capability matrix).",
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
        "Blocked by D2 (storage engine and shape).",
        "Storage engine choice, schema, migrations, the sync boundary, and the line between "
        "configuration (versioned files) and user data (the store).",
        [
            "Configuration never lives in the database",
            "Migrations run forward on a populated store without data loss",
            "The application starts and works with no network available",
        ],
    ),
    (
        "E7",
        "Terminal-grid browser bridge",
        "area:browser",
        "Blocked by E3 (cell-grid renderer) and D7 (performance budgets).",
        "The `omnis-browser` Chromium/CDP worker; semantic mode (AXTree to styled cells with "
        "interactive cell coordinates and CDP navigation events); pixel mode (screencast to Sixel "
        "or Unicode Braille); and `auto`/`hybrid` mode selection with an FPS budget.",
        [
            "A documentation page is readable and navigable in semantic mode by keyboard alone",
            "Pixel mode holds the configured FPS without starving the daemon",
            "Crashing the browser worker does not affect the daemon or other surfaces",
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
        "Renderer-agnostic view model",
        "area:core",
        "Blocked by E9 (capability matrix). Must land before E3.",
        "The scene tree: panes, focus, buffers, selections, decorations. This is the abstraction "
        "boundary that makes a second renderer affordable instead of a second product.",
        [
            "The DOM renderer is rewritten to consume only the scene tree",
            "No feature code references a renderer directly",
            "A feature that cannot be expressed in the scene tree is rejected, not special-cased",
        ],
    ),
]

#: (decision id, question, what it blocks).
DECISIONS: List[Tuple[str, str, str]] = [
    (
        "D1",
        "What does a user actually do with Omnis on day one, before any theming exists?",
        "Everything. The whole of Phase 1, and the sequencing of E1.",
    ),
    (
        "D2",
        "Which storage engine and shape for local-first user data? "
        "Postgres is rejected for configuration; the store for user data is undecided.",
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
        "What is the target platform matrix, and which platform is primary for v1?",
        "E2, E3",
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
        "Is renderer switching restart-tolerant only, or live hot-swap?",
        "E3",
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
