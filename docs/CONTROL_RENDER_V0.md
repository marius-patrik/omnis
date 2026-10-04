# OmnisControl v0 ControlTree and RenderScene Contract

**Status: NORMATIVE.** This document freezes the presentation data model and one-renderer lowering.
Implementation agents do not choose a widget toolkit, layout engine, scene primitive model, coordinate
system, paint order, clipping strategy, text shaper, path tessellator, hit-test algorithm or native
surface composition path.

Canonical sources:

```text
protocol/control_scene.capnp
protocol/control.capnp
spec/control_render.toml
theme/omnis-dark.json
```

## 1. One presentation tree

The persistent/interactive presentation structure is the ControlTree. First-party nodes use the
closed v0 `ControlNodeKind` enum from `control_scene.capnp`:

```text
container
split
scroll
graphProjection
text
terminal
document
editor
table
chart
media
inspector
nativeSurface
inputSurface
overlay
timeline
```

A node can represent a shared semantic graph NodeId, but its presentation identity is a ControlNodeId.
No first-party v0 code creates ad-hoc string node kinds or untyped property bags.

Node state is exactly `ControlNodeState`; public Agent/user mutations replace typed state through
`TreeTransaction`.

## 2. Tree ownership and ordering

Each node has zero or one parent. The root has none.

Sibling order is the child index established by `create`/reparent. A reparent index greater than the
new parent's child count appends. Reparenting a node under itself or its descendant is Conflict.

Maximum ControlTree depth is 256. A mutation exceeding it is InvalidArgument.

Paint/layout sibling order is:
1. zIndex ascending;
2. ControlTree child index ascending.

Equal zIndex therefore remains stable across frames.

Removing a node recursively removes its presentation descendants in one TreeTransaction but never
deletes represented semantic graph identities.

## 3. Layout

v0 uses `taffy` and only the `LayoutStyle` subset in the schema.

Coordinates before 3D graph lowering are logical pixels:
- origin top-left;
- +x right;
- +y down.

`Dimension` semantics:
- auto: Taffy auto;
- px: logical pixels, finite >=0;
- fraction: flex fraction, finite >=0;
- percent: fraction of containing block in [0,100].

All dimensions, offsets, opacity and ratios must be finite. Invalid numeric input is InvalidArgument.

`split` is a two-child container. Exactly two children are required. Ratio is [0.1,0.9], default
0.5. Horizontal means left/right; vertical means top/bottom.

`scroll` clips to its layout box and applies the stored logical-pixel scroll offset to its child
content. Negative offsets are clamped to zero; maximum is content size minus viewport size.

Other container flow/flex semantics map directly to the pinned Taffy version; no CSS engine or second
layout implementation exists.

## 4. Tree node bodies

- `graphProjection`: projection roots/lens/frontier; graph layout rules come from the existing
  decision-complete graph-layout sections.
- `text`: UTF-8 text + explicit TextStyle.
- `terminal`: references the Terminal semantic/presentation node; VTE cell model lowers into text and
  rectangle scene leaves.
- `document/editor`: reference a resource/artifact; editor parsing/LSP behavior remains the frozen
  editor contract.
- `table/chart`: data is one `TableDataset` serialized as unpacked Cap'n Proto bytes with media type
  `application/vnd.omnis.table.v1+capnp`.
- `media`: references a graph Resource; decoded frame/audio handles come from Manager/PipeWire/GStreamer.
- `inspector`: references the inspected graph identity.
- `nativeSurface`: references exactly one Wayland/XWayland surface graph identity.
- `inputSurface`: the primary semantic input or another explicitly materialized text input.
- `overlay`: presentation overlay; modal=true captures input within its subtree.
- `timeline`: references an optional EventId frontier; none means live.

## 5. Accessibility

Every ControlNode has explicit `AccessibilityState`.

Default role when materializer did not override:

```text
container/split/scroll/overlay -> group
graphProjection               -> application
text                          -> text
terminal                      -> terminal
document                      -> document
editor/inputSurface           -> textbox
table                         -> table
chart                         -> chart
media                         -> image
inspector                     -> group
nativeSurface                 -> application
timeline                      -> list
```

Name derives from `omnis.identity.display_name` when the node represents a graph identity; otherwise
it is the materializer's explicit name. An empty name is valid only for hidden/pure layout groups.

Focus cannot land on an accessibility-hidden or disabled node.

Custom Control accessibility is published through AccessKit/AT-SPI. NativeSurface publishes a
container in the Omnis tree and delegates its child subtree to the client's platform accessibility
bridge when available.

## 6. RenderScene lowering

RenderScene is private, disposable render IR. It is regenerated from ControlTree/layout and never
written into the semantic graph.

Fixed primitive union:

```text
Group
Transform
Clip
Rect
RoundedRect
Path
GlyphRun
Image
Mesh
NativeSurface
```

No first-party primitive type can be added in v0 without changing `control_scene.capnp`.

Scene items form a tree. Only Group, Transform and Clip may have children; all drawable leaf
primitives must have zero children.

Each SceneItem carries:
- one layer: world/ui/overlay;
- zIndex;
- inherited opacity multiplier;
- optional hit-target ControlNodeId.

Lowering assigns private scene UInt64 IDs monotonically from 1 for each RenderScene revision in
depth-first generation order.

## 7. Coordinates and transforms

Mat4 is 16 finite Float32 values, column-major: `m[column*4+row]`.

2D Control layout is embedded in the UI plane with top-left/y-down coordinates.

3D world is right-handed:
- +X right;
- +Y up;
- +Z toward viewer;
- camera looks toward -Z.

Transform composition for a child is:

```text
world = parent_world * local_transform
```

A non-invertible transform makes its subtree non-hittable and emits one diagnostic event per scene
revision.

## 8. Color and blending

Theme files contain sRGB hex colors. Parse channels to [0,1] and convert sRGB to linear with IEC
61966-2-1:

```text
c <= 0.04045 : c / 12.92
otherwise    : ((c + 0.055) / 1.055) ^ 2.4
```

Scene Color stores **linear-sRGB premultiplied RGBA**.

Renderer uses premultiplied alpha:
- source factor One;
- destination factor OneMinusSrcAlpha.

Output is SDR sRGB only in v0. Preferred surface formats remain BGRA8UnormSrgb then RGBA8UnormSrgb.

## 9. Text

Text shaping occurs before RenderScene using `cosmic-text`. Renderer receives positioned glyph IDs;
it never shapes text.

Font lookup uses fontconfig + the NixOS font set. Stable FontKey is:
- BLAKE3-256 raw font file bytes;
- face index.

Variation axes are not exposed in v0. Synthetic bold/italic is not generated: requested weight/style
uses font fallback; if unavailable, nearest installed face selected by cosmic-text/fontdb ordering.

Default sizes/line heights are the values in `spec/control_render.toml`.

Glyph atlas policy remains the decision-complete 2048→8192 per scale-class LRU contract.

## 10. Paths

`lyon` is the sole v0 path tessellator.

Commands are Move/Line/Quadratic/Cubic/Close. Fill rule is non-zero. Stroke join is miter, cap is butt,
miter limit 4.0. Path coordinates are logical pixels before scene transform.

Tessellation failure omits that Path leaf and emits a diagnostic; it never falls back to another
library.

## 11. Rendering layers

For each output:

1. clear to theme `editor.background`;
2. render world layer with `Depth32Float`, LessEqual depth, CCW front face and back-face culling;
3. render UI layer in painter order with depth testing disabled;
4. render overlay layer in painter order with depth testing disabled;
5. present synchronized to output vblank.

Within a layer, siblings use zIndex then child index; traversal is depth-first preorder.

Batching may combine only adjacent items when doing so preserves this exact order.

MSAA is 4x when target support includes sample count 4, otherwise 1x.

## 12. Clipping

Axis-aligned rectangular clips in output space use GPU scissor intersection.

Rounded or transformed clips use an R8Unorm mask. Nested mask depth up to 8 remains live. At the
ninth nested mask, renderer rasterizes the accumulated intersection to one new mask and continues
from depth 1.

Clip applies to both drawing and hit testing.

## 13. Images and media

Image primitive references a private renderer texture handle and UV rectangle. Hit testing uses its
geometry, not alpha pixels.

Decoded static image textures come from the pinned `image` decoder. Video frames are GStreamer /
PipeWire resources imported as textures. Decoding is never performed on the render thread.

Texture-cache budget and LRU are the frozen global values from the decision-complete contract.

## 14. Native surfaces

A Wayland/XWayland client's buffer is imported into the same wgpu composition path whenever Control
must composite it. The client owns pixels; Control owns geometry, transforms, clips, z-order, focus
and semantic identity.

In 3D, NativeSurface is always a composited texture plane.

Direct scan-out is allowed only when:
- exactly one visible NativeSurface covers the entire physical output;
- its transform is the identity/output scale transform;
- no Control UI/overlay/cursor composition is required;
- Smithay/DRM marks the buffer eligible.

Any failed condition uses normal composition.

Pointer coordinates for a NativeSurface are inverse-transformed from output coordinates to
client-local logical coordinates before Wayland input delivery.

## 15. Hit testing

2D:
1. traverse visible/enabled leaves in reverse paint order;
2. apply inverse transform and every clip;
3. Rect/RoundedRect use exact geometry;
4. Path fill uses non-zero rule; stroke uses stroke geometry + 3 logical px slop;
5. GlyphRun uses its shaped bounds;
6. Image/NativeSurface use rect geometry;
7. Mesh uses ray/triangle intersection.

3D:
- construct camera ray through pointer;
- test world Mesh/card/native planes;
- choose smallest positive ray distance;
- equal distance within 1e-5 chooses later paint order;
- then test UI/overlay layers in normal reverse-paint 2D order, which wins over world hits.

The resolved SceneItem's nearest ancestor/self `hitTarget` is the ControlNodeId receiving the input.
No screenshot/vision step participates.

## 16. Animation

Default transition:
- duration 180 ms;
- cubic-bezier(0.2,0,0,1);
- properties: position, size, opacity, camera;
- no spring physics.

At reduced-motion=true duration is 0.

Animation samples use the compositor monotonic clock. A new target starts from the exact currently
sampled value, not the previous target.

Force-layout iterations are layout computation, not this presentation animation.

## 17. Tables and charts

`TableDataset` columns are typed and every row must have exactly the column count with matching cell
types or the dataset is InvalidArgument.

Table virtualization starts above 200 rows with 20-row overscan, as previously frozen.

Chart input uses the same dataset. More than 10000 visible points per series is downsampled to 5000
with Largest-Triangle-Three-Buckets before scene lowering. The selected/rendered point carries its
source row NodeId when present.

## 18. Render-thread boundary

The compositor/Tokio domains publish immutable RenderScene snapshots to the render thread through the
capacity-3 newest-wins queue.

The render thread owns wgpu Device/Queue, texture/glyph/path GPU caches and imported client-buffer GPU
handles. It performs no graph RPC, filesystem/network I/O, model call, text shaping, image/video
decode or Nix/Manager operation.

Dropping an unsubmitted RenderScene snapshot cannot drop ControlTree state; the next snapshot contains
the latest authoritative presentation state.
