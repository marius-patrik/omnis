@0xb061e4cf1f2d9a37;

using C = import "common.capnp";
using G = import "graph.capnp";

struct ContextCapsule {
  id @0 :C.Uuid;
  trigger @1 :C.Uuid;
  activity @2 :C.Uuid;
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
  checkpoint @4 :C.ArtifactRef;
}

struct MemoryQuery {
  text @0 :Text;
  kinds @1 :List(Text);
  limit @2 :UInt32;
  atEvent @3 :C.Uuid;
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
  handshake @0 (request :C.HandshakeRequest) -> (response :C.HandshakeResponse);
  submitEvent @1 (event :G.EventEnvelope) -> ();
  intend @2 (request :IntentionRequest) -> (activity :C.Uuid);
  searchMemory @3 (query :MemoryQuery) -> (hits :List(MemoryHit));
  compileContext @4 (trigger :C.Uuid, activity :C.Uuid, budgetTokens :UInt32) -> (context :ContextCapsule);
  getWorker @5 (id :C.Uuid) -> (worker :WorkerState);
  explain @6 (identity :C.Uuid) -> (evidence :C.ArtifactRef);
  worldlineGet @7 (eventId :C.Uuid) -> (event :G.EventEnvelope);
}
