@0xf18d5c82b0764a45;

using C = import "common.capnp";
using S = import "control_scene.capnp";

enum SpatialMode { twoD @0; threeD @1; }

struct ProjectionSpec {
  roots @0 :List(C.Uuid);
  lens @1 :List(Text);
  maxDepth @2 :UInt16;
  atRevision @3 :UInt64;
}

struct ControlNode {
  id @0 :C.Uuid;
  represents @1 :C.MaybeUuid;
  parent @2 :C.MaybeUuid;
  state @3 :S.ControlNodeState;
}

struct TreeMutation {
  union {
    create @0 :Create;
    remove @1 :C.Uuid;
    reparent @2 :Reparent;
    setState @3 :SetState;
  }

  struct Create {
    node @0 :ControlNode;
    index @1 :UInt32; # > child count means append
  }

  struct Reparent {
    node @0 :C.Uuid;
    parent @1 :C.MaybeUuid;
    index @2 :UInt32;
  }

  struct SetState {
    node @0 :C.Uuid;
    state @1 :S.ControlNodeState;
  }
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
  getNode @9 (node :C.Uuid) -> (status :C.RpcStatus, value :ControlNode);
}
