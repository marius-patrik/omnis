# Omnis Protocols and Cross-Component Contracts

**Status: normative implementation contract.**

This document freezes the minimum cross-component semantics required to implement Omnis without
creating parallel subsystem-specific models.

---

## 1. Wire protocol and transport

Canonical v0 schemas are Cap'n Proto protocol version 1.0. Rust and C++ bindings are generated from the same `.capnp`
sources owned by the umbrella `omnis` repository. Local RPC runs over Unix-domain `SOCK_STREAM`;
native remote Omnis RPC uses the same logical messages over QUIC/TLS 1.3.

JSON is allowed only as a diagnostic/export representation; it is not a second RPC contract.

Every RPC returns a `C.RpcStatus`. Transport failures use Cap'n Proto transport exceptions; all
expected/domain failures use `RpcStatus.error` with `RpcError`. Callers never infer absence from zero
UUIDs or empty strings when a `Maybe*` union exists.

Every request/event carries:

```text
protocol_version
message_id
actor
trace_id
causal_parents[] where applicable
graph_revision where applicable
```

Large payloads are referenced as artifacts rather than copied through every message. Artifact bytes
use `ArtifactUpload`/`ArtifactDownload`; each chunk is at most 1 MiB. The old whole-payload put/get
shape is not a v0 API.

---

## 2. Graph API

Minimum operations:

```text
node.get(id)
node.resolve(alias)
query.execute(query)
query.subscribe(query)
transaction.commit(txn)
revision.get()
revision.read(revision, query)
provenance.expand(ref)
```

`transaction.commit` is the only mutation path.

A transaction response includes:

```text
transaction_id
previous_revision
new_revision
changed_ids[]
event_payload_ref
```

---

## 3. Event API

Components durably enqueue first-party events through the graph substrate. OmnisAgent has no public
`submitEvent` bypass; graphd outbox is the sole first-party durable event ingress:

```text
outbox.enqueue(EventEnvelope)
outbox.enqueue_batch([...])
artifact.put(...)
```

Graph transactions enqueue their events atomically with graph mutations. OmnisAgent drains the
outbox into its worldline and then calls `outbox.ack(event_id)`.

Agent exposes durable subscriptions/query:

```text
worldline.tail(filter)
worldline.query(filter)
worldline.get(event_id)
worldline.causes(event_id)
worldline.effects(event_id)
```

Enqueue success means graphd durably owns the event for lossless delivery. Delivery to Agent is
at-least-once and Agent deduplicates EventId. Silent event drop is not valid first-party behavior.

---

### 3.1 Dense event batches

High-rate producers may enqueue an EventEnvelope whose payload is a BLAKE3 artifact containing an
ordered batch of original events. The batch header carries producer identity, first/last sequence
and monotonic time range. Each item retains sequence, monotonic timestamp, type and payload.

Lossless batching is permitted; semantic sampling/drop is not permitted for first-party event
classes declared lossless.

### 3.2 Event payload encoding

Every first-party event type in `spec/events.toml` maps to exactly one union variant in
`protocol/events.capnp::Payload`. `EventEnvelope.payload` is that typed union; arbitrary JSON or
component-private binary payloads are not valid first-party event encoding.

Persistent/event-outbox bytes use standard **unpacked Cap'n Proto message serialization** of the full
EventEnvelope with deterministic field/list ordering supplied by the producer. Worldline stores those
exact envelope bytes in `events.envelope` while indexing the identity/type/source/time/revision
columns separately.

Dense-batch item `payload` contains the same unpacked Cap'n Proto serialization of the mapped
`events.capnp::Payload` variant for that item's event type.

## 4. Manager API

Minimum operations:

```text
resource.get/list/search
capability.get/list/search
binding.get/list
binding.declare
resource.discover
capability.resolve
execution.start
execution.cancel
execution.get
placement.explain
protected.resolve_handle
nix.explain
nix.plan
```

### 4.1 Resolve request

```text
ResolveRequest
  capability
  inputs/schema refs
  hard_constraints
  soft_preferences
  activity/actor
  graph_revision
```

### 4.2 Resolve result

```text
ResolveResult
  candidate_bindings[]
  selected_binding?
  rejected_candidates + reasons
  scoring/policy inputs
  placement
  required_authorities
```

No selected binding is acceptable when the caller requested discovery-only resolution.

---

### 4.3 Capability payload encoding

Every first-party capability in `spec/capabilities.toml` maps to exact input/output structs in
`protocol/capabilities.capnp` and one fixed effect class. Execution input/output artifacts contain
the **unpacked Cap'n Proto message bytes** for those mapped structs. An adapter must reject a payload
whose declared capability does not match the mapped type.

Provider-specific adapters translate only at the foreign boundary; they do not redefine the Omnis
capability schema.

## 5. OmnisOS API

Minimum operations:

```text
host.inventory
execution_envelope.create/destroy
physical_process.launch/get/signal/stop
system.evaluate(candidate)
system.build(candidate)
system.diff(active, candidate)
system.activate(generation)
system.rollback(generation)
system.generation.get/list
system.invariant.check
protected_handle.inject
```

Persistent mutation uses system candidate/generation APIs. Transient Manager executions use execution
envelopes without changing system generation unless requested.

---

### 5.1 Physical launch ownership

`omnis-managerd` never launches a restricted process itself. It sends `PhysicalLaunchRequest` to
`omnis-osd`. osd validates the envelope, starts the transient systemd service and returns either
pipe or PTY stream capabilities. ExecutionId is preserved across Manager/OS/process graph state.

## 6. Agent API

Agent is event-driven but exposes explicit operations for Control/CLI/Manager:

```text
agent.event
agent.ask / agent.intend
agent.memory.search
agent.memory.get
agent.memory.remember
agent.context.compile
agent.activity.get/list
agent.worker.get/list
agent.workflow.get/list
agent.worldline.query
agent.explain(identity/event/action)
```

Explicit calls become events and use the same worldline/memory semantics as spontaneous/external
inputs.

---

## 7. Control API

Control exposes structural operations, not simulated input, for first-party automation:

```text
control.scene.get/list
control.materialize(graph_ids, intent)
control.focus(node)
control.select(nodes)
control.lens.set(lens)
control.mode.set(2d|3d)
control.layout.apply(...)
control.tree.transaction(...)
control.native_surface.attach(...)
control.navigate(address)
control.input.submit(...)
```

Every successful structural mutation emits a Control event to Agent.

---

## 8. Artifact references

Large immutable data uses content-addressed artifact references:

```text
ArtifactRef
  digest (BLAKE3)
  length
  media_type
  protection metadata
  optional storage locator
```

Artifacts may include files, model output, logs, screenshots, patches, traces, large event payloads,
and historical snapshots.

Graph/event objects refer to artifacts; artifact storage does not become semantic authority.

---

## 9. Protected values

Protocol values can be marked:

```text
public
local-only
agent-visible
model-local-only
model-external-denied
control-hidden
execution-handle-only
```

Protected values should normally travel as opaque handles. Serialization endpoints must enforce
disclosure metadata rather than rely on callers to remember redaction.

---

## 10. Versioning

Protocols use explicit semantic versioning.

Rules:

- additive fields are backward compatible within a major version;
- unknown optional fields are ignored/preserved where forwarding is required;
- unknown required capability/field produces explicit incompatibility;
- identity formats cannot be silently reinterpreted;
- graph relation names are stable compatibility surface;
- migrations preserve semantic IDs and provenance.

---

## 11. Tracing

One trace may cross all four components.

Required correlation chain:

```text
user/control event
  -> Agent judgement/intention
  -> Manager resolution
  -> OS execution/generation
  -> resulting graph changes
  -> Control update
  -> Agent events
```

Tracing metadata is operational observability. Causal event IDs remain the semantic history.

---

## 12. Failure semantics

Failures are explicit typed results/events.

Required distinctions:

```text
unresolved capability
ambiguous binding
constraint unsatisfied
placement unavailable
authority denied
protected-value denied
build failure
activation failure
execution failure
external effect ambiguous
protocol incompatible
graph conflict
Agent/model unavailable
Control unavailable
```

A model failure must not imply Manager/OS failure. The machine must retain deterministic operation
without AI availability.

---

## 13. v0 endpoints and handshake

System endpoints:

```text
/run/omnis/graph.sock
/run/omnis/os.sock
/run/omnis/manager.sock
/run/omnis/nix-control.sock
```

User endpoints:

```text
$XDG_RUNTIME_DIR/omnis/agent.sock
$XDG_RUNTIME_DIR/omnis/control.sock
```

Each connection negotiates protocol major/minor, component identity, build ID and supported
interfaces. Major mismatch rejects the connection; minor versions intersect optional features.

Effectful requests carry RequestId, TraceId, actor NodeId, causal EventIds, authority scope, deadline
and an idempotency key when retry is legal. Execution creation is idempotent on ExecutionId.

Semantic/event IDs are UUIDv7 binary 16-byte values. Artifact IDs are BLAKE3-256. Inline payloads
remain small; large payloads travel by ArtifactRef through the graphd CAS.

## 14. Canonical schema ownership

The umbrella repository owns six schema source files. Implementation repositories consume a pinned
schema revision and generate bindings during their Nix build:

```text
protocol/common.capnp
protocol/graph.capnp
protocol/os.capnp
protocol/manager.capnp
protocol/agent.capnp
protocol/control.capnp
```

`common.capnp` defines UUIDv7 IDs, ArtifactId, protocol/version handshake, TraceContext, provenance,
protection labels, typed values and typed errors. Domain schemas import it; they may not redefine
identity or error envelopes.

Cap'n Proto field ordinals are append-only. Removed fields are reserved rather than reused. Every
service interface exposes a `getCapabilities`/handshake feature set so minor-version peers can
negotiate optional operations without guessing.

Graph subscriptions resume from GraphRevision. Event delivery resumes from EventId/ingest sequence.
Streaming APIs must expose backpressure and explicit cancellation; unbounded producer queues are
forbidden.


## 15. Canonical semantic registries

Wire fields carrying kind/relation/event/capability names must use the first-party identifiers in
`ONTOLOGY_V0.md`. Unknown third-party names are transported opaquely; a component must not invent a
new `omnis.*` identifier during implementation.

Domain state strings for Execution, Worker, Activity, Generation and Memory use the exact state
machines from `ONTOLOGY_V0.md`.
