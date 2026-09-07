"""Tests for the generated documentation site: ADR discovery, index, and navigation."""

import os
import re
from typing import Dict, List

import pytest

import docs_hooks
from docs_hooks import ADR_SOURCE_DIR, discover_adrs, render_adr_index

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
    """Adding a record must publish it without editing properdocs.yml."""
    config = {"config_file_path": os.path.join(REPO_ROOT, "properdocs.yml"), "nav": None}
    result = docs_hooks.on_config(config)

    flattened = repr(result["nav"])
    for record in discover_adrs(REPO_ROOT):
        assert record["dest"] in flattened, f"ADR-{record['number']} missing from nav"
    assert "pipeline.md" in flattened, "the automation pipeline must be in the navigation"
    assert "architecture/index.md" in flattened


def test_properdocs_config_declares_no_static_nav():
    """A static nav would have to be edited by hand for every new record."""
    with open(os.path.join(REPO_ROOT, "properdocs.yml"), encoding="utf-8") as handle:
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


def test_theme_is_first_party_and_self_contained():
    """The theme is ours: ProperDocs ships none, and a vendor theme would constrain the markup."""
    theme = os.path.join(REPO_ROOT, "theme")
    for relative in ("main.html", "partials/nav.html", "assets/theme.css", "assets/theme.js"):
        assert os.path.isfile(os.path.join(theme, *relative.split("/"))), f"{relative} missing"


def test_theme_is_declared_in_the_config():
    """A custom_dir that is not wired produces a build with no templates at all."""
    with open(os.path.join(REPO_ROOT, "properdocs.yml"), encoding="utf-8") as handle:
        config = handle.read()
    assert "custom_dir: theme" in config
    assert re.search(r"^\s+name:\s*null", config, re.MULTILINE), "no vendor theme may be selected"


def test_stylesheet_defines_both_palettes():
    """A token defined in only one palette renders as an invalid colour in the other."""
    with open(os.path.join(REPO_ROOT, "theme", "assets", "theme.css"), encoding="utf-8") as handle:
        css = handle.read()

    def tokens(block: str) -> set:
        start = css.index(block)
        end = css.index("}", start)
        return set(re.findall(r"(--[a-z-]+):", css[start:end]))

    light = tokens('[data-theme="light"]')
    dark = tokens('[data-theme="dark"]')
    assert light and dark
    assert light == dark, f"palette token mismatch: {light ^ dark}"


def test_no_hardcoded_colours_outside_the_token_blocks():
    """Every colour must resolve from a token, or the design system is decorative only."""
    with open(os.path.join(REPO_ROOT, "theme", "assets", "theme.css"), encoding="utf-8") as handle:
        css = handle.read()
    body = css[css.index("/* ── Reset") :]
    stray = [m for m in re.findall(r"#[0-9a-fA-F]{3,8}\b", body)]
    assert not stray, f"hardcoded hex colours outside the token blocks: {stray}"


def test_search_uses_the_generated_index():
    """The theme must read the index the search plugin emits rather than shipping its own."""
    with open(os.path.join(REPO_ROOT, "theme", "assets", "theme.js"), encoding="utf-8") as handle:
        js = handle.read()
    assert "search/search_index.json" in js
    assert "textContent" in js, "results must be assigned as text, never as markup"
