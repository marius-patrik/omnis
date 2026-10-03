# Shared Multidimensional Graph

**Status: normative supporting specification.**

The shared graph is the current structured state substrate of Omnis. It is used directly by
OmnisOS, OmnisManager, OmnisAgent, and OmnisControl.

It is not a fifth product, not an agent memory database, and not a rendering scene graph.

---

## 1. Design goals

The graph must provide:

- one stable identity space across the whole system;
- simultaneous physical, semantic, cognitive, resource, causal, and presentation relations;
- explicit write ownership;
- atomic graph transactions;
- versioned current state;
- subscriptions to committed changes;
- efficient neighborhood and dimension queries;
- provenance on facts and relations;
- temporal validity where state changes over time;
- enough structure for OmnisControl to derive interactive projections;
- enough structure for OmnisAgent to reason without scraping subsystem-specific stores.

The graph is optimized for **shared identity and current state**, not for preserving the complete
causal past. The causal past belongs to OmnisAgent's worldline.

---

## 2. Identity

### 2.1 Stable semantic identity

Every graph object has an opaque `NodeId` that survives changes to:

- name;
- filesystem path;
- process ID;
- host;
- package version;
- Nix store path;
- model/provider;
- UI position;
- execution runtime.

Omnis v0 uses UUIDv7 for allocated semantic identities. IDs are encoded as 16 bytes on the wire and
as canonical lowercase hyphenated UUID text only at human-facing boundaries.

Immutable artifacts may additionally use content identity (`blake3:<digest>`), but content identity
must not replace semantic identity for mutable concepts.

### 2.2 Aliases

Human-readable names, paths, package attributes, hostnames, URIs, PIDs, and provider IDs are aliases
or properties. They may resolve to graph identities but are not graph identity themselves.

### 2.3 External identity

When a foreign system already has durable identity, retain it in provenance:

```text
foreign.system = "github"
foreign.identity = "repo:123456"
```

Do not reuse a foreign ID as the global graph ID unless the protocol explicitly guarantees globally
stable semantics.

---

## 3. Node model

A node contains minimal common structure:

```rust
struct Node {
    id: NodeId,
    kinds: SmallVec<KindId>,
    properties: PropertyMap,
    provenance: Vec<ProvenanceRef>,
    created_revision: GraphRevision,
    deleted_revision: Option<GraphRevision>,
}
```

`kinds` is open-ended. It is not a closed enum that requires the graph core to understand every
domain concept.

Examples:

```text
host
process
package
resource
capability
model
repository
project
worker
memory
scene
view
surface
generation
device
```

Kinds describe discoverable semantics. Authority remains defined by dimension/property namespaces,
not by a giant central type switch.

---

## 4. Edge model

```rust
struct Edge {
    id: EdgeId,
    source: NodeId,
    relation: RelationId,
    target: NodeId,
    dimensions: SmallVec<DimensionId>,
    properties: PropertyMap,
    validity: Validity,
    provenance: Vec<ProvenanceRef>,
    created_revision: GraphRevision,
    deleted_revision: Option<GraphRevision>,
}
```

Relations are stable identifiers such as:

```text
physical.runs
physical.attached_to
system.realizes
resource.installed_on
capability.provides
capability.requires
binding.realizes
execution.uses
execution.placed_on
causal.caused_by
provenance.derived_from
authority.may_access
activity.belongs_to
cognitive.about
cognitive.recalled_with
presentation.represents
presentation.focus
presentation.selection
presentation.contains
```

Relation names are namespaced by the authority/domain that defines their semantics.

---

## 5. Dimensions and ownership

### 5.1 OmnisOS namespaces

OmnisOS owns canonical writes to:

```text
physical.*
system.*
enforcement.*
```

Examples:

- process lifecycle;
- current mounts;
- network interfaces;
- device attachment;
- active Nix generation;
- desired/actual service state;
- cgroup/resource envelope;
- kernel/driver facts.

### 5.2 OmnisManager namespaces

OmnisManager owns:

```text
resource.*
capability.*
binding.*
execution.*
placement.*
foreign.*
```

Examples:

- package provides executable;
- harness provides `code.agent`;
- model runtime can execute model artifact;
- resource requires credential;
- execution placed on host;
- capability discovered from D-Bus/CLI/API.

### 5.3 OmnisAgent namespaces

OmnisAgent owns:

```text
cognitive.*
memory.*
goal.*
context.*
judgement.*
worker.*
learning.*
```

Examples:

- memory about repository;
- hypothesis supported by events;
- active project goal;
- worker context activation;
- learned procedure;
- expectation/prediction.

### 5.4 OmnisControl namespaces

OmnisControl owns:

```text
presentation.*
interaction.*
scene.*
navigation.*
```

Examples:

- scene contains projection;
- projection represents resource;
- current focus/selection;
- 2D/3D mode;
- lens;
- layout relation;
- native surface attachment.

### 5.5 Shared facts

A component may propose a mutation outside its namespace only through the owning component's API.
Graph core rejects unauthorized direct writes.

This makes ownership structural rather than conventional.

---

## 6. Properties

Properties are namespaced and strongly encoded at the wire level:

```text
string
bytes
bool
i64
u64
f64
timestamp
duration
node_ref
artifact_ref
sequence
mapping
```

Domain-specific schemas are discoverable metadata layered above this primitive representation.

The graph core does not require a globally closed user-defined type system.

---

## 7. Temporal validity

State that changes over time must distinguish historical observation from current validity.

An edge/property may carry:

```text
observed_at
valid_from
valid_until
confidence
```

Deleting current graph state does not delete historical worldline events.

Example:

```text
Project --resource.framework--> React   valid T1..T2
Project --resource.framework--> Svelte  valid T2..present
```

Agent memory may interpret both while current graph queries select the valid present edge by
default.

---

## 8. Provenance

Every nontrivial discovered/inferred graph fact should record provenance quality.

Required provenance categories:

```text
native-authoritative
nix-evaluation
kernel-observation
protocol-descriptor
structured-tooling
foreign-api
source-analysis
deterministic-probe
learned-inference
user-declared
agent-derived
```

Provenance may additionally point to:

- event IDs;
- artifacts;
- foreign versions/hashes;
- commands/protocol calls;
- model invocation IDs;
- graph revisions.

A richer label must never imply stronger evidence than is actually known.

---

## 9. Transactions

All changes occur through `GraphTransaction`.

```rust
struct GraphTransaction {
    id: TxnId,
    actor: NodeId,
    authority: Authority,
    causal_parents: Vec<EventId>,
    expected_revision: Option<GraphRevision>,
    preconditions: Vec<GraphPredicate>,
    mutations: Vec<Mutation>,
    provenance: Vec<ProvenanceRef>,
}
```

Mutations:

```text
create_node
set_property
remove_property
create_edge
set_edge_property
remove_edge
tombstone_node
```

A successful transaction returns:

```text
new revision
changed node/edge IDs
normalized graph-change event payload
```

Failed preconditions produce no partial graph mutation.

---

## 10. Graph predicates

The first implementation requires deterministic predicates for:

- node exists/does not exist;
- property equals/does not equal;
- relation exists/does not exist;
- revision matches;
- authority owns namespace;
- target identity still refers to expected foreign realization;
- optional cardinality constraints.

Graph predicates are operational consistency checks, not a replacement for OmnisOS system
invariants or OmnisAgent reasoning.

---

## 11. Queries

Minimum graph query capabilities:

```text
lookup by NodeId
resolve aliases
filter nodes by kind/property/dimension
outgoing/incoming relation traversal
bounded neighborhood traversal
path queries
current-validity filtering
graph-revision snapshot reads
provenance expansion
dimension/lens projection
subscription to node/relation/query changes
```

The graph protocol should support query plans rich enough for Control to maintain live projections
without polling entire subgraphs.

---

## 12. Subscriptions

A client can subscribe to:

- exact node IDs;
- relation patterns;
- dimension namespaces;
- query result sets;
- all committed transactions for its authority.

Subscriptions deliver revision-ordered changes.

Control uses subscriptions to update projections. Agent receives the normalized event stream and
does not need a separate observe call to know what changed.

---

## 13. Event handoff

Every committed graph transaction yields an Agent event containing at least:

```text
transaction id
actor
authority
previous revision
new revision
causal parents
changed identities
mutation summary
payload/artifact references where needed
```

Subsystem-specific lifecycle/input events that do not correspond to graph mutation are durably
enqueued through graphd's outbox. Dense event classes may use lossless batch artifacts, but Agent can
recover every original ordered item without observing the scene.

No first-party component silently mutates durable state without producing an event.

---

## 14. Storage

Omnis v0 storage is fixed:

```text
SQLite WAL + synchronous=FULL
+ one serialized writer
+ normalized node/kind/property/edge/provenance tables
+ revision validity intervals
+ relation/alias indexes
+ graph transaction metadata
+ durable event outbox
+ filesystem BLAKE3 CAS for large payloads
```

Rationale:

- local-first;
- transactional;
- easy recovery;
- inspectable;
- zero external server requirement;
- sufficient for the first single-machine implementation.

The protocol must permit later replacement with a distributed implementation without changing graph
identity or relation semantics.

Vector indexes, search indexes, spatial indexes, and Agent memory indexes are derived accelerators
outside the graph's canonical state.

---

## 15. Control projection contract

Control requests a projection using:

```text
focus identities
lens/dimensions
relation filters
semantic level of detail
historical/current frontier
authority/visibility constraints
layout intent
```

The result preserves graph IDs and produces an interactive `ControlTree`.

A Control node that semantically represents an existing graph object must retain that `NodeId`.
Ephemeral layout-only nodes use Control-local identity and must not masquerade as domain objects.

---

## 16. Agent relationship

Agent memory may point directly to graph nodes:

```text
Memory:m1 --cognitive.about--> Repository:r1
```

It should not duplicate current operational facts when the graph already contains authoritative
state. Derived memories explain, generalize, predict, associate, or preserve historical meaning.

Agent context compilation may query the graph at a specific revision/frontier and include stable node
references rather than copied descriptions.

---

## 17. Manager relationship

Manager expresses possibility through graph structure:

```text
Resource:ClaudeCode --capability.provides--> Capability:code.agent
Resource:RTX5090    --capability.provides--> Capability:cuda.compute
Model:Qwen          --resource.runnable_by--> Runtime:vLLM
```

Resolution is a graph query plus constraint evaluation, not an independent registry with separate
identity.

---

## 18. OS relationship

OS publishes authoritative current physical state:

```text
Host:h --physical.has_device--> GPU:g
Host:h --physical.runs--> Process:p
Generation:g42 --system.active_on--> Host:h
```

OmnisOS may retain rebuildable caches, but every cached object keeps its shared NodeId and graph
identity remains the cross-system reference point.

---

## 19. Hard invariants

1. One real-world object must not acquire separate canonical IDs merely because different components
   see it.
2. Graph core cannot invent domain meaning.
3. Graph writes are atomic and revisioned.
4. Namespace ownership is enforced.
5. Provenance is retained when available.
6. Current graph state is not historical truth.
7. Agent worldline is not replaced by graph transaction WAL.
8. Control render state is not graph truth.
9. Derived indexes are disposable.
10. Every committed first-party graph mutation emits an Agent event.
---

## 20. v0 storage and delivery binding

The concrete v0 graph implementation is `omnis-graphd` from OmnisOS.

Canonical locations:

```text
/var/lib/omnis/graph/graph.sqlite3
/var/lib/omnis/cas/blake3/
/run/omnis/graph.sock
```

`graph.sqlite3` uses SQLite WAL, `synchronous=FULL`, one serialized writer task, independent reader
connections, validity intervals for revision reads, and schema migrations owned by graphd.

The graph database also contains the durable event outbox. A graph transaction commits graph
mutations and its normalized event envelopes atomically. Non-graph first-party producers enqueue
events through graphd before considering publication durable. OmnisAgent drains the outbox into its
worldline and acknowledges EventId; delivery is at-least-once and deduplicated by EventId.

Large payloads use the BLAKE3 CAS rather than SQLite/RPC blobs. The graph stores ArtifactId references
plus media/protection/provenance metadata.

The exact relational table families, transaction operations and query policy are frozen in
`IMPLEMENTATION.md`. No alternative graph DB, broker or query language is introduced in v0.
