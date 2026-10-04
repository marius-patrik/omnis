# Omnis — Core Implementation Roadmap

This roadmap implements the three core authorities only: OmnisOS, OmnisManager and OmnisControl.
No agent runtime or external agent runtime is a core dependency. Concrete behavior is frozen by the
normative contracts and `spec/contract.toml`; workers report SpecificationDefect instead of designing
missing behavior.

## Phase 0 — Architecture reset and repository split

- land the three-authority architecture;
- maintain `omnis-os`, `omnis-manager`, `omnis-control`;
- keep shared protocol/spec ownership in `omnis`;
- establish upstream NixOS/nixpkgs and Nix tracking;
- remove core built-in agent-runtime assumptions;
- establish end-to-end compatibility CI.

Exit: all core implementation work has one owner and no fourth core authority remains normative.

## Phase 1 — Shared graph and core event journal

Implement in OmnisOS/shared substrate:
- stable NodeId/EdgeId/EventId identity;
- graph namespace/dimension ownership;
- SQLite/WAL graph store with serialized writer and revision validity;
- BLAKE3 artifact CAS;
- append-only core event journal with monotonic ingest_seq;
- atomic graph mutation + event commit;
- query/path/alias/provenance APIs;
- graph subscriptions;
- event replay/live subscription from any cursor;
- CLI inspector.

Exit: independent clients can create/query allowed graph state and replay every first-party event.

## Phase 2 — OmnisManager foundation

Implement:
- Resource/Capability/Binding/Execution graph model;
- Nix derivation/store-path resource publication;
- deterministic discovery/resolution;
- arbitrary CLI/API/MCP/model/container/VM/native bindings;
- protected handles;
- placement;
- execution lifecycle;
- Nix explain/realization planning.

Exit: Manager resolves and executes interchangeable semantic bindings without any agent dependency.

## Phase 3 — OmnisOS vertical system integration

Implement:
- NixOS/nixpkgs fork/patch stack;
- boot of graph + Manager services;
- hardware/device/process/service observation;
- generation metadata/semantic diff;
- evaluate/build/activate/rollback;
- cgroup/systemd/eBPF execution envelopes;
- host identity, pairing and physical capability publication.

Exit: a booted machine can inspect and mutate system state entirely through graph/OS/Manager APIs.

## Phase 4 — OmnisControl minimum usable environment

Implement:
- Smithay compositor;
- wgpu renderer;
- typed ControlTree/RenderScene;
- graph projection/focus/selection/lens;
- PTY/shell default surface;
- native Wayland/XWayland surfaces;
- unified deterministic input resolver;
- 2D graph desktop;
- complete Control event publication.

Exit: boot lands in Control and works fully with no agent installed.

## Phase 5 — Agent-runtime-agnostic agent access

Implement exactly `docs/AGENT_ACCESS_V0.md` + `spec/agent_access.toml`:
- `omnis mcp` stdio server;
- `@omnis/agent-access` typed client package;
- complete OS/Manager/Control/graph operation projection;
- core event journal replay/subscription;
- parity generator/checker;
- authority propagation;
- extension graph namespaces.

Exit: an arbitrary external agent can inspect/control all three core surfaces and receive every event
without core changes.

## Phase 6 — Generic inference and foreign capability depth

Manager:
- classifier/embed/rerank/generate/reason/vision/audio bindings;
- local inference engines;
- remote model APIs;
- HTTP/OpenAPI;
- MCP foreign endpoints;
- repository/VCS/LSP/tooling discovery.

These are semantic resources, not external agent runtimes.

Exit: agents can use Manager's generic capabilities or their own stack interchangeably.

## Phase 7 — OmnisControl full graph desktop

Implement:
- clustering/LOD;
- core event-journal timeline;
- causal/resource/provenance lenses;
- inspectors;
- graph mutation affordances;
- 3D mode;
- lossless 2D/3D toggle;
- direct external-agent tree mutation;
- tables/charts/editors/media/web semantics;
- accessibility.

Exit: core system operation is fully graph-native and externally agent-controllable.

## Phase 8 — Distributed multi-host core

Implement:
- host pairing;
- remote typed RPC;
- capability advertisement;
- remote execution;
- artifact transfer/cache;
- placement;
- federated graph queries with shared identities;
- event/provenance continuity.

Exit: OS/Manager/Control can span multiple Omnis hosts without an agent runtime.

## Phase 9 — Hardening and first core release

- recovery/backup/migration;
- protocol conformance;
- authority/security tests;
- event losslessness tests;
- MCP/plugin parity tests;
- performance budgets;
- release provenance;
- real-machine/VM acceptance suite.

Exit: every criterion in `ARCHITECTURE.md §18` passes.

## Separate reference-agent track

`marius-patrik/dsh-stack` evolves independently into the reference Omnis agent environment. It is
not in the dependency chain above and never blocks a core release. Its Omnis integration must consume
the same MCP/plugin surface available to any other agent.
