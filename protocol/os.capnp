@0xe1172d73455a9c81;

using C = import "common.capnp";

struct HostInventory {
  host @0 :C.Uuid;
  graphRevision @1 :UInt64;
  snapshot @2 :C.ArtifactRef;
}

struct GenerationCandidate {
  id @0 :C.Uuid;
  parent @1 :C.MaybeUuid;
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
  systemPath @1 :Text;
  evidence @2 :List(C.ArtifactRef);
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
  handshake @0 (request :C.HandshakeRequest) -> (status :C.RpcStatus, response :C.HandshakeResponse);
  inventory @1 () -> (status :C.RpcStatus, inventory :HostInventory);
  createEnvelope @2 (envelope :ExecutionEnvelope) -> (status :C.RpcStatus);
  destroyEnvelope @3 (id :C.Uuid) -> (status :C.RpcStatus);
  evaluate @4 (candidate :GenerationCandidate) -> (status :C.RpcStatus, diff :GenerationDiff);
  build @5 (candidate :GenerationCandidate) -> (status :C.RpcStatus, result :BuildResult);
  activate @6 (generation :C.Uuid, trace :C.TraceContext) -> (status :C.RpcStatus);
  rollback @7 (generation :C.Uuid, trace :C.TraceContext) -> (status :C.RpcStatus);
  checkInvariants @8 (candidate :C.Uuid) -> (status :C.RpcStatus, report :C.ArtifactRef);
}
