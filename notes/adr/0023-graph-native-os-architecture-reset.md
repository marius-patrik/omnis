# ADR-0023 — Reset Omnis around a graph-native four-authority operating system

- **Status:** Accepted
- **Date:** 2026-10-03
- **Supersedes:** the previous `omnisd`-centred product topology and every earlier ADR where it
  conflicts with this record or the rewritten `ARCHITECTURE.md`.

## Context

The previous Omnis specification correctly identified several durable ideas: bind existing services,
use Nix declarations/generations, give the agent first-class machine access, use one interaction
model, share a renderer/scene representation, treat hosts/placement explicitly, and make
self-optimization inspectable.

It nevertheless remained a workspace daemon layered above an existing operating system. Subsequent
Invariant-Oriented Engineering work and the event-driven Agent/memory work exposed a simpler and
stronger boundary: the operating system itself should provide one shared multidimensional graph;
resources and capabilities should be separated from their realizations; the persistent Agent should
receive every meaningful event directly; and the interface should be a graph-native control
environment rather than a collection of product-specific panes.

## Decision

Omnis consists of four first-class authorities:

```text
OmnisOS      physical/system state, NixOS integration, generations, enforcement
OmnisManager resources, capabilities, bindings, executions, placement; Nix-derived
OmnisAgent   events/worldline, memory, context, cognition, workers
OmnisControl graph desktop, shell, interaction, 2D/3D projection, rendering
```

All use one shared multidimensional graph with stable identity. The graph is a substrate, not a fifth
semantic authority.

OmnisOS is based on a maintained NixOS/nixpkgs fork. OmnisManager is based on a maintained Nix fork.
OmnisAgent and OmnisControl are first-party Omnis components.

OmnisAgent owns the causal worldline. OmnisControl derives its semantic Control tree from the shared
graph and lowers it into private render state. Agent receives Control events directly and has
structural access to Control state.

The desktop is an interactive graph projection with toggleable 2D and 3D modes over the same
identities.

## Reaffirmed earlier ideas

The following earlier decisions remain conceptually valid where reinterpreted through the new
architecture:

- bind existing tools instead of reimplementing them;
- Nix/NixOS declarative persistent state and generations;
- harness/provider independence;
- secrets as protected handles, not Agent context;
- host/placement as explicit system concepts;
- native/delegated surfaces for existing applications/content;
- one input/navigation model;
- self-optimization through inspectable candidate changes;
- renderer source/representation separation.

## Superseded earlier ideas

The following are no longer architectural truths:

- `omnisd` as the central semantic kernel;
- a separate per-subsystem process architecture as the universal composition model;
- a standalone semantic scene tree independent of the shared graph;
- GUI as a privileged or separate product surface;
- context fragments as the main memory abstraction;
- a settings/declaration schema as the Agent's primary model of the whole machine;
- mandatory human escrow as the center of all Agent cognition/effects;
- the old roadmap/crate topology.

Historical ADRs remain useful design provenance but do not override `ARCHITECTURE.md` after this
reset.

## Consequences

Implementation restarts from the shared graph/protocol boundary rather than preserving unimplemented
legacy structure. Nix and nixpkgs forks become first-class project dependencies. The umbrella
repository becomes architecture/integration authority while component implementation is split into
OmnisOS, OmnisManager, OmnisAgent, and OmnisControl.
