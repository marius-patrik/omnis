@0x8c1820c1aa7df621;

using C = import "common.capnp";
using I = import "inference.capnp";

struct Empty {}

struct ShellExecuteInput { command @0 :Text; cwd @1 :Text; env @2 :List(Env); pty @3 :Bool; }
struct Env { key @0 :Text; value @1 :Text; }
struct ExecutionOutput { execution @0 :C.Uuid; output @1 :C.MaybeArtifactRef; }

struct ProcessExecuteInput {
  executable @0 :Text;
  argv @1 :List(Text);
  cwd @2 :Text;
  env @3 :List(Env);
  pty @4 :Bool;
}

enum PackageScope { execution @0; user @1; system @2; }
struct PackageInput { package @0 :Text; scope @1 :PackageScope; }
struct PackageOutput { resource @0 :C.Uuid; realization @1 :C.Uuid; }

struct GenerationInput { assignments @0 :List(Assignment); }
struct Assignment { option @0 :Text; value @1 :C.Value; }
struct GenerationOutput { generation @0 :C.Uuid; evidence @1 :C.ArtifactRef; }
struct GenerationRefInput { generation @0 :C.Uuid; }

struct RepositoryInput { repository @0 :C.Uuid; worktree @1 :C.MaybeUuid; }
struct VcsCommitInput { repository @0 :C.Uuid; worktree @1 :C.MaybeUuid; message @2 :Text; paths @3 :List(Text); }
struct VcsPushInput { repository @0 :C.Uuid; remote @1 :Text; refspec @2 :Text; }
struct TextArtifactOutput { artifact @0 :C.ArtifactRef; }

struct CodeToolInput { repository @0 :C.Uuid; worktree @1 :C.MaybeUuid; paths @2 :List(Text); }
struct CodeAgentInput {
  repository @0 :C.Uuid;
  worktree @1 :C.Uuid;
  goal @2 :Text;
  acceptance @3 :C.ArtifactRef;
  context @4 :C.ArtifactRef;
}
struct CodeAgentOutput { execution @0 :C.Uuid; patch @1 :C.MaybeArtifactRef; commit @2 :Text; }

struct ModelTextInput { context @0 :C.ArtifactRef; }
struct InferenceRequestInput { request @0 :I.InferenceRequest; }
struct InferenceResultOutput { result @0 :I.InferenceResult; }
struct ClassifyOutput { labels @0 :List(LabelScore); }
struct LabelScore { label @0 :Text; score @1 :Float64; }
struct EmbedOutput { model @0 :C.Uuid; dimension @1 :UInt32; vectorF32Le @2 :Data; }
struct RerankInput { query @0 :Text; candidates @1 :List(C.ArtifactRef); }
struct RerankOutput { orderedIndices @0 :List(UInt32); scores @1 :List(Float64); }
struct GenerateOutput { content @0 :C.ArtifactRef; }
struct VisionInput { media @0 :C.ArtifactRef; context @1 :C.MaybeArtifactRef; }
struct AudioInput { media @0 :C.ArtifactRef; context @1 :C.MaybeArtifactRef; }

struct BrowserNavigateInput { browser @0 :C.MaybeUuid; url @1 :Text; }
struct BrowserNavigateOutput { browser @0 :C.Uuid; page @1 :C.MaybeUuid; }
struct BrowserInspectInput { browser @0 :C.Uuid; page @1 :C.MaybeUuid; query @2 :Text; }
struct BrowserInteractInput { browser @0 :C.Uuid; page @1 :C.MaybeUuid; action @2 :C.ArtifactRef; }

struct HttpRequestInput {
  method @0 :Text;
  url @1 :Text;
  headers @2 :List(Env);
  body @3 :C.MaybeArtifactRef;
}
struct HttpResponseOutput { status @0 :UInt16; headers @1 :List(Env); body @2 :C.ArtifactRef; }

struct McpInvokeInput { server @0 :C.Uuid; tool @1 :Text; arguments @2 :C.ArtifactRef; }
struct ContainerRunInput { image @0 :Text; argv @1 :List(Text); cwd @2 :Text; }
struct VmRunInput { resource @0 :C.Uuid; action @1 :Text; }

struct GraphQueryInput { query @0 :C.ArtifactRef; }
struct GraphQueryOutput { result @0 :C.ArtifactRef; }

struct ControlMaterializeInput { identities @0 :List(C.Uuid); lens @1 :List(Text); }
struct ControlMaterializeOutput { root @0 :C.Uuid; }
struct ControlMutateInput { transaction @0 :C.ArtifactRef; }

struct IngestInput { paths @0 :List(Text); explicitLargeFiles @1 :Bool; }
struct IngestOutput { resources @0 :List(C.Uuid); artifacts @1 :List(C.ArtifactRef); }


struct HostPairingCodeOutput {
  code @0 :Text;
  expiresUnixNs @1 :Int64;
}

struct HostPairInput {
  address @0 :Text;
  code @1 :Text;
}

struct HostPairOutput {
  host @0 :C.Uuid;
  publicKey @1 :Data;
  certificateFingerprint @2 :Data;
}

struct HostUnpairInput {
  host @0 :C.Uuid;
}
