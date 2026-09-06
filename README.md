# Omnis

**An AI-first operating system for a power user's machine.**

Omnis is a kernel. It owns nothing you could get elsewhere — `git`, `sl`, Nix, podman, libvirt,
Chromium, Tailscale, and the coding-agent CLIs are all **bound, not built** — and everything that
makes them compose: one bus, one scene tree, one declaration, one modification surface, one audit
trail.

> **Status: specification.** The governance rules and the autonomous delivery pipeline are in place
> and running. The product tree is not: it is specified in [ARCHITECTURE.md](ARCHITECTURE.md),
> decided in [decision records](notes/adr/), and sequenced in [ROADMAP.md](ROADMAP.md).

## The whole machine, in one file

Subsystems, guest operating systems, where each process runs, and how it looks are one declaration.
Applying it produces a **generation** — a parent, a diff, an author — so rollback is one operation
and an agent reconfiguring your machine leaves a reviewable change rather than a mutation.

```nix
{
  omnis = {
    hosts.core.backend = "docker";        # native · docker · wsl · podman · nspawn · remote
    placement = { daemon = "core"; gui = "workstation"; };

    subsystems.vcs = {
      enable   = true;
      backends = [ "git" "sapling" ];     # drop one and it leaves entirely — binary,
      default  = "git";                   # completions, credential helper, menu entries, all
    };

    environments.windows = {
      kind = "vm";                        # container · vm · compat (Wine/Proton)
      apps.integration = "remoteapp";     # Windows apps as ordinary windows
    };

    presentation = { profile = "zed"; theme = "catppuccin-mocha"; };
    remote = { enable = true; via = "tailscale"; };
  };
}
```

The full reference is [`examples/omnis.nix`](examples/omnis.nix).

Removing something removes it **completely** — the processes, the packages, the files, and
everything it contributed to the rest of the system. "Disabled" and "not installed" are not
different states.

## What makes it AI-first

Not a chat panel. An agent is a **first-class operator**: it calls the same API as you, reads the
same option schema the settings UI is generated from, addresses the same objects by the same URIs,
and is bound by the same approval gate and audit trail.

That is only safe because every change is a generation — gated before it takes effect, reversible
after. The accountability machinery is not a constraint on the goal; it is what makes the goal
achievable.

The documentation is generated from that same option schema and lives **inside** the product, so you
read about the system in the window you are declaring it in — and so does the agent proposing the
change.

## Start here

| Document | What it is |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | **The only normative document.** What Omnis is, why, and how it is built. |
| [Decision records](notes/adr/) | Every decision that binds the implementation, with the alternatives it rejected. |
| [ROADMAP.md](ROADMAP.md) | Epics, entry gates, sequencing. |
| [AGENTS.md](AGENTS.md) | Binding rules for every contributor, human or agent. Also `CONTRIBUTING.md`. |
| [notes/pipeline.md](notes/pipeline.md) | How the delivery pipeline works, and how it fails. |
| [notes/transcript.md](notes/transcript.md) | Source material only. Specifies nothing. |

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

Two human gates before anything is written, one before anything merges. Specification runs
**architecture → decision records → roadmap → issues**, and an issue is only filed for work that is
already settled.

Full rules in [AGENTS.md](AGENTS.md); mechanics in [notes/pipeline.md](notes/pipeline.md).

## Local development

```bash
pip install -r requirements-dev.txt
pytest -v                    # repository automation tests
black --check .              # formatting
properdocs serve             # documentation site
```

Reproduce the GitHub-side configuration — labels, board, protection, permissions — at any time:

```bash
python .github/scripts/repo_settings.py --plan     # show drift
python .github/scripts/repo_settings.py --apply    # reconcile
```

## License

GPL-3.0. See [LICENSE](https://github.com/marius-patrik/omnis/blob/main/LICENSE).
