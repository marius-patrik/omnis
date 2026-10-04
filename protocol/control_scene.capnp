@0xa04e3f88b6e3d917;

using C = import "common.capnp";

struct Vec2 { x @0 :Float32; y @1 :Float32; }
struct Vec3 { x @0 :Float32; y @1 :Float32; z @2 :Float32; }
struct Vec4 { x @0 :Float32; y @1 :Float32; z @2 :Float32; w @3 :Float32; }

struct Mat4 {
  # Column-major: m[column * 4 + row].
  m @0 :List(Float32);
}

struct Color {
  # Linear-sRGB premultiplied RGBA, each finite in [0,1].
  r @0 :Float32;
  g @1 :Float32;
  b @2 :Float32;
  a @3 :Float32;
}

struct Rect { origin @0 :Vec2; size @1 :Vec2; }
struct Insets { top @0 :Float32; right @1 :Float32; bottom @2 :Float32; left @3 :Float32; }

struct Dimension {
  union {
    auto @0 :Void;
    px @1 :Float32;
    fraction @2 :Float32;
    percent @3 :Float32;
  }
}

enum PositionMode { flow @0; absolute @1; }
enum Overflow { visible @0; clip @1; scroll @2; }
enum Axis { horizontal @0; vertical @1; }
enum Align { auto @0; start @1; center @2; end @3; stretch @4; }
enum Justify { start @0; center @1; end @2; spaceBetween @3; spaceAround @4; spaceEvenly @5; }

struct LayoutStyle {
  position @0 :PositionMode;
  width @1 :Dimension;
  height @2 :Dimension;
  minWidth @3 :Dimension;
  minHeight @4 :Dimension;
  maxWidth @5 :Dimension;
  maxHeight @6 :Dimension;
  margin @7 :Insets;
  padding @8 :Insets;
  flexGrow @9 :Float32;
  flexShrink @10 :Float32;
  alignSelf @11 :Align;
  justifySelf @12 :Align;
  overflowX @13 :Overflow;
  overflowY @14 :Overflow;
  absoluteOffset @15 :Vec2;
}

enum AccessibilityRole {
  group @0;
  window @1;
  terminal @2;
  document @3;
  text @4;
  textbox @5;
  table @6;
  chart @7;
  image @8;
  button @9;
  list @10;
  listItem @11;
  application @12;
  genericContainer @13;
}

struct AccessibilityState {
  role @0 :AccessibilityRole;
  name @1 :Text;
  description @2 :Text;
  value @3 :Text;
  actions @4 :List(Text);
  hidden @5 :Bool;
}

struct GraphProjectionState {
  roots @0 :List(C.Uuid);
  lens @1 :List(Text);
  maxDepth @2 :UInt16;
  atRevision @3 :UInt64;
}

struct SplitState { axis @0 :Axis; ratio @1 :Float32; }
struct ScrollState { offset @0 :Vec2; }
struct TextState { text @0 :Text; style @1 :TextStyle; }

struct TextStyle {
  sizePx @0 :Float32;
  weight @1 :UInt16; # CSS numeric weight, 1..1000
  italic @2 :Bool;
  color @3 :Color;
  lineHeight @4 :Float32; # multiplier
  monospace @5 :Bool;
}

struct TerminalState { terminal @0 :C.Uuid; }
struct DocumentState { resource @0 :C.Uuid; artifact @1 :C.MaybeArtifactRef; }
struct EditorState { resource @0 :C.Uuid; language @1 :Text; readOnly @2 :Bool; }

struct TableState {
  dataset @0 :C.ArtifactRef; # application/vnd.omnis.table.v1+capnp
  sortColumn @1 :Text;
  sortDescending @2 :Bool;
}

enum ChartKind { line @0; scatter @1; bar @2; histogram @3; heatmap @4; }

struct ChartState {
  dataset @0 :C.ArtifactRef; # application/vnd.omnis.table.v1+capnp
  kind @1 :ChartKind;
  xColumn @2 :Text;
  yColumns @3 :List(Text);
}

struct MediaState { resource @0 :C.Uuid; }
struct InspectorState { target @0 :C.Uuid; }
struct NativeSurfaceState { surface @0 :C.Uuid; }
struct InputSurfaceState { placeholder @0 :Text; multiline @1 :Bool; }
struct TimelineState { frontier @0 :C.MaybeUuid; }
struct OverlayState { modal @0 :Bool; }

enum ControlNodeKind {
  container @0;
  split @1;
  scroll @2;
  graphProjection @3;
  text @4;
  terminal @5;
  document @6;
  editor @7;
  table @8;
  chart @9;
  media @10;
  inspector @11;
  nativeSurface @12;
  inputSurface @13;
  overlay @14;
  timeline @15;
}

struct ControlBody {
  union {
    container @0 :Void;
    split @1 :SplitState;
    scroll @2 :ScrollState;
    graphProjection @3 :GraphProjectionState;
    text @4 :TextState;
    terminal @5 :TerminalState;
    document @6 :DocumentState;
    editor @7 :EditorState;
    table @8 :TableState;
    chart @9 :ChartState;
    media @10 :MediaState;
    inspector @11 :InspectorState;
    nativeSurface @12 :NativeSurfaceState;
    inputSurface @13 :InputSurfaceState;
    overlay @14 :OverlayState;
    timeline @15 :TimelineState;
  }
}

struct ControlNodeState {
  kind @0 :ControlNodeKind;
  layout @1 :LayoutStyle;
  visible @2 :Bool;
  enabled @3 :Bool;
  opacity @4 :Float32;
  zIndex @5 :Int32;
  accessibility @6 :AccessibilityState;
  body @7 :ControlBody;
}

enum ColumnType { bool @0; sint @1; uint @2; float @3; text @4; timestampNs @5; nodeRef @6; }

struct TableColumn {
  name @0 :Text;
  type @1 :ColumnType;
}

struct TableCell {
  union {
    null @0 :Void;
    bool @1 :Bool;
    sint @2 :Int64;
    uint @3 :UInt64;
    float @4 :Float64;
    text @5 :Text;
    timestampNs @6 :Int64;
    nodeRef @7 :C.Uuid;
  }
}

struct TableRow { cells @0 :List(TableCell); source @1 :C.MaybeUuid; }

struct TableDataset {
  columns @0 :List(TableColumn);
  rows @1 :List(TableRow);
}

enum SceneLayer { world @0; ui @1; overlay @2; }

struct SceneTransform { matrix @0 :Mat4; }

struct ClipShape {
  union {
    rect @0 :Rect;
    roundedRect @1 :RoundedGeometry;
  }
}

struct RoundedGeometry { rect @0 :Rect; radiusPx @1 :Float32; }

struct SceneClip { shape @0 :ClipShape; }

struct RectPrimitive { rect @0 :Rect; color @1 :Color; }
struct RoundedRectPrimitive { geometry @0 :RoundedGeometry; color @1 :Color; }

enum PathCommandKind { moveTo @0; lineTo @1; quadTo @2; cubicTo @3; close @4; }

struct PathCommand {
  kind @0 :PathCommandKind;
  p0 @1 :Vec2;
  p1 @2 :Vec2;
  p2 @3 :Vec2;
}

struct PathPrimitive {
  commands @0 :List(PathCommand);
  fill @1 :Color;
  stroke @2 :Color;
  strokeWidthPx @3 :Float32;
  fillEnabled @4 :Bool;
  strokeEnabled @5 :Bool;
}

struct FontKey {
  fileDigest @0 :C.ArtifactId;
  faceIndex @1 :UInt32;
}

struct PositionedGlyph {
  glyphId @0 :UInt32;
  position @1 :Vec2;
  sizePx @2 :Float32;
}

struct GlyphRunPrimitive {
  font @0 :FontKey;
  glyphs @1 :List(PositionedGlyph);
  color @2 :Color;
  bounds @3 :Rect;
}

struct ImagePrimitive {
  textureHandle @0 :UInt64;
  rect @1 :Rect;
  uvMin @2 :Vec2;
  uvMax @3 :Vec2;
  opacity @4 :Float32;
}

struct MeshVertex {
  position @0 :Vec3;
  normal @1 :Vec3;
  uv @2 :Vec2;
  color @3 :Color;
}

struct MeshPrimitive {
  vertices @0 :List(MeshVertex);
  indices @1 :List(UInt32);
  textureHandle @2 :UInt64; # 0 = none
}

struct NativeSurfacePrimitive {
  surfaceHandle @0 :UInt64;
  rect @1 :Rect;
}

struct Primitive {
  union {
    group @0 :Void;
    transform @1 :SceneTransform;
    clip @2 :SceneClip;
    rect @3 :RectPrimitive;
    roundedRect @4 :RoundedRectPrimitive;
    path @5 :PathPrimitive;
    glyphRun @6 :GlyphRunPrimitive;
    image @7 :ImagePrimitive;
    mesh @8 :MeshPrimitive;
    nativeSurface @9 :NativeSurfacePrimitive;
  }
}

struct SceneItem {
  id @0 :UInt64;
  layer @1 :SceneLayer;
  zIndex @2 :Int32;
  opacity @3 :Float32;
  hitTarget @4 :C.MaybeUuid;
  primitive @5 :Primitive;
  children @6 :List(SceneItem);
}

struct Camera3d {
  position @0 :Vec3;
  target @1 :Vec3;
  up @2 :Vec3;
  verticalFovDegrees @3 :Float32;
  nearPlane @4 :Float32;
  farPlane @5 :Float32;
}

struct OutputScene {
  outputName @0 :Text;
  logicalSize @1 :Vec2;
  physicalWidth @2 :UInt32;
  physicalHeight @3 :UInt32;
  scale @4 :Float32;
  camera @5 :Camera3d;
  items @6 :List(SceneItem);
}

struct RenderScene {
  revision @0 :UInt64;
  outputs @1 :List(OutputScene);
}
