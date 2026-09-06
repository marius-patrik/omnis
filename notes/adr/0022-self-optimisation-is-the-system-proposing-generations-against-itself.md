# ADR-0022 — Self-optimisation is the system proposing generations against itself

- **Status**: Accepted · **Date**: 2026-09-06
- **Depends on**: ADR-0003, ADR-0006, ADR-0012

## Context

A system that observes its own behaviour can improve it: disable a subsystem nothing has called in a
month, resize a cache that always misses, move a process off a saturated host, prefetch what is
always fetched.

The obvious way to build that is a tuner with privileged access that adjusts things directly. That
version is also the one that produces "why is my machine different today" with no answer, which is
exactly the unattributable change ADR-0003 exists to prevent.

## Decision

**Self-optimisation is not a new mechanism.** The system acts as an agent against itself and goes
through the ordinary path: it **proposes a generation**, carrying a diff, an author, and the
measurements that motivated it, and that proposal passes the same escrow as any other change
(ADR-0006).

Approving it is the same action as approving anything else. Rolling it back is the same operation
(ADR-0012).

**It is never silent.** Whether a class of optimisation may be auto-approved is a policy in the
declaration — **off by default**, and never for anything that removes or relocates. A cache resize
is a candidate for standing approval; removing a subsystem is not.

## Alternatives rejected

- **A privileged tuner that adjusts the system directly.** Simplest to build and it creates changes
  with no author, no diff, and no rollback — the precise failure ADR-0003 was written against. That
  it is the system rather than an external agent making the change does not improve the position; it
  makes it harder to notice.
- **Optimisation as configuration hints the daemon interprets at runtime.** Keeps the declaration
  honest and moves the behaviour somewhere unobservable: the running system stops matching the
  declaration, which is the drift ADR-0012 rejects.
- **Everything auto-approved, with an undo.** Sounds equivalent to gating and is not: undo requires
  noticing, and the changes most worth gating are the ones least likely to be noticed.
- **No self-optimisation at all.** Defensible, and it leaves real waste in place on a system whose
  whole premise is knowing what it is running.

## Consequences

- **It is only as good as the telemetry.** Data that answers "is this subsystem worth keeping"
  is a design problem in its own right, not a side effect of logging, and building the proposer
  before the measurements produces confident nonsense.
- Proposal quality matters more than proposal frequency. A system that suggests ten changes a day
  trains the user to approve without reading, which defeats the gate — so the bar for proposing is
  high, and silence is a valid output.
- Auto-approval policy is a security surface: an over-broad standing grant is a privileged tuner
  reintroduced through configuration.
- Because proposals are generations, the history of what the system changed about itself is
  inspectable after the fact — which is what makes the whole idea defensible.
