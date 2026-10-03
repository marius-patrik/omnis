@0xf18d5c82b0764a45;

using C = import "common.capnp";

enum SpatialMode { twoD @0; threeD @1; }

struct ProjectionSpec {
  roots @0 :List(C.Uuid);
  lens @1 :List(Text);
  maxDepth @2 :UInt16;
  atRevision @3 :UInt64;
}

struct ControlProperty {
  key @0 :Text;
  value @1 :C.Value;
}

struct ControlNode {
  id @0 :C.Uuid;
  kind @1 :Text;
  represents @2 :C.MaybeUuid;
  parent @3 :C.MaybeUuid;
  properties @4 :List(ControlProperty);
}

struct TreeMutation {
  union {
    create @0 :ControlNode;
    remove @1 :C.Uuid;
    reparent @2 :Reparent;
    setProperties @3 :SetProperties;
  }
  struct Reparent { node @0 :C.Uuid; parent @1 :C.MaybeUuid; index @2 :UInt32; }
  struct SetProperties { node @0 :C.Uuid; properties @1 :List(ControlProperty); }
}

struct TreeTransaction {
  id @0 :C.Uuid;
  trace @1 :C.TraceContext;
  mutations @2 :List(TreeMutation);
}

interface ControlService {
  handshake @0 (request :C.HandshakeRequest) -> (status :C.RpcStatus, response :C.HandshakeResponse);
  materialize @1 (projection :ProjectionSpec) -> (status :C.RpcStatus, root :C.Uuid);
  transact @2 (transaction :TreeTransaction) -> (status :C.RpcStatus);
  focus @3 (node :C.Uuid, trace :C.TraceContext) -> (status :C.RpcStatus);
  select @4 (nodes :List(C.Uuid), trace :C.TraceContext) -> (status :C.RpcStatus);
  setLens @5 (lens :List(Text), trace :C.TraceContext) -> (status :C.RpcStatus);
  setMode @6 (mode :SpatialMode, trace :C.TraceContext) -> (status :C.RpcStatus);
  navigate @7 (address :Text, trace :C.TraceContext) -> (status :C.RpcStatus);
  submitInput @8 (text :Text, trace :C.TraceContext) -> (status :C.RpcStatus);
}
