@0xb061e4cf1f2d9a37;

using C = import "common.capnp";
using G = import "graph.capnp";

struct ContextCapsule {
  id @0 :C.Uuid;
  trigger @1 :C.Uuid;
  activity @2 :C.MaybeUuid;
  sources @3 :List(C.Uuid);
  artifacts @4 :List(C.ArtifactRef);
  capabilities @5 :List(Text);
  serializedModelContext @6 :C.ArtifactRef;
}

struct WorkerState {
  id @0 :C.Uuid;
  activity @1 :C.Uuid;
  status @2 :Text;
  context @3 :C.Uuid;
  checkpoint @4 :C.MaybeArtifactRef;
}

struct MemoryQuery {
  text @0 :Text;
  kinds @1 :List(Text);
  limit @2 :UInt32;
  atEvent @3 :C.MaybeUuid;
}

struct MemoryHit {
  identity @0 :C.Uuid;
  score @1 :Float64;
  evidence @2 :List(C.Uuid);
}

struct IntentionRequest {
  trace @0 :C.TraceContext;
  text @1 :Text;
  contextIds @2 :List(C.Uuid);
}

interface AgentService {
  handshake @0 (request :C.HandshakeRequest) -> (status :C.RpcStatus, response :C.HandshakeResponse);
  intend @1 (request :IntentionRequest) -> (status :C.RpcStatus, activity :C.Uuid);
  searchMemory @2 (query :MemoryQuery) -> (status :C.RpcStatus, hits :List(MemoryHit));
  compileContext @3 (
    trigger :C.Uuid,
    activity :C.MaybeUuid,
    budgetTokens :UInt32
  ) -> (status :C.RpcStatus, context :ContextCapsule);
  getWorker @4 (id :C.Uuid) -> (status :C.RpcStatus, worker :WorkerState);
  explain @5 (identity :C.Uuid) -> (status :C.RpcStatus, evidence :C.ArtifactRef);
  worldlineGet @6 (eventId :C.Uuid) -> (status :C.RpcStatus, event :G.EventEnvelope);
}
