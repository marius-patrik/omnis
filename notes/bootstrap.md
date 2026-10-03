# Repository bootstrap and operator runbook

This document describes the **GitHub repository and delivery automation**, not the OmnisOS machine
boot sequence. Product boot/recovery is specified in `docs/OMNIS_OS.md`.

## Current repository state

- Repository: `marius-patrik/omnis`.
- Visibility: private.
- `main` is the protected integration branch.
- Repository automation, ProperDocs, the agent delivery pipeline, and historical ADRs predate the
  graph-native architecture reset and remain operational infrastructure.
- ADR-0023 and the current `ARCHITECTURE.md` supersede the old `omnisd` product topology.

## Architecture-reset implementation order

Implementation now follows `ROADMAP.md` and starts from the shared graph/protocol boundary:

```text
shared graph + protocol contracts
  -> OmnisOS / OmnisManager foundations
  -> OmnisControl bootable graph desktop
  -> OmnisAgent worldline/memory/cognition
  -> external harness/model bindings
  -> multi-host and self-evolution
```

Do not revive the old crate/subsystem topology simply because repository automation or historical
notes still mention it.

## Repository prerequisites

The delivery agent is harness-agnostic. To enable it, configure at least one supported provider
credential and set `AGENT_ENABLED=true`. Credentials belong in repository secrets, never source.

The project-board token should be narrowly scoped to this repository/project rather than using a
broad maintainer credential.

## Routine operations

| Task | Command |
|---|---|
| Show GitHub-side config drift | `python .github/scripts/repo_settings.py --plan` |
| Re-apply GitHub-side config | `python .github/scripts/repo_settings.py --apply` |
| Repair board state | trigger **Project Board Automation** via `workflow_dispatch` |
| Open a bot-authored draft PR | `python .github/scripts/open_pr.py --branch <b> --title <t> --body <b>` |
| Run repository tests/docs | `pytest -v && black --check . && properdocs build --strict` |

## Reproducing repository automation

Bootstrap order remains: initial scaffold push, apply repository settings without protection, set
project variables/secrets, then enable branch protection. `repo_settings.py` is idempotent and is the
authority for GitHub-side settings that it manages.

Architecture decisions are not derived from this runbook. See `ARCHITECTURE.md`, `docs/`, and
`notes/architecture_decisions.md`.
