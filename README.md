# Omnis

**Universal developer workspace and local-first personal data OS.**

One engine, many presets. Omnis is a desktop workspace whose entire presentation layer — renderer,
layout topology, input routing, keymap, window chrome, and iconography — is a *configuration state
of a single engine* rather than a set of alternative implementations. A "theme" here is not a
stylesheet; it is a named point in an orthogonal capability matrix.

> **Status: scaffold.** The repository, its governance rules, and its autonomous delivery pipeline
> are in place. The product tree is not: it is decomposed into epics in
> [ROADMAP.md](ROADMAP.md) and built one approved plan at a time.

## Start here

| Document | What it is |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | **Normative.** Process topology, the capability matrix, renderer separation, and the eight open decisions that gate the roadmap. |
| [ROADMAP.md](ROADMAP.md) | Epics, entry gates, and sequencing rationale. |
| [AGENTS.md](AGENTS.md) | The binding rules for every contributor, human or agent. Also `CONTRIBUTING.md`. |
| [VISION.md](VISION.md) | **Reference only.** Captured scoping conversation. Never overrides the architecture. |

## How work happens here

```
user request  ──▶  Request issue      ──▶  interpretation  ──▶  you comment `approve`
                   (verbatim wording)      (agent)
                                                    │
                                                    ▼
                   Plan issue (sub-issue) ──▶  you comment `approve`
                                                    │
                                                    ▼
                   branch ─▶ Draft PR (bot-authored) ─▶ self-review loop ─▶ plan alignment
                                                    │
                                                    ▼
                   you Approve  ──▶  auto-merge  ──▶  issues closed, board set to Done
```

Two human gates, both explicit: you approve the *interpretation* before anything is planned, and the
*plan* before anything is written. Nothing merges without a review approval from you.

Full rules in [AGENTS.md](AGENTS.md).

## Repository automation

| Path | Purpose |
|---|---|
| `.github/workflows/ci.yml` | Pipeline, Rust, web, and docs jobs. Language jobs are guarded, so they stay green while the product tree is still a scaffold. |
| `.github/workflows/agent.yml` | Containerized autonomous agent, dispatched on issues and comments. |
| `.github/workflows/project-automation.yml` | Board status transitions from lifecycle events. |
| `.github/workflows/pr-approval-automerge.yml` | Approval detection, auto-merge, post-merge reconciliation. |
| `.github/workflows/open-pr.yml` | Opens bot-authored draft PRs so the maintainer can review them. |
| `.github/scripts/repo_settings.py` | Every GitHub setting that otherwise only exists in the web UI, as re-runnable code. |

Reproduce the GitHub-side configuration at any time:

```bash
python .github/scripts/repo_settings.py --plan     # show what would change
python .github/scripts/repo_settings.py --apply    # apply it
```

## Local development

```bash
pip install -r requirements-dev.txt
pytest -v                 # repository automation tests
black --check .           # formatting
mkdocs serve              # documentation site
```

## License

GPL-3.0. See [LICENSE](https://github.com/marius-patrik/omnis/blob/main/LICENSE).
