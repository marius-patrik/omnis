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

## 3. Core event journal API

Every first-party OS/Manager/Control producer durably appends typed `EventEnvelope` values through
graphd. Graph transactions append their events atomically with graph mutations.

```text
events.read(after_ingest_seq, limit)
events.subscribe(after_ingest_seq)
events.get(event_id)
artifact.put/get(...)
```

There is no Agent-specific ingress and no global ACK.

`ingest_seq` is strictly increasing. Any consumer persists its own cursor and reconnects from that
sequence. v0 performs no automatic journal deletion, so a newly attached authorized agent can replay
every core event since initialization.

### 3.1 Dense event batches

High-rate producers use `events.capnp::DenseBatch` with the exact lossless limits from the core
decision contract. Each original ordered item retains producer sequence, monotonic timestamp, type
and typed payload.

### 3.2 Event payload encoding

Every first-party event type in `spec/events.toml` maps to exactly one union variant in
`protocol/events.capnp::Payload`. Arbitrary component-private JSON/binary payloads are invalid.

Persistent journal bytes use standard unpacked Cap'n Proto serialization of the full EventEnvelope.
Dense-batch item payload contains the same serialization of the mapped Payload variant.

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
nix.plan_realization
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

### 4.4 Nix control projection

The low-level Nix protocol is `protocol/nix_control.capnp`. Manager's public `nixExplain` returns
one unpacked Cap'n Proto `NixExplanation` artifact. `nixPlanRealization` returns the exact typed
`RealizationPlan` produced by the store control surface.

The evaluator/store split, ordering and provenance rules are normative in `NIX_CONTROL_V0.md`.
Callers never receive scraped Nix CLI text as structured evidence.

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

## 6. Harness-agnostic agent projections

There is no AgentService protocol.

`docs/AGENT_ACCESS_V0.md` and `spec/agent_access.toml` project the public GraphService, OsService,
ManagerService and ControlService APIs into:
- MCP tools/resources via `omnis mcp`;
- native plugin methods via `@omnis/agent-access`.

Projection parity is mechanical. A tool/plugin operation cannot invent semantics absent from the
typed core service methods.

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

Every successful structural mutation appends a Control event to the core journal.

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

Protected secret bytes NEVER appear in ordinary protocol Value/Event/Artifact bodies. Cross-component
references use opaque HandleId/LeaseId identities; serialization endpoints enforce protection labels
and reject disallowed disclosure rather than relying on caller redaction.

---

## 10. Versioning

Protocols use explicit semantic versioning.

Rules:

- additive fields are backward compatible within a major version;
- Cap'n Proto unknown fields are preserved according to generated-library behavior; v0 defines no optional RPC feature negotiation;
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
$XDG_RUNTIME_DIR/omnis/control.sock
```

Each connection negotiates protocol major/minor, component identity, build ID and supported
interfaces. v0 accepts only protocol 1.0 exactly, per `DECISION_COMPLETE_V0.md §72`.

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
protocol/control.capnp
```

`common.capnp` defines UUIDv7 IDs, ArtifactId, protocol/version handshake, TraceContext, provenance,
protection labels, typed values and typed errors. Domain schemas import it; they may not redefine
identity or error envelopes.

Cap'n Proto field ordinals are append-only. Removed fields are reserved rather than reused. Every
service interface exposes the common handshake and the exact v1 interface string; v0 has no minor-version optional-operation negotiation.

Graph subscriptions resume from GraphRevision. Event delivery resumes from EventId/ingest sequence.
Streaming APIs must expose backpressure and explicit cancellation; unbounded producer queues are
forbidden.


## 15. Canonical semantic registries

Wire fields carrying kind/relation/event/capability names must use the first-party identifiers in
`ONTOLOGY_V0.md`. Unknown third-party names are transported opaquely; a component must not invent a
new `omnis.*` identifier during implementation.

Domain state strings for Execution and Generation use the exact state
machines from `ONTOLOGY_V0.md`.


## 16. Canonical inference protocol

`protocol/inference.capnp` is the only first-party model request/result semantic IR. The local
OpenAI/Anthropic gateway and concrete model/provider adapters translate to/from this schema.

`model.generate` and `model.reason` use the `InferenceRequestInput` /
`InferenceResultOutput` capability contracts. Tool/message semantics are not provider-specific
inside Manager.

The exact HTTP compatibility subset and unsupported-feature behavior are defined in
`HARNESS_ADAPTERS_V0.md`. Provider-specific raw request/response bytes are retained only as
protected provenance artifacts.
