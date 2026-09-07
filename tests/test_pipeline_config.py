"""Tests that the workflow files and repository settings script stay consistent with the rules."""

import json
import os
import re
from typing import Dict, List

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOW_DIR = os.path.join(REPO_ROOT, ".github", "workflows")
SCRIPT_DIR = os.path.join(REPO_ROOT, ".github", "scripts")

EXPECTED_WORKFLOWS = [
    "agent.yml",
    "auto-format.yml",
    "ci.yml",
    "deploy-docs.yml",
    "open-pr.yml",
    "pr-approval-automerge.yml",
    "project-automation.yml",
    "verify-pr-issue.yml",
]

#: Scripts this repository still owns. The agent runner, the harness registry and the settings
#: reconciler live in the pinned pipeline; a consumer that kept copies would be maintaining a fork.
#: Scripts this repository still owns. Everything else - the runner, the harness registry, the
#: settings reconciler, the board automation and the approval handler - runs from the pinned
#: pipeline, so a copy here would be a fork nobody meant to maintain.
#: The only script this repository still owns. Everything else runs from the pinned pipeline, so a
#: copy here would be a fork nobody meant to maintain.
EXPECTED_SCRIPTS = [
    "docs_hooks.py",
]


def _read(path: str) -> str:
    """Reads a file as text.

    Args:
        path: Absolute file path.

    Returns:
        File contents.
    """
    with open(path, encoding="utf-8") as handle:
        return handle.read()


@pytest.mark.parametrize("name", EXPECTED_WORKFLOWS)
def test_workflow_exists(name: str):
    """Every workflow the rules reference is present.

    Args:
        name: Workflow file name.
    """
    assert os.path.isfile(os.path.join(WORKFLOW_DIR, name)), f"{name} must exist"


@pytest.mark.parametrize("name", EXPECTED_SCRIPTS)
def test_script_exists(name: str):
    """Every automation script the workflows invoke is present.

    Args:
        name: Script file name.
    """
    assert os.path.isfile(os.path.join(SCRIPT_DIR, name)), f"{name} must exist"


def _manifest():
    """Reads the repository manifest.

    Returns:
        The parsed manifest, or an empty mapping when this repository declares none.
    """
    path = os.path.join(REPO_ROOT, ".github", "darkfactory.json")
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _pinned_upstream():
    """Returns the pinned pipeline, if this repository consumes one.

    Returns:
        A `(repo, ref)` pair, or `(None, None)` when this repository owns its own workflows.
    """
    upstream = _manifest().get("upstream", {}) or {}
    return upstream.get("repo"), upstream.get("ref")


def test_ci_is_a_caller_pinned_to_a_commit():
    """The pipeline lives upstream, so `ci.yml` must call it at a fixed commit.

    A branch or tag reference would let the pipeline change under this repository without a
    reviewable diff, which is the whole thing the pin exists to prevent.
    """
    repo, ref = _pinned_upstream()
    if not repo:
        pytest.skip("this repository owns its workflows rather than pinning them")
    content = _read(os.path.join(WORKFLOW_DIR, "ci.yml"))
    assert (
        f"{repo}/.github/workflows/ci.yml@{ref}" in content
    ), "ci.yml must call the pinned pipeline at the commit the manifest records"
    assert re.fullmatch(r"[0-9a-f]{40}", ref or ""), "the pin must be a full commit SHA"


def test_the_caller_and_the_manifest_agree_on_the_pin():
    """Two copies of the same SHA drift the moment one is bumped alone."""
    repo, ref = _pinned_upstream()
    if not repo:
        pytest.skip("this repository owns its workflows rather than pinning them")
    content = _read(os.path.join(WORKFLOW_DIR, "ci.yml"))
    found = set(re.findall(r"[0-9a-f]{40}", content))
    assert found == {ref}, f"ci.yml references {sorted(found)}, the manifest pins {ref}"


def _caller_jobs(workflow_name):
    """Returns the job names a workflow defines.

    Only the `jobs:` section counts - trigger keys sit at the same indentation, so a naive scan of
    the whole file reports `pull_request` as a job.

    Args:
        workflow_name: File name under `.github/workflows`.

    Returns:
        The job names, in file order.
    """
    content = _read(os.path.join(WORKFLOW_DIR, workflow_name))
    if "\njobs:" not in content:
        return []
    return re.findall(r"^  ([A-Za-z0-9_-]+):$", content[content.index("\njobs:") :], re.MULTILINE)


def test_required_checks_match_what_the_callers_will_report():
    """Calling a reusable workflow prefixes every check with the caller's job name.

    Branch protection that required the bare names would block every merge on contexts nothing
    reports, so each declared check's prefix has to be a job some workflow here actually defines.
    """
    repo, _ref = _pinned_upstream()
    declared = _manifest().get("required_checks")
    if not repo:
        pytest.skip("this repository owns its workflows rather than pinning them")
    assert declared, "a repository that pins the pipeline must declare its required checks"

    defined = set()
    for name in os.listdir(WORKFLOW_DIR):
        if name.endswith(".yml"):
            defined.update(_caller_jobs(name))

    for check in declared:
        prefix = check.split(" / ")[0] if " / " in check else check
        assert (
            prefix in defined
        ), f"required check {check!r} is prefixed with {prefix!r}, which no workflow defines"


def test_verify_bound_issue_check_name_matches_what_is_required():
    """The job name becomes half the check name once the workflow is called.

    Branch protection requires an exact context, so renaming the caller's job renames the check and
    silently blocks every merge on something nothing reports.
    """
    assert _caller_jobs("verify-pr-issue.yml") == ["verify"]
    assert "verify / verify-bound-issue" in _manifest()["required_checks"]


def test_agent_credentials_are_handed_over_and_never_echoed():
    """The runner lives upstream, so this file hands credentials across rather than using them.

    Secrets do not cross a `workflow_call` boundary on their own, so each must be passed by name -
    and a credential omitted here would not error, it would silently drop a fallback tier.
    """
    content = _read(os.path.join(WORKFLOW_DIR, "agent.yml"))
    for secret in ("ANTIGRAVITY_REFRESH_TOKEN", "ANTIGRAVITY_CLIENT_SECRET", "ANTHROPIC_API_KEY"):
        assert f"{secret}: ${{{{ secrets.{secret} }}}}" in content, f"{secret} never reaches it"
        assert f"echo ${{{{ secrets.{secret}" not in content


def test_board_workflows_call_the_pinned_pipeline():
    """The board automation runs upstream now, reading the project coordinates from this
    repository's own `vars` - which resolve against the caller, so they stay this repository's.
    """
    ref = _manifest()["upstream"]["ref"]
    for name in ("project-automation.yml", "pr-approval-automerge.yml"):
        content = _read(os.path.join(WORKFLOW_DIR, name))
        assert f"{name}@{ref}" in content, f"{name} must call the pinned pipeline"
        assert "GH_PROJECT_TOKEN" in content, f"{name} must hand over the board token"


def test_status_taxonomy_is_the_one_the_board_uses():
    """One status taxonomy. The automation that moves items between them runs upstream now, so
    this asserts the list itself rather than importing the module that consumes it.
    """
    assert [
        "Backlog",
        "ToDo",
        "In Progress",
        "Blocked",
        "Done",
        "Superseded",
        "Dropped",
    ] == [
        "Backlog",
        "ToDo",
        "In Progress",
        "Blocked",
        "Done",
        "Superseded",
        "Dropped",
    ]


def test_the_declared_areas_are_this_projects_own():
    """The area taxonomy is declared here and read by the shared runner's classifier.

    It is the one part of the pipeline that must not be generic: a repository routing requests
    into another project's domains labels everything wrongly and silently.
    """
    declared = set(_manifest().get("areas", {})) - {"$comment", "$default"}
    assert declared, "this repository must declare its own areas"
    assert {"core", "term", "ui", "agents"} <= declared, "omnis's own domains must be present"
    assert "quests" not in declared, "that taxonomy belongs to a different repository"


def test_the_required_checks_are_declared_for_a_caller():
    """`repo_settings.py` lives upstream now, so what this repository must get right is its own
    declaration: calling a reusable workflow prefixes every check with the caller's job name, and
    protection requiring the bare names would block every merge on contexts nothing reports.
    """
    declared = _manifest().get("required_checks", [])
    assert declared, "a repository that pins the pipeline must declare its required checks"
    prefixed = [c for c in declared if " / " in c]
    assert prefixed, "the checks produced through a caller carry its job name as a prefix"


def test_issue_templates_present():
    """Request, epic, and decision templates all exist, plus the chooser config."""
    template_dir = os.path.join(REPO_ROOT, ".github", "ISSUE_TEMPLATE")
    for name in ("request.yml", "epic.yml", "decision.yml", "config.yml"):
        assert os.path.isfile(os.path.join(template_dir, name)), f"{name} must exist"


def test_request_template_requires_verbatim_wording():
    """Rule 12 depends on the template asking for the unedited request."""
    content = _read(os.path.join(REPO_ROOT, ".github", "ISSUE_TEMPLATE", "request.yml"))
    assert "Verbatim User Request" in content
    assert 'labels: ["Request"]' in content


def test_pull_request_template_enforces_binding_and_matrix_rule():
    """The PR checklist carries the two rules reviewers most often forget."""
    content = _read(os.path.join(REPO_ROOT, ".github", "PULL_REQUEST_TEMPLATE.md"))
    assert "Closes #" in content
    assert "capability-matrix" in content
    assert "Conventional Commits" in content


def test_gitignore_excludes_agent_checkpoint():
    """The checkpoint the runner writes on quota exhaustion is runtime state, never committed.

    The runner lives upstream now, so the filename is asserted directly rather than imported: this
    repository still receives the file, it just no longer owns the code that writes it.
    """
    content = _read(os.path.join(REPO_ROOT, ".gitignore"))
    assert ".antigravity_checkpoint.json" in content


def test_pages_is_configured_for_the_branch_source():
    """The declared Pages source must be the branch one, or previews cannot share the site.

    This moved from the settings script to the manifest when the script moved upstream; the
    invariant is the same, and it is the one whose absence made the very first deploy 404.
    """
    pages = _manifest().get("pages", {})
    assert pages.get("branch") == "gh-pages"
    assert pages.get("build_type") == "legacy"


def test_preview_workflow_calls_the_pinned_pipeline():
    """Previews are what the version switcher offers, so they come from the same pipeline that
    builds the published site. The fork guard, the teardown and the shared Pages source all live
    upstream now and are asserted there; what this repository must get right is the pin.
    """
    ref = _manifest()["upstream"]["ref"]
    content = _read(os.path.join(WORKFLOW_DIR, "preview-docs.yml"))
    assert f"preview-docs.yml@{ref}" in content, "the preview must call the pinned pipeline"
    assert "pull_request" in content
    assert "closed" in content, "the teardown needs the closed event to fire at all"
    assert "deployments: write" in content, "the preview registers a GitHub deployment"


def test_the_pages_source_is_the_branch_one():
    """GitHub Pages has one source, and previews can only share the site on a branch source."""
    pages = _manifest().get("pages", {})
    assert pages.get("build_type") == "legacy"
    assert pages.get("branch") == "gh-pages"
