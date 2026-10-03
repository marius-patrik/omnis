# OmnisControl

**Status: normative supporting specification.**

OmnisControl is the interactive control environment of Omnis. It owns the graph desktop, Control
tree, input/navigation, shell integration, native surface composition, and GPU rendering.

It replaces the old `OmnisGUI` concept because rendering is only one part of its responsibility.

---

## 1. Desktop thesis

Omnis has a desktop, but the desktop is not an application launcher plus windows. It is an
interactive projection of the shared multidimensional graph.

Everything visible should either:

- represent one or more shared graph identities; or
- be ephemeral Control structure required to arrange/interact with those identities.

The primary desktop modes are **2D** and **3D**. They are different spatial projections of the same
state, not separate applications or backends.

---

## 2. 2D mode

2D is the precision/control mode, inspired by Airgraph-like focus navigation and Blueprint/node
editors without exposing an unreadable wall of nodes.

Required behaviors:

- focus+context neighborhoods;
- typed relations/ports where useful;
- semantic clustering/collapse;
- smooth re-centering on selected identity;
- inline inspectors;
- edge/lens filtering;
- DAG/workflow editing where the underlying object is executable structure;
- drag/drop operations mapped to semantic graph actions;
- pane/split representations when dense conventional layouts are superior;
- timeline integration.

The complete graph is never the default view. Control queries the relevant neighborhood for current
focus/lens/LOD.

---

## 3. 3D mode

3D is the large-scale spatial exploration mode.

The extra dimension must encode meaning, such as:

- causal depth;
- time;
- abstraction level;
- host/physical topology;
- semantic cluster separation;
- activity/workflow depth.

3D may not add arbitrary depth merely for appearance.

Navigation must preserve stable identity and allow seamless transition back to 2D at the same focus,
selection, lens, and timeline frontier.

---

## 4. Lenses

The same focus can be projected through lenses including:

```text
physical
system
resource
capability
binding
execution
causal
activity
authority
memory/cognitive
provenance
temporal
presentation
network
```

A lens changes which relations, annotations, clusters, and controls are emphasized. It does not
change graph identity.

Multiple compatible dimensions may be overlaid.

---

## 5. Semantic levels of detail

Zoom/focus depth changes semantic granularity rather than only visual scale.

Example:

```text
far      -> hosts, projects, major activities, memory regions
medium   -> services, workflows, repositories, worker groups, capability clusters
near     -> processes, executions, events, files, workers, resources
closer   -> context, evidence, tool calls, graph mutations, AST/workflow nodes
inspect  -> raw artifacts, source, model output, traces, exact properties
```

Collapsed clusters retain stable identity where they correspond to meaningful graph groups.

---

## 6. Timeline/worldline

Control exposes OmnisAgent's causal worldline as a first-class navigation dimension.

Timeline interaction must support:

- chronological browsing;
- causal branches;
- worker/activity lanes;
- speculative/self-evolution branches;
- selecting a historical event/frontier;
- reconstructing available graph/memory projections for that frontier where retained data permits;
- returning to live state.

The timeline is not merely a log viewer.

---

## 7. Control tree

Control builds `ControlTree` from graph projections.

Conceptual node classes:

```text
Container/Layout
GraphProjection
Text/Glyph content
Terminal/PTYShell
Document/Editor
Table
Chart/Plot
2DGraph
3DGraph
Media
Inspector
NativeSurface
InputSurface
Overlay
```

These are presentation constructs, not new domain identities.

A control representing a graph object stores that `NodeId` directly.

---

## 8. Render scene

Control lowers `ControlTree` to a GPU-oriented scene. Initial primitives may include:

```text
quad
text/glyph run
path/vector geometry
texture/render target
material/3D layer
native/delegated surface region
```

This scene is private render IR and can be aggressively optimized/rebuilt.

It must never become the semantic source of truth.

---

## 9. Renderer implementation

OmnisControl v0 uses:

- Smithay for Wayland compositor/DRM/input foundations;
- wgpu for the GPU renderer;
- a Rust text shaping/font stack pinned by the component lockfile;
- XWayland compatibility;
- platform accessibility publication;
- direct input handling.

Omnis should not fork a full traditional desktop environment because that would import the wrong
interaction ontology.

`omnis-control` is implemented directly on Smithay; it does not fork a traditional desktop or a
second compositor framework.

---

## 10. Native applications

Existing Wayland/XWayland applications run unmodified.

A native application surface is represented in the graph and delegated to the compositor in a
`NativeSurface` Control region.

Control may know/process:

- surface identity;
- owning process/resource;
- geometry/z-order;
- focus/input routing;
- accessibility/protocol metadata;
- associated Manager capabilities.

It does not need to re-render application pixels when native composition is more correct or required.

---

## 11. Web/browser content

"Browser" is not a second Omnis renderer.

Web content may be represented through several levels:

```text
semantic DOM/accessibility translation into Control primitives
browser engine surface/native surface
texture capture when appropriate
external browser application surface
```

Navigation state and web identities are graph-addressable. Exact URL input should bypass broad Agent
reasoning.

---

## 12. Shell

The shell is a first-class Control surface and may be the default focused view at boot.

It must expose real Linux shell semantics rather than reimplementing them incompletely:

- pipes/redirection;
- job control;
- environment;
- TTY/PTY behavior;
- signals;
- interactive programs;
- completions.

Control wraps/hosts a real shell execution backend while adding graph-aware resolution around it.

---

## 13. Unified input resolver

One primary input surface can route:

```text
shell syntax/executable -> shell
URI/path/address        -> navigate/open
Graph NodeId/alias      -> focus/materialize
known capability        -> Manager invoke
structured Control cmd  -> Control mutation
otherwise               -> Agent semantic event
```

The resolver uses deterministic parsing before classification/LLM reasoning.

---

## 14. User and Agent authority

User and Agent interact with the same Control state but through different affordances.

User:

```text
click/type/drag/scroll/select/focus/gesture/voice
```

Agent:

```text
query graph projection
create/remove/replace Control nodes
change lens
change focus/selection
bind identities/data/capabilities
restructure layout
materialize a resource
attach interactions
open native surfaces
```

Agent therefore has **more structural access to Control than the user interface exposes directly**.
This is intentional. Machine authority for external effects remains governed by Manager/OS execution
capabilities; Control structural access alone does not grant arbitrary filesystem/network/secret
access.

---

## 15. Events

Every meaningful Control transition emits an Agent event, including:

- input submissions;
- clicks/selections/focus;
- navigation;
- drag/drop semantic operations;
- scene/control mutations;
- 2D/3D toggle;
- lens/timeline changes;
- native surface lifecycle;
- shell lifecycle/results;
- generated visualization interactions.

Agent-originated Control mutations also emit events so their consequences are part of the same
causal history.

---

### 15.1 Raw event delivery

Control never requires Agent to inspect the rendered scene to discover first-party interaction.
Keyboard, button, touch, scroll, focus, selection, navigation, tree mutation and native-surface
lifecycle events are emitted directly with stable ordering metadata.

Pointer-motion and other dense streams may be grouped into short lossless batches before durable
enqueue. Each original item retains producer sequence and monotonic timestamp inside the batch;
Agent can expand/replay it exactly.

## 16. Accessibility

Because Control owns custom rendering, native accessibility trees are mandatory, not optional.

Graph semantics should improve accessibility: a rendered identity already has role, label,
relationships, actions, and provenance that can inform AT-SPI and other platform accessibility
interfaces.

Delegated native surfaces retain their platform accessibility semantics where available.

---

## 17. Persistence

Presentation state may be transient or persistent.

Persistent Control state includes only useful user/system intent such as:

- saved workspaces/scenes;
- pinned identities;
- preferred lenses/layouts;
- keymaps/themes;
- explicit materializations.

Incidental render/layout cache state remains ephemeral.

Agent may propose/persist useful workspace arrangements through the same Control state APIs.

---

## 18. Hard invariants

1. One semantic object retains one shared graph identity in every view.
2. 2D and 3D are projections of the same Control/graph state.
3. Switching mode preserves focus/selection/lens/frontier.
4. Control does not maintain a competing semantic scene graph.
5. Render scene is an implementation lowering.
6. Every meaningful interaction emits an Agent event.
7. Agent has direct structural Control access.
8. Existing native apps remain runnable without Omnis rewrites.
9. Shell is real Linux shell execution, not an imitation.
10. Deterministic routing precedes model reasoning.
---

## 19. v0 runtime binding

`omnis-control` is one process with three execution domains: Smithay/calloop on the compositor
thread, a dedicated wgpu render thread, and a Tokio runtime for graph/Agent/Manager RPC, PTYs and
browser protocol I/O. All queues are bounded and the frame loop never waits for Agent/model work.

The render pipeline is:

```text
graph revision -> ProjectionSpec/Lens -> ControlTree -> layout -> RenderScene -> wgpu -> DRM/KMS
```

Initial render primitives are `Group`, `Rect`, `RoundedRect`, `Path`, `GlyphRun`, `Image`, `Mesh`,
`NativeSurface`, `Clip` and `Transform`.

The shell uses a real PTY, parses terminal output through `vte` into a cell model, then renders cells
as normal scene primitives. XWayland is a managed child. Existing browsers are Wayland clients; CDP,
WebDriver BiDi and accessibility data are Manager bindings rather than a second browser renderer.

2D and 3D consume the same selected graph identities. Mode switching changes only layout/projection
state and therefore preserves focus, selection, lens and timeline frontier.
