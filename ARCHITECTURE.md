# Omnis — Architecture

**Status: NORMATIVE.** This document defines the system architecture. Supporting documents may
expand implementation detail but must not contradict it.

Omnis is a graph-native, agentic operating system built initially on Linux, Nix, and NixOS. It is
not a desktop application, an AI assistant, a shell wrapper, or a new programming language.

The system has four first-class authorities:

1. **OmnisOS** — physical/system authority.
2. **OmnisManager** — resource/capability authority.
3. **OmnisAgent** — cognitive/event/memory authority.
4. **OmnisControl** — interaction/presentation authority.

They share one multidimensional graph and one stable identity space. They do not maintain competing
models of the same object.

---

## 1. Architectural thesis

Omnis is built around five statements.

### 1.1 One world, one graph

Every meaningful object in the machine has one stable identity in a shared multidimensional graph.
A repository, process, model, package, host, GPU, capability, worker, memory, scene, surface, or Nix
generation is not copied into four subsystem-specific databases and reconciled later.

Different components contribute different dimensions and relations over the same identities.

### 1.2 One worldline

OmnisAgent stores the immutable causal worldline of experience. The graph is current structured
state; the worldline is what happened.

The graph may be rebuilt, reinterpreted, reindexed, or projected differently. Historical events are
not silently rewritten to match newer interpretations.

### 1.3 Bind reality; do not require it to become Omnis

Existing applications, CLIs, services, libraries, models, agent harnesses, containers, VMs, package
managers, protocols, and devices remain real external systems. Omnis discovers, binds, controls, and
progressively understands them.

Reimplementation requires a material reason. Integration is preferred to replacement.

### 1.4 AI chooses semantics; deterministic systems realize physics

AI never becomes part of Nix evaluation or another deterministic build primitive.

OmnisAgent may form an intention. OmnisManager resolves resources, capabilities, bindings, and
placement. OmnisOS deterministically realizes persistent state and enforces physical constraints.

### 1.5 The interface is the graph made interactive

OmnisControl does not maintain a separate semantic UI universe. It projects graph identities into a
control tree, lowers that tree into render state, and emits interactions back as graph mutations and
events.

The Agent receives events directly and can structurally mutate Control state. It does not need to
observe screenshots or simulate clicks for first-party surfaces.

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
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            │                         │                         │
            ▼                         ▼                         ▼
       ┌─────────┐              ┌──────────────┐           ┌────────────┐
       │ OmnisOS │              │ OmnisManager │           │ OmnisAgent │
       └────┬────┘              └──────┬───────┘           └─────┬──────┘
            │                          │                         │
            │ physical realization     │ capability execution    │ cognition
            └──────────────┬───────────┴───────────────┬─────────┘
                           ▼                           ▼
                        Linux                      external reality
```

Every meaningful transition produced by OS, Manager, Control, external integrations, or Agent
workers enters OmnisAgent's event gateway.

The graph substrate is **not a fifth product or semantic authority**. It is a shared system ABI and
current-state substrate supplied by OmnisOS and used by all four components.

---

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

OmnisOS provides a minimal internal service, working name `omnis-graphd`, responsible only for:

- stable identity allocation;
- atomic graph transactions;
- current-state storage;
- subscriptions/change streams;
- indexed graph queries;
- authority/write validation;
- revisioning and local recovery.

It contains no cognition, capability policy, UI logic, package semantics, or memory semantics.

The first implementation may use SQLite/WAL plus purpose-built indexes. Storage is replaceable; the
graph contract is not.

---

## 4. Worldline and events

### 4.1 Ownership

OmnisAgent owns the canonical event worldline.

Every meaningful transition from a first-party component must be represented as an event. Components
do not require Agent polling to discover their state transitions.

### 4.2 Event shape

```text
Event
  id
  type
  schema
  source
  actor
  timestamp
  causal_parents[]
  graph_revision
  entities[]
  artifact_refs[]
  payload_ref
  provenance
  correlation/trace
```

Events form an append sequence for replay and a causal DAG for meaning.

### 4.3 Event coverage

Required event producers include:

- graph transactions;
- keyboard, pointer, focus, selection, navigation, and control interactions;
- scene/control-tree changes;
- process/service lifecycle;
- filesystem/repository changes;
- package/build/generation activity;
- device/network/resource changes;
- Manager discovery/resolution/execution;
- model and inference requests/results;
- external agent harness lifecycle/tool results;
- Agent worker lifecycle/results;
- memory/context/consolidation events;
- internally generated Agent events.

High-frequency physical telemetry may be represented through lossless aggregation windows or
referenced artifacts, but causal identity and provenance must not disappear merely because the Agent
cannot process each raw sample synchronously.

### 4.4 Graph versus worldline

```text
worldline = historical causal truth
shared graph = current structured state
indexes = derived query accelerators
Control tree = interactive projection
render scene = GPU-oriented lowering
```

No derived layer becomes canonical merely because it is convenient to query.

---

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

Upstream changes should be carried as a minimal reviewable patch stack until a permanent divergence
is justified.

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

Pure configuration invariants should be checked before activation where possible. Runtime invariants
may be continuously evaluated from current graph state and enforced by physical mechanisms.

### 5.5 Physical enforcement

Semantic authority must compile into real physical authority. Depending on the operation, OmnisOS may
use Linux mechanisms such as namespaces, cgroups, seccomp, LSM/Landlock/eBPF hooks, UID/GID
boundaries, mount/network namespaces, device isolation, and credential brokers.

The Agent may reason freely; execution receives only the capabilities physically granted to it.

### 5.6 Persistent transitions

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
- external agent harnesses;
- MCP servers/clients;
- protocol/API endpoints;
- repositories/workspaces;
- credential/protected-value handles;
- arbitrary native/foreign handles.

### 6.5 Agent harnesses and inference

External harnesses and inference engines belong in Manager, not Agent.

Examples:

```text
Capability: code.agent
  bindings -> Claude Code, Codex, OpenCode, future harnesses

Capability: model.embed
  bindings -> local embedding runtime, ONNX, remote endpoint

Capability: model.reason
  bindings -> local LLM, remote API, specialist service
```

OmnisAgent requests capabilities; it does not embed provider-specific integration into its cognitive
core.

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

Bindings should declare or infer execution properties where known:

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

## 7. OmnisAgent

OmnisAgent is a core subsystem and the persistent cognitive identity of the machine. It is not a
single model and has no privileged universal LLM loop.

### 7.1 Responsibilities

OmnisAgent owns:

- event ingestion and causal worldline;
- episodic/semantic/procedural/project memory;
- entity and relation interpretation;
- judgement/routing;
- context compilation;
- working-memory activation;
- goals, commitments, hypotheses, expectations;
- worker/workflow orchestration;
- reflection and consolidation;
- learned procedures and routing;
- endogenous events/internal dynamics;
- self-model and candidate self-evolution.

### 7.2 Event-driven cognition

The basic cognitive unit is an event:

```text
event
  -> judgement
  -> context compilation
  -> worker/workflow dispatch or null action
  -> observations/effects
  -> new events
```

External user requests are one event source among many. There is no semantic `IDLE` state. A living
Agent may be busy, waiting, consolidating, exploring, sleeping, or doing nothing.

### 7.3 Memory

The event worldline is historical ground truth. Derived memory is revisable.

Required memory forms include:

- events;
- episodes;
- assertions/facts with temporal validity;
- entities and relationships;
- decisions;
- goals and commitments;
- preferences with scope;
- project state;
- procedures/skills;
- expectations/predictive memory;
- artifacts and provenance.

Embeddings, summaries, graphs, and indexes are representations, not canonical truth.

### 7.4 Context

Context is compiled for a specific event, worker, and purpose. It is not an ever-growing transcript.

The context compiler may combine causal ancestors, graph neighborhoods, activated memories, project
state, code structure, artifacts, prior attempts, negative evidence, and protected-information
constraints under token/latency/privacy budgets.

### 7.5 Models and workers

Models are Manager resources. Workers are Agent cognitive roles/activations that may use one or more
Manager capabilities.

Initial worker families include judgement, retrieval, reasoning, research, code, verification,
simulation, memory/reflection, learning, and evolution.

Every worker result re-enters the event stream. No worker maintains a hidden alternate history.

### 7.6 External agents

Claude Code, Codex, OpenCode, and future harnesses are Manager resources that OmnisAgent may invoke as
workers. Native harness hooks should emit events. Inference interception may provide a universal
fallback so model-bound contexts can still participate in Omnis memory even when a harness exposes
little semantic lifecycle information.

---

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

The user primarily manipulates materialized controls through pointer/keyboard/touch/voice. The Agent
has direct structural access and may:

- create/remove/replace/move views;
- bind a view to another graph identity;
- change lens or representation;
- focus/select/navigate;
- split or reorganize the workspace;
- create live visualizations;
- attach actions/interactions;
- persist a useful control arrangement where appropriate.

These mutations emit events like user interactions do.

### 8.5 One renderer

Terminal, browser semantics, widgets, code, graphs, media, 2D, and 3D do not require independent
renderer architectures.

Control lowers them into one GPU-oriented render scene. The initial compositor implementation should
be Wayland-native, built using Smithay-class compositor primitives and wgpu-class GPU rendering.

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
otherwise                       -> OmnisAgent semantic interpretation
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

Public URI details are implementation-specific until the protocol spec freezes them, but all first-
party surfaces must be able to exchange stable references rather than copied descriptive text.

---

## 10. API and protocol principles

### 10.1 Shared semantics

There must not be separate GUI, CLI, Agent, or MCP semantics for the same capability. Different
surfaces may expose different representations of one operation.

### 10.2 Event-first integration

First-party components publish events; Agent does not depend on scraping/polling them.

### 10.3 Deterministic-first operation

Exact structured mechanisms are preferred to learned interpretation whenever they can satisfy the
same requirement.

### 10.4 Explicit incompatibility

If a target/control mode cannot preserve required semantics, it reports incompatibility rather than
silently degrading behavior.

### 10.5 Provenance

Resources, bindings, graph relations, memories, and generated views retain enough provenance to
explain where they came from and how strongly they are known.

---

## 11. Security model

Security belongs at the physical boundary rather than as a semantic censor of cognition.

The cognitive plane may formulate arbitrary hypotheses/plans within model capability. The effect
plane grants only the physical handles and authorities available to that execution.

Required principles:

- secrets are handles, not prompt text;
- no worker inherits broad user authority by default;
- host/graph visibility follows granted authority;
- protected data carries disclosure constraints into model/Control projections;
- external effects retain causal and actor identity;
- candidate self-modification is isolated from the active system until realization/promotion;
- persistent system changes remain representable as generations and reversible where the underlying
  physical operation permits it.

---

## 12. Self-modification and optimization

Omnis may optimize itself at several levels.

### 12.1 Runtime optimization

Manager may change placement, runtime implementation, batching, caching, model routing, or resource
allocation when semantics permit it.

### 12.2 Cognitive adaptation

Agent may learn memories, procedures, retrieval policies, routing preferences, competence estimates,
and worker strategies.

### 12.3 Structural evolution

Changes to Omnis components themselves are candidate implementations/generations. They are built and
evaluated outside the currently active implementation before promotion.

For OmnisOS and Manager, Nix derivations/generations provide the natural realization boundary.
Agent/Control variants should use similarly reproducible candidate artifacts and explicit lineage.

---

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

The Agent may initially interact through weak interfaces and later compile repeated successful
behavior into stronger deterministic capabilities.

Vision + synthetic mouse/keyboard is a compatibility fallback, not the preferred first-party
interaction mechanism.

---

## 15. Repository/product topology

The intended project split is:

```text
omnis/             umbrella architecture, integration, compatibility tests
omnis-os/          NixOS/nixpkgs-derived operating system
omnis-manager/     Nix-derived manager
omnis-agent/       event/memory/cognition subsystem
omnis-control/     graph desktop/compositor/control subsystem
```

A future organization may host maintained upstream forks separately, but the product boundaries above
remain.

The umbrella repository owns cross-component protocol versions, architecture, end-to-end tests,
reference configuration, release composition, and compatibility matrices.

---

## 16. Implementation invariants

The following are hard architectural constraints:

1. **One stable identity space across OS, Manager, Agent, and Control.**
2. **One shared multidimensional current-state graph.**
3. **OmnisAgent owns the immutable causal worldline and memory.**
4. **Every meaningful first-party transition reaches Agent as an event; Agent does not poll the UI.**
5. **Graph dimensions have explicit write ownership.**
6. **Control tree is derived from/shared with graph state; render scene is only a lowering.**
7. **2D and 3D Control modes represent the same identities and interaction state.**
8. **Agent may structurally mutate Control state directly.**
9. **Models, inference engines, and external agent harnesses are Manager resources.**
10. **Nix evaluation/build remains deterministic and model-free.**
11. **Persistent structural system changes are realized as inspectable generations.**
12. **Transient execution does not require rewriting persistent Nix configuration.**
13. **Capabilities describe meaning; bindings describe concrete realizations.**
14. **Existing mature tools are bound before equivalent functionality is reimplemented.**
15. **Discovery is deterministic-first and preserves foreign provenance.**
16. **Protected values remain handles unless explicit authorized disclosure is required.**
17. **Semantic identity survives version, host, path, process, and provider changes.**
18. **External effects are accounted for honestly; opaque effects are not falsely rolled back.**
19. **Agent context is compiled per event/worker, never a global ever-growing transcript.**
20. **No LLM or provider is the identity of OmnisAgent.**
21. **There is no semantic idle state; null/no work is valid.**
22. **No component creates a parallel authoritative world model for objects already in the shared graph.**

---

## 17. Non-goals

The initial architecture explicitly does not require:

- a custom programming language;
- a custom Linux kernel;
- replacement of nixpkgs packages;
- replacement of existing applications;
- a new model-provider API standard;
- a traditional desktop shell/dock/application launcher model;
- a monolithic executive LLM;
- forcing all software into Omnis-native UI;
- representing every kernel interrupt/syscall as a high-level cognitive event.

A custom kernel may be explored later only if Linux becomes a demonstrated blocker to required
semantics, security, or performance.

---

## 18. Completion criterion

A first complete Omnis implementation exists when one machine can:

1. boot OmnisOS from its NixOS-derived configuration;
2. expose authoritative physical/system state into the shared graph;
3. use OmnisManager to install/discover/resolve arbitrary packages and resource bindings;
4. run local/remote inference engines and external agent harnesses as Manager resources;
5. maintain OmnisAgent's causal event worldline and structured memory;
6. compile task-specific context and dispatch heterogeneous workers;
7. boot OmnisControl as the primary environment;
8. present the same graph desktop in interactive 2D and 3D modes;
9. execute real Linux shell commands and unmodified Wayland/XWayland applications;
10. allow Agent and user actions to operate on the same graph identities;
11. allow Agent direct structural mutation of Control projections;
12. apply persistent system changes through candidate Nix generations and roll them back;
13. preserve events/provenance across restart;
14. continue functioning when any particular model/provider/harness is replaced or unavailable.

At that point Omnis is not merely an AI-enabled Linux distribution. It is a machine whose operating
state, available actions, cognition, and interface are all different projections of one persistent,
addressable system.