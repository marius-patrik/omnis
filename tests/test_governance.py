"""Tests that the governance documents actually state the rules the automation relies on.

These are contract tests between prose and code. If someone softens a rule in `AGENTS.md`, the
automation that enforces it becomes a lie; these tests fail first.
"""

import os
import re

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(*parts: str) -> str:
    """Reads a repository file as text.

    Args:
        *parts: Path components relative to the repository root.

    Returns:
        File contents.
    """
    with open(os.path.join(REPO_ROOT, *parts), encoding="utf-8") as handle:
        return handle.read()


def test_agents_file_exists_and_is_the_canonical_source():
    """`AGENTS.md` is real and `CLAUDE.md` / `CONTRIBUTING.md` point at it."""
    assert os.path.isfile(os.path.join(REPO_ROOT, "AGENTS.md"))
    for alias in ("CLAUDE.md", "CONTRIBUTING.md"):
        path = os.path.join(REPO_ROOT, alias)
        assert os.path.exists(path), f"{alias} must exist"
        # On platforms without symlink support git materializes the link as a text file whose
        # content is the target path; accept either form.
        target = os.path.realpath(path)
        if os.path.basename(target) != "AGENTS.md":
            with open(path, encoding="utf-8") as handle:
                assert handle.read().strip() == "AGENTS.md", f"{alias} must resolve to AGENTS.md"


def test_agents_mandates_branches_prs_ci_and_protection():
    """Rule 7 keeps `main` protected and all work on branches behind pull requests."""
    content = _read("AGENTS.md").lower()
    for token in ("pull request", "branch", "ci", "protect", "main", "draft"):
        assert token in content, f"AGENTS.md must mention {token!r}"


def test_agents_mandates_issue_binding_and_board_taxonomy():
    """Rule 9 binds every PR to an issue and names the full status taxonomy."""
    content = _read("AGENTS.md").lower()
    assert "closes" in content
    assert "project board" in content
    for status in ("backlog", "todo", "in progress", "blocked", "done", "superseded", "dropped"):
        assert status in content, f"AGENTS.md must define the {status!r} status"


def test_agents_mandates_plan_gate_and_verbatim_requests():
    """Rules 10 and 12 keep both human approval gates in the process."""
    content = _read("AGENTS.md")
    assert "Matches Plan: Yes" in content
    assert "Plan Alignment:" in content
    assert "verbatim" in content.lower()
    assert "### Interpretation" in content


def test_agents_documents_every_declared_area():
    """The taxonomy in prose must match the one declared for the classifier.

    The classifier lives upstream and reads `.github/darkfactory.json`, so the pairing to check is
    prose against manifest: an area the agent can emit but the rules never mention is a label
    nobody can interpret.
    """
    import json

    with open(os.path.join(REPO_ROOT, ".github", "darkfactory.json"), encoding="utf-8") as handle:
        areas = json.load(handle).get("areas", {})
    content = _read("AGENTS.md")
    for name in areas:
        if name.startswith("$"):
            continue
        assert f"area:{name}" in content, f"AGENTS.md must document the 'area:{name}' scope"


def test_architecture_is_the_normative_root():
    """Architecture is the normative root and the transcript remains source material."""
    architecture = _read("ARCHITECTURE.md")
    transcript = _read("notes", "transcript.md")

    assert "Status: NORMATIVE" in architecture
    for term in ("OmnisOS", "OmnisManager", "OmnisAgent", "OmnisControl"):
        assert term in architecture, f"architecture must define {term}"
    assert "shared multidimensional graph" in architecture.lower()

    assert "SOURCE MATERIAL" in transcript, "the transcript must declare that it is not a spec"
    assert "ARCHITECTURE.md" in transcript, "the transcript must point at the normative document"
    assert not os.path.exists(
        os.path.join(REPO_ROOT, "VISION.md")
    ), "VISION.md would reintroduce a competing normative vision"


def test_architecture_states_implementation_invariants():
    """The architecture must end in explicit implementation-checkable invariants."""
    architecture = _read("ARCHITECTURE.md")
    assert "## 16. Implementation invariants" in architecture
    section = architecture[
        architecture.index("## 16. Implementation invariants") : architecture.index("## 17.")
    ]
    invariants = re.findall(r"^\d+\. \*\*", section, re.MULTILINE)
    assert len(invariants) >= 15, f"expected substantial hard invariants, found {len(invariants)}"
    for phrase in (
        "One stable identity space",
        "shared multidimensional current-state graph",
        "OmnisAgent owns the immutable causal worldline",
        "Nix evaluation/build remains deterministic",
    ):
        assert phrase in section


def test_architecture_defines_graph_worldline_and_authority_boundaries():
    """The reset must explicitly separate current state, causal history, and four authorities."""
    architecture = _read("ARCHITECTURE.md")
    for phrase in (
        "worldline = historical causal truth",
        "shared graph = current structured state",
        "OmnisOS",
        "OmnisManager",
        "OmnisAgent",
        "OmnisControl",
        "write ownership",
    ):
        assert phrase.lower() in architecture.lower()


def test_roadmap_phases_are_addressable():
    """The implementation roadmap must expose a concrete dependency-ordered phase sequence."""
    roadmap = _read("ROADMAP.md")
    phases = set(re.findall(r"^## Phase (\d+) ", roadmap, re.MULTILINE))
    assert {str(i) for i in range(0, 11)} <= phases, f"missing roadmap phases: {sorted(phases)}"


def test_transcript_declares_its_provenance():
    """Source material must say where it came from and how completely it was captured."""
    transcript = _read("notes", "transcript.md")
    assert "gemini.google.com" in transcript, "the transcript must cite its source conversation"
    assert "vision_capture.md" in transcript, "the transcript must link the provenance note"


def test_transcript_gap_markers_agree_with_the_capture_note():
    """Completeness is claimed in one place; the two documents must not contradict each other."""
    transcript = _read("notes", "transcript.md")
    capture = _read("notes", "vision_capture.md")

    if "Status: complete" in capture:
        assert "[GAP]" not in transcript, (
            "vision_capture.md claims the capture is complete, "
            "but the transcript still carries [GAP] markers"
        )
    else:
        assert "[GAP]" in transcript, (
            "vision_capture.md does not claim completeness, "
            "so the transcript must mark where it is partial"
        )


def test_transcript_carries_review_notes():
    """Recording a source faithfully is not the same as endorsing it."""
    transcript = _read("notes", "transcript.md")
    assert "Review notes" in transcript or "[REVIEW]" in transcript
    assert "ARCHITECTURE.md" in transcript, "the transcript must defer to the normative document"


def test_reference_declaration_exists_and_matches_new_component_split():
    """The v0 declaration must demonstrate the frozen Omnis module families."""
    declaration = _read("examples", "omnis.nix")
    architecture = _read("ARCHITECTURE.md")

    assert "examples/omnis.nix" in architecture
    for token in (
        "graph = {",
        "manager = {",
        "agent.users.alice",
        "control.users.alice",
        "security = {",
        'dataDir = "/var/lib/omnis/graph"',
        'nixControlSocket = "/run/omnis/nix-control.sock"',
        'vectorIndex = "sqlite-vec"',
        'defaultMode = "2d"',
        "quic.enable = true",
        "systemdCredentials.enable = true",
    ):
        assert token in declaration, f"reference declaration must show {token!r}"


@pytest.mark.parametrize(
    "document",
    ["README.md", "AGENTS.md", "ARCHITECTURE.md", "ROADMAP.md"],
)
def test_core_documents_are_present_and_substantial(document: str):
    """Placeholder documents are worse than missing ones; require real content.

    Args:
        document: Repository-root document name.
    """
    content = _read(document)
    assert len(content) > 500, f"{document} looks like a placeholder"


def test_v0_implementation_profile_is_concrete():
    """Foundational implementation choices must be frozen rather than delegated to workers."""
    implementation = _read("docs", "IMPLEMENTATION.md")
    for term in (
        "Rust 2024",
        "Tokio",
        "Cap'n Proto",
        "UUIDv7",
        "BLAKE3",
        "SQLite",
        "FTS5",
        "Smithay",
        "wgpu",
        "systemd",
        "QUIC",
        "omnis-graphd",
        "omnis-managerd",
        "omnis-agentd",
        "omnis-control",
    ):
        assert term in implementation, f"v0 implementation profile must freeze {term}"
    assert "durable event outbox" in implementation.lower()
    assert "at-least-once" in implementation


def test_protocol_schema_sources_exist():
    """The frozen wire contract must exist as schema source, not prose only."""
    for name in ("common", "graph", "os", "manager", "agent", "control"):
        path = os.path.join(REPO_ROOT, "protocol", f"{name}.capnp")
        assert os.path.isfile(path), f"missing canonical protocol schema {name}.capnp"
        content = _read("protocol", f"{name}.capnp")
        assert content.startswith("@0x"), f"{name}.capnp must declare a schema ID"
    common = _read("protocol", "common.capnp")
    assert "struct Uuid" in common
    assert "struct ArtifactId" in common
