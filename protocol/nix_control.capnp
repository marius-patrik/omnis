@0xc1c73f75f65a2c4b;

using C = import "common.capnp";

struct OptionalText {
  union {
    none @0 :Void;
    some @1 :Text;
  }
}

struct OptionalUInt32 {
  union {
    none @0 :Void;
    some @1 :UInt32;
  }
}

struct SourcePosition {
  file @0 :Text;
  line @1 :OptionalUInt32;
  column @2 :OptionalUInt32;
}

struct ValueFingerprint {
  encoding @0 :Text; # json | opaque-function | opaque-external
  digest @1 :C.ArtifactId;
  json @2 :OptionalText;
  storePaths @3 :List(Text);
}

struct OptionDefinition {
  source @0 :SourcePosition;
  fileDigest @1 :C.ArtifactId;
  finalOrder @2 :UInt32;
  highestPriority @3 :Int32;
  value @4 :ValueFingerprint;
}

struct OptionRecord {
  path @0 :Text;
  typeName @1 :Text;
  typeDescription @2 :Text;
  declarations @3 :List(SourcePosition);
  definitions @4 :List(OptionDefinition);
  finalValue @5 :ValueFingerprint;
  readOnly @6 :Bool;
  internal @7 :Bool;
  visible @8 :Bool;
  mergeApi @9 :Text; # legacy | v2
}

struct EvalTraceRecord {
  id @0 :UInt64;
  parent @1 :UInt64; # 0 means root
  source @2 :SourcePosition;
  expressionKind @3 :Text;
}

struct EvaluationRecord {
  union {
    option @0 :OptionRecord;
    trace @1 :EvalTraceRecord;
  }
}

interface EvaluationStream {
  next @0 () -> (status :C.RpcStatus, record :EvaluationRecord, done :Bool);
  cancel @1 () -> (status :C.RpcStatus);
}

struct EvaluateSystemRequest {
  trace @0 :C.TraceContext;
  evaluationId @1 :C.Uuid;
  nixpkgsPath @2 :Text;
  baseModule @3 :Text;
  managedModule @4 :Text;
  system @5 :Text;
}

struct SystemEvaluation {
  evaluationId @0 :C.Uuid;
  systemDerivation @1 :Text;
  systemToplevel @2 :Text;
  optionCount @3 :UInt64;
  traceRecordCount @4 :UInt64;
  stream @5 :EvaluationStream;
}

interface NixEvalService {
  handshake @0 (request :C.HandshakeRequest) -> (status :C.RpcStatus, response :C.HandshakeResponse);
  evaluateSystem @1 (request :EvaluateSystemRequest) -> (status :C.RpcStatus, evaluation :SystemEvaluation);
}

struct StorePathInfo {
  path @0 :Text;
  narHash @1 :Text;
  narSize @2 :UInt64;
  deriver @3 :OptionalText;
  references @4 :List(Text);
  signatures @5 :List(Text);
  registrationTimeUnixNs @6 :Int64;
  ultimate @7 :Bool;
}

struct DerivationOutput {
  name @0 :Text;
  path @1 :OptionalText;
  hashAlgorithm @2 :Text;
  hash @3 :OptionalText;
}

struct InputDerivation {
  drvPath @0 :Text;
  outputs @1 :List(Text);
}

struct DerivationInfo {
  drvPath @0 :Text;
  name @1 :Text;
  system @2 :Text;
  builder @3 :Text;
  args @4 :List(Text);
  environment @5 :C.ArtifactRef;
  inputDerivations @6 :List(InputDerivation);
  inputSources @7 :List(Text);
  outputs @8 :List(DerivationOutput);
}

enum RealizationAction {
  alreadyValid @0;
  substitute @1;
  build @2;
}

struct PlannedPath {
  path @0 :Text;
  action @1 :RealizationAction;
  estimatedDownloadBytes @2 :UInt64;
  estimatedNarBytes @3 :UInt64;
  substituter @4 :OptionalText;
  drvPath @5 :OptionalText;
}

struct RealizationPlan {
  requested @0 :List(Text);
  paths @1 :List(PlannedPath);
  totalDownloadBytes @2 :UInt64;
  totalNarBytes @3 :UInt64;
}

struct GcCandidate {
  path @0 :Text;
  narBytes @1 :UInt64;
}

struct GcPlan {
  roots @0 :List(Text);
  candidates @1 :List(GcCandidate);
  reclaimableBytes @2 :UInt64;
}

struct StoreSnapshotRecord {
  union {
    validPath @0 :StorePathInfo;
    gcRoot @1 :Text;
  }
}

interface StoreSnapshotStream {
  next @0 () -> (status :C.RpcStatus, record :StoreSnapshotRecord, done :Bool);
  cancel @1 () -> (status :C.RpcStatus);
}

struct StoreSnapshot {
  daemonBootId @0 :C.Uuid;
  sequence @1 :UInt64;
  stream @2 :StoreSnapshotStream;
}

enum StoreEventKind {
  buildStarted @0;
  buildCompleted @1;
  substituted @2;
  pathRegistered @3;
  pathDeleted @4;
  gcStarted @5;
  gcCompleted @6;
}

struct StoreEvent {
  daemonBootId @0 :C.Uuid;
  sequence @1 :UInt64;
  kind @2 :StoreEventKind;
  trace @3 :C.TraceContext;
  path @4 :OptionalText;
  drvPath @5 :OptionalText;
  success @6 :Bool;
  detail @7 :OptionalText;
  wallUnixNs @8 :Int64;
  monotonicNs @9 :UInt64;
}

interface StoreSubscription {
  next @0 () -> (status :C.RpcStatus, event :StoreEvent);
  cancel @1 () -> (status :C.RpcStatus);
}

struct RealizeRequest {
  trace @0 :C.TraceContext;
  paths @1 :List(Text);
  buildMode @2 :Text; # normal only in v0
}

struct GcRequest {
  trace @0 :C.TraceContext;
  roots @1 :List(Text);
  deletePaths @2 :List(Text);
}

interface NixStoreControl {
  handshake @0 (request :C.HandshakeRequest) -> (status :C.RpcStatus, response :C.HandshakeResponse);
  pathInfo @1 (path :Text) -> (status :C.RpcStatus, info :StorePathInfo);
  derivation @2 (drvPath :Text) -> (status :C.RpcStatus, info :DerivationInfo);
  closure @3 (roots :List(Text), includeOutputs :Bool) -> (status :C.RpcStatus, paths :List(Text));
  planRealization @4 (paths :List(Text), trace :C.TraceContext) -> (status :C.RpcStatus, plan :RealizationPlan);
  realize @5 (request :RealizeRequest) -> (status :C.RpcStatus, plan :RealizationPlan);
  planGc @6 (roots :List(Text), trace :C.TraceContext) -> (status :C.RpcStatus, plan :GcPlan);
  gc @7 (request :GcRequest) -> (status :C.RpcStatus, deleted :List(GcCandidate));
  snapshot @8 () -> (status :C.RpcStatus, snapshot :StoreSnapshot);
  subscribe @9 (daemonBootId :C.MaybeUuid, afterSequence :UInt64) -> (status :C.RpcStatus, subscription :StoreSubscription);
}


struct NixExplanation {
  identity @0 :C.Uuid;
  options @1 :List(OptionRecord);
  storePaths @2 :List(StorePathInfo);
  derivations @3 :List(DerivationInfo);
  evaluationTrace @4 :C.MaybeArtifactRef;
}
