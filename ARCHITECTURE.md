# Omnis — Architecture

**Status: NORMATIVE.** This document defines the system architecture. Supporting documents may
expand implementation detail but must not contradict it. The concrete v0 substrate is frozen in
[`docs/IMPLEMENTATION.md`](docs/IMPLEMENTATION.md) and ADR-0024. All remaining v0 algorithms,
constants, defaults and fallback behavior are frozen by
[`docs/DECISION_COMPLETE_V0.md`](docs/DECISION_COMPLETE_V0.md) and ADR-0025. Canonical first-party
kind/relation/capability/event names and lifecycle states are frozen by
[`docs/ONTOLOGY_V0.md`](docs/ONTOLOGY_V0.md); public NixOS configuration is frozen by
[`docs/NIX_OPTIONS_V0.md`](docs/NIX_OPTIONS_V0.md). Harness-agnostic agent access is frozen by
[`docs/AGENT_ACCESS_V0.md`](docs/AGENT_ACCESS_V0.md) and `spec/agent_access.toml`.

Omnis is a graph-native, agentic operating system built initially on Linux, Nix, and NixOS. It is
not a desktop application, an AI assistant, a shell wrapper, or a new programming language.

The system has exactly three first-class authorities:

1. **OmnisOS** — physical/system authority.
2. **OmnisManager** — resource/capability/execution authority.
3. **OmnisControl** — interaction/presentation authority.

They share one multidimensional graph, one durable core event journal, and one stable identity space.
No agent implementation is part of the core authority model. Agents are replaceable clients of these
three surfaces.

---

## 1. Architectural thesis

Omnis is built around five statements.

### 1.1 One world, one graph

Every meaningful object in the machine has one stable identity in a shared multidimensional graph.
A repository, process, model, package, host, GPU, capability, worker, memory, scene, surface, or Nix
generation is not copied into four subsystem-specific databases and reconciled later.

Different components contribute different dimensions and relations over the same identities.

### 1.2 One core event journal; agent-owned memory

Every meaningful first-party OS/Manager/Control transition enters the shared append-only core event
journal. The journal is system history, not cognition.

An attached agent consumes this journal and may maintain its own richer causal worldline, memory,
goals, workers, model state, or learned procedures. Those structures belong to the agent
implementation and are not required for OmnisOS, OmnisManager, or OmnisControl to boot or operate.

### 1.3 Bind reality; do not require it to become Omnis

Existing applications, CLIs, services, libraries, models, containers, VMs, package managers,
protocols, agents, and devices remain real external systems. Omnis discovers, binds, controls, and
progressively understands them.

Reimplementation requires a material reason. Integration is preferred to replacement.

### 1.4 AI chooses semantics; deterministic systems realize physics

AI never becomes part of Nix evaluation or another deterministic build primitive.

An attached agent may form an intention, but the core never depends on one. OmnisManager resolves
resources, capabilities, bindings, execution and placement. OmnisOS deterministically realizes
persistent state and enforces physical constraints.

### 1.5 The interface is the graph made interactive

OmnisControl does not maintain a separate semantic UI universe. It projects graph identities into a
control tree, lowers that tree into render state, and emits interactions back as graph mutations and
events.

Authorized agent clients receive the same first-party event journal directly and can structurally
mutate Control state through its typed API. They do not need to observe screenshots or simulate
clicks for first-party surfaces.

---

## 2. System topology

```text
                                     USER
                                       │
                                       ▼
                                ┌──────────────┐
                                │ OmnisControl │
                                └──────┬───────┘
                                       │
                                       ▼
                         SHARED MULTIDIMENSIONAL GRAPH
                         + APPEND-ONLY CORE EVENT JOURNAL
                                       │
                 ┌─────────────────────┴─────────────────────┐
                 │                                           │
                 ▼                                           ▼
            ┌─────────┐                                ┌──────────────┐
            │ OmnisOS │                                │ OmnisManager │
            └────┬────┘                                └──────┬───────┘
                 │                                            │
                 ▼                                            ▼
               Linux                                  external reality

        optional/replacable agent clients
           │               │
           ├── MCP ─────────┤
           └── native plugin/SDK adapters
                 │
                 ▼
       OS + Manager + Control + graph/events
```

The graph substrate is **not a fourth product authority**. It is a shared system ABI and current-state
substrate supplied by OmnisOS and used by all three authorities.

Agent access is also **not a fourth authority**. MCP and plugin adapters are projections over the same
typed APIs and event journal. Removing every agent integration leaves a fully usable Omnis machine.

## 3. Shared multidimensional graph

### 3.1 Purpose

The graph is the common current-state model of the machine and its cognitive/interactive extensions.
It exists so every subsystem can refer to the same object without copying identity.

A process may simultaneously participate in physical, resource, causal, activity, authority,
temporal, cognitive, and presentation dimensions while remaining one process identity.

### 3.2 Core representation

The graph is a dynamic property graph with stable opaque identities.

```text
Node
  id
  kinds[]
  properties{}
  provenance[]

Edge
  id
  source
  relation
  target
  dimensions[]
  properties{}
  validity
  provenance[]
```

Semantic identities use stable opaque IDs independent of filesystem path, PID, Nix store path,
host, model provider, UI location, or current implementation.

Immutable artifacts may additionally use content identities.

### 3.3 Dimensions

Dimensions are typed relation/property namespaces over shared identities. The initial required
dimensions are:

```text
physical       hardware, process, filesystem, network, device, service
system         desired configuration, generation, invariant, realization
resource       package, executable, library, model, endpoint, runtime
capability     provides, requires, implements, declines
binding        semantic/resource identity -> concrete realization
execution      invocation, placement, lifecycle, resource consumption
causal         caused_by, emitted, derived_from, observed
provenance     source, version, hash, discovery method, evidence
authority      may_access, may_invoke, protected_by, credential handle
temporal       valid_from, valid_until, created_at, active interval
activity       project, goal, task, worker, execution membership
cognitive      memory, belief, hypothesis, context, attention, procedure
presentation   scene, view, focus, selection, lens, layout, surface
```

The dimension set is extensible. New dimensions must reuse existing identities rather than minting
parallel shadow objects for the same thing.

### 3.4 Write ownership

Each authority owns canonical writes to particular dimensions:

| Authority | Canonical writes |
|---|---|
| OmnisOS | physical, system, enforcement facts, graph substrate state |
| OmnisManager | resource, capability, binding, placement, execution facts |
| OmnisAgent | cognitive, memory, goal, context, learned semantic relations |
| OmnisControl | presentation, focus, selection, interactive layout/control state |

Cross-authority references are normal. Cross-authority mutation must go through the owning API or a
validated graph transaction.

### 3.5 Graph transactions

Graph updates are atomic transactions containing:

```text
actor
causal parents
preconditions
mutations
provenance
authority namespace
```

A committed transaction increments graph revision and emits one or more normalized events to
OmnisAgent.

The graph service may keep an implementation WAL for crash recovery. That WAL is not a replacement
for OmnisAgent's causal worldline.

### 3.6 Internal graph service

OmnisOS provides the internal service `omnis-graphd`, responsible only for:

- stable identity allocation;
- atomic graph transactions;
- current-state storage;
- subscriptions/change streams;
- indexed graph queries;
- authority/write validation;
- revisioning and local recovery.

It contains no cognition, capability policy, UI logic, package semantics, or memory semantics.

Omnis v0 uses SQLite in WAL mode with one serialized writer, revision-addressable validity rows, a
durable event outbox, and a filesystem BLAKE3 CAS as specified in `docs/IMPLEMENTATION.md`. Storage
remains replaceable behind the graph contract.

---

## 4. Core events and external agent worldlines

### 4.1 Core ownership

The shared graph substrate owns one append-only, revision-addressable **core event journal** for every
first-party OS, Manager and Control event.

The journal exists so any authorized agent can attach at any time, replay from an ingest sequence,
then follow the live stream without polling any subsystem.

No global Agent ACK exists. One consumer can never delete or advance another consumer's history.

### 4.2 Event shape

Every event carries stable EventId, type, producer identity, graph revision where applicable,
monotonic/wall time, TraceId, referenced NodeIds/ArtifactIds and one typed payload from
`protocol/events.capnp`.

### 4.3 Event coverage

The core journal includes:
- graph commits;
- process/service/device/network/generation transitions;
- Manager discovery/resolution/execution/credential/inference transitions;
- every Control input, focus, selection, mode, lens, tree, native-surface, terminal, navigation and
  notification transition;
- dense lossless batches for high-rate input/telemetry classes.

An agent does not infer these transitions from screenshots or periodically scrape current state.

### 4.4 Agent-owned continuity

A specific agent may store:
- its own causal worldline;
- memory and retrieval indexes;
- goals/commitments;
- model conversations;
- worker/task state;
- learned procedures;
- preferences and self-model.

Those are agent implementation details. They may reference core NodeIds/EventIds, and an authorized
plugin may project agent-owned semantic dimensions into extension graph namespaces, but none becomes
a core Omnis authority.

## 5. OmnisOS

OmnisOS is the operating-system substrate. It is initially a Linux distribution derived from a
maintained fork of `nixpkgs`/NixOS. Linux remains the hardware kernel; OmnisOS is the system kernel in
Omnis product architecture.

### 5.1 Responsibilities

OmnisOS owns:

- boot and system activation;
- hardware and driver integration;
- users and sessions;
- filesystems and mounts;
- networking;
- service/process supervision integration;
- NixOS system configuration;
- system generations and rollback;
- physical resource enforcement;
- isolation and authority enforcement;
- host identity and remote-host participation;
- publication of authoritative physical/system facts into the graph;
- the shared graph substrate.

### 5.2 NixOS fork

OmnisOS must remain compatible with nixpkgs packages and as much upstream NixOS module behavior as
possible. The fork exists to add deep graph/event/control integration, not to gratuitously diverge
from the package ecosystem.

Upstream changes MUST remain a minimal reviewable patch stack. A permanent divergence requires an
explicit ADR naming the upstream behavior being replaced.

### 5.3 Desired and actual state

OmnisOS maintains a distinction between:

```text
desired persistent system state
actual physical/runtime system state
```

Nix/NixOS realizes the first. Runtime observation publishes the second. Their relationship is visible
in the graph.

### 5.4 Invariants

IOE's invariant concept survives as system-level machine constraints rather than language syntax.
Examples include:

- a required service is reachable;
- a protected model must remain local;
- a worker may consume at most a resource envelope;
- a credential must not be disclosed into model context;
- a host must provide a required capability before placement;
- a persistent package/service relationship remains satisfied.

An invariant whose inputs are entirely candidate Nix/graph state is checked before activation.
An invariant depending on live physical state is evaluated after activation and continuously from
authoritative OS observations. The invariant kind therefore determines the evaluation phase; an
implementation does not choose ad hoc timing.

### 5.5 Physical enforcement

Semantic authority compiles into the fixed v0 enforcement stack in `DECISION_COMPLETE_V0.md §§53–55,71`:
systemd transient services, mount/device/cgroup/system-call restrictions, cgroup v2, eBPF process and
network filters, UID/GID boundaries, and protected credential injection.

The Agent may reason freely; execution receives only the capabilities physically granted to it.

### 5.6 Reference configuration

The umbrella repository carries the v0 reference shape at [`examples/omnis.nix`](examples/omnis.nix).
`docs/IMPLEMENTATION.md` freezes the initial module families and the machine-managed Nix mutation
boundary; implementation must converge the example to those exact option paths rather than inventing
a second declaration schema.

### 5.7 Persistent transitions

Persistent structural changes use candidate system generations:

```text
Agent/user intention
  -> Manager resolves plan/resources
  -> candidate NixOS configuration
  -> evaluate
  -> build
  -> inspect graph/closure diff
  -> activate generation
  -> publish resulting events/state
```

Transient actions such as opening an application, running a compiler, navigating a URL, or invoking
a model do not create NixOS generations unless the desired persistent state changes.

---

## 6. OmnisManager

OmnisManager is a maintained fork/extension of `NixOS/nix`. It preserves Nix's evaluator, store,
derivations, package/environment semantics, and ecosystem compatibility while extending the manager
into a universal resource/capability/binding layer.

### 6.1 Canonical concepts

The Manager intentionally keeps its ontology small:

```text
Resource     something available or realizable
Capability   something that can be done
Binding      a resource/foreign identity can realize a capability
Execution    one concrete use of a binding
Constraint   a condition on resolution, placement, or execution
```

Packages, models, harnesses, GPUs, services, CLIs, APIs, libraries, devices, containers, VMs,
credentials, and remote hosts are resources rather than separate architecture families.

### 6.2 Nix integration

Nix remains the canonical mechanism for packages, derivations, store paths, environments, and builds.
Manager adds graph identities and semantic metadata above physical realizations.

A resource identity survives changes in:

- store path;
- version;
- host;
- provider;
- runtime;
- container/VM placement.

### 6.3 Capability resolution

A request is resolved conceptually as:

```text
semantic requirement
  -> capability
  -> constraints
  -> candidate bindings/resources
  -> placement/resource evaluation
  -> deterministic policy/ranking
  -> concrete execution
```

Selection policy must be inspectable and reproducible from its inputs. Learned recommendations may
inform candidate scoring, but hidden nondeterministic "first match wins" behavior is forbidden.

### 6.4 Required resource classes

The initial Manager must support resources for:

- Nix packages and derivations;
- executables and libraries;
- system/user services;
- local and remote hosts;
- containers and VMs;
- CPUs/GPUs/accelerators;
- devices;
- model artifacts;
- inference engines;
- model/API providers;
- MCP servers/clients;
- protocol/API endpoints;
- repositories/workspaces;
- credential/protected-value handles;
- arbitrary native/foreign handles.

### 6.5 Models and inference

Models and inference engines are ordinary Manager resources when the machine chooses to expose them.

```text
Capability: model.embed
  bindings -> local embedding runtime, ONNX, remote endpoint

Capability: model.reason
  bindings -> local LLM, remote API, specialist service
```

An external agent may use these Manager capabilities or its own model stack. Omnis does not embed,
launch, adapt, version-pin, or depend on external coding-agent harnesses.

### 6.6 Discovery

Discovery is deterministic-first:

1. existing graph/package metadata;
2. native descriptors/reflection;
3. protocol schemas and APIs;
4. compiler/runtime/LSP/index metadata;
5. CLI completion/manifests/structured help/man pages;
6. filesystem/source/debug symbols when available;
7. deterministic probing;
8. specialized learned interpretation;
9. general reasoning only for unresolved meaning.

Foreign provenance must record how each capability/relationship was learned.

### 6.7 Protected values

Credentials and sensitive data are protected resources/handles.

The Agent may know that a credential exists and what capabilities it can authorize without receiving
its plaintext value. Manager resolves authorized handles at execution time; OmnisOS enforces the
physical access boundary.

### 6.8 Effect metadata

Every Binding declares exactly one effect class from `manager.capnp::EffectClass`; discovery may
infer the class only when deterministic evidence supports it, otherwise the class is `opaque`:

```text
pure/deterministic
read-only
idempotent
retriable
reversible
compensatable
persistent external effect
opaque foreign effect
```

Unknown foreign operations are treated conservatively. A completed opaque external effect cannot be
pretended to roll back because a later internal operation failed.

### 6.9 Placement and optimization

Manager resolves both implementation and placement across local/remote resources.

Relevant constraints may include:

- CPU/GPU/RAM;
- latency;
- locality;
- privacy;
- credential availability;
- network reachability;
- model quality/context capacity;
- monetary/token cost;
- energy;
- warm caches/state;
- user/system policy.

Agent asks for semantic outcomes and hard constraints. Manager chooses the weakest/cheapest adequate
realization unless the caller requests a specific implementation.

---

## 7. Harness-agnostic agent access

There is no core OmnisAgent service.

Any authorized agent can consume Omnis through the **same three semantic surfaces**:

```text
OmnisOS       -> physical/system inspection and mutation
OmnisManager  -> resources/capabilities/executions
OmnisControl  -> interaction tree, graph desktop and renderer structure
```

The shared graph and core event journal provide common state and observation.

### 7.1 Two projections, one semantics

v0 ships two agent-access projections:

1. **MCP** — `omnis mcp` exposes the exact public OS/Manager/Control/graph operations as MCP
   tools/resources and exposes the core event journal as a replayable/subscribable resource.
2. **Plugin SDK** — typed generated clients expose the exact same operations/events to native agent
   plugins without MCP serialization.

Neither path owns additional semantics. `spec/agent_access.toml` is the parity registry and CI fails
when a public core operation/event exists without both projections.

### 7.2 No harness dependency

The core does not know Claude Code, Codex, OpenCode, DeepSeek Harness, or any other agent runtime.
There are no built-in harness adapters, harness version pins, harness routing chains, or provider
credentials injected into foreign agent processes.

An agent is simply a client with authority.

### 7.3 Direct Control authority

Authorized agents receive more structural interface access than ordinary pointer/keyboard interaction
exposes. They can create/remove/reparent Control nodes, materialize graph projections, bind semantic
identities, change representation/lens/mode, navigate/focus/select, attach actions and build
visualizations directly.

This is typed tree mutation, not screenshot observation or synthetic input.

### 7.4 Reference agent

The reference agent environment is developed separately by evolving `marius-patrik/dsh-stack`.
That project owns cognition, memory, model/provider use, tasks/workers and agent UX. Its Omnis
integration is an ordinary plugin/MCP client and is not required by an Omnis system release.

## 8. OmnisControl

OmnisControl is the universal machine control environment. It replaces the old `OmnisGUI` concept.
Rendering is one responsibility among several.

### 8.1 Responsibilities

OmnisControl owns:

- graph desktop;
- 2D and 3D graph interaction;
- graph-to-control projection;
- control tree and layout;
- shell/PTY interaction;
- navigation/focus/selection/lenses;
- inspectors and arbitrary visualizations;
- native Wayland/XWayland application regions;
- input routing;
- GPU rendering/composition;
- presentation events and structural mutation APIs.

### 8.2 Desktop model

Omnis has a desktop, but not a traditional app-grid desktop.

The desktop is an interactive representation of the shared graph. It has two equivalent modes over
the same identities:

- **2D** — Airgraph/Blueprint-like focus+context graph optimized for editing, precise manipulation,
  workflows, causal inspection, and dense information.
- **3D** — spatial graph projection optimized for large neighborhoods, clusters, causal depth,
  temporal exploration, and multidimensional relationships.

Toggling mode preserves focus, selection, lens, graph identities, and timeline frontier.

### 8.3 Control tree

Control derives an interactive tree from graph queries/projections:

```text
shared graph
  -> projection query/lens
  -> Control tree
  -> layout
  -> render scene
  -> GPU/platform compositor
```

The Control tree may contain ephemeral layout nodes, but semantic leaves reference shared graph
identities. The render scene is an optimized lowering, never a semantic source of truth.

### 8.4 Agent access

User interaction and Agent structural control share the same underlying state.

The user primarily manipulates materialized controls through pointer, keyboard, touch, and explicit push-to-talk voice input. An authorized agent client has direct structural access and may:

- create/remove/replace/move views;
- bind a view to another graph identity;
- change lens or representation;
- focus/select/navigate;
- split or reorganize the workspace;
- create live visualizations;
- attach actions/interactions;
- persist a Control arrangement only when the user explicitly requests persistence, an existing durable presentation preference requires it, or the Agent-selected action has a persistence postcondition; otherwise the arrangement remains transient.

These mutations emit events like user interactions do.

### 8.5 One renderer

Terminal, browser semantics, widgets, code, graphs, media, 2D, and 3D do not require independent
renderer architectures.

Control lowers them into one GPU-oriented render scene. The v0 compositor is Wayland-native, built
with Smithay and wgpu according to `docs/CONTROL_RENDER_V0.md`.

Existing applications remain existing applications. Wayland/XWayland surfaces are delegated/native
regions where direct semantic rendering is unavailable or undesirable.

### 8.6 Shell and input

The default interaction may be visually terminal-centric, but the shell is a graph-native Control
surface rather than a separate product.

Submission resolution is deterministic-first:

```text
valid shell syntax / executable -> real shell execution
known URI/path/graph identity    -> navigate/open
known capability                -> invoke
known structured query          -> query graph
otherwise                       -> unresolved semantic input event / registered agent client
```

No explicit switch between "terminal" and "AI chat" is required.

---

## 9. Addressing and identity

Every stable graph identity is addressable. Human-friendly names are aliases, not identity.

An internal URI scheme may expose graph objects, for example:

```text
omnis://node/<id>
omnis://event/<id>
omnis://resource/<id>
omnis://capability/<id>
omnis://scene/<id>
omnis://memory/<id>
```

Protocol v0 uses `omnis://` stable-reference URIs as defined by `docs/PROTOCOLS.md`; first-party
surfaces exchange NodeId/EventId/ArtifactId values directly on the wire rather than copied
descriptive text.

---

## 10. API and protocol principles

### 10.1 Shared semantics

There must not be separate GUI, CLI, MCP, or plugin semantics for the same capability. All are
projections of the same typed core operation.

### 10.2 Event-first integration

First-party components publish every meaningful transition to the core event journal; agents consume
that journal rather than scraping/polling subsystems.

### 10.3 Deterministic-first operation

Exact structured mechanisms are preferred to learned interpretation whenever they can satisfy the
same requirement.

### 10.4 Explicit incompatibility

If a target/control mode cannot preserve required semantics, it reports incompatibility rather than
silently degrading behavior.

### 10.5 Provenance

Resources, bindings, graph relations, events, and generated views retain enough provenance to
explain where they came from and how strongly they are known.

---

## 11. Security model

Security belongs at the physical/core API boundary, not inside one privileged agent.

Required principles:
- agents receive only the OS/Manager/Control authorities granted to their caller/session;
- secrets are protected handles, not MCP/plugin payload text;
- one agent client never inherits another client's cursor/state/credentials;
- graph visibility and extension-namespace writes follow granted authority;
- external effects retain caller, TraceId and causal identity;
- persistent system changes remain inspectable generations and reversible where the physical
  operation permits it.

## 12. Core optimization and external cognition

OmnisManager may optimize placement, runtime implementation, batching, caching and resource
allocation when semantics permit it.

Cognitive adaptation, memory learning, worker strategies, self-modeling and agent self-modification
are outside the three core authorities. A connected agent may propose Control mutations, Manager
executions or OmnisOS generation changes, but those proposals cross the same typed boundaries as any
other client.

Changes to OmnisOS, OmnisManager or OmnisControl themselves are candidate builds/generations evaluated
outside the active implementation before promotion.

## 13. Host independence

A semantic resource or activity is not identified by the machine currently executing it.

Manager may place execution on:

- local host;
- another Omnis machine;
- container;
- VM;
- remote server;
- cloud resource;
- GPU/accelerator host.

Placement preserves graph/resource/activity identity and emits causal events describing the physical
realization.

The long-term system may span laptop, workstation, phone, and server without treating one device as
the conceptual owner of all computation.

---

## 14. Existing software compatibility

Unmodified Linux software must work from the beginning.

Existing software progresses through understanding levels rather than requiring a port:

```text
opaque executable/surface
  -> OS-observable
  -> metadata/CLI-discoverable
  -> accessibility/protocol discoverable
  -> API/source/tooling discoverable
  -> semantically rich Manager binding
```

An external agent can initially interact through weaker foreign interfaces and may later propose
stronger deterministic Manager bindings.

Vision + synthetic mouse/keyboard is a compatibility fallback, not the preferred first-party
interaction mechanism.

---

## 15. Repository/product topology

The core project split is:

```text
omnis/             umbrella architecture, shared contracts, MCP/plugin projection, integration tests
omnis-os/          NixOS/nixpkgs-derived operating system
omnis-manager/     Nix-derived resource/capability/execution manager
omnis-control/     graph desktop/compositor/control subsystem
```

The reference agent is **not** a core repository boundary:

```text
dsh-stack/         separately released reference agent environment + Omnis integration plugin
```

The umbrella repository owns cross-component protocol versions, architecture, end-to-end tests,
agent-access parity, reference configuration, release composition and compatibility matrices.
A core release does not pin a DSH/agent version.

## 16. Implementation invariants

The following are hard architectural constraints:

1. **Exactly three core authorities: OmnisOS, OmnisManager, OmnisControl.**
2. **One stable identity space and one shared multidimensional current-state graph.**
3. **One append-only core event journal contains every meaningful first-party transition.**
4. **No agent implementation is required for boot, Control, package management, execution or recovery.**
5. **Every public OS/Manager/Control/graph operation has MCP and native-plugin projection parity.**
6. **No MCP/plugin projection invents semantics absent from the typed core APIs.**
7. **Graph dimensions have explicit write ownership; external agents use granted extension namespaces.**
8. **Control tree is derived from/shared with graph state; render scene is only a lowering.**
9. **2D and 3D Control modes represent the same identities and interaction state.**
10. **Authorized agents may structurally mutate Control directly without screenshot observation.**
11. **Nix evaluation/build remains deterministic and model-free.**
12. **Persistent structural system changes are inspectable generations.**
13. **Transient execution does not require rewriting persistent Nix configuration.**
14. **Capabilities describe meaning; bindings describe concrete realizations.**
15. **Existing mature tools are bound before equivalent functionality is reimplemented.**
16. **Discovery is deterministic-first and preserves foreign provenance.**
17. **Protected values remain handles unless explicit authorized disclosure is required.**
18. **Semantic identity survives version, host, path, process, provider and agent changes.**
19. **External effects are accounted for honestly; opaque effects are not falsely rolled back.**
20. **The core contains no built-in external-agent harness integration or harness-specific version policy.**

## 17. Non-goals

The initial architecture explicitly does not require:

- a custom programming language;
- a custom Linux kernel;
- replacement of nixpkgs packages;
- replacement of existing applications;
- a new model-provider API standard;
- a traditional desktop shell/dock/application launcher model;
- a built-in agent runtime or monolithic executive LLM;
- forcing all software into Omnis-native UI;
- representing every kernel interrupt/syscall as a high-level cognitive event.

A custom kernel may be explored later only if Linux becomes a demonstrated blocker to required
semantics, security, or performance.

---

## 18. Completion criterion

A first complete **core Omnis** implementation exists when one machine can:

1. boot OmnisOS from its NixOS-derived configuration;
2. expose authoritative physical/system state into the shared graph;
3. durably journal every first-party OS/Manager/Control event;
4. use OmnisManager to install/discover/resolve arbitrary packages and resource bindings;
5. run generic model/inference resources without requiring any agent runtime;
6. boot OmnisControl as the primary environment;
7. present the same graph desktop in interactive 2D and 3D modes;
8. execute real Linux shell commands and unmodified Wayland/XWayland applications;
9. apply persistent system changes through candidate Nix generations and roll them back;
10. expose **all** public OS/Manager/Control/graph operations and the complete event journal through
    MCP;
11. expose the same operation/event set through the native plugin SDK with automated parity tests;
12. permit an independently installed agent, including the DSH reference agent, to inspect state,
    receive every event and structurally mutate Control without any core change;
13. continue functioning identically when that agent is absent, replaced or disconnected.

At that point Omnis is an agent-ready operating environment rather than an operating system whose
identity depends on a particular agent implementation.

### 18.1 Decision completeness

For v0, implementation workers do not choose observable behavior. If `ARCHITECTURE.md`,
`docs/IMPLEMENTATION.md`, `docs/DECISION_COMPLETE_V0.md`, subsystem specs, protocol schemas and
tests do not determine a behavior, the item is blocked as a specification defect. "Reasonable
default", "equivalent library", and "temporary fallback" are not implementation authority.


### 18.2 Canonical implementation source files

The following are normative v0 implementation inputs, not examples:

```text
schema/graph.sql
protocol/*.capnp
spec/agent_access.toml
docs/AGENT_ACCESS_V0.md
docs/ONTOLOGY_V0.md
docs/NIX_OPTIONS_V0.md
```

An implementation worker copies/uses these contracts; it does not redesign their schema, prompt,
identifier or option surfaces.
