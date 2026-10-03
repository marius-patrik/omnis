# Omnis v0 — Decision-Complete Implementation Contract

**Status: NORMATIVE.** This document removes implementation-design discretion from Omnis v0.

`ARCHITECTURE.md` defines what Omnis is. `docs/IMPLEMENTATION.md` defines the concrete substrate.
This document defines the remaining algorithms, constants, defaults, ordering and acceptance behavior.

For v0, an implementation agent **MUST NOT choose an alternative** to anything specified here.
If a specified mechanism proves impossible, the agent stops that item, records the evidence, and
requires an ADR/spec change. It does not substitute a "reasonable equivalent."

The only implementation discretion left is semantically invisible code expression: variable names,
private helper decomposition, comments, local refactoring, and equivalent code that passes the exact
contracts/tests below.

---

## 1. Frozen source baselines

The initial forks are created from exactly these upstream revisions:

```text
NixOS/nixpkgs master:
be5021eb406d32e8df6462a1c0986a70bdf03e02

NixOS/nix master:
2ab29c63d3273d4e2b4d1346b1aefede9b5af350

Rust toolchain:
1.99.0, profile=minimal, components=rustfmt,clippy,rust-src

crates.io index snapshot used for initial Cargo dependency resolution:
cddab5f1c359539147959163142ff95a24995f6a
```

Each component repo commits:

```text
rust-toolchain.toml
Cargo.toml
Cargo.lock
flake.nix
flake.lock
```

after its first successful build. Thereafter Cargo.lock and flake.lock are authoritative until an
explicit dependency-update change.

Dependency resolution procedure is fixed:

1. use Rust 1.99.0;
2. use the crate families named in §2;
3. resolve the highest non-yanked stable crate release compatible with Rust 1.99.0 from the pinned
   crates.io index snapshot above;
4. commit the resulting Cargo.lock;
5. do not use git dependencies when a crates.io release exists, except Smithay if the pinned release
   lacks a required protocol fix demonstrated by a failing acceptance test; such an exception requires
   an ADR.

No implementation agent chooses older/familiar versions manually.

---

## 2. Frozen first-party dependency families

### 2.1 Common Rust services

Every Rust service uses these crates where the corresponding concern exists:

```text
tokio                 async runtime
capnp + capnp-rpc     protocol serialization/RPC
uuid                  UUIDv7
blake3                artifact hashing
rusqlite              SQLite access
tracing               structured spans/events
tracing-journald      journald sink
thiserror             typed library errors
anyhow                 binary/application boundary aggregation only
clap                  CLI parsing
futures               async stream combinators
serde + serde_json    debug/export JSON only
bytes                  byte buffers
parking_lot           local short critical sections
```

Rules:

- no second async runtime;
- no protobuf/gRPC/MessagePack/CBOR RPC stack;
- no ORM;
- no general actor framework;
- no embedded JavaScript/Python runtime in core services;
- no hidden global singleton runtime.

### 2.2 Graph/Agent persistence

```text
rusqlite              SQLite
sqlite-vec            derived vector search extension
unicode-normalization NFC normalization
```

SQLite is linked from pinned nixpkgs, not a second bundled SQLite build.

### 2.3 OS integration

```text
zbus                   systemd/logind D-Bus
udev                   libudev bindings
rtnetlink              network state/events
aya                    eBPF program loading/event streams
rustix                 low-level Linux/Unix primitives
nix                    only where an API is absent/clearer than rustix; do not duplicate wrappers
```

### 2.4 Manager remote/security

```text
quinn                  QUIC
rustls                 TLS 1.3
rcgen                  local Omnis host certificate generation
ed25519-dalek          stable host signing identity
```

### 2.5 Control

```text
smithay                compositor/Wayland/DRM/input
calloop                compositor event loop
wgpu                   GPU rendering
cosmic-text            shaping/font fallback
vte                    terminal parser
rustix                 PTY/process primitives
glam                   vectors/matrices/transforms
petgraph               graph traversal/topology
accesskit + accesskit_unix
                       custom Control accessibility publication
image                  image decoding
```

Control does not use egui, iced, GTK, Qt, Electron, Tauri or a browser engine as its primary UI.

---

## 3. Filesystem and service names

These paths/names are exact v0 contracts.

### 3.1 System state

```text
/var/lib/omnis/graph/graph.sqlite3
/var/lib/omnis/cas/blake3/
/var/lib/omnis/candidates/
/var/lib/omnis/backups/graph/
/var/lib/omnis/backups/config/
/etc/omnis/configuration.nix
/etc/omnis/managed.nix
/run/omnis/graph.sock
/run/omnis/os.sock
/run/omnis/manager.sock
/run/omnis/nix-control.sock
```

### 3.2 Per-user state

```text
$XDG_STATE_HOME/omnis/agent/worldline.sqlite3
$XDG_STATE_HOME/omnis/agent/index.sqlite3
$XDG_STATE_HOME/omnis/agent/checkpoints/
$XDG_STATE_HOME/omnis/control/
$XDG_RUNTIME_DIR/omnis/agent.sock
$XDG_RUNTIME_DIR/omnis/control.sock
```

If XDG_STATE_HOME is unset, use `$HOME/.local/state`. If XDG_RUNTIME_DIR is absent, interactive
Omnis user services do not start; do not invent a fallback under /tmp.

### 3.3 systemd units

```text
omnis-graphd.service
omnis-osd.service
omnis-managerd.service
omnis-recovery.target

user:
omnis-agentd.service
omnis-control.service

execution scopes:
omnis-exec-<32 lowercase UUID hex>.scope
```

### 3.4 identities/groups

System users:

```text
omnis-graph
omnis-os
omnis-manager
```

Shared local IPC group:

```text
omnis
```

Sockets are root/owning-service:omnis, mode 0660. User Agent/Control sockets are mode 0600.

---

## 4. Identity, text and time encoding

### 4.1 IDs

All mutable semantic IDs are UUIDv7.

Binary wire representation: exactly 16 bytes in network UUID byte order.
Human representation: lowercase canonical 8-4-4-4-12 hyphenated UUID.

Typed IDs are distinct newtypes:

```text
NodeId EdgeId EventId TransactionId ActivityId ExecutionId WorkerId
TraceId RequestId GenerationId HandleId LeaseId HostId ControlNodeId
```

Never cast between types without an explicit constructor.

### 4.2 artifacts

ArtifactId is exactly BLAKE3-256 of the raw payload bytes, represented as 32 wire bytes or 64
lowercase hex characters.

### 4.3 names

First-party relation/event/capability/kind identifiers are lowercase ASCII dotted names:

```text
omnis.<authority>.<concept>[.<concept>...]
```

Examples:

```text
omnis.capability.model.embed
omnis.event.control.selection
omnis.relation.execution.placed_on
```

Third-party namespaces use reverse-DNS prefixes.

### 4.4 Unicode

Human text is UTF-8. Identifiers supplied as free text are normalized to Unicode NFC before indexing.
Do not lowercase arbitrary Unicode. Exact aliases are case-sensitive unless their owning namespace
defines ASCII case-folding.

### 4.5 timestamps

Wall time: signed i64 nanoseconds since Unix epoch UTC.
Monotonic time: unsigned u64 nanoseconds from CLOCK_MONOTONIC_RAW origin local to producer.

Every event records both when available. Cross-host causal order uses causal parents + ingest
sequence, never wall-clock comparison alone.

---

## 5. SQLite configuration and schemas

Every Omnis SQLite database executes:

```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=FULL;
PRAGMA foreign_keys=ON;
PRAGMA busy_timeout=5000;
PRAGMA wal_autocheckpoint=1000;
PRAGMA temp_store=MEMORY;
PRAGMA trusted_schema=OFF;
```

Page size remains SQLite's database-creation default from the pinned package. Agents do not tune it.

### 5.1 graph writer

One Tokio task owns the only graph write connection.

Writer input channel capacity: 4096 GraphTransactions.
When full, producers await capacity; they do not drop transactions.

Maximum one GraphTransaction:

```text
mutations: 4096
inline event payload total: 64 KiB
preconditions: 1024
causal parents: 256
```

Payload exceeding 64 KiB goes to CAS before transaction commit.

### 5.2 graph revisions

Revision 0 is empty initialized schema.
Each successful GraphTransaction increments revision by exactly 1.
A transaction with no semantic mutation is rejected as InvalidArgument; it does not consume revision.

Historical validity intervals are inclusive `valid_from_revision`, exclusive
`valid_to_revision`. NULL valid_to means current.

### 5.3 graph query limits

Defaults and hard limits:

```text
default result nodes: 1000
hard result nodes: 10000
default traversal depth: 2
hard traversal depth: 8
hard returned edges: 50000
subscription replay window before snapshot fallback: 100000 revisions
```

Traversal is breadth-first.

At each frontier, deterministic edge order is:

1. relation UTF-8 byte lexical order;
2. target/source NodeId byte order according to direction;
3. EdgeId byte order.

If a request exceeds a hard limit, return InvalidArgument; do not silently truncate except where the
request explicitly sets a lower limit.

### 5.4 aliases

Exact alias resolution returns:

- one NodeId: success;
- zero: NotFound;
- more than one: Conflict with all candidate NodeIds.

Fuzzy/search resolution is a separate search operation and never substitutes for exact alias lookup.

---

## 6. CAS

Inline RPC/database payload threshold: 64 KiB.

Objects >= 64 KiB are stored in:

```text
/var/lib/omnis/cas/blake3/<first-2-hex>/<remaining-62-hex>
```

Write algorithm:

1. stream to same-filesystem temporary file;
2. compute BLAKE3 while writing;
3. fsync file;
4. compare requested/derived digest;
5. chmod according to protection class;
6. atomic rename;
7. fsync containing directory.

Existing digest is reused after size/hash verification.

CAS GC runs Sunday 04:17 local time and on manual request.
Mark roots:

- current graph ArtifactRefs;
- unexpired historical graph refs retained by backup policy;
- Agent worldline ArtifactRefs;
- active worker checkpoints;
- active Nix candidate metadata.

Unmarked objects receive a tombstone timestamp; deletion occurs only on the next GC >=7 days later.

---

## 7. Event delivery

### 7.1 producer contract

A first-party producer considers an event published only after graphd confirms durable outbox enqueue.

Graph mutation events are inserted in the same SQLite transaction as the graph mutation.

### 7.2 delivery

Graphd outbox has monotonically increasing u64 ingest_seq.

Agent requests from `after_ingest_seq`.
Graphd delivers in ascending ingest_seq.
Agent transactionally inserts EventId + ingest_seq into worldline.
Only after commit does Agent ACK that exact pair.

Semantics: at-least-once transport, exactly-once worldline identity through EventId primary-key
deduplication.

ACKed outbox rows remain for 24 hours, then are purged hourly.

### 7.3 dense event batching

The following are dense-batch eligible:

```text
pointer motion
touch motion
high-rate sensor/telemetry samples
audio timing samples
render/performance samples explicitly marked lossless
```

Flush a batch on the first condition:

```text
256 items
16 ms since first item
64 KiB uncompressed encoded payload
producer shutdown
```

Every item retains producer sequence, monotonic timestamp, type and payload.
No coalescing/replacement is allowed in a lossless batch.

Render-frame state itself is not an Agent event. Semantic Control mutations and user input events are.

---

## 8. RPC, backpressure and retries

### 8.1 local

Unix SOCK_STREAM + Cap'n Proto RPC.

Connect timeout: 2 seconds.
Handshake timeout: 2 seconds.
Default read/query RPC deadline: 30 seconds.
Discovery RPC deadline: 30 seconds.
No default deadline for long-running execution/build; caller receives ExecutionId/GenerationId and
observes lifecycle asynchronously.

### 8.2 channels

Default bounded channel capacities:

```text
graph writer:              4096
graph subscription:        4096 deltas
Agent ingest internal:     8192 events
Agent ready-worker queue:  1024
Manager execution events:  4096
Control semantic input:    4096
Control graph deltas:      4096
Control render snapshots:  3
```

When a durable semantic queue is full, apply backpressure.
Render snapshots are the exception: retain newest pending snapshot and discard older unrendered
snapshots because graph/control state remains authoritative.

### 8.3 retries

Automatic retry is allowed only for operations classified pure, read_only, idempotent or retry_safe.

Retry delays exactly:

```text
100 ms
250 ms
500 ms
1 s
2 s
```

Maximum 5 retries after the initial attempt.

No automatic retry for opaque/persistent_external effects after request bytes may have reached the
target unless the protocol has an idempotency key and the target guarantees it.

Execution creation uses ExecutionId as idempotency key.

---

## 9. Remote Omnis transport and federation

### 9.1 host identity

Each host generates one Ed25519 keypair at installation.
Private key is protected as a systemd encrypted credential.
HostId is UUIDv7 and is not derived from the key.

Pairing records:

```text
HostId
public key
certificate fingerprint
display name
authority grants
first-seen event
```

### 9.2 network

Native Omnis remote RPC: QUIC using Quinn + rustls, TLS 1.3 only.
ALPN: `omnis/1`.

Default port: UDP 7443.

Listening on non-loopback is disabled until the host is explicitly paired/configured.
Tailscale/VPN is transport only.

### 9.3 graph federation

There is no multi-master replicated graph database in v0.

Logical shared graph across hosts is federated:

- each host graphd is authoritative for its local physical/system facts;
- Manager is authoritative for executions/bindings it owns;
- Agent cognitive state remains on the Agent's home host;
- remote queries use remote graph RPC and preserve original NodeIds;
- remote facts cached locally carry source HostId, source GraphRevision and stale_after;
- default remote cache stale_after = 30 seconds for live physical state, infinite for immutable
  resource/provenance facts;
- cached remote state is never presented as locally authoritative;
- offline remote hosts remain visible with availability=offline and last-known revision/time.

No CRDT is implemented in v0.

---

## 10. Nix and persistent mutation

### 10.1 generated module ownership

`/etc/omnis/managed.nix` is **fully machine generated**. Users do not edit it.

Canonical desired Omnis-managed option assignments live as system.* graph facts.
The Nix fork serializes those typed values into one deterministic generated module sorted by option
path UTF-8 lexical order.

Do not edit arbitrary user Nix AST.

`/etc/omnis/configuration.nix` imports user configuration and `managed.nix`; it is not rewritten on
every mutation.

### 10.2 candidate generation

For persistent mutation:

1. snapshot active graph revision and active NixOS GenerationId;
2. materialize desired option assignments;
3. generate candidate managed.nix;
4. store candidate under `/var/lib/omnis/candidates/<GenerationId>/managed.nix`;
5. run NixOS evaluation;
6. export option provenance;
7. compute closure, derivation, service and semantic diffs;
8. build candidate;
9. run evaluation/runtime-preflight invariants;
10. create graph Generation node;
11. switch with NixOS `switch-to-configuration switch`;
12. reconcile OS observations for max 30 seconds;
13. if required services/invariants fail, invoke previous generation `switch-to-configuration switch`;
14. publish success/failure events;
15. only on success atomically replace active `/etc/omnis/managed.nix`.

No model call exists in steps 3–15.

### 10.3 reconcile timeout

Post-activation required-service/invariant convergence window: 30 seconds.
Poll exact APIs/events, not sleep-only polling, with a final reconciliation at 30 seconds.

---

## 11. OS observation

Startup sequence:

1. enumerate /proc processes;
2. enumerate systemd units;
3. enumerate udev devices;
4. enumerate rtnetlink state;
5. enumerate cgroup tree;
6. enumerate logind sessions;
7. commit one reconciliation transaction per source;
8. attach incremental event streams;
9. start eBPF fork/exec/exit observation;
10. publish `omnis.event.os.reconciled`.

Process eBPF ring buffer: 16 MiB.
On ring-buffer loss counter >0, immediately trigger /proc process reconciliation and publish
`omnis.event.os.observation_gap`.

Filesystem observation is opt-in per declared watched root.
Default watched roots: none.
Repository/workspace Manager bindings request watched roots explicitly.

---

## 12. Security defaults

### 12.1 execution envelope

Non-interactive Agent/Manager executions default to:

```text
filesystem: deny except explicit read-only inputs + explicit writable workdir
network: deny
devices: deny
GPU: deny
protected handles: none
CPU quota: 100% of one logical CPU
memory max: 2 GiB
pids max: 512
wall timeout: none unless capability declares one
```

Bindings declare required expansions. Manager grants only the union of binding requirements and caller
authority.

Interactive user shell is the logged-in user's ordinary authority and is not forced into the worker
default envelope.

### 12.2 network

Network is granted only when:

- binding metadata says network is required; and
- caller authority permits it.

Default allowed destination set is empty.
Provider/API bindings declare exact hostname + port; generic browser/user shell bindings may request
normal user network scope.

### 12.3 credentials

`systemd-creds encrypt --with-key=auto` is the persistent encryption mechanism.
TPM2 is used when available by systemd; otherwise host credential key behavior from pinned systemd is
used.

Default LeaseId TTL: 5 minutes.
Lease ends earlier when ExecutionId completes/cancels.
Secret bytes are never logged, graph-stored, worldline-stored or model-context serialized.

---

## 13. Manager discovery

Exactly this order:

1. existing graph/resource metadata;
2. Nix package/derivation metadata;
3. registered native protocol descriptors;
4. D-Bus/service/desktop metadata;
5. OpenAPI/MCP/LSP/DAP/compiler/runtime metadata;
6. shell completion metadata;
7. `--help` / `help`;
8. man page;
9. source/config/debug-symbol inspection;
10. deterministic active probe;
11. specialist model interpretation if configured;
12. general reasoning model if configured and unresolved semantics remain.

Timeouts per resource:

```text
--help/help: 2 s
man extraction: 2 s
active deterministic probe: 5 s
specialist model: 30 s
reasoning model: 60 s
```

Global discovery concurrency: 16 resources.
Per-resource discovery concurrency: 1.

Failure at one step records provenance/evidence and proceeds to the next unless it is an authority
failure.

---

## 14. Manager resolution and placement algorithm

Hard constraints are applied first. A rejected candidate never receives a score.

For each remaining Binding, calculate features in [0,1]:

```text
quality
latency
cost
locality
warmth
preference
```

Normalization:

- quality: binding/model advertised score, else 0.5;
- latency: among candidates with estimates, min-max inverted; equal values => 1.0; missing => 0.5;
- cost: among candidates with estimates, min-max inverted; equal => 1.0; missing => 0.5;
- locality:
    same process/native library = 1.00
    same host = 0.90
    paired LAN/VPN Omnis host = 0.70
    generic remote host = 0.50
    public remote API/cloud = 0.30
- warmth:
    already-running/loaded = 1.00
    installed/realized but cold = 0.60
    available in local Nix store but not installed = 0.40
    requires build/download = 0.20
- preference:
    explicit preferred binding = 1.00
    explicit neutral = 0.50
    explicit discouraged = 0.00
    unspecified = 0.50

Score:

```text
0.30*quality
+ 0.20*latency
+ 0.15*cost
+ 0.15*locality
+ 0.10*warmth
+ 0.10*preference
```

Round only for display; compare f64 values directly.
Tie within 1e-9 => lexicographically smaller BindingId bytes wins.

Placement uses the same candidate score after capability binding expansion. Privacy/local-only,
hardware capacity, credential availability and authority are hard constraints, never soft score
features.

Resolver returns every considered candidate with rejection reason/features/score.

---

## 15. Manager execution

Local process execution uses a systemd transient scope.

Environment starts empty then receives exactly:

```text
PATH
HOME
USER
LOGNAME
LANG
LC_* present in caller
TERM when PTY attached
TMPDIR allocated per ExecutionId
```

plus binding-declared variables and protected-handle injection.

Working directory must be explicit. If absent, use a fresh private TMPDIR, not caller cwd.

stdout/stderr:

- PTY execution: ordered PTY byte stream artifact + terminal events;
- non-PTY: separate stdout/stderr byte-stream artifacts;
- chunk size: 64 KiB;
- stream flush: 100 ms or chunk full, whichever first.

Cancellation:

1. SIGTERM;
2. wait 5 seconds;
3. SIGKILL entire cgroup;
4. publish final state.

---

## 16. Agent event priority and cognition

### 16.1 base event priority

```text
security/invariant violation     1.00
explicit user semantic request   0.95
persistent mutation failure      0.95
execution/worker failure         0.90
worker/model result              0.75
goal/commitment deadline         0.85
Control submit/action            0.75
Control focus/selection          0.55
file/repo semantic change        0.55
process/service lifecycle        0.45
resource availability change     0.45
dense telemetry batch            0.20
periodic internal timer          0.10
```

Unknown event type base priority: 0.40.

Additional features [0,1]:

```text
goal_relevance
novelty
urgency
```

If a classifier capability is unavailable, goal_relevance=0.5, novelty=0.5, urgency derives only from
explicit deadlines else 0.

Salience:

```text
clamp01(0.55*base + 0.20*goal_relevance + 0.15*novelty + 0.10*urgency)
```

Routing:

```text
>= 0.75 immediate judgement queue
>= 0.40 normal judgement queue
<  0.40 deterministic reducers + memory only
```

An event causally attached to an active user Activity is raised to at least 0.75.

### 16.2 exact fast path

Before any generative model:

1. exact Control command;
2. exact URI/path/NodeId;
3. exact registered capability;
4. deterministic query/transform;
5. classifier;
6. retrieval/reranker;
7. generative reasoning;
8. external agent/search workflow.

Stop at the first level that can satisfy the postcondition.

---

## 17. Agent candidate scheduling

Every judgement cycle includes NullIntention.

Each non-null candidate has normalized features:

```text
goal_progress
information_gain
urgency
risk_reduction
novelty
user_relevance
normalized_cost
```

Priority:

```text
0.30*goal_progress
+0.20*information_gain
+0.15*urgency
+0.15*risk_reduction
+0.10*novelty
+0.10*user_relevance
-0.20*normalized_cost
```

NullIntention priority = 0.15.

Candidates with hard unsatisfied constraints are removed.
Pareto-dominated candidates on benefit dimensions with >= cost are removed.
Remaining candidates sort by priority descending then candidate UUID ascending.

Run candidates only while priority > NullIntention and budgets permit.

### 17.1 concurrency

```text
global active Workers: min(16, max(4, logical_cpu_count))
generative/reasoning model Workers: 4
external coding-agent Workers: 2 per repository
mutating coding-agent Workers: 1 per repository/worktree
local single-GPU non-batching model executions: 1 per GPU
retrieval/classifier Workers: min(8, logical_cpu_count)
```

Repository mutation lock key = Repository NodeId + worktree path identity.

---

## 18. Agent retrieval

Mandatory context is gathered first:

- trigger event;
- causal parents recursively to max 32 events;
- explicit referenced NodeIds/ArtifactIds;
- active Activity/Goal/Commitment state;
- current user request;
- capability schemas selected for the worker.

Retrieval candidates:

```text
FTS5 top 64
vector cosine top 64 when model.embed exists
graph neighborhood depth 2, max 128 nodes
same Activity recent events top 64
procedures matching requested capability top 32
```

Merge lexical/vector lists with Reciprocal Rank Fusion:

```text
RRF score = sum(1 / (60 + rank))
```

Graph/activity/procedure candidates receive a synthetic RRF rank of 1, 8 and 16 respectively when
not already retrieved.

Deduplicate by semantic NodeId/EventId.

If `model.rerank` is available, rerank the top 32 RRF candidates and use reranker order.
Otherwise use RRF score descending then ID bytes ascending.

---

## 19. Agent context compilation

Model context window W is taken from selected Manager model metadata.

Input budget:

```text
if W >= 8192:
  min(floor(W * 0.70), 65536)
else:
  floor(W * 0.60)
```

Output reserve:

```text
if W >= 8192:
  min(floor(W * 0.20), 16384)
else:
  floor(W * 0.30)
```

Remaining context is safety margin.

Input budget allocation after mandatory system/tool headers:

```text
trigger + causal history     20%
active goal/project state    15%
retrieved memories           25%
artifacts/code               30%
negative evidence/attempts   10%
```

If a bucket does not use its allocation, redistribute in this exact order:

1. artifacts/code;
2. retrieved memories;
3. trigger/causal;
4. goal/project;
5. negative evidence.

Truncation within a bucket removes lowest-ranked items first.
Never truncate an artifact in the middle of a UTF-8 codepoint; text excerpts truncate at line
boundaries when possible.

Token counting:

- use provider/model tokenizer binding when advertised;
- otherwise estimate `ceil(UTF8_bytes / 3.5)` and apply additional 15% guard.

The selected source refs and serialized final context are persisted as ContextCapsule provenance.

---

## 20. Agent model-role fallback

Agent core names roles only; Manager selects bindings by §14.

When a role is unavailable:

```text
model.classify  -> deterministic default features in §16
model.embed     -> disable vector retrieval; FTS/graph remain
model.rerank    -> use RRF order
model.generate  -> generative worker is infeasible
model.reason    -> reasoning worker is infeasible
model.vision    -> opaque visual content remains uninterpreted except metadata
model.audio.transcribe -> audio remains artifact-only
agent.code      -> code-agent worker infeasible; deterministic code tools remain
```

No remote model provider is enabled by default.
No credential is generated or requested during boot.
The system remains deterministic-operable without any model binding.

---

## 21. Agent consolidation/internal time

Physics emits internal timer events; it does not encode "improve yourself" behavior.

Timer events:

```text
omnis.event.timer.second      every 1 s
omnis.event.timer.minute      every 60 s
omnis.event.timer.hour        every 3600 s
```

Only minute/hour events enter normal cognition by default; second events are reducer-only unless a
registered commitment depends on them.

Memory consolidation becomes a candidate when either:

- 5000 new worldline events since last successful consolidation; or
- 6 hours since last successful consolidation.

It is infeasible while:
- explicit user request queue is non-empty; or
- CPU load > 70%; or
- selected local GPU memory pressure > 80%.

It must run at least once every 24 hours unless Agent is stopped.

Consolidation never deletes worldline events.

---

## 22. Control input routing

For a submitted primary-input string, exact precedence is:

1. empty/whitespace => no-op event;
2. string begins with `omnis://` => Omnis URI resolver;
3. valid explicit URI with scheme => navigation/open;
4. hostname-like token matching ASCII domain + optional path => prepend https:// and navigate;
5. existing absolute/relative filesystem path after shell-style tilde expansion => open/materialize;
6. input begins `@` followed by exact graph alias/UUID => focus graph identity;
7. valid shell syntax containing shell operator/redirection/substitution => persistent PTY shell;
8. first shell word resolves as shell builtin/function/alias or executable on current shell PATH =>
   persistent PTY shell;
9. exact registered capability name => Manager resolve/execute;
10. exact Control command name => Control structural operation;
11. otherwise => OmnisAgent semantic request event.

Do not use an LLM to choose between steps 1–10.

If an exact lookup at a higher step is ambiguous, show the ambiguity; do not fall through to Agent.

---

## 23. Terminal contract

Default shell is the account login shell from passwd/NixOS user configuration. If absent, use
`pkgs.bashInteractive`. Per-user `omnis.control.users.<name>.shell` overrides it.

PTY terminal supports:

```text
UTF-8
ECMA-48/ANSI basics handled by vte
24-bit truecolor
OSC 8 hyperlinks
bracketed paste
focus reporting
standard mouse reporting
alternate screen
job control/signals
```

Scrollback: 100000 logical lines per terminal.
Memory scrollback beyond 100000 is discarded oldest-first; PTY byte-stream artifact can retain full
session when recording is enabled.

Kitty graphics and Sixel are not implemented in v0. Unsupported graphics sequences are ignored
according to parser behavior and emit one rate-limited diagnostic event per terminal/session/minute.

---

## 24. Control render scheduling

Compositor/input thread never blocks on graph RPC, Agent or model work.

Render policy:

- render on output damage, animation, cursor movement requiring redraw, or new scene revision;
- synchronize presentation to DRM/output vblank through Smithay;
- maximum 3 GPU frames in flight;
- render-snapshot queue capacity 3;
- when full, replace the oldest unsubmitted render snapshot with the newest;
- never discard committed Control state or semantic input.

Texture cache budget: min(1 GiB, 25% of detected dedicated GPU memory), floor 128 MiB.
Evict least-recently-used resources not referenced by current/in-flight frames.

Glyph atlas starts 2048x2048 and grows to max 8192x8192 per scale class; LRU evicts unused glyphs.

---

## 25. Control graph layout

Maximum directly materialized individual graph nodes per viewport: 5000.
Above 5000, clustering is mandatory before layout.

### 25.1 algorithm selection

Use Sugiyama layout when:

- selected lens is causal/workflow/system-dependency; and
- the selected relation subgraph is acyclic after collapsing strongly connected components.

Otherwise use ForceAtlas2.

### 25.2 Sugiyama constants

1. collapse SCCs;
2. layer assignment: longest-path from roots;
3. crossing minimization: 8 alternating barycentric sweeps;
4. horizontal node gap: 32 logical px;
5. vertical layer gap: 64 logical px;
6. expand SCC members internally using circular layout radius `24 + 12*n` px;
7. edge routing: cubic Bezier with control points at 40%/60% layer distance.

### 25.3 ForceAtlas2 2D

```text
scaling = 2.0
gravity = 1.0
strong gravity = false
lin-log mode = true
edge weight influence = 1.0
Barnes-Hut enabled for n >= 512
Barnes-Hut theta = 1.2
initial settle iterations = 300
interactive iterations per frame = 4
stop when mean displacement < 0.01 logical px for 30 consecutive iterations
```

Random initial positions are forbidden. Initial position is deterministic from BLAKE3(NodeId):
two signed normalized u32 coordinates mapped to [-100,100].

### 25.4 ForceAtlas2 3D

Same parameters, generalized to xyz.
Initial z is derived from the third u32 of BLAKE3(NodeId).

Lens constraints:

- temporal lens: x is normalized wall time; y is Activity lane; z is causal depth;
- physical lens: x/y use force layout inside host cluster; host clusters are ordered on x by HostId;
  z is process/cgroup depth;
- all other lenses use unconstrained 3D ForceAtlas2.

2D and 3D maintain separate cached positions keyed by WorkspaceId + LensId but share selection, focus,
timeline frontier and graph identities.

---

## 26. Control semantic LOD

Projected node diameter:

```text
< 6 px    cluster/aggregate only
6-20 px   icon/shape + short label
20-80 px  node card + primary relations/actions
>80 px    full inline inspector eligible
```

Labels are hidden when their bounding boxes would overlap more than 20%; keep focused/selected labels
regardless.

Cluster identity is derived, not semantic: BLAKE3(sorted member NodeIds + lens + graph revision).
Clusters never masquerade as domain NodeIds.

---

## 27. Control accessibility

Every semantic Control node publishes AccessKit role/name/value/actions derived from graph/control
state.

Focused Control semantic node must have an accessibility node.
NativeSurface delegates its internal subtree to the native application accessibility bridge when
available.

CI acceptance includes an accessibility tree snapshot for:
- shell;
- graph node;
- graph edge inspector;
- native surface container;
- mode switch.

---

## 28. Backup and recovery

### 28.1 graph

Online SQLite backup:

- before every schema migration;
- before persistent Nix generation activation;
- daily at 03:17 local time.

Retention:

```text
7 daily
4 weekly (Sunday backup)
```

Backup integrity check: `PRAGMA integrity_check` must return ok before backup is marked valid.

### 28.2 Agent worldline

Online backup daily at 03:47 local time and before schema migration.
Retention: 14 daily + 8 weekly.

### 28.3 corruption

Graph corruption => `omnis-recovery.target`.
Recovery sequence:

1. preserve corrupt DB copy;
2. restore newest valid backup;
3. replay/reconcile OS physical state;
4. reconcile Manager executions;
5. reconnect Agent outbox/worldline;
6. publish recovery-gap event.

Worldline corruption:

1. stop Agent only;
2. preserve corrupt DB;
3. restore newest valid backup;
4. replay graphd outbox events still available;
5. mark unavailable historical range explicitly;
6. never fabricate events.

---

## 29. Schema migration

Each DB has integer `user_version`.

Migration rules:

- only forward migrations in normal boot;
- one migration per integer version;
- migration runs inside exclusive startup lock;
- backup first;
- migration transaction commits atomically;
- failure restores old file and service remains stopped;
- no automatic downgrade;
- downgrade requires booting older generation with its own compatible backup.

Cap'n Proto:
- field ordinals never reused;
- breaking semantic change increments protocol major;
- minor change is additive;
- major mismatch => explicit incompatible error before any effectful method.

---

## 30. Logging and privacy

Rust default log level: INFO.
Debug can be enabled per unit with `RUST_LOG`.
Logs go to journald only in v0; no cloud telemetry/exporter is enabled by default.

Every log record includes when applicable:

```text
component
build_id
TraceId
RequestId
ExecutionId
ActivityId
GraphRevision
```

Never log:
- secret bytes;
- full model prompt/context;
- user file contents;
- raw credential-bearing headers;
- protected artifact bodies.

Model request/response bodies live only as protected ArtifactRefs when retention policy allows them.

---

## 31. Model/inference retention

Default:

- model invocation metadata retained permanently in Agent worldline;
- serialized prompt/context artifact retained 30 days;
- model output artifact retained 30 days unless promoted into project/memory evidence;
- protected/sensitive artifact can specify shorter retention;
- secrets are never stored in these artifacts.

A daily 04:47 retention job removes expired artifact roots; CAS GC performs physical deletion under §6.

---

## 32. Repository/worktree execution

Coding workers never concurrently mutate the same worktree.

Default code-work workflow:

1. bind Repository NodeId;
2. create/reuse dedicated Git worktree per WorkerId;
3. branch `agent/<short-worker-id>/<slug>`;
4. give worker RW only to that worktree;
5. run tests there;
6. produce patch/commit artifacts;
7. integration/merge remains a separate capability/effect.

A worker cannot push/merge unless its binding and authority explicitly include the corresponding VCS
capability.

---

## 33. HTTP/API and browser defaults

HTTP requests:

- connect timeout 5 s;
- response-header timeout 30 s;
- idle body timeout 30 s;
- redirect limit 10;
- user agent `Omnis/<release>`;
- TLS verification required;
- no plaintext HTTP downgrade from HTTPS redirect.

Browser:
- do not embed Chromium;
- launch configured browser resource as normal Wayland client;
- structured preference order: CDP if browser exposes it, then WebDriver BiDi, then accessibility,
  then delegated surface/input;
- exact URL navigation bypasses Agent.

---

## 34. Acceptance performance budgets

These are v0 acceptance thresholds on the reference test VM/workstation, not universal promises.

Local graph operations with warm page cache:

```text
single-node get p95       < 5 ms
depth-2 <=1000-node query < 50 ms p95
transaction <=100 muts    < 20 ms p95
subscription delta emit   < 20 ms p95 after commit
```

Control:
- no synchronous model call on compositor/render thread;
- input-to-Control-state update p95 < 16 ms excluding external effect;
- maintain output refresh rate for static/simple workspace when GPU supports it;
- graph layout work is incremental and may not block compositor thread >2 ms per frame.

Event:
- durable local enqueue p95 < 20 ms for <=64 KiB;
- Agent outbox ingest begins within 100 ms while Agent healthy.

Tests fail if architecture code introduces blocking model/network work in these critical paths.

---

## 35. Test toolchain and gates

Rust repos run exactly:

```text
cargo fmt --check
cargo clippy --workspace --all-targets --all-features -- -D warnings
cargo test --workspace --all-features
cargo doc --workspace --no-deps
nix flake check
```

Property tests use proptest.
Fuzz targets use cargo-fuzz/libFuzzer.
No code-coverage percentage gate in v0; behavior gates are scenario-based.

Umbrella integration tests use real processes and Unix sockets once both endpoints exist.

Required acceptance scenarios are those in `docs/IMPLEMENTATION.md §17` plus:

1. Agent offline for 10 minutes while Control/OS/Manager emit events, then exact semantic catch-up;
2. duplicate EventEnvelope delivery produces one worldline EventId;
3. Manager retry of same ExecutionId starts one scope;
4. graphd crash during transaction produces either full old or full new revision, never partial;
5. Control switch 2D→3D→2D preserves selected NodeIds/focus/lens/frontier;
6. remote host disconnect marks cached live state stale/offline without deleting semantic identity;
7. protected credential never appears in graph DB, worldline DB, journald or model context;
8. failed Nix generation activation restores prior generation and records failure causally.

---

## 36. Configuration defaults

These are defaults, not suggestions:

```text
omnis.enable = true

omnis.graph.enable = true
omnis.graph.dataDir = /var/lib/omnis/graph
omnis.graph.writerQueue = 4096
omnis.graph.inlinePayloadMax = 65536
omnis.graph.query.defaultLimit = 1000
omnis.graph.query.hardLimit = 10000

omnis.os.enable = true
omnis.os.observe.systemd = true
omnis.os.observe.udev = true
omnis.os.observe.rtnetlink = true
omnis.os.observe.processes = true
omnis.os.observe.watchedFileScopes = []

omnis.manager.enable = true
omnis.manager.discovery.enable = true
omnis.manager.discovery.concurrency = 16
omnis.manager.remote.listen = false
omnis.manager.remote.port = 7443

omnis.agent default = enabled per explicitly declared Omnis interactive user
omnis.agent.modelProviders = []
omnis.agent.maxWorkers = formula in §17.1

omnis.control default = enabled per explicitly declared local interactive Omnis user
omnis.control.defaultMode = 2d
omnis.control.xwayland.enable = true
omnis.control.scrollbackLines = 100000

omnis.security.protectedHandles.enable = true
omnis.security.executionIsolation.enable = true
omnis.security.defaultWorkerNetwork = deny
```

No undeclared user automatically gets Agent/Control state.

---

## 37. Explicit v0 non-features

Implementation agents do not add these while implementing v0:

- custom Linux kernel;
- PID1 replacement;
- distributed/multi-master graph database;
- CRDT graph synchronization;
- custom browser engine;
- custom shell language;
- second TUI renderer;
- web/Electron/Tauri primary desktop;
- Kubernetes dependency;
- cloud control plane;
- mandatory account/login service;
- mandatory remote model provider;
- autonomous plaintext secret storage;
- direct LLM participation in Nix evaluation, boot, compositor frame loop or enforcement path;
- semantic state duplicated into component-local authoritative databases;
- compatibility layer for unimplemented historical Omnis APIs.

Adding any item requires a later ADR.

---

## 38. Implementation task rule

A coding agent assigned a v0 task follows this order:

1. read `ARCHITECTURE.md`;
2. read `docs/IMPLEMENTATION.md`;
3. read this document;
4. read the owning subsystem spec;
5. read `docs/PROTOCOLS.md` and relevant `protocol/*.capnp`;
6. implement exactly the specified mechanism;
7. add/execute the specified tests;
8. if any required choice is absent, **do not choose**—file a specification defect.

"Best judgment", "reasonable default", "equivalent library", "simpler alternative", "temporary
fallback" and "we can decide later" are not valid implementation authority.

---

## 39. Precedence

If active docs appear to conflict for v0 implementation mechanics:

1. `ARCHITECTURE.md` controls semantic/product invariants;
2. this document controls concrete algorithm/default/mechanism decisions;
3. `docs/IMPLEMENTATION.md` controls process/repository/substrate topology;
4. subsystem specs control subsystem semantics;
5. `docs/PROTOCOLS.md` + `protocol/*.capnp` control wire compatibility;
6. ADR-0023/0024/0025 explain why;
7. roadmap controls sequence only.

An implementation agent does not resolve a real contradiction itself. It reports the conflicting
clauses and waits for a documentation fix.
