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

struct EnvironmentEntry {
  key @0 :Text;
  value @1 :Text;
}

interface ByteSource {
  read @0 (maxBytes :UInt32) -> (status :C.RpcStatus, chunk :Data, done :Bool);
  cancel @1 () -> (status :C.RpcStatus);
}

interface ByteSink {
  write @0 (chunk :Data) -> (status :C.RpcStatus);
  close @1 () -> (status :C.RpcStatus);
}

interface PtyStream {
  read @0 (maxBytes :UInt32) -> (status :C.RpcStatus, chunk :Data, done :Bool);
  write @1 (chunk :Data) -> (status :C.RpcStatus);
  resize @2 (rows :UInt32, cols :UInt32, pixelWidth :UInt32, pixelHeight :UInt32) -> (status :C.RpcStatus);
  close @3 () -> (status :C.RpcStatus);
}

struct PipeIo {
  stdin @0 :ByteSink;
  stdout @1 :ByteSource;
  stderr @2 :ByteSource;
}

struct PhysicalLaunchRequest {
  trace @0 :C.TraceContext;
  execution @1 :C.Uuid;
  envelope @2 :C.Uuid;
  executable @3 :Text;
  argv @4 :List(Text);
  environment @5 :List(EnvironmentEntry);
  workingDirectory @6 :Text;
  usePty @7 :Bool;
  rows @8 :UInt32;
  cols @9 :UInt32;
  pixelWidth @10 :UInt32;
  pixelHeight @11 :UInt32;
}

struct PhysicalProcess {
  execution @0 :C.Uuid;
  processNode @1 :C.MaybeUuid;
  pid @2 :UInt64;
  union {
    pipes @3 :PipeIo;
    pty @4 :PtyStream;
  }
}

enum ProcessSignal {
  interrupt @0;
  terminate @1;
  kill @2;
  hangup @3;
  user1 @4;
  user2 @5;
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
  launch @9 (request :PhysicalLaunchRequest) -> (status :C.RpcStatus, process :PhysicalProcess);
  getProcess @10 (execution :C.Uuid) -> (status :C.RpcStatus, process :PhysicalProcess);
  signal @11 (execution :C.Uuid, signal :ProcessSignal, trace :C.TraceContext) -> (status :C.RpcStatus);
  stop @12 (execution :C.Uuid, trace :C.TraceContext) -> (status :C.RpcStatus);
}
