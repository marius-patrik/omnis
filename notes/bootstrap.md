# Bootstrap and operator runbook

How this repository was brought up, what still needs a human, and how to reproduce it from empty.

---

## What is already done

| Item | State |
|---|---|
| Repository `marius-patrik/omnis`, public | created |
| Governance: `AGENTS.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `notes/transcript.md` | committed |
| Decision records — 10 in `notes/adr/`, index and navigation generated | committed |
| Workflows: CI, auto-format, docs deploy, bound-issue check, board automation, open-PR, approval auto-merge, agent | committed, green on `main` |
| Automation scripts and their test suite | committed, passing |
| Labels (32), merge settings, topics, Actions write + PR-approval permission, Pages | applied |
| Project board **Omnis** (`#15`), all seven Status options | created |
| Repository variables `PROJECT_NUMBER=15` | set |
| Branch protection on `main`: 8 required checks, strict, 1 review, conversation resolution | applied |
| `GH_PROJECT_TOKEN` | set |

## What still needs a human

### 1. Agent provider secrets — the agent does not run without them

```bash
gh secret set ANTHROPIC_API_KEY          --repo marius-patrik/omnis   # or any one harness
gh secret set OPENAI_API_KEY             --repo marius-patrik/omnis
gh secret set ANTIGRAVITY_REFRESH_TOKEN  --repo marius-patrik/omnis
gh variable set AGENT_ENABLED --body "true" --repo marius-patrik/omnis
```

Any *one* harness is enough — the pipeline is harness-agnostic (ADR-0004) and skips those without
credentials. The job is gated on `AGENT_ENABLED` so that filing an issue before any secret exists
does not start a container build that cannot authenticate; its first step re-checks, because
`secrets` is not available in a job-level `if`.

### 2. Replace `GH_PROJECT_TOKEN` with a scoped credential

It currently holds the maintainer's `gh` CLI OAuth token, which carries `delete_repo`. It works, but
a fine-grained PAT limited to this repository plus projects has a far smaller blast radius. See
[the pipeline documentation](pipeline.md#tokens-and-why-there-are-two) for why two tokens exist.

### 3. Answer the open decisions

`ARCHITECTURE.md` §8 lists the open decisions; ten are resolved in `notes/adr/`. **D1 gates the
most**: not "what does Omnis do" — the architecture answers that — but which vertical slice is built
first, which determines the first bus messages, the first subsystem, and the first surface.

By `AGENTS.md` rule 13 none of these becomes an issue until it is settled: specification runs
VISION → ARCHITECTURE → ADRs → ROADMAP → issues, and an issue may only be filed for work that is
already decided.

---

## Reproducing this from an empty repository

Order matters. Branch protection goes on **after** the first push, or the initial commit cannot land.

```bash
gh repo create omnis --public
git init -b main && git remote add origin https://github.com/<owner>/omnis.git

# 1. Commit the scaffold and push while `main` is still unprotected.
git add -A && git commit -m "feat(ci): scaffold repository, governance, and pipeline"
git push -u origin main

# 2. Apply everything except protection, so the first CI run can report.
python .github/scripts/repo_settings.py --apply --skip-protection

# 3. Point the workflows at the board that step 2 created.
gh variable set PROJECT_NUMBER --body "<number>"

# 4. Protect `main`. From here on, every change goes through a pull request.
python .github/scripts/repo_settings.py --apply
```

`repo_settings.py` is idempotent, so step 4 re-applies step 2's settings; `--plan` shows what would
change without touching anything.

### If a bootstrap commit is still pending when protection goes on

Lift protection, push, restore it — and say so in the commit or the PR. A bootstrap-ordering escape
hatch, not a way around the rules:

```bash
gh api -X DELETE repos/<owner>/omnis/branches/main/protection
git push origin main
python .github/scripts/repo_settings.py --apply
```

---

## Routine operations

| Task | Command |
|---|---|
| Show GitHub-side config drift | `python .github/scripts/repo_settings.py --plan` |
| Re-apply GitHub-side config | `python .github/scripts/repo_settings.py --apply` |
| Repair board items with no status | trigger **Project Board Automation** via `workflow_dispatch` |
| Open a bot-authored draft PR | `python .github/scripts/open_pr.py --branch <b> --title <t> --body <b>` |
| Add a decision record | create `notes/adr/NNNN-title.md`; index and navigation generate themselves |
| Run the local suite | `pytest -v && black --check . && properdocs build --strict` |

## Adding a required status check

Required checks live in `repo_settings.REQUIRED_CHECKS`, and a test asserts every entry is produced
by a job in `ci.yml`. Add the job first, let it report once, then add the context and re-apply. Never
require a job that can be **skipped**: a skipped job does not satisfy a required check, so it blocks
every merge permanently. That is why the `rust` and `web` jobs guard their individual steps with
`hashFiles` rather than guarding the job.
