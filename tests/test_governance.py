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
    for term in ("OmnisOS", "OmnisManager", "OmnisControl"):
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
        "Exactly three core authorities",
        "append-only core event journal",
        "Nix evaluation/build remains deterministic",
    ):
        assert phrase in section


def test_architecture_defines_three_core_authorities_and_external_agents():
    """Core authority stops at OS/Manager/Control; agents are replaceable clients."""
    architecture = _read("ARCHITECTURE.md")
    for phrase in (
        "exactly three first-class authorities",
        "OmnisOS",
        "OmnisManager",
        "OmnisControl",
        "There is no core OmnisAgent service",
        "omnis mcp",
        "@omnis/agent-access",
    ):
        assert phrase.lower() in architecture.lower()
    assert "OmnisAgent — cognitive/event/memory authority" not in architecture


def test_roadmap_phases_are_addressable():
    """The implementation roadmap must expose a concrete dependency-ordered phase sequence."""
    roadmap = _read("ROADMAP.md")
    phases = set(re.findall(r"^## Phase (\d+) ", roadmap, re.MULTILINE))
    assert {str(i) for i in range(0, 10)} <= phases, f"missing roadmap phases: {sorted(phases)}"


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
        "agentAccess = {",
        "control.users.alice",
        "security = {",
        'dataDir = "/var/lib/omnis/graph"',
        'nixControlSocket = "/run/omnis/nix-control.sock"',
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
        "Smithay",
        "wgpu",
        "systemd",
        "QUIC",
        "omnis-graphd",
        "omnis-managerd",
        "omnis-control",
    ):
        assert term in implementation, f"v0 implementation profile must freeze {term}"
    assert "core event journal" in implementation.lower()
    assert "no global ack" in implementation.lower()


def test_protocol_schema_sources_exist():
    """The frozen wire contract must exist as schema source, not prose only."""
    for name in (
        "common",
        "events",
        "capabilities",
        "inference",
        "graph",
        "os",
        "manager",
        "control",
    ):
        path = os.path.join(REPO_ROOT, "protocol", f"{name}.capnp")
        assert os.path.isfile(path), f"missing canonical protocol schema {name}.capnp"
        content = _read("protocol", f"{name}.capnp")
        assert content.startswith("@0x"), f"{name}.capnp must declare a schema ID"
    common = _read("protocol", "common.capnp")
    assert "struct Uuid" in common
    assert "struct ArtifactId" in common


def test_decision_complete_v0_contract():
    """Implementation workers receive frozen core algorithms/defaults instead of design gaps."""
    spec = _read("docs", "DECISION_COMPLETE_V0.md")
    required = (
        "Frozen source baselines",
        "Event delivery",
        "Nix and persistent mutation",
        "OS observation",
        "Manager discovery",
        "Manager resolution and placement algorithm",
        "Manager execution",
        "Control input routing",
        "Control graph layout",
        "Backup and recovery",
        "Package persistence scopes",
        "Desktop compatibility services",
        "Specification completeness invariant",
        "Native remote-host pairing",
        "Graph value and query semantics",
        "Watched-filesystem observation",
        "Linux enforcement primitives",
        "Protocol handshake",
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
        "no global ACK",
        "UDP 7443",
        "omnis.graph.v1",
        "omnis.os.v1",
        "omnis.manager.v1",
        "omnis.control.v1",
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
    delegation = re.compile(
        r"\\b(?:the\\s+)?(?:implementer|implementation agent|coding agent|worker)"
        r"\\s+(?:may|can|should)\\s+(?:choose|select|decide|pick)\\b",
        re.IGNORECASE,
    )
    imperative = re.compile(
        r"\\b(?:choose whichever|pick any equivalent|use whichever|implementation-specific until)\\b",
        re.IGNORECASE,
    )
    negative_guard = re.compile(
        r"\\b(?:must not|do not|does not|cannot|can't|forbid(?:den)?|reject|invalid|no\\s+"
        r"(?:implementation )?(?:agent|worker|implementer))\\b",
        re.IGNORECASE,
    )

    for document in documents:
        in_fence = False
        for lineno, line in enumerate(_read(*document.split("/")).splitlines(), 1):
            if line.lstrip().startswith("~~~") or line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence or negative_guard.search(line):
                continue
            assert not delegation.search(
                line
            ), f"{document}:{lineno} positively delegates a design decision: {line.strip()!r}"
            assert not imperative.search(
                line
            ), f"{document}:{lineno} positively delegates a design decision: {line.strip()!r}"


def test_canonical_v0_source_contracts():
    """Decision-complete core inputs must be checked in and addressable."""
    required = (
        "docs/ONTOLOGY_V0.md",
        "docs/NIX_OPTIONS_V0.md",
        "docs/AGENT_ACCESS_V0.md",
        "schema/graph.sql",
        "spec/agent_access.toml",
    )
    for rel in required:
        assert os.path.isfile(os.path.join(REPO_ROOT, rel)), f"missing canonical v0 source {rel}"

    ontology = _read("docs", "ONTOLOGY_V0.md")
    assert "exactly three core authorities" in _read("ARCHITECTURE.md").lower()
    assert "omnis.capability.ingest" in _read("spec", "ontology.toml")
    assert "omnis.event.graph.committed" in _read("spec", "ontology.toml")
    assert "no `omnis.capability.code.agent`" in ontology

    nix_options = _read("docs", "NIX_OPTIONS_V0.md")
    for token in (
        "omnis.graph.writerQueue",
        "omnis.agentAccess.mcp.enable",
        "omnis.control.users",
        "omnis.security.defaultExecutionNetwork",
    ):
        assert token in nix_options


def test_sql_v1_schemas_parse_with_sqlite():
    """The canonical core graph schema must execute on SQLite."""
    import sqlite3

    sql = _read("schema", "graph.sql")
    db = sqlite3.connect(":memory:")
    try:
        db.executescript(sql)
    finally:
        db.close()
    assert "CREATE TABLE event_log" in sql
    assert "acked_at_ns" not in sql


def test_machine_readable_v0_manifests_parse_and_are_unique():
    """Scalar and ontology manifests must be valid TOML with unique canonical identifiers."""
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib

    with open(os.path.join(REPO_ROOT, "spec", "v0.toml"), "rb") as handle:
        v0 = tomllib.load(handle)
    assert v0["version"] == 1
    assert v0["profile"] == "omnis-v0"
    assert v0["rust_toolchain"] == "1.99.0"
    assert v0["paths"]["graph_socket"] == "/run/omnis/graph.sock"
    assert v0["graph"]["event_journal_retention"] == "indefinite-v0"
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
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib

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


def test_capability_registry_has_wire_schema_mapping():
    """Every first-party capability must map to fixed input/output/effect contracts."""
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib

    def load(name):
        with open(os.path.join(REPO_ROOT, "spec", name), "rb") as handle:
            return tomllib.load(handle)

    ontology = load("ontology.toml")
    capabilities = load("capabilities.toml")["capabilities"]
    assert set(capabilities) == set(ontology["capabilities"])
    capnp = _read("protocol", "capabilities.capnp")
    for contract in capabilities.values():
        assert f"struct {contract['input']}" in capnp or contract["input"] == "Empty"
        assert f"struct {contract['output']}" in capnp or contract["output"] == "Empty"


def test_nix_control_contract_is_typed_and_split():
    """AI-visible Nix behavior must use the frozen typed evaluator/store surfaces."""
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib

    with open(os.path.join(REPO_ROOT, "spec", "nix_control.toml"), "rb") as handle:
        spec = tomllib.load(handle)

    assert spec["transport"]["store"]["path"] == "/run/omnis/nix-control.sock"
    assert spec["transport"]["eval"]["process"] == "omnis-nix-eval"
    assert spec["transport"]["eval"]["fd"] == 3
    assert spec["evaluation"]["pure"] is True
    assert spec["evaluation"]["network"] is False
    assert spec["evaluation"]["base_module"] == "/etc/omnis/base.nix"
    assert spec["store"]["event_buffer"] == 100000

    protocol = _read("protocol", "nix_control.capnp")
    for token in (
        "interface NixEvalService",
        "interface NixStoreControl",
        "struct OptionRecord",
        "struct RealizationPlan",
        "struct GcPlan",
        "struct NixExplanation",
    ):
        assert token in protocol

    manager_protocol = _read("protocol", "manager.capnp")
    assert 'using N = import "nix_control.capnp";' in manager_protocol
    assert "explanation :N.NixExplanation" in manager_protocol
    assert "plan :N.RealizationPlan" in manager_protocol


def test_control_render_contract_is_typed():
    """Control must have one typed tree/render schema rather than property-bag renderer choices."""
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib

    with open(os.path.join(REPO_ROOT, "spec", "control_render.toml"), "rb") as handle:
        spec = tomllib.load(handle)

    assert spec["control_tree"]["layout_engine"] == "taffy"
    assert spec["renderer"]["backend"] == "wgpu"
    assert spec["renderer"]["compositor"] == "smithay"
    assert spec["renderer"]["path_tessellator"] == "lyon"
    assert spec["renderer"]["text_shaper"] == "cosmic-text"
    assert spec["hit_test"]["order_2d"] == "reverse-paint"
    assert spec["native_surface"]["world_mode"] == "composited-texture"

    scene = _read("protocol", "control_scene.capnp")
    for token in (
        "struct ControlNodeState",
        "enum ControlNodeKind",
        "struct RenderScene",
        "struct SceneItem",
        "struct GlyphRunPrimitive",
        "struct NativeSurfacePrimitive",
        "struct TableDataset",
    ):
        assert token in scene

    control = _read("protocol", "control.capnp")
    assert 'using S = import "control_scene.capnp";' in control
    assert "state @3 :S.ControlNodeState" in control
    assert "ControlProperty" not in control
    assert "setProperties" not in control


def test_contract_manifest_references_existing_files():
    """One machine-readable root enumerates the complete core contract."""
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib

    with open(os.path.join(REPO_ROOT, "spec", "contract.toml"), "rb") as handle:
        contract = tomllib.load(handle)

    assert contract["version"] == 1
    assert contract["profile"] == "omnis-v0"

    for section in ("normative", "machine", "protocol", "database", "assets"):
        for _, rel in contract[section].items():
            assert os.path.isfile(
                os.path.join(REPO_ROOT, rel)
            ), f"contract manifest references missing {section} source {rel}"

    required_normative = {
        "ARCHITECTURE.md",
        "docs/DECISION_COMPLETE_V0.md",
        "docs/IMPLEMENTATION.md",
        "docs/AGENT_ACCESS_V0.md",
        "docs/CONTROL_RENDER_V0.md",
        "docs/NIX_CONTROL_V0.md",
    }
    assert required_normative <= set(contract["normative"].values())
    assert "agent" not in contract.get("ownership", {})


def test_core_has_no_builtin_agent_or_harness_contracts():
    """External agents are clients; no harness-specific core architecture may remain."""
    ontology = _read("spec", "ontology.toml")
    assert "omnis.kind.agent_harness" not in ontology
    assert "omnis.capability.code.agent" not in ontology
    assert "omnis.event.agent." not in ontology

    for rel in (
        "docs/OMNIS_AGENT.md",
        "docs/HARNESS_ADAPTERS_V0.md",
        "docs/LEARNING_V0.md",
        "protocol/agent.capnp",
        "spec/harnesses.toml",
        "spec/inference_gateway.toml",
        "spec/generic_harness.schema.json",
        "spec/learning.toml",
        "spec/event_priorities.toml",
        "schema/worldline.sql",
        "schema/index.sql",
    ):
        assert not os.path.exists(
            os.path.join(REPO_ROOT, rel)
        ), f"obsolete core agent artifact: {rel}"


def test_event_journal_is_permanent_multi_consumer():
    graph = _read("protocol", "graph.capnp")
    sql = _read("schema", "graph.sql")
    access = _read("docs", "AGENT_ACCESS_V0.md")
    assert "interface EventSubscription" in graph
    assert "readEvents @6" in graph
    assert "subscribeEvents @7" in graph
    assert " ack @" not in graph
    assert "CREATE TABLE event_log" in sql
    assert "acked_at_ns" not in sql
    assert "no global ACK" in access
    assert "no automatic deletion" in access


def test_agent_access_projects_all_three_core_surfaces():
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib

    with open(os.path.join(REPO_ROOT, "spec", "agent_access.toml"), "rb") as handle:
        access = tomllib.load(handle)
    assert set(access["surfaces"]) == {"os", "manager", "control"}
    assert access["substrates"]["graph"]["interface"] == "GraphService"
    assert access["mcp_transport"] == "stdio"
    assert access["plugin_package"] == "@omnis/agent-access"
    assert access["parity"]["require_mcp"] is True
    assert access["parity"]["require_plugin"] is True
    assert access["parity"]["require_all_events"] is True


def test_reference_configuration_has_no_agent_service():
    declaration = _read("examples", "omnis.nix")
    assert "agent.users" not in declaration
    assert "harnesses." not in declaration
    assert "agentAccess = {" in declaration


def test_permanent_events_keep_cas_artifacts_alive():
    decision = _read("docs", "DECISION_COMPLETE_V0.md")
    assert 'owner_kind = "event"' in decision
    assert "every ArtifactRef reachable from every retained core EventEnvelope" in decision
    assert "never removed by ordinary CAS GC" in decision

def test_three_authority_adr_supersedes_four_authority_reset():
    old = _read("notes", "adr", "0023-graph-native-os-architecture-reset.md")
    substrate = _read("notes", "adr", "0024-freeze-v0-implementation-substrate.md")
    current = _read("notes", "adr", "0026-three-core-authorities-external-agents.md")
    assert "Superseded by ADR-0026" in old
    assert "Superseded in part by ADR-0026" in substrate
    assert "Status**: Accepted" in current
    assert "exactly three core semantic authorities" in current
    assert "no core `OmnisAgent` service" in current
