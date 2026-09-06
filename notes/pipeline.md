# The automation pipeline

Omnis is built by an autonomous agent pipeline under human approval gates. This documents how it
works, what each part is for, and where it can fail. The binding rules are in `AGENTS.md`; this is
the explanation behind them.

---

## The lifecycle

```
  you file a Request  ──▶  agent posts an Interpretation  ──▶  you comment `approve`
   (verbatim wording)          (scope, plan of attack)              [GATE 1]
                                                                        │
                                                                        ▼
                          agent opens a child Plan issue  ──▶  you comment `approve`
                            (linked as a sub-issue)                 [GATE 2]
                                                                        │
                                                                        ▼
        branch ──▶ implement ──▶ format ──▶ test ──▶ Draft PR ──▶ self-review loop
                                                                        │
                                                                        ▼
                              plan alignment  ──▶  you Approve the PR
                                                          [GATE 3]
                                                                        │
                                                                        ▼
                    bot proxy approval ──▶ auto-merge ──▶ issues closed, board → Done
```

**Three human gates, all explicit.** You approve the *interpretation* before anything is planned, the
*plan* before anything is written, and the *pull request* before anything merges. The agent never
crosses a gate on its own, and it never merges anything.

---

## Why each gate exists

**Gate 1 — interpretation.** The most expensive failure in agent work is a confident implementation
of the wrong thing. Rule 12 requires the `Request` issue to carry your *verbatim* wording, then an
`### Interpretation` section stating how the agent read it. Approving that is cheap; discovering the
misreading after a branch and a PR is not.

**Gate 2 — plan.** The plan is a child issue linked as a native sub-issue of the request. It states
objectives, the code changes, and the verification. This is where scope creep gets caught, because
scope creep is legible in a plan and invisible in a diff.

**Gate 3 — pull request review.** Branch protection requires one approving review; nothing reaches
`main` without it.

---

## Components

### Workflows

| Workflow | Trigger | Does |
|---|---|---|
| `ci.yml` | push, PR | `pipeline` (Python 3.10–3.13), `rust`, `web`, `docs`. Language jobs guard their *steps* with `hashFiles`, so they report green rather than being skipped — a skipped job never satisfies a required check and would block every merge permanently. |
| `agent.yml` | issue opened, comment created | Builds the agent container and dispatches it. Gated on the `AGENT_ENABLED` variable. |
| `project-automation.yml` | issue/PR lifecycle, push to main | Moves items on the board and maintains status labels. |
| `pr-approval-automerge.yml` | review submitted, comment created | Detects your approval, readies the draft, submits the bot's proxy review, arms auto-merge, reconciles afterwards. |
| `open-pr.yml` | `workflow_dispatch` | Opens the draft PR, so PRs are not authored by your local credentials. |
| `auto-format.yml` | push to any branch | Formats and commits. Formatting is never a review topic. |
| `deploy-docs.yml` | push to main | Builds with `mkdocs build --strict` and deploys to Pages. |

### Scripts

| Script | Responsibility |
|---|---|
| `harnesses.py` | The harness registry (ADR-0004). Declares each coding-agent CLI as a binary, an argv template, a model chain, and credential keys. |
| `agent_runner.py` | The stages: interpret, plan, implement, self-review, plan-alignment, respond. Knows nothing about which CLI is executing. |
| `project_automation.py` | Board transitions and exclusive status labels. Field and option ids are resolved at runtime, never hardcoded. |
| `handle_pr_approval.py` | Approval detection, proxy review, auto-merge, post-merge reconciliation. |
| `open_pr.py` | Dispatches `open-pr.yml` and waits for the PR to appear. |
| `repo_settings.py` | Every GitHub setting that otherwise exists only in the web UI, as re-runnable code. |
| `mkdocs_hooks.py` | Publishes the canonical root documents and the ADR directory as site pages, and generates the decision index and navigation. |

---

## Harness agnosticism

Per ADR-0004, no pipeline code knows which CLI is running. `harnesses.py` declares Antigravity
(`agy`), Claude Code (`claude`), Codex (`codex`), Kimi (`kimi`), Grok (`grok`), Cursor
(`cursor-agent`), and opencode (`opencode`).

- **Fallback escalates across harnesses**, not only across models. One provider's quota outage no
  longer halts delivery — which it demonstrably did before this existed.
- **Missing binaries and missing credentials are skipped, not failed.** An image carrying four of
  seven CLIs works with a shorter chain, and the container build prints a manifest of what landed.
- **Everything is overridable at runtime.** `AGENT_HARNESS_CHAIN` sets the order;
  `AGENT_HARNESS_CONFIG` overrides any field of any harness, and can define one the code has never
  heard of. An upstream flag rename is a variable change, not a code change and a rebuild.
- **Prompts are argv elements, never shell strings**, so a prompt containing shell metacharacters
  cannot escape into a command.

```jsonc
// AGENT_HARNESS_CONFIG — a repository variable
{
  "claude": { "model_chain": ["opus", "sonnet"], "extra_args": ["--add-dir", "/workspace"] },
  "grok":   { "binary": "grok-cli" }
}
```

## Quota exhaustion and resume

When every harness and model is exhausted, the agent does not fail loudly and lose its work. It
writes a checkpoint, commits and pushes it on the branch, moves the item to `Blocked`, and comments
with the completed steps and how to resume. Commenting `resume` picks up from the checkpoint on
whichever harness is then available.

---

## The board

Seven statuses, and an item carries exactly one at a time: `Backlog`, `ToDo`, `In Progress`,
`Blocked`, `Done`, `Superseded`, `Dropped`.

Status labels are **exclusive**: applying one removes the other six in the same `gh issue edit`, and
`add_issue_label` delegates to that setter so no call site can bypass the invariant. Without this a
closed issue keeps advertising itself as `In Progress`, and the board and the labels disagree.

Board field and option ids are discovered through `gh project field-list` and cached per process.
Hardcoding them means the automation breaks silently the first time the board is rebuilt — the writes
fail, the exception is caught, and the workflow still reports success.

---

## Tokens, and why there are two

| Token | Used for | Why it cannot be the other |
|---|---|---|
| `GH_PROJECT_TOKEN` | Checkout, board writes, opening PRs | The default `GITHUB_TOKEN` cannot write to a **user-owned** Projects v2 board, and events it causes do not start workflow runs — so a PR it opens never triggers the required checks. |
| `BOT_TOKEN` (`secrets.GITHUB_TOKEN`) | The proxy approving review only | `GH_PROJECT_TOKEN` belongs to the maintainer, and the PR is opened with it — so an approval sent with it is **self-approval, which GitHub rejects**. The approval must come from `github-actions[bot]`. |

This is subtle and it bit us: the approval failed, the error was swallowed, auto-merge armed anyway,
and the pull request sat at `REVIEW_REQUIRED` with nothing in the log. The handler now sends the
review with `BOT_TOKEN` and **reads the reviews back to verify it landed**, reporting plainly when it
did not.

It also requires the repository's `can_approve_pull_request_reviews` permission, which
`repo_settings.py` sets.

---

## Failure modes worth knowing

| Symptom | Cause |
|---|---|
| Board stops updating, workflows still green | Token cannot write user-owned Projects v2. Look for `gh project item-add` exiting 1 in the logs. |
| PR stuck at `REVIEW_REQUIRED` with auto-merge armed | Proxy approval failed. Check `BOT_TOKEN` is set. |
| Every merge blocked forever | A required status check names a job that can be *skipped*. Required checks may only name jobs that always report. |
| Agent does nothing on a new issue | `AGENT_ENABLED` is not `"true"`, or no harness has credentials. |
| Agent replies to itself in a loop | Bot-comment detection. Agent comments carry an `<!-- omnis-agent -->` marker and are ignored on the way back in. |

## Running it locally

```bash
python .github/scripts/repo_settings.py --plan      # show GitHub-side drift
python .github/scripts/repo_settings.py --apply     # reconcile it
pytest -v && black --check . && mkdocs build --strict
```

Setup state and the reproduction sequence are in [bootstrap.md](bootstrap.md).
