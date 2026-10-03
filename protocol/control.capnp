@0xf18d5c82b0764a45;

using C = import "common.capnp";

enum SpatialMode { twoD @0; threeD @1; }

struct ProjectionSpec {
  roots @0 :List(C.Uuid);
  lens @1 :List(Text);
  maxDepth @2 :UInt16;
  atRevision @3 :UInt64;
}

struct ControlNode {
  id @0 :C.Uuid;
  kind @1 :Text;
  represents @2 :C.Uuid;
  parent @3 :C.Uuid;
  properties @4 :Data;
}

struct TreeMutation {
  union {
    create @0 :ControlNode;
    remove @1 :C.Uuid;
    reparent @2 :Reparent;
    setProperties @3 :SetProperties;
  }
  struct Reparent { node @0 :C.Uuid; parent @1 :C.Uuid; index @2 :UInt32; }
  struct SetProperties { node @0 :C.Uuid; properties @1 :Data; }
}

struct TreeTransaction {
  id @0 :C.Uuid;
  trace @1 :C.TraceContext;
  mutations @2 :List(TreeMutation);
}

interface ControlService {
  handshake @0 (request :C.HandshakeRequest) -> (response :C.HandshakeResponse);
  materialize @1 (projection :ProjectionSpec) -> (root :C.Uuid);
  transact @2 (transaction :TreeTransaction) -> ();
  focus @3 (node :C.Uuid, trace :C.TraceContext) -> ();
  select @4 (nodes :List(C.Uuid), trace :C.TraceContext) -> ();
  setLens @5 (lens :List(Text), trace :C.TraceContext) -> ();
  setMode @6 (mode :SpatialMode, trace :C.TraceContext) -> ();
  navigate @7 (address :Text, trace :C.TraceContext) -> ();
  submitInput @8 (text :Text, trace :C.TraceContext) -> ();
}
