# Omnis Protocols and Cross-Component Contracts

**Status: implementation contract draft.**

This document freezes the minimum cross-component semantics required to implement Omnis without
creating parallel subsystem-specific models.

---

## 1. Transport rule

Protocol semantics are transport-independent. Initial local transport should use Unix domain sockets
with a binary-capable framed protocol. JSON/CBOR/MessagePack/protobuf are implementation choices;
the data model below is normative.

Every request/event carries:

```text
protocol_version
message_id
actor
trace_id
causal_parents[] where applicable
graph_revision where applicable
```

Large payloads are referenced as artifacts rather than copied through every message.

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

Components publish events to OmnisAgent:

```text
event.publish(EventEnvelope)
event.publish_batch([...])
artifact.put(...)
```

Agent exposes durable subscriptions/query:

```text
worldline.tail(filter)
worldline.query(filter)
worldline.get(event_id)
worldline.causes(event_id)
worldline.effects(event_id)
```

Publishing success means Agent durably accepted the event or the configured local spool accepted it
for lossless delivery. Silent event drop is not valid first-party behavior.

---

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

## 5. OmnisOS API

Minimum operations:

```text
host.inventory
execution_envelope.create/destroy
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
