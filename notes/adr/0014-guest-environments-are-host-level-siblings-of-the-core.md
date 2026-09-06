# ADR-0014 — Guest environments are host-level siblings of the core

- **Status**: Accepted · **Date**: 2026-09-06
- **Depends on**: ADR-0011, ADR-0012, ADR-0013 · **Constrains**: D4

## Context

A power user's tools are not all on one distribution, and some are not on Linux at all. Omnis should
let a user run other operating systems beside the core — another distribution's userland, a full
guest, and ideally Windows applications.

## Decision

An **environment** is a declared OS userland or machine running beside the core, presented through
one contract regardless of what is inside it.

| Kind | Mechanism | Cost | For |
|---|---|---|---|
| `container` | podman, systemd-nspawn, distrobox-style integration | Near zero; shares the kernel | Arch, Debian, Fedora, Ubuntu userlands |
| `vm` | libvirt/QEMU, or the platform hypervisor | Heavy; own kernel | Windows, or a different kernel |
| `compat` | Wine / Proton | Light; no guest OS at all | Windows *applications*, without Windows |

Every mechanism is bound, never built (ADR-0011). Environments are declared in the configuration
(ADR-0012) and are subsystems in the "next to" layer (ADR-0013), fronted by an adapter that speaks
the bus.

### Placement is forced

**Environments are siblings of the core at host level. They are never nested inside it.**

This is not a preference. Where the core itself is hosted in a VM, running a guest VM *inside* it
means nested virtualisation — commonly unavailable, and unusably slow where it is available. Siblings
avoid the problem entirely and keep one placement rule on every platform.

### Windows in three tiers

1. **Wine/Proton** — no guest, per-application compatibility, best experience where it works.
2. **VM with RDP RemoteApp** — a real Windows guest, but individual applications presented as
   ordinary windows rather than a desktop in a box.
3. **Full desktop session** — the fallback when neither of the above works.

Two limits stated rather than discovered: **we cannot ship Windows** — the user supplies a licence
and an image — and **Wine compatibility is per-application and never a blanket guarantee**.
"Runs Windows apps" is a promise that cannot be kept; a three-tier path with honest fallbacks can.

### Guest windows add no primitive

A guest application window is a **pixel source composited into the scene tree** — the same shape as
browser raster mode. It rides the existing `texture` primitive and therefore passes the test
`ARCHITECTURE.md` §4.2 sets: adding a source must not add a primitive class.

In the TUI backend a guest GUI window degrades to its declared fallback (§4.7). A Windows
application cannot render in a terminal, and the architecture says so rather than implying parity it
cannot hold.

## Alternatives rejected

- **VMs only, uniformly.** Conceptually simple and needlessly heavy: most of the value is another
  Linux userland, which a container delivers at near-zero cost.
- **Containers only.** Cannot run Windows or a different kernel, which is a large part of the point.
- **Nesting environments inside the core container.** Tidy on Linux, broken everywhere else, and it
  would make the topology differ per platform.
- **Writing our own guest-window integration.** RDP RemoteApp, Wayland socket sharing, and Wine's
  own window handling already exist. Ours would be worse and permanent.
- **Shipping a curated Windows image.** Removes the licensing problem by committing a licensing
  violation.

## Consequences

- The environment abstraction, its declaration schema, its lifecycle contract, and the
  window-to-scene-tree binding are ours. The mechanisms are not. That is a small owned surface for a
  large capability.
- Environments are a substantial epic in their own right, and the three Windows tiers have very
  different costs — tier 1 is a dependency, tier 2 is a subsystem, tier 3 is nearly free once tier 2
  exists.
- **D4 is constrained but not resolved.** The placement rule holds on every platform; whether
  macOS and Windows are v1 targets or later ports remains open, and this record does not decide it.
- Guest filesystem and clipboard integration are where this design will actually be judged, and
  neither is specified here.
