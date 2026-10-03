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


---

## 40. Package persistence scopes

Package realization has exactly three scopes:

```text
execution   ephemeral realization for one Execution/Activity
user        persistent package for one user
system      persistent package/service/configuration for the machine
```

Default interpretation:

- "run/use X" => execution;
- "install X" with no scope => user;
- "install X system-wide", service enablement, driver/kernel/network/security changes => system.

User profile path:

```text
/nix/var/nix/profiles/per-user/<user>/omnis
```

Manager operates it through Nix profile APIs and records profile generation/resource relations in the
graph. It does not mutate the user's unrelated default Nix profile.

System package persistence is emitted through `environment.systemPackages` in generated
`/etc/omnis/managed.nix`.

Execution scope creates/realizes the closure and supplies it to the Execution environment without
adding a persistent profile root after the Activity finishes unless another graph root references it.

---

## 41. Nix update, generation and GC policy

No automatic upstream update exists in v0.

`omnis system update` performs an explicit candidate update of the pinned OmnisOS/nixpkgs inputs,
shows source/closure/semantic diff, builds, validates and activates using the normal generation path.

Successful system generations retained as GC roots: newest 10 plus current, even if older.
Failed candidate generations/artifacts retained 7 days.

Nix GC timer: Sunday 05:17 local time.

Before GC:

1. collect active system generation roots;
2. newest 10 successful rollback roots;
3. all Omnis-managed user profile roots;
4. active/candidate execution roots;
5. model/artifact store paths referenced by current Manager graph state;
6. call Nix GC.

Manager emits planned deletion set before GC and resulting deletion event after GC.

---

## 42. Inference gateway and universal model-event interception

`omnis-managerd` exposes a loopback-only inference gateway:

```text
127.0.0.1:7331
[::1]:7331
```

It serves:

- OpenAI-compatible HTTP endpoints under `/v1/*`;
- Anthropic-compatible endpoints under `/anthropic/v1/*`.

It never listens externally in v0.

Every gateway request is processed in this order:

1. authenticate local execution identity/HandleId;
2. parse provider-compatible request;
3. create `omnis.event.inference.request` with metadata + protected ArtifactRef for request body;
4. ask Agent context service for injection material when the calling Execution is attached to an
   Omnis Worker/Activity and injection is enabled;
5. inject context using §43;
6. resolve concrete model/provider binding through Manager;
7. execute upstream request using protected provider credential;
8. stream response to caller while recording protected response artifact;
9. enqueue `omnis.event.inference.response` or failure event;
10. update invocation cost/token/latency facts.

Provider request bodies and responses are never written inline to ordinary logs.

External harness adapters set their supported provider base URL/environment to this gateway. A
built-in harness binding that can route through this gateway must do so; direct provider access is
not allowed for that binding.

If a harness cannot be routed or hooked, its binding is marked
`memory_coverage = process_only`, not `full`.

---

## 43. Context injection into external harnesses

Coverage tiers are exact:

```text
full          native pre-model hook + inference gateway
gateway       inference gateway only
hook          native harness hook only
process_only  process/PTY/tool events only
```

Manager exposes this tier in Binding metadata.

Injection precedence:

1. harness-native context/pre-prompt hook when the pinned harness version supports one;
2. otherwise inference-gateway injection.

Gateway injection rules:

- OpenAI chat-compatible request: prepend one system/developer message named logically
  `omnis_context` after provider-required system messages and before user conversation;
- Anthropic-compatible request: append an `<omnis-context>...</omnis-context>` block to the system
  field;
- never rewrite tool results or user content;
- inject one context capsule per model request;
- max injected text = min(25% input budget, 16384 tokens);
- include stable NodeId/EventId citations inside the capsule serialization;
- omit protected material disallowed for the resolved provider.

The Agent context service returns an empty capsule when no relevant memory is activated; Manager does
not manufacture filler context.

Built-in Claude Code, Codex and OpenCode adapters must implement the highest coverage tier supported
by their pinned versions. Their adapter tests assert the tier; implementers do not choose a weaker
tier for convenience.

---

## 44. Desktop compatibility services

OmnisControl owns compatibility bridges required by ordinary Linux desktop applications rather than
requiring a second desktop shell.

### 44.1 XDG portals

OmnisOS runs `xdg-desktop-portal`.
OmnisControl ships `xdg-desktop-portal-omnis`.

v0 portal interfaces:

```text
OpenURI
FileChooser
Screenshot
ScreenCast
Settings
Inhibit
GlobalShortcuts
```

Behavior:

- OpenURI -> Manager/Control unified resolver;
- FileChooser -> Control resource/file picker backed by filesystem + graph;
- Screenshot -> Control compositor render capture;
- ScreenCast -> Control compositor DMA-BUF/PipeWire stream;
- Settings -> Control theme/appearance values;
- Inhibit -> graph-visible inhibition resource;
- GlobalShortcuts -> Control input binding service.

Unsupported portal interfaces return the standard NotImplemented/Unavailable response; do not launch
another desktop portal backend automatically.

### 44.2 clipboard/drag-drop

Implement Wayland data-device and primary-selection protocols.

Clipboard history is **off by default**.
Clipboard contents are events only when the user/Agent performs a semantic paste/copy operation inside
first-party Control; passive clipboard bytes are not persisted to worldline.

Protected values with `control-hidden` or `execution-handle-only` cannot be put on clipboard.

### 44.3 notifications

Control provides `org.freedesktop.Notifications` on the user D-Bus.

A notification becomes a presentation graph node + Agent event with app/resource identity, summary,
body, actions and lifecycle. It is shown in the current workspace as a non-modal overlay for 5
seconds unless urgency=critical, which remains until dismissed/actioned.

Maximum visible simultaneous notifications: 3; additional notifications queue FIFO.
Notification history persists as events, not as a separate notification database.

### 44.4 status/tray

Implement StatusNotifierWatcher/StatusNotifierItem bridge.
Tray items are graph resources materialized in a compact Control region only when at least one item
exists. There is no permanent taskbar solely for tray hosting.

---

## 45. Audio, media and screen streams

PipeWire is the v0 audio/video stream substrate.

OmnisControl/Manager bind:

- default audio sink/source;
- application streams;
- ScreenCast portal streams;
- camera/microphone resources.

Wire audio/media bytes do not travel through Cap'n Proto; graph stores stream/resource identity and
PipeWire node identifiers as realizations.

Agent receives lifecycle/semantic stream events, not every PCM/video frame by default.
If a Worker explicitly requests raw media cognition, Manager binds the stream to the selected
vision/audio model capability and resulting observations enter the normal event path.

---

## 46. Input/gesture contract

### 46.1 2D

```text
left click             select/focus
shift+left click       toggle selection membership
left drag node         pin/move selected semantic/control node
left drag background   pan
wheel/trackpad scroll  pan
ctrl+wheel/pinch       zoom around pointer
double click node      focus + semantic inspect level
right click            context actions from graph capabilities
Esc                    back one focus/navigation level
Alt+Left/Right         global back/forward
Ctrl+L                 focus primary input/address surface
Ctrl+Space             focus primary input/semantic command surface
```

### 46.2 3D

```text
left click             select/focus
left drag selected     move/pin in current layout plane/constraint
right drag             orbit camera
middle drag            pan camera
wheel/pinch            dolly/zoom
double click node      fly/focus on node
F                      frame current selection
2                      switch same workspace to 2D
3                      switch same workspace to 3D
```

Touch maps one-finger to select/pan contextually, two-finger to pan/zoom, and three-finger horizontal
swipe to back/forward.

All semantic gestures emit Control events.

---

## 47. Appearance and theme

Theme format is VS Code color-theme JSON, preserving the accepted historical decision where compatible
with the reset.

Built-in default theme name: `Omnis Dark`.

Default appearance:

```text
dark background
font UI: system sans through fontconfig/cosmic-text
font monospace: system monospace through fontconfig/cosmic-text
base UI scale: compositor output scale
animation duration: 180 ms
reduced-motion: follows portal/system setting; when true durations = 0
corner radius: 8 logical px
spacing unit: 4 logical px
```

Do not hard-code font family names; fontconfig result is deterministic for installed system
configuration.

Theme changes are presentation graph state and apply live to terminal/graph/Control chrome, not to
native client-rendered surfaces.

---

## 48. Native surface policy

Wayland/XWayland clients run unmodified.

Toplevel behavior:

- client-side decorations are preserved;
- if client supplies no decorations and xdg-decoration negotiates server-side, Control draws a
  minimal title/control region;
- native surface gets one stable graph semantic identity for its lifetime;
- closing the toplevel ends its active validity but does not delete historical worldline identity;
- focus follows explicit user/Agent Control focus, never pointer-enter alone;
- new application surface is inserted beside the currently focused view in 2D and into the focused
  workspace cluster in 3D;
- fullscreen maps to the current output but remains graph-addressable;
- popups/subsurfaces remain owned by the parent NativeSurface.

Direct scan-out is enabled only when Smithay reports eligibility and no Control overlay/interception
requires composition.

---

## 49. Browser resource behavior

Default browser resource is the user's `xdg-settings get default-web-browser` resolution if that
desktop entry exists; otherwise the first Manager binding for `browser.navigate` by normal §14
resolution.

URL-like input from §22 opens in the currently focused browser resource if one exists; otherwise
Manager launches the default browser binding.

Structured browser control preference is fixed:

1. CDP when the selected browser advertises it;
2. WebDriver BiDi;
3. accessibility tree;
4. delegated native surface + synthetic input only for operations with no structured binding.

Synthetic input against browser content must record that lower-confidence binding in provenance.

---

## 50. Configuration/settings mutation

There is no separate privileged Settings application.

All settings are one of:

- persistent NixOS options -> OmnisOS generation path;
- Manager resource/binding preferences -> Manager-owned graph/config;
- Agent cognitive/user preference memory -> Agent-owned graph;
- Control presentation preference -> Control-owned graph.

Control can materialize a settings view from those graph schemas.
CLI uses the same owning RPC.

A settings mutation is never written directly to a component's private file when an owning graph/Nix
contract exists.

---

## 51. Shutdown and suspend

System shutdown:

1. systemd stops user Control;
2. Control commits pending presentation mutations and closes native surfaces;
3. Agent checkpoints active durable workers and worldline transaction;
4. Manager marks/cancels non-persistent local executions according to binding lifecycle;
5. osd stops incremental observers;
6. graphd drains writer queue and checkpoints WAL;
7. systemd continues shutdown.

Maximum graceful stop timeout per Omnis service: 15 seconds; then systemd kill policy applies.

Suspend:

- Control stops rendering and records suspend event;
- Agent receives suspend event and stops starting new local work;
- Manager pauses/cancels executions only if their binding declares suspend-sensitive;
- on resume OS performs process/device/network reconciliation before publishing resume-complete event.

---

## 52. Specification completeness invariant

For every observable v0 behavior, one of these must exist before implementation:

- an exact clause in active normative docs;
- an exact protocol schema;
- an exact configuration default;
- an exact acceptance test.

If none exists, the correct implementation action is **SpecificationDefect**, not an implementation
choice.

The umbrella CLI command `omnis spec check` will eventually automate this mapping, but its absence
does not weaken the rule.


---

## 53. Privileged execution launch path

OmnisManager owns the semantic Execution. OmnisOS owns physical process creation and sandbox
enforcement.

`omnis-managerd` **does not** call systemd `StartTransientUnit` directly.

Exact path:

1. Manager resolves Binding, placement and ExecutionId;
2. Manager asks OmnisOS for validated ExecutionEnvelope;
3. Manager sends `PhysicalLaunchRequest` to `omnis-osd`;
4. osd validates peer is managerd, envelope ownership and executable/store-path identity;
5. osd creates `omnis-exec-<uuidhex>.service` with systemd `StartTransientUnit`;
6. systemd starts the target under requested UID/GID;
7. osd publishes process/cgroup facts;
8. Manager tracks semantic Execution state from OS events;
9. cancellation/signals go Manager -> osd -> systemd;
10. outputs are streamed back through the typed OS process-stream capability and persisted by Manager.

`omnis-osd` runs as root because it is the physical enforcement authority. Its service unit uses
`NoNewPrivileges=false` only because it must create lower-privilege units; it exposes no generic
shell/exec method outside the typed Manager-only launch API.

Graphd and managerd remain unprivileged dedicated users.

---

## 54. Execution sandbox systemd properties

Every non-interactive restricted Execution transient service starts from these properties:

```text
Type=exec
UMask=0077
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=tmpfs
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectKernelLogs=yes
ProtectControlGroups=yes
ProtectClock=yes
RestrictRealtime=yes
LockPersonality=yes
RestrictSUIDSGID=yes
RemoveIPC=yes
CapabilityBoundingSet=
AmbientCapabilities=
KillMode=control-group
TimeoutStopSec=5s
TasksMax=512
MemoryMax=2G
CPUQuota=100%
```

Filesystem grants are translated to:

- read-only roots -> `BindReadOnlyPaths=`;
- writable roots -> `BindPaths=`;
- workdir -> explicit writable bind;
- no implicit HOME visibility.

Network:

- deny => `PrivateNetwork=yes`, `RestrictAddressFamilies=AF_UNIX`;
- allowed internet/user network => `PrivateNetwork=no`;
- hostname/port constrained binding => `PrivateNetwork=no`,
  `IPAddressDeny=any`, `IPAddressAllow=<resolved IPs>`, plus the binding port enforced by the
  Omnis cgroup-connect eBPF filter.

Hostname allowlists resolve immediately before launch; DNS answers are frozen for that Execution.
Long-running bindings that declare DNS refresh update the allow map every 60 seconds.

Devices:

- `DevicePolicy=closed`;
- add `DeviceAllow=` for each explicitly granted device;
- GPU binding adds only the selected DRM/render or accelerator device nodes.

System calls:

```text
SystemCallFilter=~@mount @reboot @raw-io @swap
```

A Binding requiring a syscall in those denied groups must declare it as a hard execution requirement;
OmnisOS then records the exact exception in the envelope and event provenance.

`MemoryDenyWriteExecute=no` in v0 because JIT runtimes/agent harnesses are legitimate resources.
No binding can gain Linux capabilities unless an explicit privileged capability is added to the
ontology by a spec change.

---

## 55. Physical process I/O

OmnisOS creates pipes or a PTY before launching the transient service.

Typed OS stream interfaces:

```text
ByteSource.read(max <= 65536)
ByteSink.write(chunk <= 65536)
PtyStream.read/write/resize/close
```

PTY resize uses rows/columns + pixel width/height.

Backpressure:
- per stream buffer = 1 MiB;
- when full, producer process blocks through normal pipe/PTY backpressure;
- semantic output is never dropped by Omnis.

Manager simultaneously chunks stdout/stderr/PTY recording into CAS-backed artifacts using the
64 KiB / 100 ms rule.

---

## 56. Graph clustering above direct-layout limit

When a projection contains >5000 visible semantic nodes, clustering is deterministic.

Order:

1. apply lens-specific mandatory grouping:
   - physical: HostId;
   - activity: ActivityId;
   - execution: Execution placement HostId then ActivityId;
   - presentation: WorkspaceId;
2. if any resulting group still has >5000 nodes, apply deterministic Louvain modularity clustering;
3. relation edge weight = 1.0 unless ontology marks an explicit weight later;
4. Louvain resolution = 1.0;
5. process nodes in NodeId byte order;
6. move a node only for strictly positive modularity gain >1e-9;
7. equal gains choose cluster whose smallest member NodeId is lexicographically smallest;
8. repeat passes until total modularity gain <1e-6;
9. recursively cluster oversized communities.

Cluster render identity is the derived BLAKE3 identity defined in §26 and is never written as a
semantic graph NodeId.

---

## 57. Default boot workspace

First interactive login creates exactly one persistent Workspace when none exists.

Initial workspace:

```text
mode = 2d
lens = ["physical","activity","presentation"]
focus = local Host NodeId
central view = Terminal/InputSurface
terminal = user's configured login shell
graph context = local Host + Omnis core services + active Agent/Activity nodes, depth 1
timeline frontier = live
```

The Terminal view occupies 70% width and full height initially.
The graph context occupies the remaining 30% on the right.
Below 900 logical px output width, graph context starts collapsed and Terminal occupies full width.

No dock, taskbar, app launcher or wallpaper surface is created by default.

Opening an application inserts its NativeSurface beside the currently focused view using the same
split algorithm:

- landscape workspace: split horizontally 50/50;
- portrait workspace: split vertically 50/50.

User/Agent rearrangement persists as Control graph state.

---

## 58. CLI grammar

The `omnis` CLI is exact:

```text
omnis graph get <omnis-uri>
omnis graph query --root <uri> [--relation <name>] [--depth N] [--limit N]
omnis graph watch [--root <uri>]

omnis system status
omnis system diff <generation>
omnis system plan <nix-option-assignment>...
omnis system build <generation>
omnis system activate <generation>
omnis system rollback <generation>
omnis system update

omnis manager resources [query]
omnis manager capabilities [query]
omnis manager discover <uri>
omnis manager resolve <capability> [--constraint key=value]...
omnis manager run <capability> [--input <path-or-json>]
omnis manager executions [--active]
omnis manager models
omnis manager harnesses
omnis manager host pairing-code
omnis manager host pair <host-or-ip> --code <base64url>
omnis manager host unpair <host-uuid>

omnis agent ask <text...>
omnis agent memory search <text...>
omnis agent events [--after <event-uri>]
omnis agent activities
omnis agent workers
omnis agent explain <omnis-uri>

omnis control open <address-or-uri>
omnis control focus <omnis-uri>
omnis control mode <2d|3d>
omnis control lens <name>...
omnis control workspace

omnis ingest <path>...
omnis trace <trace-uri>
omnis spec check
```

Global flags:

```text
--json        canonical JSON debug/export form
--timeout     override finite query timeout only
--socket      explicit endpoint for debugging; not persisted
```

Human output is concise tables/text. `--json` emits UTF-8 JSON with stable snake_case field names
derived from protocol fields. Exit status: 0 success, 2 invalid input, 3 not found, 4 conflict,
5 unauthorized, 6 unavailable, 7 execution/build failure, 8 protocol incompatibility,
9 specification defect.

CLI never reads/writes SQLite directly.

---

## 59. Additional Control/editor/media dependency families

Add to the frozen dependency policy where used:

```text
ropey                 text rope
tree-sitter           syntax trees
pulldown-cmark        Markdown
gstreamer             video/audio playback bindings
mime_guess            deterministic MIME hinting before libmagic binding
```

System libraries come from the pinned nixpkgs revision.

For MIME detection, order is:
1. explicit protocol/content type;
2. Nix/package metadata;
3. filename extension via mime_guess;
4. libmagic Manager binding;
5. application/octet-stream.

---

## 60. External harness version/package policy

Omnis does not vendor or silently download proprietary/external coding harnesses.

Built-in harness adapters bind an executable resource discovered from:

1. an existing Nix store/profile resource;
2. PATH;
3. an explicitly declared executable path.

The adapter records `--version` output and refuses unsupported major versions with
`incompatible`, rather than guessing flags.

Installing a harness is a normal package/resource operation under §40. If pinned nixpkgs contains the
requested package, use it. Otherwise a package definition with exact source version/hash must be added
to OmnisManager/OmnisOS in a reviewed change before installation; runtime curl-to-shell installers are
forbidden.

Adapters are tested against explicit supported version fixtures. A new harness major version requires
updating the adapter compatibility fixture before it can claim full/hook/gateway coverage.

---

## 61. `omnis spec check`

`omnis spec check` is required in the first umbrella CLI implementation.

It validates:

1. `spec/v0.toml` parses and has the expected schema version;
2. `spec/ontology.toml` contains no duplicate first-party identifier;
3. every `omnis.*` identifier referenced by protocol/schema/prompt source is registered or is a
   documented property prefix;
4. all six Cap'n Proto schema files exist and compile;
5. all three SQL v1 schemas execute on an empty SQLite database;
6. every prompt listed in the prompt registry exists and contains its exact version header;
7. Nix option documentation and example paths exist in the option contract;
8. scalar constants duplicated in generated language outputs match `spec/v0.toml`;
9. no active normative document contains `TBD`, `TO BE DECIDED`,
   `IMPLEMENTER MAY CHOOSE`, `IMPLEMENTATION AGENT MAY CHOOSE`,
   `CHOOSE WHICHEVER`, or `IMPLEMENTATION-SPECIFIC UNTIL`.

Exit 0 only if all checks pass; otherwise exit 9.


---

## 62. Static and dynamic identity derivation

Dynamic semantic identities use UUIDv7.

Registry-defined immutable concept nodes use deterministic UUIDv5 so all hosts refer to the same
concept NodeId without prior synchronization.

UUIDv5 algorithm:

```text
namespace = UUID namespace URL = 6ba7b811-9dad-11d1-80b4-00c04fd430c8
name = UTF-8 bytes of "urn:omnis:v0:" + canonical_identifier
```

Use this only for registry concepts that are materialized as nodes, including first-party Capability
nodes. Example conceptual input:

```text
urn:omnis:v0:omnis.capability.model.embed
```

Kinds, relations, event type names and property keys remain canonical strings and do not need NodeIds
unless explicitly materialized as graph resources.

Dynamic objects—including hosts, processes, resources discovered from reality, bindings,
executions, events, activities, workers, memories, workspaces and surfaces—use UUIDv7.

### 62.1 Host identity

On the first successful OmnisOS activation:

1. if `/var/lib/omnis/host-id` exists, parse exactly one canonical UUIDv7;
2. otherwise generate one UUIDv7 using kernel CSPRNG;
3. write temp file, fsync, rename atomically, fsync directory;
4. owner root:root, mode 0444.

Reinstall preserving `/var/lib/omnis` preserves HostId.
Restoring a full machine clone to become a distinct machine requires `omnis system rekey-host`,
which generates a new HostId and host key before network participation.

### 62.2 Agent identity

Each enabled Omnis Agent user has:

```text
$XDG_STATE_HOME/omnis/agent/identity
```

containing one UUIDv7, mode 0600, created atomically on first Agent start. It survives Agent/provider
replacement.

### 62.3 Foreign identity reuse

For a foreign object with stable foreign identity, Manager exact alias namespace is:

```text
foreign:<lowercase-provider-or-protocol-name>
```

alias bytes are the provider's canonical textual identifier.

Rediscovery performs exact alias lookup first:
- one match => reuse NodeId;
- zero => allocate UUIDv7 and create alias;
- multiple => Conflict and discovery stops for that object.

No fuzzy match can merge semantic identities.

---

## 63. Component repository bootstrap

The v0 implementation repositories are exactly:

```text
marius-patrik/omnis
marius-patrik/omnis-os
marius-patrik/omnis-manager
marius-patrik/omnis-agent
marius-patrik/omnis-control
```

All are private during v0 development.

### 63.1 omnis-os

Create by forking/importing the complete `NixOS/nixpkgs` history at the frozen baseline.

Remotes:

```text
origin   git@github.com:marius-patrik/omnis-os.git
upstream https://github.com/NixOS/nixpkgs.git
```

Default branch: `main`.
`main` begins at the frozen nixpkgs commit with one Omnis bootstrap commit on top.

Upstream MIT licensing remains intact. Omnis changes inside this fork are distributed under the same
MIT license to avoid file-level license ambiguity.

### 63.2 omnis-manager

Create from the complete `NixOS/nix` history at the frozen baseline.

Remotes:

```text
origin   git@github.com:marius-patrik/omnis-manager.git
upstream https://github.com/NixOS/nix.git
```

Default branch: `main`.

Existing Nix LGPL-2.1-or-later licensing remains intact; Omnis derivative changes inside the fork use
LGPL-2.1-or-later. The Rust managerd code in the same repository also uses LGPL-2.1-or-later so the
repository has one clear redistribution regime.

### 63.3 omnis-agent / omnis-control / umbrella omnis

Original Omnis code remains **not licensed for third-party reuse** in v0, matching the umbrella
repository's existing `license.spdx = NONE` decision. No agent inserts an OSS license automatically.

### 63.4 branch/release policy

Every component:
- default branch `main`;
- implementation only through PRs;
- branch names `<area>/<short-description>`;
- conventional commits under existing Omnis governance;
- Cargo.lock/flake.lock committed;
- tags use `v0.MINOR.PATCH`;
- first integrated release is `v0.1.0`.

The umbrella `omnis` release tag is the system release identity. Its flake.lock pins exact component
commits plus exact Nix/nixpkgs baselines. Component tags are convenience markers; the umbrella lock
is authoritative for a complete OmnisOS release.

No component independently selects an incompatible protocol major.

---

## 64. First boot and first login

### 64.1 first boot

Exact sequence after NixOS activation:

1. initialize HostId if absent;
2. initialize host Ed25519 identity credential if absent;
3. create/upgrade graph schema;
4. start graphd and publish Host node;
5. start nix-daemon and Omnis Nix observer endpoint;
6. start osd;
7. perform full OS reconciliation;
8. start managerd;
9. materialize canonical Capability nodes from `spec/ontology.toml` using §62 UUIDv5;
10. run deterministic Manager discovery for enabled built-in providers;
11. enable login/session target.

No Agent/model is called during this sequence.

### 64.2 first login for an enabled user

1. initialize Agent UUIDv7 identity if absent;
2. initialize/upgrade worldline/index DB;
3. start Agent outbox drain;
4. create default Workspace if none exists;
5. start Control compositor;
6. materialize §57 default workspace;
7. focus primary terminal/input view;
8. publish user-session/control lifecycle events.

Agent may still be catching up on queued events while Control becomes usable. Control does not wait
for Agent catch-up.

---

## 65. System release provenance

Every Omnis system closure embeds a generated read-only
`/etc/omnis/release.json` containing:

```json
{
  "version": "0.MINOR.PATCH",
  "umbrella_commit": "<40 hex>",
  "omnis_os_commit": "<40 hex>",
  "omnis_manager_commit": "<40 hex>",
  "omnis_agent_commit": "<40 hex>",
  "omnis_control_commit": "<40 hex>",
  "nixpkgs_commit": "<40 hex>",
  "nix_commit": "<40 hex>",
  "protocol_major": 1,
  "protocol_minor": 0,
  "spec_version": 1
}
```

Keys are emitted in the exact order above, UTF-8, LF newline, two-space JSON indentation.
The file is generated by Nix from pinned inputs; no runtime mutation is permitted.


---

## 66. Event-to-cognition routing

`spec/event_priorities.toml` is the canonical base-priority table.

For every ingested event:

1. apply deterministic reducers;
2. obtain base priority by exact event type; unknown => 0.40;
3. if causally attached to an active explicit user Activity, base becomes max(base, 0.75);
4. compute goal_relevance/novelty/urgency:
   - call `model.classify` only when base >=0.40 and a binding exists;
   - otherwise use deterministic fallback values from §16;
5. compute salience using §16 formula;
6. run exact fast-path resolver;
7. if fast path satisfies the postcondition, execute it and do not invoke intention/reason model;
8. if salience >=0.40, no fast path satisfies the event, and `model.reason` exists, run
   `omnis.prompt.intention.v1`;
9. if no reasoning binding exists, retain the unresolved/deferred intention state and do not invent an
   action.

Memory extraction:
- deterministic memory rules in `ONTOLOGY_V0.md §11` always run;
- generative `omnis.prompt.memory_extract.v1` runs only for:
  - explicit user input;
  - Activity/Worker terminal result;
  - Generation success/failure/rollback;
  - execution/inference failure;
  - event with final salience >=0.75;
- and only when `model.generate` exists.
- model-derived records then pass the confidence/provenance rules before graph commit.

Do not run generative memory extraction for raw dense telemetry unless the telemetry triggered a
higher-level event satisfying the rules above.

---

## 67. Renderer, text and 3D camera constants

### 67.1 output/color

v0 output is SDR only.

Render working/output space: sRGB.
Preferred DRM/wgpu format order:

1. BGRA8UnormSrgb;
2. RGBA8UnormSrgb.

If neither is supported, Control fails that output with an explicit incompatibility event; it does
not silently render in a non-sRGB format.

Alpha convention: premultiplied.
Vector/mesh MSAA: 4x when adapter supports sample-count 4 for the target; otherwise 1x.
Text glyph masks are rendered without MSAA through the glyph atlas.

### 67.2 text

Default sizes in logical pixels:

```text
UI body          14
UI small         12
UI heading       18
terminal         14
graph label      13
graph metadata   11
```

Default line-height multiplier: 1.35 UI/document, 1.20 terminal.
Font fallback comes exclusively from fontconfig/cosmic-text against the NixOS font set.

### 67.3 graph geometry

```text
default node card width       180 logical px
default node card min height   56 logical px
node corner radius              8 logical px
normal edge width             1.5 logical px
selected edge width           2.5 logical px
selected node border          2.0 logical px
port diameter                   8 logical px
```

### 67.4 3D camera

Perspective camera:

```text
vertical FOV        60 degrees
near plane          0.1 world units
far plane           100000 world units
orbit sensitivity   0.005 radians / pointer px
wheel dolly factor  exp(-wheel_delta * 0.001)
keyboard move       5 world units/s, Shift = 4x
```

Camera starts looking at focused node from +Z at distance that fits the focused cluster in 70% of
vertical FOV. If only one node exists, start distance = 10 world units.

Pan converts pointer delta at focus depth using the exact perspective projection scale; no fixed
world-unit-per-pixel constant.

### 67.5 built-in theme

`theme/omnis-dark.json` is the exact built-in `Omnis Dark` theme asset. An implementation does
not recreate or approximate it.

---

## 68. Native remote-host pairing

Pairing is an explicit capability; there is no trust-on-first-use.

Server command:

```text
omnis manager host pairing-code
```

creates:
- 32 random bytes from kernel CSPRNG;
- base64url-without-padding display code;
- BLAKE3 hash stored in manager memory only;
- TTL 10 minutes;
- single use.

Client:

```text
omnis manager host pair <host-or-ip> --code <base64url>
```

Pair protocol over QUIC/TLS:

1. connect to UDP 7443 using ALPN `omnis-pair/1`;
2. both sides present self-signed certificates containing their Ed25519 host public key;
3. client sends pairing code over encrypted QUIC;
4. server constant-time compares BLAKE3(code) to active token hash;
5. on success exchange HostId/public key/certificate fingerprint/display name;
6. both sides persist peer records atomically;
7. server destroys token;
8. reconnect using normal ALPN `omnis/1` with mutual pinned-key verification;
9. publish host-paired events.

Pair failure consumes no token except after 5 failed attempts from any peers, when token is revoked.
Only one active pairing token exists per host.

Unpair:

```text
omnis manager host unpair <host-uuid>
```

removes authority grants/cache roots and marks peer binding unavailable; it does not delete historical
Host identity/worldline events.


---

## 69. Graph value and query semantics

### 69.1 property storage encoding

`spec/value_types.toml` is canonical.

For every node/edge property, SQLite `value_type` is the corresponding numeric union code and
`value` stores the standard **unpacked Cap'n Proto message serialization** of
`common.capnp::Value`.

Graphd decodes values for semantic comparison; SQLite BLOB byte equality is never used as semantic
value equality.

Rules:

- float values must be finite; reject NaN and +/-Infinity;
- text must be valid UTF-8 and is normalized to NFC before storage;
- UUID is exactly 16 bytes;
- maps have unique keys sorted by UTF-8 byte lexical order before storage;
- lists preserve order;
- nested maps/lists recursively obey the same rules.

### 69.2 selectors

`NodeSelector` semantics:

- empty `ids` means no ID restriction; otherwise node ID must be in the list;
- empty `kinds` means no kind restriction; otherwise node must have at least one listed kind;
- all propertyFilters are ANDed;
- equals/notEquals compare decoded typed values;
- exists/notExists ignore the supplied value field;
- selector groups (ID/kind/properties) are ANDed;
- an entirely empty selector selects all visible nodes subject to query limit.

### 69.3 traversal

- depth 0 returns roots only;
- relation list empty => all visible relations;
- dimension list empty => all visible dimensions;
- traversal is breadth-first;
- a node appears once at its shallowest discovered depth;
- edges are ordered by relation UTF-8 bytes, opposite NodeId bytes, then EdgeId bytes;
- output nodes are ordered by discovery depth then NodeId bytes;
- `both` explores outgoing before incoming for the same ordered relation/peer tuple.

### 69.4 paths

Path query uses breadth-first search and returns shortest paths only until `maxPaths`.
Default `maxPaths=16` when caller supplies 0; hard max 256.
Maximum path depth is graph configured hard depth (8).

Path ordering:
1. edge count ascending;
2. node-ID byte sequence lexicographic;
3. edge-ID byte sequence lexicographic.

### 69.5 aliases

Alias namespace and alias are exact, case-sensitive UTF-8 NFC strings.

`resolveAlias` returns candidate NodeIds sorted by bytes.
Callers interpret 0 as NotFound, 1 as resolved, >1 as Conflict unless they explicitly requested all
candidates.

### 69.6 transaction events

Every successful GraphTransaction:

1. validates expectedRevision equals current revision exactly;
2. rejects zero mutations;
3. evaluates all preconditions inside `BEGIN IMMEDIATE`;
4. applies mutations in listed order;
5. sets supplied transaction-event `graphRevision` to new revision;
6. enqueues supplied events in listed order;
7. graphd creates and enqueues exactly one `omnis.event.graph.committed` event last;
8. commits graph rows, transaction row and all outbox rows atomically.

The synthesized graph-committed EventId is returned in CommitResult.

For non-transaction `enqueueEvent`, graphRevision stays whatever valid revision the producer
observed, including 0 only when genuinely unrelated to graph state.

All events carry producer wall and monotonic timestamps. Graphd never replaces producer timestamps
with ingest time; outbox `created_at_ns` separately records graphd receipt time.

### 69.7 preconditions

- propertyEquals compares canonical decoded Value semantics;
- propertyAbsent means no current row for exact node/namespace/key;
- relationExists/Absent match exact source/relation/target;
- cardinality counts current matching edges in requested direction;
- `max = 4294967295` means unbounded maximum;
- authority namespace ownership is always checked independently and cannot be bypassed by
  preconditions.

A precondition failure returns Conflict and performs no writes.
