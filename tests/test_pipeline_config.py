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

EXPECTED_SCRIPTS = [
    "agent_runner.py",
    "handle_pr_approval.py",
    "docs_hooks.py",
    "open_pr.py",
    "project_automation.py",
    "repo_settings.py",
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


def test_required_checks_match_what_the_caller_will_report():
    """Calling a reusable workflow prefixes every check with the caller's job name.

    Branch protection that still required the bare names would block every merge on contexts
    nothing reports, so the declared checks must carry the prefix.
    """
    repo, _ref = _pinned_upstream()
    declared = _manifest().get("required_checks")
    if not repo:
        pytest.skip("this repository owns its workflows rather than pinning them")
    assert declared, "a repository that pins the pipeline must declare its required checks"

    content = _read(os.path.join(WORKFLOW_DIR, "ci.yml"))
    caller_jobs = set(re.findall(r"^  ([\w-]+):$", content, re.MULTILINE))
    assert caller_jobs, "the caller must define at least one job"

    for check in declared:
        if check == "verify-bound-issue":
            continue
        prefix = check.split(" / ")[0]
        assert (
            prefix in caller_jobs
        ), f"required check {check!r} is prefixed with {prefix!r}, which is not a caller job"


def test_verify_bound_issue_job_name_is_stable():
    """The required check name must match the job id in `verify-pr-issue.yml`."""
    content = _read(os.path.join(WORKFLOW_DIR, "verify-pr-issue.yml"))
    assert re.search(r"^  verify-bound-issue:$", content, re.MULTILINE)


def test_agent_workflow_never_leaks_secrets_into_the_log():
    """Secrets are passed as container env, never echoed."""
    content = _read(os.path.join(WORKFLOW_DIR, "agent.yml"))
    for secret in ("ANTIGRAVITY_REFRESH_TOKEN", "ANTIGRAVITY_CLIENT_SECRET"):
        assert f"-e {secret}=" in content
        assert f"echo ${{{{ secrets.{secret}" not in content


def test_board_workflows_receive_project_coordinates():
    """Automation must know which project to write to without a hardcoded number in code."""
    for name in ("project-automation.yml", "pr-approval-automerge.yml"):
        content = _read(os.path.join(WORKFLOW_DIR, name))
        assert "PROJECT_OWNER:" in content, f"{name} must pass PROJECT_OWNER"
        assert "PROJECT_NUMBER:" in content, f"{name} must pass PROJECT_NUMBER"


def test_repo_settings_status_options_match_automation():
    """One status taxonomy, three places: prose, board settings, and the automation."""
    import project_automation
    import repo_settings

    assert repo_settings.STATUS_OPTIONS == project_automation.STATUS_NAMES


def test_repo_settings_labels_cover_every_area_and_status():
    """Every label the pipeline can apply exists in the label taxonomy."""
    import agent_runner
    import project_automation
    import repo_settings

    label_names = {name for name, _color, _desc in repo_settings.LABELS}
    for area in agent_runner.AREA_LABELS:
        assert area in label_names, f"missing area label {area}"
    for status in project_automation.STATUS_NAMES:
        assert status in label_names, f"missing status label {status}"
    for type_label in agent_runner.TYPE_LABELS:
        assert type_label in label_names, f"missing type label {type_label}"
    for role in ("Request", "Plan", "epic", "decision"):
        assert role in label_names, f"missing pipeline label {role}"


def test_repo_settings_enables_bot_pr_approval():
    """Without `can_approve_pull_request_reviews` every bot PR stalls at REVIEW_REQUIRED."""
    content = _read(os.path.join(SCRIPT_DIR, "repo_settings.py"))
    assert '"can_approve_pull_request_reviews": True' in content
    assert '"delete_branch_on_merge": True' in content
    assert '"allow_auto_merge": True' in content


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
    """The checkpoint file is runtime state and must never be committed."""
    import agent_runner

    content = _read(os.path.join(REPO_ROOT, ".gitignore"))
    assert agent_runner.CHECKPOINT_FILENAME in content


def test_preview_workflow_exists_and_is_scoped():
    """Pull request previews must not run for forks, whose token cannot write here."""
    content = _read(os.path.join(WORKFLOW_DIR, "preview-docs.yml"))
    assert "pull_request" in content
    assert "head.repo.full_name == github.repository" in content, "forks must be skipped"
    assert "deployments: write" in content, "the preview must register a GitHub deployment"
    assert "transient_environment" in content, "preview environments are transient"


def test_preview_and_main_deploy_share_one_pages_source():
    """GitHub Pages has one source; two mechanisms would silently fight."""
    preview = _read(os.path.join(WORKFLOW_DIR, "preview-docs.yml"))
    deploy = _read(os.path.join(WORKFLOW_DIR, "deploy-docs.yml"))
    for content in (preview, deploy):
        assert "branch: gh-pages" in content
    assert "upload-pages-artifact" not in deploy, "the Actions build type conflicts with a branch"
    assert "clean-exclude" in deploy, "publishing the site must not delete live previews"
    assert "target-folder: pr-" in preview


def test_preview_is_torn_down_when_the_pull_request_closes():
    """A preview left behind after merge accumulates forever."""
    content = _read(os.path.join(WORKFLOW_DIR, "preview-docs.yml"))
    assert "closed" in content
    assert "git rm" in content, "the preview directory must be removed"
    assert "inactive" in content, "the deployment must be deactivated"


def test_pages_is_configured_for_the_branch_source():
    """repo_settings must match the workflows, or the first deploy silently 404s."""
    content = _read(os.path.join(SCRIPT_DIR, "repo_settings.py"))
    assert '"branch": "gh-pages"' in content
    assert '"build_type": "legacy"' in content


def test_teardown_does_not_use_git_without_a_checkout():
    """The teardown job has no checkout, so `git ls-remote origin` silently no-ops.

    That is not hypothetical: it shipped once and left the preview for #22 behind while reporting
    success.
    """
    content = _read(os.path.join(WORKFLOW_DIR, "preview-docs.yml"))
    teardown = content[content.index("  teardown:") :]
    assert (
        "actions/checkout" in teardown or "git ls-remote" not in teardown
    ), "teardown must either check out the repository or avoid git commands that need a remote"
    assert "branches/gh-pages" in teardown, "branch existence must be checked through the API"
