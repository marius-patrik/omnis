# Omnis — Implementation Roadmap

This roadmap replaces the old daemon/workspace epic sequence. The ordering is dependency-driven and
is intended to reach a bootable vertical slice as early as possible. Concrete mechanisms and paths
are frozen by `docs/IMPLEMENTATION.md`; roadmap workers implement them rather than selecting substitutes.

## Phase 0 — Architecture reset and repository split

Deliverables:

- land the architecture reset in `omnis`;
- mark conflicting historical ADRs non-normative/superseded;
- create/restore repositories for `omnis-os`, `omnis-manager`, `omnis-agent`, `omnis-control`;
- establish upstream tracking for NixOS/nixpkgs and Nix forks;
- define protocol/version ownership in umbrella repo;
- add end-to-end compatibility CI skeleton.

Exit: all implementation work has a canonical target repo and no old `omnisd` architecture remains
normative.

## Phase 1 — Shared graph substrate

Implement in OmnisOS/integration layer:

- stable NodeId/EdgeId identity;
- graph namespaces/dimension ownership;
- SQLite/WAL graph store with serialized writer, validity intervals and migrations;
- BLAKE3 artifact CAS;
- durable graphd event outbox with Agent ACK/dedup;
- atomic transactions/revisions;
- query/traversal API;
- subscriptions;
- normalized graph-change events;
- CLI inspector.

Exit: two independent test clients can create/query shared identities and receive ordered changes.

## Phase 2 — OmnisManager foundation

Fork/extend Nix with:

- Resource/Capability/Binding/Execution graph model;
- Nix derivation/store-path resource publication;
- generic command/path/service/API/native bindings;
- deterministic capability resolution;
- discovery framework;
- execution lifecycle events;
- protected handle contract;
- placement abstraction.

Exit: Manager can discover and execute at least three interchangeable bindings for one semantic
capability while preserving graph identity/provenance.

## Phase 3 — OmnisOS vertical system integration

Implement:

- NixOS/nixpkgs fork/patch stack;
- boot of graph + Manager core services;
- hardware/device/process/service graph publication;
- generation metadata/semantic diff;
- candidate evaluate/build/activate/rollback API;
- execution envelopes using cgroups/namespaces/security primitives;
- host identity and physical capability advertisement.

Exit: a booted machine can inspect itself entirely through graph + Manager APIs and switch/rollback
an OmnisOS generation.

## Phase 4 — OmnisControl minimum usable environment

Implement:

- Wayland compositor bootstrap;
- wgpu render scene;
- ControlTree projection engine;
- graph identity/focus/selection/lens model;
- shell/PTY as default surface;
- native Wayland/XWayland delegated surfaces;
- unified input resolver;
- 2D focus+context graph desktop;
- Agent/control structural API stub and full Control event publication.

Exit: boot lands in OmnisControl; user can execute Linux shell commands, open native applications,
and navigate system graph in 2D.

## Phase 5 — OmnisAgent event/worldline core

Implement:

- durable SQLite worldline fed from graphd outbox;
- EventId deduplication + causal DAG + append ingest order;
- graph-change and Control/Manager/OS event ingestion;
- embedded artifact CAS;
- event/entity/project state;
- judgement interface;
- worker lifecycle;
- context capsule model;
- deterministic/null-action handling.

Exit: Agent survives restart, reconstructs active state, and receives all first-party system/control
transitions without polling.

## Phase 6 — Structured memory and context

Implement:

- episodic/semantic/procedural memory;
- assertions with temporal validity;
- evidence/provenance;
- contradictions/supersession;
- graph + FTS5 lexical + pinned sqlite-vec derived vector retrieval;
- activation/reranking;
- context compiler;
- projection deduplication/feedback-loop prevention;
- consolidation jobs.

Exit: Agent can continue a long-running project across restarts with inspectable evidence for every
recalled memory.

## Phase 7 — Models, inference, and external harnesses

Manager bindings:

- classifier;
- embedding model;
- reranker;
- reasoning model;
- vision/audio where useful;
- local inference engines;
- remote model APIs;
- Claude Code;
- Codex;
- OpenCode;
- generic harness;
- MCP.

Agent integration:

- worker-specific model capability resolution;
- universal inference-boundary interception;
- native harness hooks;
- code/research/reasoning/verification workers.

Exit: replacing model provider or code harness requires Manager binding/config change, not Agent core
changes.

## Phase 8 — OmnisControl full graph desktop

Implement:

- semantic clustering and LOD;
- worldline timeline;
- causal/memory/resource/provenance lenses;
- graph-aware inspectors;
- interactive graph mutation affordances;
- 3D spatial graph mode;
- lossless 2D/3D toggle preserving state;
- Agent-driven materialization and tree mutation;
- charts/tables/editors/media/web semantic sources;
- accessibility tree.

Exit: the system can be operated primarily through the graph desktop, and Agent-created interfaces
are indistinguishable in authority from user-created Control arrangements.

## Phase 9 — Distributed placement and multi-host system

Implement:

- remote Omnis host protocol;
- capability advertisement;
- remote execution envelopes;
- artifact transfer/cache;
- GPU/CPU placement;
- remote graph synchronization required for shared identities;
- QUIC/TLS remote RPC with the same EventId/TraceId/NodeId contracts.

Exit: one Agent activity can use local Control, remote GPU, local repository, and remote worker while
preserving shared graph/activity/event identity.

## Phase 10 — Learning and self-optimization

Implement:

- memory utility learning;
- procedure induction;
- learned routing estimates;
- competence/self-model;
- endogenous intention generation;
- consolidation/sleep regimes;
- candidate Agent variants;
- candidate Control/Manager/OS generation proposals;
- replay/evaluation/promotion lineage.

Exit: repeated expensive behavior can compile toward reusable procedures/capabilities and structural
changes are evaluated as candidate generations rather than mutating live code in place.

## Parallelization

After Phase 1 protocol freeze, the following lanes can run concurrently:

```text
OmnisOS physical integration
OmnisManager capability/binding work
OmnisAgent worldline/memory work
OmnisControl compositor/2D work
```

Cross-lane integration tests live in `omnis` and must exercise actual protocols rather than mocks once
both sides exist.

## First complete release criterion

The first release is complete only when all criteria in `ARCHITECTURE.md §18` pass end to end on a
real booted machine.