# ADR-0003 — The modification surface is one API for every caller

- **Status**: Accepted · **Date**: 2026-09-06

## Context

The system must be fully modifiable by the user, the integrated agent, and external agents. The
transcript treats configuration as something the GUI edits and the database stores; it never states
how an agent changes anything, nor what stops one from changing something it should not.

## Decision

Everything configurable is modifiable at runtime through **one** control-socket API
(`ARCHITECTURE.md` §3.2): no privileged surface, introspectable rather than guessable, one validation
and approval path regardless of caller, every mutation attributed, every change reversible.

## Alternatives rejected

- **A privileged GUI API plus a limited API for everyone else.** Guarantees drift: the GUI path gets
  the attention, the scriptable path rots, and agents work around it.
- **A separate agent API.** Two APIs to keep in sync, and agents end up with either less power than
  the user (useless) or more (unsafe).
- **Trusting the integrated agent more than external ones.** Identity is not a security boundary
  here — both execute arbitrary model output. The gate belongs on the *action*, not the caller.
- **Modification without attribution.** An unattributable change is indistinguishable from a
  compromise.

## Consequences

Every setting needs a machine-readable schema, and the introspection endpoints become a compatibility
surface. Approval escrow sits on the mutation path and must be fast enough not to be routed around.
Any "GUI-only" feature is a defect by definition.

**This ADR is incomplete on its own.** It grants external agents the user's power without stating
what records or gates that power; the accountability invariant is still open.
