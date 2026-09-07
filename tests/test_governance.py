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


def test_architecture_is_the_only_normative_document():
    """Vision and architecture are one file; the transcript specifies nothing."""
    architecture = _read("ARCHITECTURE.md")
    transcript = _read("notes", "transcript.md")

    assert "Status: NORMATIVE" in architecture
    assert "only normative document" in architecture

    assert "SOURCE MATERIAL" in transcript, "the transcript must declare that it is not a spec"
    assert "ARCHITECTURE.md" in transcript, "the transcript must point at the normative document"
    assert not os.path.exists(
        os.path.join(REPO_ROOT, "VISION.md")
    ), "VISION.md was merged into ARCHITECTURE.md; a second one would reintroduce the split"


def test_architecture_states_its_principles_with_enforcement():
    """A principle nobody enforces erodes; the table must say what enforces each one."""
    architecture = _read("ARCHITECTURE.md")
    principles = set(re.findall(r"^\| (P\d+) \|", architecture, re.MULTILINE))
    assert len(principles) >= 8, f"expected the principle table, found {sorted(principles)}"
    section = architecture[architecture.index("## 2. Principles") : architecture.index("## 3.")]
    for line in section.splitlines():
        if re.match(r"^\| P\d+ \|", line):
            assert line.count("|") >= 4, f"principle has no enforcement column: {line[:60]}"


def test_architecture_lists_open_decisions_with_identifiers():
    """Every open decision is addressable, so an issue and an ADR can reference it."""
    architecture = _read("ARCHITECTURE.md")
    identifiers = set(re.findall(r"\bD([1-9]\d*)\b", architecture))
    assert {"1", "2", "3", "4", "5", "6", "7", "8"} <= identifiers


def test_roadmap_epics_are_addressable():
    """Every epic has an `E<n>` identifier that issues and gates can cite."""
    roadmap = _read("ROADMAP.md")
    epics = set(re.findall(r"\bE(\d+)\b", roadmap))
    assert len(epics) >= 8, f"expected at least 8 epics, found {sorted(epics)}"


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


def test_reference_declaration_exists_and_is_documented():
    """The declaration is the product's central artifact; a stale example is worse than none."""
    declaration = _read("examples", "omnis.nix")
    architecture = _read("ARCHITECTURE.md")

    assert "examples/omnis.nix" in architecture, "the architecture must point at the declaration"
    for section in ("hosts", "placement", "subsystems", "environments", "presentation", "secrets"):
        assert (
            f"{section} = " in declaration or f"{section} =" in declaration
        ), f"the reference declaration must show `{section}`"
    assert "keychain:" in declaration, "secrets must appear as references, never values"


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
