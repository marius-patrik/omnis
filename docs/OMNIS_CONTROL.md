# OmnisControl

**Status: normative supporting specification.**

OmnisControl is the interactive control environment of Omnis. It owns the graph desktop, Control
tree, input/navigation, shell integration, native surface composition, and GPU rendering.

It replaces the old `OmnisGUI` concept because rendering is only one part of its responsibility.

---

## 1. Desktop thesis

Omnis has a desktop, but the desktop is not an application launcher plus windows. It is an
interactive projection of the shared multidimensional graph.

Every first-party visible element MUST either:

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

The v0 ControlTree is exactly the typed structure in
[`CONTROL_RENDER_V0.md`](CONTROL_RENDER_V0.md) and `protocol/control_scene.capnp`.

First-party node kinds are the closed v0 enum:

```text
container split scroll graphProjection text terminal document editor
table chart media inspector nativeSurface inputSurface overlay timeline
```

Each Control RPC node carries one typed `ControlNodeState`; arbitrary first-party string kinds and
untyped property maps are not a v0 surface. A node representing shared semantic state retains that
NodeId separately from its ControlNodeId.

Layout uses Taffy under the exact constraints/order in `CONTROL_RENDER_V0.md`.

---

## 8. Render scene

ControlTree lowers to the private `RenderScene` defined in `control_scene.capnp`:

```text
Group Transform Clip Rect RoundedRect Path GlyphRun Image Mesh NativeSurface
```

The schema, coordinates, color encoding, paint/depth order, clipping, hit testing, text shaping, path
tessellation, native-buffer import and frame boundary are all normative in `CONTROL_RENDER_V0.md`.

RenderScene is disposable lowering and never semantic truth.

---

## 9. Renderer implementation

OmnisControl v0 uses exactly:

- Smithay/calloop for Wayland, DRM/KMS and input;
- wgpu for GPU rendering;
- Taffy for ControlTree box/flex layout;
- cosmic-text/fontconfig for shaping and font fallback;
- Lyon for vector path tessellation;
- VTE for terminal parsing;
- AccessKit/AT-SPI for custom accessibility;
- XWayland for X11 compatibility.

There is one renderer. No GTK/Qt/Electron/Tauri/TUI/browser-engine renderer is introduced.

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

Navigation state and web identities are graph-addressable. Exact URL input bypasses broad Agent
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

Graph semantics feed accessibility directly: a rendered identity already has role, label,
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
