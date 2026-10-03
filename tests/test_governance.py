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
    for name in ("common", "events", "capabilities", "graph", "os", "manager", "agent", "control"):
        path = os.path.join(REPO_ROOT, "protocol", f"{name}.capnp")
        assert os.path.isfile(path), f"missing canonical protocol schema {name}.capnp"
        content = _read("protocol", f"{name}.capnp")
        assert content.startswith("@0x"), f"{name}.capnp must declare a schema ID"
    common = _read("protocol", "common.capnp")
    assert "struct Uuid" in common
    assert "struct ArtifactId" in common


def test_decision_complete_v0_contract():
    """Implementation workers must receive frozen algorithms/defaults instead of design gaps."""
    spec = _read("docs", "DECISION_COMPLETE_V0.md")
    required = (
        "Frozen source baselines",
        "Manager resolution and placement algorithm",
        "Agent event priority and cognition",
        "Agent candidate scheduling",
        "Agent retrieval",
        "Agent context compilation",
        "Control input routing",
        "Control graph layout",
        "Backup and recovery",
        "Package persistence scopes",
        "Inference gateway and universal model-event interception",
        "Desktop compatibility services",
        "Specification completeness invariant",
        "SpecificationDefect",
    )
    for heading in required:
        assert heading in spec, f"decision-complete spec is missing {heading!r}"

    for token in (
        "be5021eb406d32e8df6462a1c0986a70bdf03e02",
        "2ab29c63d3273d4e2b4d1346b1aefede9b5af350",
        "Rust toolchain:",
        "1.99.0",
        "cddab5f1c359539147959163142ff95a24995f6a",
        "NullIntention priority = 0.15",
        "RRF score = sum(1 / (60 + rank))",
        "127.0.0.1:7331",
        "UDP 7443",
    ):
        assert token in spec, f"decision-complete spec must freeze {token!r}"


def test_active_specs_forbid_implementer_choice_markers():
    """Active v0 specs must not positively delegate observable design decisions."""
    documents = (
        "ARCHITECTURE.md",
        "ROADMAP.md",
        "docs/IMPLEMENTATION.md",
        "docs/DECISION_COMPLETE_V0.md",
        "AGENTS.md",
    )
    forbidden = (
        "IMPLEMENTER MAY CHOOSE",
        "IMPLEMENTATION AGENT MAY CHOOSE",
        "CHOOSE WHICHEVER",
        "IMPLEMENTATION-SPECIFIC UNTIL",
        "PICK ANY EQUIVALENT",
        "USE WHICHEVER",
    )
    for document in documents:
        content = _read(*document.split("/")).upper()
        for marker in forbidden:
            assert marker not in content, f"{document} contains delegated-choice marker {marker!r}"


def test_canonical_v0_source_contracts():
    """Decision-complete implementation inputs must be checked in and addressable."""
    required = (
        "docs/ONTOLOGY_V0.md",
        "docs/NIX_OPTIONS_V0.md",
        "schema/graph.sql",
        "schema/worldline.sql",
        "schema/index.sql",
        "prompts/judgement.md",
        "prompts/intention.md",
        "prompts/memory_extract.md",
        "prompts/reason.md",
        "prompts/code_worker.md",
        "prompts/candidate_evaluate.md",
    )
    for rel in required:
        assert os.path.isfile(os.path.join(REPO_ROOT, rel)), f"missing canonical v0 source {rel}"

    ontology = _read("docs", "ONTOLOGY_V0.md")
    for token in (
        "omnis.capability.ingest",
        "omnis.event.graph.committed",
        "Execution state machine",
        "Worker state machine",
        "Memory ontology",
    ):
        assert token in ontology

    nix_options = _read("docs", "NIX_OPTIONS_V0.md")
    for token in (
        "omnis.graph.writerQueue",
        "omnis.manager.inferenceGateway.port",
        "omnis.agent.users",
        "omnis.control.users",
        "omnis.security.defaultWorkerNetwork",
    ):
        assert token in nix_options


def test_sql_v1_schemas_parse_with_sqlite():
    """The canonical SQLite v1 schemas must execute on the runtime SQLite parser."""
    import sqlite3

    for name in ("graph", "worldline", "index"):
        sql = _read("schema", f"{name}.sql")
        db = sqlite3.connect(":memory:")
        try:
            db.executescript(sql)
        finally:
            db.close()


def test_agent_prompt_registry_is_versioned_and_structured():
    """First-party generative calls must use checked-in prompts with structured outputs."""
    for name in (
        "judgement",
        "intention",
        "memory_extract",
        "reason",
        "candidate_evaluate",
    ):
        prompt = _read("prompts", f"{name}.md")
        assert f"omnis.prompt.{name}.v1" in prompt
        assert "Return JSON only" in prompt


def test_machine_readable_v0_manifests_parse_and_are_unique():
    """Scalar and ontology manifests must be valid TOML with unique canonical identifiers."""
    import tomllib

    with open(os.path.join(REPO_ROOT, "spec", "v0.toml"), "rb") as handle:
        v0 = tomllib.load(handle)
    assert v0["version"] == 1
    assert v0["profile"] == "omnis-v0"
    assert v0["rust_toolchain"] == "1.99.0"
    assert v0["paths"]["graph_socket"] == "/run/omnis/graph.sock"
    assert v0["paths"]["inference_port"] == 7331
    assert v0["paths"]["remote_quic_port"] == 7443

    with open(os.path.join(REPO_ROOT, "spec", "ontology.toml"), "rb") as handle:
        ontology = tomllib.load(handle)
    assert ontology["version"] == 1
    for field in ("kinds", "relations", "capabilities", "events"):
        values = ontology[field]
        assert len(values) == len(set(values)), f"duplicate identifier in {field}"
        assert all(value.startswith("omnis.") for value in values)


def test_v0_registries_cross_check():
    """Machine-readable ontology/event/capability/property/state registries must agree."""
    import tomllib

    def load(name):
        with open(os.path.join(REPO_ROOT, "spec", name), "rb") as handle:
            return tomllib.load(handle)

    ontology = load("ontology.toml")
    events = load("events.toml")["events"]
    capabilities = load("capabilities.toml")["capabilities"]
    properties = load("properties.toml")["properties"]
    machines = load("state_machines.toml")["state_machines"]

    assert set(events) == set(ontology["events"])
    assert set(capabilities) == set(ontology["capabilities"])
    assert all(name.startswith("omnis.") for name in properties)

    for name, machine in machines.items():
        states = set(ontology["states"][name])
        assert machine["initial"] in states
        assert set(machine["terminal"]) <= states
        for transition in machine["transitions"]:
            source, target = transition.split("->", 1)
            assert source in states
            assert target in states

    valid_effects = {
        "pure",
        "readOnly",
        "idempotent",
        "retrySafe",
        "reversible",
        "compensatable",
        "transactional",
        "persistentExternal",
        "opaque",
    }
    for schema in capabilities.values():
        assert schema["effect"] in valid_effects
        assert schema["input"]
        assert schema["output"]


def test_worldline_stores_exact_event_envelope_bytes():
    worldline = _read("schema", "worldline.sql")
    assert "envelope BLOB NOT NULL" in worldline
    assert "inline_payload" not in worldline
    assert "payload_artifact" not in worldline
