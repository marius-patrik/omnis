# ADR-0016 — Hosts are declared execution targets, and processes are placed on them

- **Status**: Accepted · **Date**: 2026-09-06
- **Depends on**: ADR-0012, ADR-0013, ADR-0015 · **Reshapes**: D4

## Context

The earlier framing asked a binary question: does the core run in a container, or natively? And it
answered per platform — container on Linux, VM on macOS and Windows.

That is too rigid in two directions. It pins a single container runtime, when Windows has both WSL
and Docker, macOS has Docker, and Linux has several; and it assumes every process runs in one place,
when the interesting configurations are heterogeneous. A user with a Linux workstation and a laptop
wants the daemon on the workstation and the interface in front of them.

`ARCHITECTURE.md` §2.3 already says surfaces are stateless with respect to the daemon and may attach,
detach, or crash at any point. A surface on a *different machine* is therefore already
architecturally legal. This record makes that explicit and declarable.

## Decision

### Hosts

A **host** is a named execution target declared in the configuration (ADR-0012), backed by a runtime:

| Backend | Available on | Notes |
|---|---|---|
| `native` | all | Runs directly on the machine |
| `docker` | Linux, macOS, Windows | The common denominator |
| `wsl` | Windows | A WSL2 distribution as a first-class host |
| `podman` · `nspawn` | Linux | Daemonless, and systemd-native, respectively |
| `remote` | all | Another personal machine, reached over the tailnet (ADR-0015) |

The container runtime is itself an abstraction with backends. Pinning one would exclude users for no
architectural gain, and every one of these already exists — we bind, we do not build (ADR-0011).

### Placement

Each core process — **daemon, CLI, GUI, TUI, web** — is **placed on a host** in the declaration.
Placement is a first-class property of the system, not an installation detail.

### Constraints

Processes carry placement constraints the resolver checks before applying a generation:

| Process | Requires |
|---|---|
| `daemon` | The workspace filesystem; durable storage |
| `gui` | A display, a GPU, and the platform's window system — effectively `native` |
| `tui` | A TTY |
| `cli` | Nothing; attaches to a daemon wherever it is |
| `web` | Reachability on the tailnet |

**Placement resolution can fail, and must fail with an explanation** — "no host satisfies the GUI's
display constraint" is a configuration error to report at evaluation time, not a runtime crash.

The GUI constraint is the load-bearing one: a GPU compositor inside a container without GPU
passthrough is crippled, and passthrough on macOS and Windows ranges from fragile to unavailable.
**The GUI runs natively; the daemon is what gets containerised.**

## Alternatives rejected

- **One fixed topology per platform** (the earlier proposal). Cannot express "daemon on the
  workstation, interface on the laptop", which is a principal reason to want this at all.
- **Requiring a single container runtime.** Docker Desktop has licensing constraints on macOS and
  Windows, podman is not everywhere, `nspawn` is Linux-only. Choosing one excludes users to save an
  abstraction that is a thin dispatch.
- **Everything native, no containers.** Discards the reproducibility that motivates ADR-0012.
- **Everything containerised, including the GUI.** Uniform and unusable: no reliable GPU or window
  system access on two of three platforms.
- **Automatic placement with no declaration.** Convenient until it guesses wrong, and then
  undebuggable. Placement is exactly the kind of decision that should be written down and diffable.

## Consequences

- **The daemon may be remote, so filesystem access may be remote.** The VFS and content-addressed
  store stop being optimisations and become load-bearing for correctness and latency.
- **Input-to-frame latency crosses a network** in split configurations, which turns D7 from an
  internal budget into a user-visible one.
- **The tailnet boundary carries real trust** when the daemon is remote, consistent with ADR-0015 and
  its rejection of public exposure.
- **D4 changes shape.** It is no longer "which platforms do we support" but "which host backends are
  supported on each platform, and which placements are we willing to test". That is a smaller, more
  answerable question, and it is the one the roadmap should carry.
- Splitting processes across hosts multiplies the configuration space. The tested combinations must
  be named explicitly, or "it works on my placement" becomes the standard bug report.
