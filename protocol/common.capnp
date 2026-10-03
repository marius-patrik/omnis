@0xd8b5c0f15c62a901;

# Canonical Omnis protocol primitives. UUID fields contain exactly 16 bytes.
# Artifact digests contain exactly 32 BLAKE3 bytes. Services must reject wrong lengths.

struct Uuid {
  bytes @0 :Data;
}

struct ArtifactId {
  blake3 @0 :Data;
}

struct ProtocolVersion {
  major @0 :UInt16;
  minor @1 :UInt16;
}

struct TraceContext {
  requestId @0 :Uuid;
  traceId @1 :Uuid;
  actor @2 :Uuid;
  causalParents @3 :List(Uuid);
  deadlineUnixNs @4 :UInt64;
}

enum ProtectionClass {
  public @0;
  localOnly @1;
  agentVisible @2;
  modelLocalOnly @3;
  modelExternalDenied @4;
  controlHidden @5;
  executionHandleOnly @6;
}

struct ArtifactRef {
  id @0 :ArtifactId;
  length @1 :UInt64;
  mediaType @2 :Text;
  protection @3 :ProtectionClass;
}

struct Value {
  union {
    none @0 :Void;
    bool @1 :Bool;
    sint @2 :Int64;
    uint @3 :UInt64;
    float @4 :Float64;
    text @5 :Text;
    data @6 :Data;
    uuid @7 :Uuid;
    artifact @8 :ArtifactRef;
  }
}

struct Provenance {
  id @0 :Uuid;
  source @1 :Text;
  method @2 :Text;
  version @3 :Text;
  evidence @4 :List(ArtifactRef);
  confidence @5 :Float32;
}

enum ErrorCode {
  unknown @0;
  invalidArgument @1;
  notFound @2;
  conflict @3;
  unauthorized @4;
  incompatible @5;
  unavailable @6;
  deadlineExceeded @7;
  unresolvedCapability @8;
  ambiguousBinding @9;
  constraintUnsatisfied @10;
  placementUnavailable @11;
  protectedValueDenied @12;
  buildFailure @13;
  activationFailure @14;
  executionFailure @15;
  externalEffectAmbiguous @16;
}

struct RpcError {
  code @0 :ErrorCode;
  message @1 :Text;
  details @2 :Data;
  retryable @3 :Bool;
}

struct HandshakeRequest {
  version @0 :ProtocolVersion;
  component @1 :Text;
  buildId @2 :Text;
  interfaces @3 :List(Text);
}

struct HandshakeResponse {
  version @0 :ProtocolVersion;
  component @1 :Text;
  buildId @2 :Text;
  interfaces @3 :List(Text);
}
