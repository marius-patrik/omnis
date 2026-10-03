@0xc426f3120e4d7809;

using C = import "common.capnp";

struct ResourceRef { id @0 :C.Uuid; kind @1 :Text; name @2 :Text; }

struct CapabilityRef {
  id @0 :C.Uuid;
  name @1 :Text;
  inputSchema @2 :C.ArtifactRef;
  outputSchema @3 :C.ArtifactRef;
}

struct BindingRef {
  id @0 :C.Uuid;
  resource @1 :C.Uuid;
  capability @2 :C.Uuid;
  effect @3 :EffectClass;
}

enum EffectClass {
  pure @0; readOnly @1; idempotent @2; retrySafe @3; reversible @4;
  compensatable @5; transactional @6; persistentExternal @7; opaque @8;
}

struct Constraint { key @0 :Text; value @1 :C.Value; hard @2 :Bool; }

struct ResolveRequest {
  trace @0 :C.TraceContext;
  capability @1 :Text;
  constraints @2 :List(Constraint);
  graphRevision @3 :UInt64;
  discoveryOnly @4 :Bool;
}

struct CandidateBinding {
  binding @0 :BindingRef;
  accepted @1 :Bool;
  reasons @2 :List(Text);
  score @3 :Float64;
  placement @4 :C.Uuid;
}

struct ResolveResult {
  candidates @0 :List(CandidateBinding);
  selected @1 :C.Uuid;
  requiredAuthorities @2 :List(Text);
}

struct ExecutionRequest {
  id @0 :C.Uuid;
  trace @1 :C.TraceContext;
  binding @2 :C.Uuid;
  input @3 :C.ArtifactRef;
  placement @4 :C.Uuid;
  protectedHandles @5 :List(C.Uuid);
}

struct ExecutionState {
  id @0 :C.Uuid;
  status @1 :Text;
  output @2 :C.ArtifactRef;
  startedUnixNs @3 :UInt64;
  finishedUnixNs @4 :UInt64;
}

interface Adapter {
  describe @0 () -> (resources :List(ResourceRef), capabilities :List(CapabilityRef), bindings :List(BindingRef));
  execute @1 (request :ExecutionRequest) -> (state :ExecutionState);
  cancel @2 (execution :C.Uuid) -> ();
}

interface ManagerService {
  handshake @0 (request :C.HandshakeRequest) -> (response :C.HandshakeResponse);
  searchResources @1 (text :Text, limit :UInt32) -> (resources :List(ResourceRef));
  searchCapabilities @2 (text :Text, limit :UInt32) -> (capabilities :List(CapabilityRef));
  resolve @3 (request :ResolveRequest) -> (result :ResolveResult);
  start @4 (request :ExecutionRequest) -> (state :ExecutionState);
  cancel @5 (execution :C.Uuid, trace :C.TraceContext) -> ();
  getExecution @6 (execution :C.Uuid) -> (state :ExecutionState);
  discover @7 (resource :C.Uuid, trace :C.TraceContext) -> ();
  explainPlacement @8 (binding :C.Uuid, placement :C.Uuid) -> (evidence :C.ArtifactRef);
  resolveProtected @9 (handle :C.Uuid, execution :C.Uuid) -> (lease :C.Uuid);
  nixExplain @10 (identity :C.Uuid) -> (evidence :C.ArtifactRef);
}
