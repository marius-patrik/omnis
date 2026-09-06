"""Tests for the generated documentation site: ADR discovery, index, and navigation."""

import os
import re
from typing import Dict, List

import pytest

import mkdocs_hooks
from mkdocs_hooks import ADR_SOURCE_DIR, discover_adrs, render_adr_index

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="module")
def records() -> List[Dict[str, str]]:
    """Discovers the repository's ADRs once for the module.

    Returns:
        The discovered records.
    """
    return discover_adrs(REPO_ROOT)


def test_every_adr_file_is_discoverable(records: List[Dict[str, str]]):
    """A record the hook cannot parse would silently vanish from the site.

    Args:
        records: Discovered records.
    """
    on_disk = [
        n
        for n in os.listdir(os.path.join(REPO_ROOT, ADR_SOURCE_DIR))
        if n.endswith(".md") and n != "index.md"
    ]
    assert len(records) == len(on_disk), "every ADR file must parse into a record"
    assert records, "expected at least one decision record"


def test_adr_numbers_are_unique_and_contiguous(records: List[Dict[str, str]]):
    """Duplicate or skipped numbers make cross-references ambiguous.

    Args:
        records: Discovered records.
    """
    numbers = [int(record["number"]) for record in records]
    assert len(numbers) == len(set(numbers)), f"duplicate ADR numbers: {numbers}"
    assert numbers == list(range(1, len(numbers) + 1)), f"non-contiguous ADR numbers: {numbers}"


def test_every_adr_declares_a_known_status(records: List[Dict[str, str]]):
    """An unparseable status renders as "Unknown" in the index rather than failing loudly.

    Args:
        records: Discovered records.
    """
    for record in records:
        assert record["status"].split()[0] in {
            "Proposed",
            "Accepted",
            "Superseded",
        }, f"ADR-{record['number']} has status {record['status']!r}"


def test_every_adr_states_its_alternatives(records: List[Dict[str, str]]):
    """A record without rejected alternatives is an announcement, not a decision.

    Args:
        records: Discovered records.
    """
    for record in records:
        with open(os.path.join(REPO_ROOT, record["source"]), encoding="utf-8") as handle:
            body = handle.read()
        assert "## Alternatives rejected" in body, f"ADR-{record['number']} lists no alternatives"
        assert "## Consequences" in body, f"ADR-{record['number']} states no consequences"
        assert "## Context" in body, f"ADR-{record['number']} gives no context"


def test_index_is_generated_from_the_records(records: List[Dict[str, str]]):
    """The index must never be hand-maintained (AGENTS.md rule 2).

    Args:
        records: Discovered records.
    """
    index = render_adr_index(records)
    for record in records:
        assert record["title"] in index, f"ADR-{record['number']} missing from the index"
        assert f"{record['slug']}.md" in index, f"ADR-{record['number']} has no link"
    assert index.count("|") > len(records), "the index must render as a table"


def test_index_handles_an_empty_repository():
    """A fresh clone with no records still builds a coherent page."""
    index = render_adr_index([])
    assert "No decisions recorded yet" in index


def test_navigation_includes_every_adr():
    """Adding a record must publish it without editing mkdocs.yml."""
    config = {"config_file_path": os.path.join(REPO_ROOT, "mkdocs.yml"), "nav": None}
    result = mkdocs_hooks.on_config(config)

    flattened = repr(result["nav"])
    for record in discover_adrs(REPO_ROOT):
        assert record["dest"] in flattened, f"ADR-{record['number']} missing from nav"
    assert "pipeline.md" in flattened, "the automation pipeline must be in the navigation"
    assert "architecture/index.md" in flattened


def test_mkdocs_config_declares_no_static_nav():
    """A static nav would have to be edited by hand for every new record."""
    with open(os.path.join(REPO_ROOT, "mkdocs.yml"), encoding="utf-8") as handle:
        config = handle.read()
    assert not re.search(r"^nav:", config, re.MULTILINE), "nav must be generated, not declared"


def test_pipeline_documentation_covers_the_moving_parts():
    """The pipeline doc is the operator's map; it must name what can break."""
    with open(os.path.join(REPO_ROOT, "notes", "pipeline.md"), encoding="utf-8") as handle:
        content = handle.read()
    for topic in (
        "BOT_TOKEN",
        "GH_PROJECT_TOKEN",
        "AGENT_ENABLED",
        "harnesses.py",
        "Failure modes",
    ):
        assert topic in content, f"pipeline documentation must cover {topic}"
