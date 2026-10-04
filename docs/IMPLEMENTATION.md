# Omnis v0 Implementation Blueprint

**Status: NORMATIVE SUPPORTING SPECIFICATION.** `ARCHITECTURE.md` defines semantic architecture;
this document freezes the first implementation profile. `DECISION_COMPLETE_V0.md` freezes all v0
algorithms, constants, defaults and fallback behavior. `ONTOLOGY_V0.md` freezes semantic names/state
machines and `NIX_OPTIONS_V0.md` freezes the public NixOS option surface. Implementations may replace a mechanism later
only through an explicit architecture/ADR change.

## 1. Implementation profile

Omnis v0 is a Linux/NixOS system with four product authorities and one non-semantic shared substrate.

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
| Agent worldline | SQLite, WAL mode, append-only event tables |
| Lexical retrieval | SQLite FTS5 |
| Vector retrieval | pinned `sqlite-vec` index, derived/non-canonical |
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

marius-patrik/omnis-agent
  Rust workspace implementing worldline, memory/indexing, context, cognition and workers

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

omnis-agent/
  crates/agentd             binary/event loop
  crates/worldline          append/replay storage
  crates/memory             cognitive graph writes + retrieval indexes
  crates/context            ContextCapsule compiler
  crates/cognition          judgement/candidate/budget pipeline
  crates/workers            durable worker/activity engine
  crates/replay             deterministic replay/evaluation tooling

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
  cli/                      thin `omnis` RPC client
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
omnis agent ...
omnis control ...
omnis trace ...
```

Each command calls the owning RPC. OmnisControl and OmnisAgent use the same operations through typed
protocol clients.

## 3. Runtime process topology

### 3.1 System scope

OmnisOS starts these system services:

```text
systemd
 ├─ nix-daemon                 # OmnisManager Nix fork; normal Nix client compatibility
 ├─ omnis-graphd              # shared graph, CAS, durable event outbox
 ├─ omnis-osd                 # physical/system observation + enforcement adapter
 └─ omnis-managerd            # capabilities, bindings, placement and execution broker
```

`omnis-graphd` and `omnis-osd` are shipped from the OmnisOS fork. `omnis-managerd` belongs to the
OmnisManager product even though its orchestration layer is Rust.

### 3.2 User scope

Each interactive Omnis user gets:

```text
systemd --user
 ├─ omnis-agentd              # persistent personal cognitive subsystem
 └─ omnis-control             # Wayland compositor / graph desktop session
```

Agent and Control start independently after the user session exists. Neither is required for the
other to display a deterministic shell or for the machine to boot. If Agent is unavailable, Control
continues with exact shell, graph, Manager and OS operations.

### 3.3 Socket locations

```text
/run/omnis/graph.sock
/run/omnis/os.sock
/run/omnis/manager.sock
/run/omnis/nix-control.sock
$XDG_RUNTIME_DIR/omnis/agent.sock
$XDG_RUNTIME_DIR/omnis/control.sock
```

System sockets authenticate callers with `SO_PEERCRED`; graph authority is derived from UID/GID,
service identity and explicit grants. User sockets are mode 0600 by default.

## 4. Stable identity and naming

All mutable semantic identities are UUIDv7 values represented as 16 bytes on the wire and canonical
lowercase hyphenated text when rendered.

Distinct Rust newtypes are mandatory even though the binary shape is identical:

```text
NodeId EdgeId EventId ActivityId ExecutionId WorkerId TransactionId TraceId GenerationId
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
outbox_events(...)
artifact_refs(...)
schema_migrations(...)
```

Current-state queries select rows whose `valid_to_revision IS NULL`. Historical revision reads use
the validity interval. The graph is therefore revision-addressable without treating its internal
transaction history as the Agent worldline.

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

### 5.5 Event outbox

Every graph commit inserts its emitted Event envelopes into `outbox_events` in the same SQLite
transaction. Non-graph first-party producers also call `EventOutbox.enqueue` on graphd before
reporting a durable transition complete.

Agent drains the outbox in order, writes each event to its worldline, then acknowledges EventId.
Delivery is at-least-once. Agent deduplicates by EventId. An event is deleted from the outbox only
after durable Agent acknowledgement.

This mechanism is the reliability bridge for the requirement that Agent receives every meaningful
first-party event even when Agent is temporarily down.

### 5.6 Artifact CAS

Large immutable payloads are never copied into graph properties or RPC messages. Graphd exposes CAS
`put/get/stat` and stores objects under:

```text
/var/lib/omnis/cas/blake3/<first-two-hex>/<remaining-hex>
```

Writes go to a temporary file, fsync, verify BLAKE3, then atomic rename. Metadata records media type,
length, protection class and creator. Garbage collection traces references from graph/worldline
roots before deleting an unreferenced object.

### 5.7 High-rate event streams

Agent never discovers first-party events by inspecting rendered state. Key/button/touch/scroll/focus
and lifecycle events are emitted directly. Dense ordered streams such as pointer motion, audio timing
or fine telemetry may be losslessly batched for I/O efficiency.

A batch artifact contains each original item with producer sequence, monotonic timestamp, event type
and payload. The enclosing EventEnvelope carries the batch ArtifactId and sequence range. Agent can
replay every original item; batching is not semantic sampling or loss.

## 6. Protocol and IPC

### 6.1 Schemas

Canonical schemas live in `protocol/*.capnp` in the umbrella repository:

```text
common.capnp     IDs, values, provenance, errors, traces
graph.capnp      graph query/transaction/subscription/outbox/CAS
os.capnp         hosts, system generations, enforcement, observation
manager.capnp    resource/capability/binding/resolution/execution
agent.capnp      event/worldline/memory/context/activity/worker
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
omnis.agent.users.<name>.*
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

`omnis-manager` tracks `NixOS/nix`. Existing Nix CLI/daemon/store protocols remain compatible.
Omnis adds a separate `/run/omnis/nix-control.sock`; it does not overload the stable Nix daemon
protocol.

Minimal C++ patches add observer hooks at:

- evaluator value forcing and source positions;
- derivation creation;
- store path realization/substitution;
- build start/log/result;
- closure queries and garbage collection;
- daemon operation correlation.

The observer interface emits structured events/query results to `omnis-managerd`. No model code is
linked into Nix.

### 8.2 NixOS option provenance

The OmnisOS fork instruments the NixOS module system so each final option can be related to its
declaration, all contributing definitions, priority/merge operation, source span and evaluator
trace. Manager joins these records with Nix derivations/store paths.

This is what powers `why is this installed?`, `what will rebuild?`, `which definition enabled this
service?`, and generation semantic diffs.

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
adapters       CLI/API/MCP/model/harness binding providers
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
 -> explicit user/Agent preferences
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
Claude Code
Codex
OpenCode
generic PTY harness
container runtime
SSH/remote Omnis host
```

## 9. OmnisAgent implementation

### 9.1 State

Per-user canonical/derived files live under `$XDG_STATE_HOME/omnis/agent/`:

```text
worldline.sqlite3     canonical immutable event history
index.sqlite3         rebuildable FTS/vector/retrieval indexes
checkpoints/          durable worker/activity continuation artifacts
```

Cognitive current-state objects such as assertions, goals, procedures and memories are canonical
writes to the Agent-owned dimension of the shared graph. `index.sqlite3` is disposable.

### 9.2 Worldline schema

```text
events(
  id BLOB(16) PRIMARY KEY,
  ingest_seq INTEGER UNIQUE,
  type TEXT, schema_major INTEGER, schema_minor INTEGER,
  source BLOB(16), actor BLOB(16),
  observed_wall_ns INTEGER, observed_monotonic_ns INTEGER,
  graph_revision INTEGER NULL, trace_id BLOB(16),
  payload_artifact BLOB(32) NULL, inline_payload BLOB NULL
)
event_causes(event_id, parent_event_id)
event_entities(event_id, node_id, role)
event_artifacts(event_id, artifact_id, role)
```

Worldline tables are append-only except administrative migration metadata. Agent ACKs graphd outbox
only after the event transaction is durably committed.

### 9.3 Event pipeline

Every accepted event runs through:

```text
ingest/deduplicate
 -> deterministic reducers
 -> salience + domain classification
 -> memory activation/retrieval
 -> candidate intention generation (always includes null)
 -> feasibility/Pareto filtering
 -> budget allocation
 -> zero or more worker activations
 -> effects/observations
 -> resulting events
```

No stage requires a generative model when an exact operation is sufficient.

### 9.4 Model capabilities

Agent requests model semantics from Manager using:

```text
model.classify
model.embed
model.rerank
model.generate
model.reason
model.vision
model.audio.transcribe
agent.code
```

The registry records provider, model identity/version, context limits, modalities, latency, cost,
privacy/locality and hardware requirements. Model outputs always record the binding that produced
them.

### 9.5 Memory indexing

FTS5 indexes normalized text from graph memories/events. Vector embeddings are stored in pinned
`sqlite-vec` virtual tables keyed by NodeId/EventId and embedding-model identity. Because
`sqlite-vec` is pre-v1 and vector indexes are inherently derived, all vector state is rebuildable
from graph/worldline data.

Changing embedding model creates a new index namespace rather than rewriting provenance.

### 9.6 Context compiler

A worker receives a `ContextCapsule` with:

```text
trigger event + causal ancestors
goal/activity state
selected graph neighborhood
retrieved episodic/semantic/procedural memory
relevant artifacts/code
previous attempts + negative evidence
tool/capability descriptors
authority/protection constraints
token/byte/time budget
```

Selection uses deterministic mandatory items first, then lexical/vector/rerank scores. Protected
items are filtered before model serialization. The final capsule and source references are persisted
for reproducibility.

### 9.7 Workers

A worker is a durable Agent activation, not a provider session. State includes WorkerId, ActivityId,
trigger events, context capsule, requested capabilities, budget, status and checkpoint ArtifactId.

External coding-agent CLIs are Manager executions attached to a WorkerId. Native hooks are preferred;
PTY/process output is the fallback. Every tool/model/harness result returns through the event
outbox/worldline.

## 10. OmnisControl implementation

### 10.1 Threads and runtimes

`omnis-control` is one process with three cooperating execution domains:

```text
main compositor thread   Smithay/calloop, Wayland objects, seats, input, surface lifecycle
render thread            wgpu Device/Queue, render graph, frame pacing
Tokio runtime            graph/Agent/Manager RPC, PTYs, browser protocols, background I/O
```

Domains communicate with bounded channels. The render loop never waits for Agent/model work.

### 10.2 Control tree and scene

Pipeline:

```text
shared graph revision
 -> ProjectionSpec + Lens
 -> ControlTree
 -> layout
 -> RenderScene
 -> wgpu render graph
 -> DRM/KMS output
```

Persistent Control nodes have graph NodeIds in the presentation namespace. Frame-local GPU objects
use private integer handles and never become semantic identity.

Render primitives are fixed initially:

```text
Group Rect RoundedRect Path GlyphRun Image Mesh NativeSurface Clip Transform
```

### 10.3 2D and 3D desktop

Both modes consume the same selected graph subgraph and interaction state.

2D provides focus+context node/edge editing, hierarchical and force layouts, ports/actions, inline
inspectors and arbitrary panels. 3D maps the same nodes/edges into a camera-controlled spatial
layout and may map selected graph dimensions to axes, depth, clustering and trails.

Toggling mode changes only projection/layout state. Focus, selection, NodeIds, active lens and
timeline frontier are preserved.

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

### 10.7 Agent structural control

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
Linux capabilities/filesystem access they require. Agent and Control run as the logged-in user.

Manager creates more restricted execution scopes by default; workers do not inherit managerd/root
authority.

### 11.2 Credentials

Persistent secret bytes are stored as systemd encrypted credentials (`systemd-creds`), using TPM2
sealing when configured. The graph stores only a protected HandleId and metadata.

At execution time Manager materializes a secret into a private credential file/sealed memory handle
or environment variable only when the target interface requires that form. Secret bytes are never
placed in graph properties, worldline payloads, model context or logs.

### 11.3 Authorization

Graphd checks write namespace on every transaction. Manager checks capability grant + requested
execution envelope before effects. Privileged interactive user operations may additionally use
polkit, but polkit is not the semantic policy engine.

## 12. Backpressure and overload

Every subscription/RPC stream is bounded. Producers never drop durable semantic events silently.

Rules:

- graph outbox is durable and may grow while Agent is unavailable;
- telemetry producers coalesce declared high-rate metric classes before enqueue;
- Control input/render queues drop obsolete intermediate frames, never input commits;
- worker/model concurrency is budgeted by Agent and executed under Manager resource limits;
- overload state itself is published as graph/event state.

## 13. Crash recovery

### graphd
SQLite WAL recovers atomic graph/outbox transactions. On integrity failure, boot recovery can restore
the most recent backup and replay authoritative OS/Manager observations plus Agent worldline-derived
cognitive state where appropriate.

### Manager
On restart, osd enumerates `omnis-exec-*.service` units and physical processes, republishes their
state, and managerd reconciles semantic Executions by ExecutionId. Manager never reconstructs
physical truth directly from systemd.

### Agent
On restart, Agent resumes outbox drain after the last acknowledged EventId/sequence, rebuilds derived
indexes as required, and resumes durable workers from checkpoints. Duplicate events are harmless.

### Control
Control reconstructs its tree from presentation graph state and current native surfaces. GPU caches
and frame-local layout data are disposable.

## 14. Schema migration

SQLite databases use monotonic integer schema versions. Migrations are forward-only code shipped with
the owning component and run under an exclusive startup lock after an automatic snapshot/backup.

Graph semantic relation/type migrations are explicit graph transactions with provenance. Protocol
major incompatibility prevents connection; minor versions negotiate the common feature set.

## 15. Observability

All components use one TraceId across graph, event, Manager, Nix, Agent and Control operations.
Rust services use `tracing`; C++ Nix patches emit matching trace fields. Logs go to journald.

Operational logs/metrics are not the semantic worldline. Any operational transition that matters to
future cognition is separately emitted as an Event.

## 16. Build and packaging

Every component is built through Nix. Rust uses Cargo lockfiles but Nix is the release composition
authority. The umbrella integration flake pins exact component revisions and produces:

```text
packages.<system>.omnis-graphd
packages.<system>.omnis-osd
packages.<system>.omnis-managerd
packages.<system>.omnis-agent
packages.<system>.omnis-control
nixosModules.omnis
nixosConfigurations.<test machines>
```

Release identity records the umbrella commit plus exact Nix/nixpkgs/component revisions.

## 17. Test architecture

Required test layers:

```text
unit/property        graph mutations, resolver, context selection, layouts
schema/golden        Cap'n Proto compatibility and canonical value encodings
fuzz                 protocol decoders, graph transactions, foreign adapter parsing
integration          real service processes over Unix sockets
NixOS VM             boot, generations, rollback, system observation, execution isolation
Wayland              compositor protocol + XWayland/native surface lifecycle
Agent replay         worldline replay produces stable deterministic reductions
end-to-end           user input -> Agent/Manager/OS effect -> graph/event -> Control update
```

Foundational acceptance scenario:

1. Boot an OmnisOS VM.
2. Log into OmnisControl with Agent intentionally disabled; run a real shell command.
3. Start Agent and verify it drains queued first-party events exactly once semantically.
4. Ask to install/enable a package/service permanently.
5. Manager produces candidate NixOS generation and semantic/closure diff.
6. Activate it and observe process/service graph changes.
7. Launch an unmodified Wayland application and see its NativeSurface graph node.
8. Toggle the same workspace between 2D and 3D without losing selection/identity.
9. Restart Agent, Manager and Control independently and recover state.
10. Roll back the NixOS generation and observe the causal/resulting graph changes.

## 18. Performance invariants

These are engineering constraints, not benchmark promises:

- Control frame production must never wait synchronously on Agent or a remote model.
- graph reads and subscriptions are usable while the serialized writer is busy;
- durable event enqueue must remain bounded by local storage, not model latency;
- no model call occurs in boot, Nix evaluation, Nix build scheduling, compositor frame or Linux
  enforcement critical paths;
- bulk payloads above the protocol inline threshold use the CAS;
- high-rate telemetry is normalized/coalesced before entering cognitive event flow.

## 19. Replaceability boundaries

The following v0 mechanisms are intentionally replaceable without changing semantics:

```text
SQLite graph storage
SQLite worldline storage
sqlite-vec derived vector index
QUIC remote transport
Smithay/wgpu renderer internals
specific model/harness providers
OmnisOS transient-service executor
```

The stable boundaries are IDs, graph semantics, worldline semantics, capability/binding/execution
model, protocol schemas/versioning, authority boundaries and Control structural API.

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
silently create parallel identity, event, configuration, rendering or cognition systems.


## 21. No implementation-design discretion

Observable v0 behavior that is not determined by this document, `DECISION_COMPLETE_V0.md`, the
owning subsystem spec, protocol schema or acceptance tests is a `SpecificationDefect`. Coding agents
must not choose a library, algorithm, default, fallback, timeout, queue size, persistence behavior,
layout, routing rule or security policy on their own.


## 22. Canonical generated/runtime inputs

Database creation/migration v1 begins from the checked-in SQL sources:

```text
schema/graph.sql
schema/worldline.sql
schema/index.sql
```

Cross-process wire code is generated from `protocol/*.capnp`, including the canonical inference IR.
Harness adapters consume `spec/harnesses.toml` and `spec/inference_gateway.toml`. Agent generative calls use
`prompts/*.md`. First-party graph identifiers come from `ONTOLOGY_V0.md`. NixOS modules implement
`NIX_OPTIONS_V0.md` exactly.

These files eliminate local schema/prompt/ontology/config design inside component repos.
