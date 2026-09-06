# ADR-0011 — Omnis is a kernel: bind existing services rather than reimplement them

- **Status**: Proposed · **Date**: 2026-09-06
- **Underpins**: ADR-0012, ADR-0013, ADR-0014, ADR-0015

## Context

Read literally, `ARCHITECTURE.md` §1 says the daemon "owns version control, packages, tasks,
terminals, containers, language servers, debuggers, an embedded browser, an agent runtime, a secrets
vault, content-addressed storage, and a sync mesh". That reads as a mandate to reimplement a
decade's worth of mature software, and the roadmap that follows from it is twenty-one epics of
building.

That is the wrong goal. The target user is a power user who already has these tools and wants them
to compose. Every line we write to replace `git`, `cargo`, or Chromium is a line that is worse than
what it replaces and that we then maintain forever.

The opposite failure is equally real: a thin launcher that shells out to a dozen tools and exposes
each one raw. That is not a product, and composition is exactly what it fails to provide.

## Decision

**Omnis is a kernel.** It owns the seams, not the organs.

We **bind** — never reimplement — anything that already exists and works:

| Concern | Bound |
|---|---|
| Version control | `git`, `sl` |
| Packages and toolchains | Nix, plus each ecosystem's own resolver |
| Containers and VMs | podman, systemd-nspawn, libvirt/QEMU, the platform hypervisor |
| Terminals | existing PTY libraries, tmux control mode |
| Language tooling | existing language servers and debug adapters |
| Browser | Chromium via CDP |
| Networking and identity | Tailscale |
| Secrets at rest | the OS keychain and established key-derivation libraries |
| Rendering | wgpu, an existing text-shaping stack, an existing terminal library |
| Agents | the coding-agent CLIs, per ADR-0004 |

We **own** the abstractions that make them compose, and only those:

- the Substrate Bus and its wire schema
- the scene tree, its primitive vocabulary, and the parity contract
- the capability matrix and layered configuration resolution
- the modification surface: introspection, escrow, attribution
- the `ContextFragment` normal form and `omnis://` resolution
- the operation log over whichever VCS backend is running
- the cross-repository task graph over whichever runner executes it

**The test for new code:** does this exist already? If it does, bind it. If binding it means exposing
it raw, write the adapter — not the tool. If something genuinely does not exist, it is almost
certainly one of the abstractions above.

## Alternatives rejected

- **Reimplement for control and consistency.** The honest version of the transcript's ambition. It
  produces a worse `git`, a worse package manager, and a worse browser, each of which must then be
  maintained against the real one's moving target. The consistency it buys can be bought with an
  adapter instead.
- **A thin launcher over existing tools.** Cheap, and it fails at the only thing that matters:
  nothing composes. A task graph that cannot see across repositories, a context shelf that cannot
  read a terminal buffer, and an agent whose actions are unattributable are all consequences of
  having no abstraction layer.
- **Bind only where convenient, build where interesting.** How every project of this shape actually
  drifts. Without a stated test, "interesting" wins every argument and the kernel becomes a monolith
  one justified exception at a time.

## Consequences

- The core shrinks substantially, and the roadmap's subsystem epics shrink with it — most become
  adapters plus a declaration rather than implementations.
- We inherit our dependencies' bugs, release cadences, and breaking changes. Adapters must be thin
  enough that replacing the thing behind one is cheap, which is a real constraint on adapter design.
- Some abstractions will be harder than the tools they wrap. The scene tree is more subtle than any
  single renderer; the bus schema is more subtle than any single subsystem. That is where the effort
  belongs.
- Several existing records need re-reading against this test. ADR-0007 should say we *drive* `git`
  and `sl` rather than implement a VCS engine; ADR-0008 owns the cross-repository graph while
  delegating execution; ADR-0009 and ADR-0010 compose existing chunking, hashing, and
  key-derivation libraries rather than writing algorithms.

## What this forecloses

Any argument that begins "we should write our own" and ends anywhere other than the list of owned
abstractions above.
