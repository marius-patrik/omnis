@0x9ac85c207737e1b3;

using C = import "common.capnp";

struct GraphCommitted {
  transactionId @0 :C.Uuid;
  previousRevision @1 :UInt64;
  newRevision @2 :UInt64;
  changedIds @3 :List(C.Uuid);
}

struct Reconciled { source @0 :Text; revision @1 :UInt64; }
struct ObservationGap { source @0 :Text; lostCount @1 :UInt64; recoveryRevision @2 :UInt64; }

struct ProcessStarted {
  process @0 :C.Uuid;
  parentProcess @1 :C.MaybeUuid;
  executable @2 :C.MaybeUuid;
  pid @3 :UInt64;
}
struct ProcessExec { process @0 :C.Uuid; executable @1 :C.Uuid; argv @2 :C.MaybeArtifactRef; }
struct ProcessExited { process @0 :C.Uuid; exitCode @1 :Int32; signal @2 :Int32; hasExitCode @3 :Bool; hasSignal @4 :Bool; }
struct ServiceChanged { service @0 :C.Uuid; oldState @1 :Text; newState @2 :Text; }
struct IdentityOnly { identity @0 :C.Uuid; }
struct NetworkChanged { identity @0 :C.Uuid; changeKind @1 :Text; }
struct InvariantViolated { invariant @0 :C.Uuid; identity @1 :C.Uuid; enforcementAction @2 :Text; }

struct GenerationEvent {
  generation @0 :C.Uuid;
  parent @1 :C.MaybeUuid;
  evidence @2 :List(C.ArtifactRef);
}
struct ResourceDiscovered { resource @0 :C.Uuid; provenance @1 :C.Uuid; }
struct BindingDiscovered { binding @0 :C.Uuid; resource @1 :C.Uuid; capability @2 :C.Uuid; provenance @3 :C.Uuid; }
struct ResolutionCompleted { capability @0 :Text; selectedBinding @1 :C.MaybeUuid; candidates @2 :C.ArtifactRef; }

struct ExecutionEvent {
  execution @0 :C.Uuid;
  binding @1 :C.Uuid;
  placement @2 :C.Uuid;
  status @3 :Text;
  evidence @4 :List(C.ArtifactRef);
}

struct InferenceRequest {
  invocation @0 :C.Uuid;
  execution @1 :C.Uuid;
  modelRole @2 :Text;
  request @3 :C.ArtifactRef;
}
struct InferenceResponse {
  invocation @0 :C.Uuid;
  binding @1 :C.Uuid;
  response @2 :C.ArtifactRef;
  inputTokens @3 :UInt64;
  outputTokens @4 :UInt64;
  latencyNs @5 :UInt64;
  costMicrosUsd @6 :UInt64;
  hasCost @7 :Bool;
}
struct InferenceFailed { invocation @0 :C.Uuid; binding @1 :C.MaybeUuid; error @2 :C.RpcError; }
struct CredentialLease { handle @0 :C.Uuid; lease @1 :C.Uuid; execution @2 :C.Uuid; }

struct ActivityEvent { activity @0 :C.Uuid; goal @1 :C.MaybeUuid; }
struct WorkerEvent {
  worker @0 :C.Uuid;
  activity @1 :C.Uuid;
  context @2 :C.MaybeUuid;
  checkpoint @3 :C.MaybeArtifactRef;
  evidence @4 :List(C.ArtifactRef);
}
struct MemoryEvent { memory @0 :C.Uuid; evidence @1 :List(C.Uuid); }
struct ContextCompiled { context @0 :C.Uuid; trigger @1 :C.Uuid; sourceCount @2 :UInt32; tokenBudget @3 :UInt32; }
struct ProcedurePromoted { procedure @0 :C.Uuid; evidence @1 :List(C.Uuid); }
struct CandidateEvent { candidate @0 :C.Uuid; target @1 :C.Uuid; evidence @2 :List(C.Uuid); }

struct ControlInput { workspace @0 :C.Uuid; inputSurface @1 :C.Uuid; text @2 :C.ArtifactRef; }
struct FocusChanged { workspace @0 :C.Uuid; oldFocus @1 :C.MaybeUuid; newFocus @2 :C.MaybeUuid; }
struct SelectionChanged { workspace @0 :C.Uuid; selected @1 :List(C.Uuid); }
struct ModeChanged { workspace @0 :C.Uuid; oldMode @1 :Text; newMode @2 :Text; }
struct LensChanged { workspace @0 :C.Uuid; lenses @1 :List(Text); }
struct TreeMutated { workspace @0 :C.Uuid; transaction @1 :C.Uuid; }
struct SurfaceEvent { surface @0 :C.Uuid; process @1 :C.MaybeUuid; }
struct TerminalEvent { terminal @0 :C.Uuid; execution @1 :C.MaybeUuid; }
struct Navigation { workspace @0 :C.Uuid; address @1 :Text; resolvedIdentity @2 :C.MaybeUuid; }
struct NotificationEvent { notification @0 :C.Uuid; source @1 :C.MaybeUuid; }
struct Timer { tickUnixNs @0 :Int64; }

struct DenseItem {
  sequence @0 :UInt64;
  monotonicNs @1 :UInt64;
  type @2 :Text;
  payload @3 :Data;
}
struct DenseBatch {
  producer @0 :C.Uuid;
  firstSequence @1 :UInt64;
  lastSequence @2 :UInt64;
  firstMonotonicNs @3 :UInt64;
  lastMonotonicNs @4 :UInt64;
  items @5 :List(DenseItem);
}

struct Payload {
  union {
    none @0 :Void;
    graphCommitted @1 :GraphCommitted;
    reconciled @2 :Reconciled;
    observationGap @3 :ObservationGap;
    processStarted @4 :ProcessStarted;
    processExec @5 :ProcessExec;
    processExited @6 :ProcessExited;
    serviceChanged @7 :ServiceChanged;
    identityOnly @8 :IdentityOnly;
    networkChanged @9 :NetworkChanged;
    invariantViolated @10 :InvariantViolated;
    generationEvent @11 :GenerationEvent;
    resourceDiscovered @12 :ResourceDiscovered;
    bindingDiscovered @13 :BindingDiscovered;
    resolutionCompleted @14 :ResolutionCompleted;
    executionEvent @15 :ExecutionEvent;
    inferenceRequest @16 :InferenceRequest;
    inferenceResponse @17 :InferenceResponse;
    inferenceFailed @18 :InferenceFailed;
    credentialLease @19 :CredentialLease;
    activityEvent @20 :ActivityEvent;
    workerEvent @21 :WorkerEvent;
    memoryEvent @22 :MemoryEvent;
    contextCompiled @23 :ContextCompiled;
    procedurePromoted @24 :ProcedurePromoted;
    candidateEvent @25 :CandidateEvent;
    controlInput @26 :ControlInput;
    focusChanged @27 :FocusChanged;
    selectionChanged @28 :SelectionChanged;
    modeChanged @29 :ModeChanged;
    lensChanged @30 :LensChanged;
    treeMutated @31 :TreeMutated;
    surfaceEvent @32 :SurfaceEvent;
    terminalEvent @33 :TerminalEvent;
    navigation @34 :Navigation;
    notificationEvent @35 :NotificationEvent;
    timer @36 :Timer;
    denseBatch @37 :DenseBatch;
  }
}
