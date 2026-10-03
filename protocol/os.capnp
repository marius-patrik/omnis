@0xe1172d73455a9c81;

using C = import "common.capnp";

struct HostInventory {
  host @0 :C.Uuid;
  graphRevision @1 :UInt64;
  snapshot @2 :C.ArtifactRef;
}

struct GenerationCandidate {
  id @0 :C.Uuid;
  parent @1 :C.Uuid;
  managedModule @2 :C.ArtifactRef;
  trace @3 :C.TraceContext;
}

struct GenerationDiff {
  candidate @0 :C.Uuid;
  semanticDiff @1 :C.ArtifactRef;
  closureDiff @2 :C.ArtifactRef;
  serviceImpact @3 :C.ArtifactRef;
}

struct BuildResult {
  generation @0 :C.Uuid;
  success @1 :Bool;
  systemPath @2 :Text;
  evidence @3 :List(C.ArtifactRef);
}

struct ExecutionEnvelope {
  id @0 :C.Uuid;
  uid @1 :UInt32;
  gid @2 :UInt32;
  cpuQuotaMicros @3 :UInt64;
  memoryMaxBytes @4 :UInt64;
  filesystemPolicy @5 :C.ArtifactRef;
  networkPolicy @6 :C.ArtifactRef;
  devices @7 :List(Text);
  protectedHandles @8 :List(C.Uuid);
}

interface OsService {
  handshake @0 (request :C.HandshakeRequest) -> (response :C.HandshakeResponse);
  inventory @1 () -> (inventory :HostInventory);
  createEnvelope @2 (envelope :ExecutionEnvelope) -> ();
  destroyEnvelope @3 (id :C.Uuid) -> ();
  evaluate @4 (candidate :GenerationCandidate) -> (diff :GenerationDiff);
  build @5 (candidate :GenerationCandidate) -> (result :BuildResult);
  activate @6 (generation :C.Uuid, trace :C.TraceContext) -> ();
  rollback @7 (generation :C.Uuid, trace :C.TraceContext) -> ();
  checkInvariants @8 (candidate :C.Uuid) -> (report :C.ArtifactRef);
}
