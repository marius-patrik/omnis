"""ProperDocs hooks that publish the repository's canonical markdown without duplicating it.

`AGENTS.md` rule 2 forbids storing a static documentation mirror and forbids a manually maintained
index. The canonical documents live at the repository root (`README.md`, `ARCHITECTURE.md`,
`ROADMAP.md`, `AGENTS.md`, `VISION.md`) and under `notes/`, with one file per decision in
`notes/adr/`. Committing copies of them under `docs/` would create two sources of truth that drift.

These hooks therefore:

- map each canonical file to a virtual page at build time, so the site is generated from the
  originals and `docs/` stays empty of duplicated prose;
- discover `notes/adr/*.md`, generate the decision index table from each record's title and status,
  and inject the navigation entries - so adding an ADR needs no configuration change;
- rewrite links written for GitHub (``ARCHITECTURE.md``) to their site paths, so
  ``properdocs build --strict`` reports no broken links.
"""

import os
import re
from typing import Any, Dict, List, Optional, Tuple

from properdocs.structure.files import File, Files

#: (source path relative to the repository root, destination path inside the site).
PUBLISHED_PAGES: List[Tuple[str, str]] = [
    ("README.md", "index.md"),
    ("ARCHITECTURE.md", "architecture/index.md"),
    ("ROADMAP.md", "roadmap.md"),
    ("AGENTS.md", "agents.md"),
    ("VISION.md", "vision.md"),
    ("notes/pipeline.md", "pipeline.md"),
    ("notes/architecture_decisions.md", "architecture/decisions/process.md"),
    ("notes/vision_capture.md", "notes/vision_capture.md"),
    ("notes/bootstrap.md", "notes/bootstrap.md"),
]

#: Repository-relative markdown targets rewritten to their published counterparts.
LINK_REWRITES: Dict[str, str] = {
    "README.md": "index.md",
    "ARCHITECTURE.md": "architecture/index.md",
    "ROADMAP.md": "roadmap.md",
    "AGENTS.md": "agents.md",
    "VISION.md": "vision.md",
    "CONTRIBUTING.md": "agents.md",
    "CLAUDE.md": "agents.md",
    "notes/pipeline.md": "pipeline.md",
    "notes/architecture_decisions.md": "architecture/decisions/process.md",
    "notes/vision_capture.md": "notes/vision_capture.md",
    "notes/bootstrap.md": "notes/bootstrap.md",
    "pipeline.md": "pipeline.md",
    "bootstrap.md": "notes/bootstrap.md",
    "vision_capture.md": "notes/vision_capture.md",
    "adr/": "architecture/decisions/index.md",
    "notes/adr/": "architecture/decisions/index.md",
}

#: Where ADR records live, and where they are published.
ADR_SOURCE_DIR = os.path.join("notes", "adr")
ADR_DEST_PREFIX = "architecture/decisions"

_LINK_PATTERN = re.compile(r"\]\((?!https?://)(?P<target>[^)\s#]+)(?P<anchor>#[^)]*)?\)")
_TITLE_PATTERN = re.compile(r"^#\s+ADR-(?P<number>\d{4})\s+—\s+(?P<title>.+?)\s*$", re.M)
_STATUS_PATTERN = re.compile(r"\*\*Status\*\*:\s*(?P<status>[^·\n*]+)")
_RESOLVES_PATTERN = re.compile(r"\*\*(?:Resolves|Narrows)\*\*:\s*(?P<resolves>[^·\n]+)")


def _repo_root(config: Any) -> str:
    """Resolves the repository root from the ProperDocs configuration.

    Args:
        config: ProperDocs configuration object or mapping.

    Returns:
        Absolute path to the repository root.
    """
    config_file = getattr(config, "config_file_path", None)
    if config_file is None and hasattr(config, "get"):
        config_file = config.get("config_file_path")
    if config_file:
        return os.path.dirname(os.path.abspath(config_file))
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def discover_adrs(root: str) -> List[Dict[str, str]]:
    """Reads every ADR record and extracts what the index and navigation need.

    Args:
        root: Repository root.

    Returns:
        Records sorted by number, each with ``number``, ``title``, ``status``, ``resolves``,
        ``source`` (repository-relative), ``dest`` (site path) and ``slug``.

    Raises:
        ValueError: If a record has no parseable ``# ADR-NNNN - Title`` heading.
    """
    directory = os.path.join(root, ADR_SOURCE_DIR)
    if not os.path.isdir(directory):
        return []

    records: List[Dict[str, str]] = []
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".md") or name == "index.md":
            continue
        path = os.path.join(directory, name)
        with open(path, "r", encoding="utf-8") as handle:
            content = handle.read()

        title_match = _TITLE_PATTERN.search(content)
        if not title_match:
            raise ValueError(
                f"{ADR_SOURCE_DIR}/{name} has no '# ADR-NNNN - Title' heading; "
                f"the generated index cannot be built from it."
            )
        status_match = _STATUS_PATTERN.search(content)
        resolves_match = _RESOLVES_PATTERN.search(content)

        records.append(
            {
                "number": title_match.group("number"),
                "title": title_match.group("title"),
                "status": status_match.group("status").strip() if status_match else "Unknown",
                "resolves": resolves_match.group("resolves").strip() if resolves_match else "",
                "source": f"{ADR_SOURCE_DIR}/{name}".replace(os.sep, "/"),
                "dest": f"{ADR_DEST_PREFIX}/{name[:-3]}.md",
                "slug": name[:-3],
            }
        )
    return sorted(records, key=lambda record: record["number"])


def render_adr_index(records: List[Dict[str, str]]) -> str:
    """Builds the decision index page from the discovered records.

    Args:
        records: Output of :func:`discover_adrs`.

    Returns:
        Markdown for the index page.
    """
    lines = [
        "# Architecture decisions",
        "",
        "Every decision that binds the implementation, one record per page. This index is generated",
        "from the files in `notes/adr/` at build time - it is never hand-maintained",
        "(`AGENTS.md` rule 2).",
        "",
        "See [the process](process.md) for when an ADR is required and how to write one.",
        "",
    ]
    if not records:
        return "\n".join(lines + ["*No decisions recorded yet.*", ""])

    lines += ["| # | Decision | Status | Resolves |", "|---|---|---|---|"]
    for record in records:
        resolves = record["resolves"] or "—"
        lines.append(
            f"| [{record['number']}]({record['slug']}.md) | "
            f"[{record['title']}]({record['slug']}.md) | {record['status']} | {resolves} |"
        )

    accepted = sum(1 for r in records if r["status"].lower().startswith("accepted"))
    proposed = sum(1 for r in records if r["status"].lower().startswith("proposed"))
    lines += [
        "",
        f"{len(records)} records — {accepted} accepted, {proposed} proposed. Records are "
        "append-only: a decision that turns out wrong is superseded by a new one, never edited away.",
        "",
    ]
    return "\n".join(lines)


def _rewrite_links(markdown: str, dest_path: str) -> str:
    """Rewrites repository-relative links so they resolve inside the built site.

    Args:
        markdown: Source markdown.
        dest_path: Destination path of this page inside the site.

    Returns:
        Markdown with repository-relative links pointing at published pages.
    """
    depth = dest_path.count("/")
    prefix = "../" * depth

    def replace(match: "re.Match[str]") -> str:
        target = match.group("target")
        anchor = match.group("anchor") or ""
        normalized = target.lstrip("./")

        replacement = LINK_REWRITES.get(normalized)
        if replacement is None:
            # Records are addressed as `notes/adr/NNNN-slug.md` from the repository root and as
            # `adr/NNNN-slug.md` from within notes/; both publish under the decisions section.
            adr_match = re.fullmatch(r"(?:notes/)?adr/(?P<slug>[^/]+\.md)", normalized)
            if adr_match:
                replacement = f"{ADR_DEST_PREFIX}/{adr_match.group('slug')}"

        if replacement is None:
            return match.group(0)
        return f"]({prefix}{replacement}{anchor})"

    return _LINK_PATTERN.sub(replace, markdown)


def on_config(config: Any) -> Any:
    """Injects the Architecture section, including one entry per ADR, into ``nav``.

    Navigation is built here rather than declared in ``properdocs.yml`` so that adding a record to
    ``notes/adr/`` is the only step required to publish it.

    Args:
        config: ProperDocs configuration.

    Returns:
        The configuration with ``nav`` rewritten.
    """
    records = discover_adrs(_repo_root(config))

    decisions: List[Any] = [{"Overview": f"{ADR_DEST_PREFIX}/index.md"}]
    decisions += [
        {f"ADR-{record['number']} — {record['title']}": record["dest"]} for record in records
    ]
    decisions.append({"Process": f"{ADR_DEST_PREFIX}/process.md"})

    config["nav"] = [
        {"Overview": "index.md"},
        {
            "Architecture": [
                {"Overview": "architecture/index.md"},
                {"Decisions": decisions},
            ]
        },
        {"Roadmap": "roadmap.md"},
        {"Automation pipeline": "pipeline.md"},
        {"Contributing & Agent Rules": "agents.md"},
        {"Vision (reference only)": "vision.md"},
        {
            "Notes": [
                {"Bootstrap runbook": "notes/bootstrap.md"},
                {"Vision capture": "notes/vision_capture.md"},
            ]
        },
    ]
    return config


def on_files(files: Files, config: Any) -> Files:
    """Injects the canonical repository documents and every ADR as virtual pages.

    Args:
        files: The file collection ProperDocs discovered under ``docs_dir``.
        config: ProperDocs configuration.

    Returns:
        The augmented file collection.

    Raises:
        FileNotFoundError: If ``docs_dir`` is missing, which would otherwise yield a silently
            empty site.
    """
    root = _repo_root(config)
    docs_dir = getattr(config, "docs_dir", None) or config["docs_dir"]
    if not os.path.isdir(docs_dir):
        raise FileNotFoundError(f"docs_dir does not exist: {docs_dir}")

    records = discover_adrs(root)
    pages = list(PUBLISHED_PAGES) + [(r["source"], r["dest"]) for r in records]

    for source, dest in pages:
        source_path = os.path.join(root, source)
        if not os.path.isfile(source_path):
            continue

        existing: Optional[File] = files.get_file_from_path(dest)
        if existing is not None:
            files.remove(existing)

        with open(source_path, "r", encoding="utf-8") as handle:
            content = handle.read()

        files.append(File.generated(config, dest, content=_rewrite_links(content, dest)))

    index_dest = f"{ADR_DEST_PREFIX}/index.md"
    existing_index = files.get_file_from_path(index_dest)
    if existing_index is not None:
        files.remove(existing_index)
    files.append(File.generated(config, index_dest, content=render_adr_index(records)))

    return files
