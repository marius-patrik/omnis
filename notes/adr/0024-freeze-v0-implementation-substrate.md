# ADR-0024 — Freeze the Omnis v0 implementation substrate

- **Status**: Superseded in part by ADR-0026 · **Date**: 2026-10-03
- **Depends on**: ADR-0023

## Context

ADR-0023 reset Omnis around OmnisOS, OmnisManager, OmnisAgent, OmnisControl, one shared graph and one
Agent worldline. The architecture was semantically complete but still left foundational implementation
choices open: database, protocol, IDs, process topology, renderer stack, event delivery, Nix patch
boundary and first-party runtime language.

Leaving those choices to independent implementation workers would recreate architecture by accident.

## Decision

Freeze the v0 implementation profile defined in `docs/IMPLEMENTATION.md`.

The mandatory substrate is Rust 2024/Tokio for new first-party services; narrow C++ patches inside the
Nix fork; Cap'n Proto for cross-component schemas/RPC; Unix-domain sockets locally; QUIC/TLS for
native remote RPC; UUIDv7 semantic/event identities; BLAKE3 artifacts; SQLite WAL for graph and
worldline persistence; FTS5 plus rebuildable sqlite-vec indexes for retrieval; systemd supervision;
and Smithay + wgpu for OmnisControl.

`omnis-graphd` is additionally the durable event outbox. Graph changes enqueue their events in the
same SQLite transaction; other first-party components durably enqueue before treating an event as
published. OmnisAgent drains the outbox into its append-only worldline with at-least-once delivery
and EventId deduplication.

Nix compatibility is preserved by keeping the normal Nix daemon/client protocol intact. OmnisManager
adds a separate structured control/observer channel rather than placing cognition into Nix.

## Alternatives rejected

- **Leave all mechanisms abstract until implementation.** This delegates architectural decisions to
  whichever worker happens to implement a subsystem first and makes integration failure likely.
- **Use a distributed graph database/message broker immediately.** It adds deployment, recovery and
  identity complexity before a single-machine implementation has demonstrated the need.
- **Use JSON/HTTP as the internal universal protocol.** Easy to inspect, but weaker for typed
  high-frequency cross-process contracts and C++/Rust code generation; JSON remains a debugging
  representation, not the wire authority.
- **Put the worldline and current graph in one canonical database/model.** Current interpreted state
  and immutable causal experience have different mutability and ownership semantics; merging them
  makes reinterpretation unsafe.
- **Write a compositor/browser/terminal stack from scratch.** Smithay, Wayland clients, PTYs and
  existing browsers already supply mature physical mechanisms that Omnis can bind.
- **Embed an LLM in Nix or the compositor.** This violates deterministic realization and latency/
  availability requirements.

## Consequences

- Coding agents can now implement the substrate without selecting foundational technologies.
- SQLite single-writer behavior becomes an explicit v0 scaling boundary; graph semantics remain
  storage-independent so a later backend can replace it.
- Cap'n Proto schema discipline becomes a cross-repository compatibility requirement.
- The Nix and nixpkgs forks stay close enough to upstream that Omnis-specific changes can remain
  reviewable patch stacks.
- Agent/Control remain independently restartable and replaceable; model failure cannot prevent boot
  or deterministic machine operation.
- `sqlite-vec` is accepted only as a pinned derived index because its pre-v1 API is not a canonical
  storage contract.

## Scope limit

This ADR freezes the v0 substrate, not every future algorithm. Memory ranking, graph layout, learned
judgement policy and provider choice may evolve behind the fixed contracts without another substrate
ADR unless they change the authority/identity/protocol model.
