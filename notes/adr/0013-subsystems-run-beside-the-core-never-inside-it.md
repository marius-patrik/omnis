# ADR-0013 — Subsystems run beside the core, never inside it

- **Status**: Proposed · **Date**: 2026-09-06
- **Supersedes**: the in-process subsystem model in `ARCHITECTURE.md` §2.2
- **Depends on**: ADR-0011, ADR-0012

## Context

`ARCHITECTURE.md` §2.2 has `omnisd` initialising subsystems in-process from a `features` block, and
states that "every subsystem must be independently omittable" as a rule contributors must honour.

Rules honoured by discipline erode. With seventeen subsystems in one address space, the first
deadline produces a direct call between two of them, and the property is quietly gone with nothing
failing to signal it.

## Decision

Four layers. Nothing runs inside `omnisd`.

```
SURFACES      gui · tui · cli · web · external harnesses
                              ▲
NEXT TO       vcs · pty · lsp · dap · browser · cas · tasks · exthost · agent · environments
              supervised peers — separate processes, the bus is the only ABI
                              ▲
CORE          omnisd — bus router, registry, capability broker, convergence and generations
                              ▲
BELOW         host OS · container runtime · Nix store · systemd · Tailscale · OS keychain
              bound, never owned
```

- **Below** is infrastructure that pre-exists and the core binds (ADR-0011). The core never
  reimplements it and never assumes exclusive ownership of it.
- **Next to** are peers the core supervises but does not contain. Each is a separate process with
  only the Substrate Bus between it and everything else.
- **The core is small**: bus routing, the subsystem registry, capability brokering, and convergence.

**Supervision, restart policy, resource limits, ordering, and socket activation are systemd's**, not
ours (ADR-0011). Socket activation matters specifically: a subsystem starts on its first bus message,
which answers both the memory cost of many processes and the cold-start cost of starting them.

**Subsystems are declared, not compiled in.** Enabling one is an option in the declaration
(ADR-0012), which replaces the `features` block and the conditional-initialisation code behind it.

## Alternatives rejected

- **In-process subsystems with a plugin trait** (the current model). Cheapest to write and it makes
  the central property unenforceable. A crash in any subsystem takes the daemon with it, and nothing
  prevents two subsystems from calling each other directly.
- **In-process by default, out-of-process for the risky ones.** Two subsystem contracts to maintain,
  and the boundary is drawn by guesswork about which code will misbehave — a prediction nobody makes
  well.
- **A thread per subsystem with message passing.** Gets the discipline without the isolation: shared
  address space means a panic or a leak still crosses the boundary, and it forecloses subsystems
  written in another language.
- **Our own supervisor.** Restart backoff, health checks, ordering, and socket activation are solved
  problems with a mature implementation already present below us.

## Consequences

- **The property becomes structural.** Two subsystems *cannot* couple, because the only path between
  them is a versioned wire schema.
- **Binding becomes mechanical.** A subsystem is a process that speaks the bus, so wrapping `git` is
  a thin adapter process rather than a module inside the daemon — ADR-0011 made possible rather than
  merely intended. Subsystems may be written in any language.
- **Every subsystem call is IPC.** Control traffic is fine; the hot paths — PTY streams, language
  server traffic, screencast frames — need measuring against the data socket rather than assuming.
- **Debugging becomes distributed.** One stack trace becomes several processes and a correlation id.
  This argues for tracing being part of the bus from the first message, not retrofitted later.
- **The bus schema must be complete**, because there is no in-process escape hatch left. That
  front-loads work into E1 and is a feature, not an accident.
