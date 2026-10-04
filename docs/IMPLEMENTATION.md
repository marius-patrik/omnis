# Omnis v0 Implementation Blueprint

**Status: NORMATIVE SUPPORTING SPECIFICATION.** `ARCHITECTURE.md` defines semantic architecture;
this document freezes the first implementation profile. `DECISION_COMPLETE_V0.md` freezes all v0
algorithms, constants, defaults and fallback behavior. `ONTOLOGY_V0.md` freezes semantic names/state
machines, `NIX_OPTIONS_V0.md` freezes the public NixOS option surface, and `AGENT_ACCESS_V0.md`
freezes harness-agnostic external-agent access. A mechanism changes only through an explicit
architecture/ADR change.

## 1. Implementation profile

Omnis v0 is a Linux/NixOS system with exactly three product authorities and one shared graph/event substrate.

| Area | v0 choice |
|---|---|
| First-party runtime language | Rust 2024 edition |
| Async runtime | Tokio |
| Existing Nix code | Keep upstream C++ and patch narrowly |
| Typed protocol | Cap'n Proto schemas and RPC |
| Local transport | Unix-domain `SOCK_STREAM` sockets |
| Remote transport | QUIC with TLS 1.3 mutual host authentication |
| Semantic/event IDs | UUIDv7, 128-bit binary on wire |
| Immutable artifact IDs | BLAKE3-256 |
| Graph store | SQLite, WAL mode, single serialized writer |
| Artifact storage | filesystem BLAKE3 CAS |
| Service supervision | systemd |
| Linux compositor | Smithay |
| GPU renderer | wgpu |
| Terminal parsing | `vte` + PTY through `rustix`/libc interfaces |
| Structured logging | Rust `tracing` to journald; trace IDs preserved in protocol |

All third-party dependencies are pinned by Nix inputs and language lockfiles. Architecture documents
name dependencies but do not hard-code patch versions; dependency updates are ordinary maintenance
unless they change a contract.

## 2. Repository topology

The first implementation is split into these repositories:

```text
marius-patrik/omnis
  architecture, protocol schemas, integration flake, cross-component tests, releases

marius-patrik/omnis-os
  maintained fork of NixOS/nixpkgs
  + Omnis NixOS modules
  + omnis-graphd
  + omnis-osd
  + package definitions for the other Omnis components

marius-patrik/omnis-manager
  maintained fork of NixOS/nix
  + Nix evaluator/store/build observer patches
  + dedicated Omnis control socket in nix-daemon
  + Rust omnis-managerd service

marius-patrik/omnis-control
  Rust workspace implementing compositor, graph desktop, shell, rendering and interaction
```

`omnis` owns protocol schema versions so no component may silently redefine cross-component types.
Generated Rust/C++ protocol bindings are build artifacts; the `.capnp` sources are canonical.

## 2.1 First-party crate/workspace layout

Repository-internal crate/module names are fixed for the first implementation so cross-repository
dependencies do not grow ad hoc.

```text
omnis-os/omnis/
  graph/omnis-graphd        binary
  graph/omnis-graph         transaction/query/storage library
  graph/omnis-cas           BLAKE3 artifact store
  os/omnis-osd              binary
  os/omnis-linux-observe    Linux observation/enforcement adapters

omnis-manager/omnis/
  managerd/omnis-managerd   Rust binary
  managerd/registry         resource/capability/binding model
  managerd/resolver         deterministic resolver/placement
  managerd/executor         systemd execution broker
  managerd/adapters         subprocess adapter host
  managerd/inference        local protocol gateway + canonical inference translation
  nix-observer/             C++ observer/control additions to upstream Nix

omnis-control/
  crates/control            compositor binary
  crates/projection         graph -> ControlTree
  crates/scene              ControlTree -> RenderScene
  crates/render             wgpu renderer
  crates/wayland            Smithay/XWayland integration
  crates/shell              PTY/vte terminal source
  crates/input              deterministic resolver + event normalization

omnis/
  protocol/                 canonical Cap'n Proto schemas
  spec/agent_access.toml    MCP/plugin parity registry
  cli/                      thin `omnis` RPC client + `omnis mcp`
  packages/agent-access/    generated typed plugin client
  tests/                    cross-component protocol/NixOS VM tests
```

Generated protocol bindings come from the pinned umbrella schema revision rather than copied source.

## 2.2 CLI

The umbrella `omnis` binary is a thin Rust RPC client, not a fifth authority. It performs no direct
database writes:

```text
omnis graph ...
omnis system ...
omnis manager ...
omnis control ...
omnis trace ...
```

Each command calls the owning RPC. OmnisControl uses typed protocol clients; external agents receive projections of the same operations through MCP or the generated plugin client.

## 3. Runtime process topology

### 3.1 System scope

OmnisOS starts these system services:

```text
systemd
 ├─ nix-daemon                 # OmnisManager Nix fork; normal Nix client compatibility
 ├─ omnis-graphd              # shared graph, CAS, append-only core event journal
 ├─ omnis-osd                 # physical/system observation + enforcement adapter
 └─ omnis-managerd            # capabilities, bindings, placement and execution broker
```

`omnis-graphd` and `omnis-osd` are shipped from the OmnisOS fork. `omnis-managerd` belongs to the
OmnisManager product even though its orchestration layer is Rust.

### 3.2 User scope

Each interactive Omnis user gets:

```text
systemd --user
 └─ omnis-control             # Wayland compositor / graph desktop session
```

Control starts after the user session exists and requires no agent process. External agents may start,
stop, reconnect or be absent without affecting the deterministic shell, graph, Manager or OS.

### 3.3 Socket locations

```text
/run/omnis/graph.sock
/run/omnis/os.sock
/run/omnis/manager.sock
/run/omnis/nix-control.sock
$XDG_RUNTIME_DIR/omnis/control.sock
```

System sockets authenticate callers with `SO_PEERCRED`; graph authority is derived from UID/GID,
service identity and explicit grants. User sockets are mode 0600 by default.

## 4. Stable identity and naming

All mutable semantic identities are UUIDv7 values represented as 16 bytes on the wire and canonical
lowercase hyphenated text when rendered.

Distinct Rust newtypes are mandatory even though the binary shape is identical:

```text
NodeId EdgeId EventId ExecutionId TransactionId TraceId GenerationId
```

IDs are never derived from PID, pathname, Nix store path, window ID, provider name or host address.

Immutable artifacts use:

```text
ArtifactId = BLAKE3(payload bytes)
```

Graph kinds, relations, capabilities and event types use dotted names. `omnis.*` is reserved for
first-party semantics. Third parties use reverse-DNS namespaces, for example
`com.example.capability.export`.

## 5. Shared graph implementation

### 5.1 Ownership

`omnis-graphd` is infrastructure, not a fifth semantic authority. It validates namespace ownership
but does not decide OS, Manager, Agent or Control policy.

### 5.2 Database

The system graph lives at:

```text
/var/lib/omnis/graph/graph.sqlite3
```

SQLite pragmas for v0:

```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=FULL;
PRAGMA foreign_keys=ON;
PRAGMA busy_timeout=5000;
```

Graph writes are serialized through one writer task. Reads use independent read-only connections and
WAL snapshots. Omnis does not depend on experimental multi-writer SQLite modes.

### 5.3 Canonical tables

Logical schema:

```text
nodes(
  id BLOB(16) PRIMARY KEY,
  created_revision INTEGER NOT NULL,
  deleted_revision INTEGER NULL
)

node_kinds(
  node_id BLOB(16), kind TEXT, authority TEXT,
  valid_from_revision INTEGER, valid_to_revision INTEGER NULL
)

node_properties(
  node_id BLOB(16), namespace TEXT, key TEXT, value_type INTEGER, value BLOB,
  authority TEXT, provenance_id BLOB(16),
  valid_from_revision INTEGER, valid_to_revision INTEGER NULL
)

edges(
  id BLOB(16) PRIMARY KEY, source BLOB(16), relation TEXT, target BLOB(16),
  dimension TEXT, authority TEXT, provenance_id BLOB(16),
  valid_from_revision INTEGER, valid_to_revision INTEGER NULL
)

edge_properties(...)
provenance(...)
transactions(...)
event_log(...)
artifact_refs(...)
schema_migrations(...)
```

Current-state queries select rows whose `valid_to_revision IS NULL`. Historical revision reads use
the validity interval. The graph is therefore revision-addressable without treating its internal
transaction history as cognition or agent memory.

### 5.4 Transactions

Every write is a `GraphTransaction` containing actor, authority, expected revision, causal parents,
preconditions and mutations. The writer uses `BEGIN IMMEDIATE`; all preconditions are evaluated
inside the transaction. Success increments the global revision exactly once.

Mutation operations are fixed in v0:

```text
CreateNode
DeleteNode
AddKind / EndKind
SetProperty / EndProperty
CreateEdge / EndEdge
SetEdgeProperty / EndEdgeProperty
PutProvenance
EnqueueEvent
```

There is no embedded Cypher/SPARQL language in v0. Queries use typed selectors, traversals and
projections from the protocol schema.

### 5.5 Core event journal

Every graph commit inserts emitted Event envelopes into `event_log` in the same SQLite transaction.
Non-graph first-party producers call graphd `enqueueEvent` before reporting a durable transition
complete.

`ingest_seq` is monotonically increasing. Any number of consumers can replay from an arbitrary
sequence and then subscribe live. Consumers persist their own cursor; graphd has no global ACK.

v0 performs no automatic event-journal deletion. Event envelopes and event-referenced artifacts remain
available so an independently installed agent can replay every core event since initialization.

### 5.6 Artifact CAS

Large immutable payloads are never copied into graph properties or RPC messages. Graphd exposes CAS
`put/get/stat` and stores objects under:

```text
/var/lib/omnis/cas/blake3/<first-two-hex>/<remaining-hex>
```

Writes go to a temporary file, fsync, verify BLAKE3, then atomic rename. Metadata records media type,
length, protection class and creator. Garbage collection traces references from graph/event-journal
roots before deleting an unreferenced object.

### 5.7 High-rate event streams

External agents never need to discover first-party events by inspecting rendered state. Key/button/touch/scroll/focus
and lifecycle events are emitted directly. Dense ordered streams such as pointer motion, audio timing
or fine telemetry may be losslessly batched for I/O efficiency.

A batch artifact contains each original item with producer sequence, monotonic timestamp, event type
and payload. The enclosing EventEnvelope carries the batch ArtifactId and sequence range. Any event consumer can replay every original item; batching is not semantic sampling or loss.

## 6. Protocol and IPC

### 6.1 Schemas

Canonical schemas live in `protocol/*.capnp` in the umbrella repository:

```text
common.capnp     IDs, values, provenance, errors, traces
graph.capnp      graph query/transaction/subscription/event-journal/CAS
os.capnp         hosts, system generations, enforcement, observation
manager.capnp    resource/capability/binding/resolution/execution
control.capnp    projections, tree mutations, focus/input/navigation
```

Schema field numbers are append-only. Removed fields stay reserved. Breaking semantic changes bump
the protocol major version.

### 6.2 Local transport

Cap'n Proto RPC runs over Unix-domain `SOCK_STREAM`. Each connection begins with a handshake carrying
protocol major/minor, component identity, process build ID and requested interface set.

Large data travels by ArtifactId. GPU/native-window/audio handles continue through native Linux
mechanisms such as Wayland, DMA-BUF and PipeWire rather than being serialized into Cap'n Proto.

### 6.3 Remote transport

Remote Omnis-to-Omnis RPC uses the same logical schemas framed over QUIC. TLS 1.3 authenticates both
hosts. Each host has an Ed25519 identity key; pairing pins the peer key/certificate fingerprint in
the authority graph. A VPN such as Tailscale may carry QUIC but is not part of semantic identity.

### 6.4 Request semantics

Every effectful request carries:

```text
request_id       UUIDv7
trace_id         UUIDv7
actor            graph NodeId
causal_parents[] EventId
idempotency_key  UUIDv7 where retry is legal
authority_scope
deadline
```

RPC transport retries only operations declared idempotent. Execution creation is idempotent on
`ExecutionId`; repeated starts return the same execution record instead of spawning duplicates.

## 7. OmnisOS implementation

### 7.1 NixOS fork

`omnis-os` tracks `NixOS/nixpkgs` and keeps an upstream remote. Omnis-specific changes live in a
clearly delimited patch set plus an `nixos/modules/services/omnis/` module family.

The v0 module exposes:

```text
omnis.enable
omnis.graph.*
omnis.os.*
omnis.manager.*
omnis.agentAccess.*
omnis.control.users.<name>.*
omnis.hosts.*
omnis.security.*
```

Normal nixpkgs packages remain normal packages. Omnis binaries are packaged in the fork and can also
be built directly from their pinned component repositories.

### 7.2 Machine-managed Nix state

Omnis does not invent a second configuration language. Persistent machine mutations target a
dedicated NixOS module:

```text
/etc/omnis/configuration.nix      # stable wrapper/import root
/etc/omnis/managed.nix            # machine-writable literal option definitions
```

`configuration.nix` imports the user's normal NixOS configuration and `managed.nix`. Manager edits
`managed.nix` through the Nix parser/AST from the fork, never regex or text substitution.

Candidate mutations are built in `/var/lib/omnis/candidates/<GenerationId>/` first. The active
`managed.nix` is changed only after candidate evaluation/build succeeds and activation is ready.

### 7.3 Generation transaction

Persistent change sequence:

```text
1. create GenerationId and candidate managed.nix AST
2. evaluate full NixOS module graph
3. export option/evaluation provenance
4. compute derivation + closure + service-impact diff
5. build candidate system
6. run pre-activation invariants
7. activate using NixOS switch-to-configuration
8. reconcile actual machine state
9. atomically promote managed.nix candidate
10. publish generation/result events and graph state
```

If activation fails, the previous generation remains selectable and the candidate is retained with
failure evidence. External side effects that cannot roll back are explicitly recorded.

### 7.4 OS observation

`omnis-osd` uses exact Linux sources before inference:

- systemd D-Bus for unit lifecycle;
- udev for device lifecycle;
- rtnetlink for links, addresses and routes;
- `/proc` reconciliation at startup/resume;
- eBPF process tracepoints for fork/exec/exit after startup reconciliation;
- fanotify/inotify for explicitly watched filesystem scopes;
- logind for sessions/seats;
- cgroup v2 for resource ownership and accounting.

Raw high-rate signals are normalized before graph/event publication. The system does not forward
every syscall to Agent.

### 7.5 Recovery

Boot order is `graphd -> {osd,nix-daemon,managerd} -> user session -> {agent,control}`.

A failed Agent or Control never prevents boot. A failed graph database enters
`omnis-recovery.target`, which provides a conventional TTY, Nix generation rollback, database backup
and graph rebuild tooling.

## 8. OmnisManager implementation

### 8.1 Nix fork boundary

The complete v0 boundary is `docs/NIX_CONTROL_V0.md`.

`omnis-manager` tracks the frozen Nix revision. Upstream CLI/daemon/store protocols remain
compatible. The fork adds:
- `NixStoreControl` Cap'n Proto RPC on `/run/omnis/nix-control.sock`;
- C++ companion binary `omnis-nix-eval` with one-evaluation socketpair RPC;
- `EvalState::forceValue` source-position tracing while that helper is active;
- store/build/substitution/GC observation with daemon boot identity + ordered sequence.

There is no text parsing of Nix CLI output and no model code inside either surface.

### 8.2 NixOS option provenance

Pinned nixpkgs already exposes module-system provenance fields consumed by the evaluator. Active and
candidate configuration use exactly:

```text
/etc/omnis/base.nix
/etc/omnis/managed.nix
/etc/omnis/configuration.nix
/var/lib/omnis/candidates/<GenerationId>/{managed.nix,configuration.nix}
```

`base.nix` is user/admin-owned; `managed.nix` and the wrapper are Omnis-owned. Candidate evaluation
uses the same base module plus candidate managed module without modifying active state.

Option records, value fingerprints, evaluator trace, derivation/closure plans and four-part system
diff are specified by `NIX_CONTROL_V0.md` and `nix_control.capnp`.

### 8.3 Manager core

`omnis-managerd` is a Rust/Tokio daemon with these modules:

```text
registry       Resource/Capability/Binding graph materialization
discovery      deterministic foreign discovery pipeline
resolver       constraints + deterministic candidate scoring
placement      host/device/runtime selection
executor       launch/cancel/wait/retry/reconcile
nix_bridge     dedicated Nix control-socket client
secrets        protected-handle broker
adapters       CLI/API/MCP/model/native binding providers
```

### 8.4 Execution

Local process launch is split by authority. Manager resolves the Execution and obtains an
ExecutionEnvelope; it then calls OmnisOS `PhysicalLaunch`. `omnis-osd` is the only first-party
component that invokes systemd `StartTransientUnit` for restricted work and creates
`omnis-exec-<ExecutionId>.service`. It applies the exact sandbox properties from
`DECISION_COMPLETE_V0.md`.

Process pipes/PTY are exposed back through the typed OS stream capabilities. Manager records and
publishes semantic Execution lifecycle/output without owning physical sandbox creation.

### 8.5 Resolution

Resolution is deterministic from the recorded candidate set and scoring inputs:

```text
hard constraint filter
 -> capability/effect compatibility
 -> authority/credential availability
 -> locality/privacy filter
 -> runtime/hardware feasibility
 -> explicit caller preferences
 -> cost/latency/quality score
 -> stable tie-break by BindingId
```

A learned predictor may supply a score feature, but it never hides the candidate list or hard
rejection reasons.

### 8.6 Binding provider ABI

Built-in providers are Rust modules. Third-party providers are subprocesses speaking the Manager
Cap'n Proto adapter interface. They are not loaded as arbitrary shared libraries into managerd.

Initial providers:

```text
nix package/store
executable/CLI
systemd service
HTTP/OpenAPI
MCP
OpenAI-compatible model API
Anthropic model API
llama.cpp server/local GGUF
ONNX Runtime classifier/embedding
container runtime
SSH/remote Omnis host
```

## 9. Harness-agnostic agent-access implementation

Core ships no agent daemon.

Two projections are built from `spec/agent_access.toml`:

```text
omnis mcp
  stdio MCP server
  -> graph/os/manager/control typed clients

@omnis/agent-access
  generated TypeScript client
  -> graph/os/manager/control typed clients
```

The generator introspects the public Cap'n Proto service methods and fails CI if any non-handshake
public method is missing from MCP or plugin projection.

`omnis mcp` opens no network listener. It runs as the invoking user and carries the same Unix
credential/authority context as the CLI.

Event access uses graphd's append-only journal:
- replay from `after_ingest_seq`;
- strictly increasing sequence delivery;
- live subscription after catch-up;
- no global ACK;
- no semantic sampling.

Agent runtime state, memory, model/provider sessions, tasks and cognition are not stored by core.

## 10. OmnisControl implementation

### 10.1 Threads and runtimes

`omnis-control` is one process with three cooperating execution domains:

```text
main compositor thread   Smithay/calloop, Wayland objects, seats, input, surface lifecycle
render thread            wgpu Device/Queue, render graph, frame pacing
Tokio runtime            graph/OS/Manager RPC, PTYs, browser protocols, background I/O
```

Domains communicate with bounded channels. The render loop never waits for any external agent/model work.

### 10.2 Control tree and scene

The complete v0 data model/lowering is `docs/CONTROL_RENDER_V0.md`,
`protocol/control_scene.capnp`, `protocol/control.capnp`, and `spec/control_render.toml`.

Pipeline:

```text
shared graph revision
 -> ProjectionSpec + Lens
 -> typed ControlTree
 -> Taffy / graph layout
 -> typed RenderScene
 -> wgpu
 -> DRM/KMS output
```

ControlTree carries semantic/presentation identity and typed interactive state. RenderScene carries
private frame/render identity only. The public Control mutation API never exposes an untyped
first-party property bag.

Fixed RenderScene primitive union:

```text
Group Transform Clip Rect RoundedRect Path GlyphRun Image Mesh NativeSurface
```

### 10.3 2D and 3D desktop

Both modes use the same ControlTree identity/focus/selection/lens/frontier. Only graph layout,
camera and scene lowering differ. The exact 2D/3D coordinate, camera, hit-test and NativeSurface
composition behavior is frozen in `CONTROL_RENDER_V0.md` and `spec/control_render.toml`.

### 10.4 Wayland and legacy apps

Smithay owns Wayland compositor protocol handling and DRM/input integration. XWayland is launched as
a managed child for X11 compatibility.

Each Wayland/XWayland toplevel gets a graph identity and a `NativeSurface` Control node. Control owns
placement, clipping, z-order and graph relationships; the client owns its pixels. Direct scan-out is
allowed when Smithay/DRM eligibility permits it.

### 10.5 Shell

The shell uses a real PTY. Input first passes the deterministic resolver:

```text
shell grammar/executable -> PTY/shell
known omnis:// URI/path  -> navigate/open
known capability         -> Manager resolve/execute
known graph query        -> graph request
otherwise                -> Agent event/intention
```

Terminal output is parsed with `vte` into a cell model then lowered to ordinary GlyphRun/Rect scene
primitives. The terminal is not a second renderer.

### 10.6 Browser integration

v0 does not build a browser engine. Chromium/Firefox run as ordinary Wayland clients. Manager binds
structured browser interfaces when available (CDP, WebDriver BiDi, accessibility tree). Control
materializes browser surfaces like any other NativeSurface while semantic browser state is published
into the graph.

### 10.7 External-agent structural control

Agent calls typed Control operations directly:

```text
materialize
create/remove/reparent view
bind graph identity
set lens
set mode
focus/select
set layout constraints
navigate
attach action
persist workspace
```

These mutate the same presentation graph the user manipulates and emit events. Synthetic input is
reserved for opaque third-party surfaces/testing.

## 11. Security and protected values

### 11.1 Service privilege

`omnis-graphd`, `omnis-osd` and `omnis-managerd` run under dedicated system identities with only the
Linux capabilities/filesystem access they require. Control runs as the logged-in user. Agent clients are ordinary caller processes.

Manager creates more restricted execution scopes by default; external clients do not inherit managerd/root
authority.

### 11.2 Credentials

Persistent secret bytes are stored as systemd encrypted credentials (`systemd-creds`), using TPM2
sealing when configured. The graph stores only a protected HandleId and metadata.

At execution time Manager materializes a secret into a private credential file/sealed memory handle
or environment variable only when the target interface requires that form. Secret bytes are never
placed in graph properties, event payloads, MCP/plugin payloads or logs.

### 11.3 Authorization

Graphd checks write namespace on every transaction. Manager checks capability grant + requested
execution envelope before effects. Privileged interactive user operations may additionally use
polkit, but polkit is not the semantic policy engine.

## 12. Backpressure and overload

Every subscription/RPC stream is bounded. Producers never drop durable semantic events silently.

Rules:

- the core event journal is durable and append-only regardless of connected consumers;
- telemetry producers coalesce declared high-rate metric classes before enqueue;
- Control input/render queues drop obsolete intermediate frames, never input commits;
- overload state itself is published as graph/event state.

## 13. Crash recovery

### graphd
SQLite WAL recovers atomic graph/event-journal transactions. On integrity failure, boot recovery follows
`DECISION_COMPLETE_V0.md §28` exactly: restore the newest valid graph backup, reconcile OS physical
state, reconcile Manager executions, verify event-journal continuity, and record any recovery gap.

### Manager
On restart, osd enumerates `omnis-exec-*.service` units and physical processes, republishes their
state, and managerd reconciles semantic Executions by ExecutionId. Manager never reconstructs
physical truth directly from systemd.

### External agents

No external agent is part of core crash recovery. A client reconnects using its own persisted
`ingest_seq` cursor and replays the core event journal.

### Control
Control reconstructs its tree from presentation graph state and current native surfaces. GPU caches
and frame-local layout data are disposable.

## 14. Schema migration

SQLite databases use monotonic integer schema versions. Migrations are forward-only code shipped with
the owning component and run under an exclusive startup lock after an automatic snapshot/backup.

Graph semantic relation/type migrations are explicit graph transactions with provenance. Protocol
major incompatibility prevents connection; minor versions negotiate the common feature set.

## 15. Observability

All components use one TraceId across graph, event, Manager, Nix and Control operations.
Rust services use `tracing`; C++ Nix patches emit matching trace fields. Logs go to journald.

Operational logs/metrics are not the core event journal. Any operational transition that matters to
future consumers is separately emitted as an Event.

## 16. Build and packaging

Every component is built through Nix. Rust uses Cargo lockfiles but Nix is the release composition
authority. The umbrella integration flake pins exact component revisions and produces:

```text
packages.<system>.omnis-graphd
packages.<system>.omnis-osd
packages.<system>.omnis-managerd
packages.<system>.omnis-control
nixosModules.omnis
nixosConfigurations.<test machines>
```

Release identity records the umbrella commit plus exact Nix/nixpkgs/component revisions.

## 17. Test architecture

Required test layers:

```text
unit/property        graph mutations, resolver, agent-access parity, layouts
schema/golden        Cap'n Proto compatibility and canonical value encodings
fuzz                 protocol decoders, graph transactions, foreign adapter parsing
integration          real service processes over Unix sockets
NixOS VM             boot, generations, rollback, system observation, execution isolation
Wayland              compositor protocol + XWayland/native surface lifecycle
end-to-end           user/MCP/plugin action -> Manager/OS effect -> graph/event -> Control update
```

Foundational acceptance scenario:

1. Boot an OmnisOS VM.
2. Log into OmnisControl with no agent installed; run a real shell command.
3. Start `omnis mcp`, replay the core journal from sequence 0 and verify all prior events are present.
4. Mutate Control structurally through MCP and verify the same operation exists through the plugin client.
5. Install/enable a package/service permanently through Manager/OS APIs.
6. Manager produces candidate NixOS generation and semantic/closure diff.
7. Activate it and observe process/service graph changes.
8. Launch an unmodified Wayland application and see its NativeSurface graph node.
9. Toggle the same workspace between 2D and 3D without losing selection/identity.
10. Restart Manager and Control, reconnect from the saved event cursor, and roll back the generation.

## 18. Performance invariants

These are engineering constraints, not benchmark promises:

- Control frame production must never wait synchronously on an external agent or remote model.
- graph reads and subscriptions are usable while the serialized writer is busy;
- durable event enqueue must remain bounded by local storage, not model latency;
- no model call occurs in boot, Nix evaluation, Nix build scheduling, compositor frame or Linux
  enforcement critical paths;
- bulk payloads above the protocol inline threshold use the CAS;
- high-rate telemetry is losslessly batched before entering the core event journal.

## 19. Replaceability boundaries

The following v0 mechanisms are intentionally replaceable without changing semantics:

```text
SQLite graph storage
QUIC remote transport
Smithay/wgpu renderer internals
specific model providers
OmnisOS transient-service executor
```

The stable boundaries are IDs, graph/event-journal semantics, capability/binding/execution model,
protocol schemas/versioning, authority boundaries, agent-access parity and Control structural API.

## 20. Definition of implementation-ready

The design is decision-complete when a coding worker can take an assigned roadmap item and determine,
without inventing architecture:

- which repository/product owns it;
- which process and privilege domain runs it;
- which graph namespace it may write;
- which RPC/schema it uses;
- where durable state lives;
- how IDs/provenance/events are formed;
- how the operation recovers after crash/retry;
- how it is packaged by Nix;
- which integration test proves the contract.

This document supplies those answers for the v0 substrate. Future ADRs refine behavior; they must not
silently create parallel identity, event, configuration or rendering systems.


## 21. No implementation-design discretion

Observable v0 behavior that is not determined by this document, `DECISION_COMPLETE_V0.md`, the
owning subsystem spec, protocol schema or acceptance tests is a `SpecificationDefect`. Coding agents
must not choose a library, algorithm, default, fallback, timeout, queue size, persistence behavior,
layout, routing rule or security policy on their own.


## 22. Canonical generated/runtime inputs

Database creation/migration v1 begins from:

```text
schema/graph.sql
```

Cross-process wire code is generated from `protocol/*.capnp`.
Agent projections are generated/verified from `spec/agent_access.toml`.
First-party graph identifiers come from `ONTOLOGY_V0.md`.
NixOS modules implement `NIX_OPTIONS_V0.md` exactly.

These files eliminate local schema/ontology/config/projection design inside component repositories.

