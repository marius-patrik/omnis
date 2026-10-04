@0x9b7f3db41995f441;

using C = import "common.capnp";

enum Role {
  system @0;
  developer @1;
  user @2;
  assistant @3;
}

struct OptionalFloat64 {
  union {
    none @0 :Void;
    some @1 :Float64;
  }
}

struct Content {
  union {
    text @0 :Text;
    image @1 :C.ArtifactRef;
    file @2 :C.ArtifactRef;
  }
}

struct Message {
  role @0 :Role;
  content @1 :List(Content);
  name @2 :Text; # empty means absent
}

struct ToolResult {
  callId @0 :Text;
  content @1 :List(Content);
  isError @2 :Bool;
}

struct InputItem {
  union {
    message @0 :Message;
    toolResult @1 :ToolResult;
  }
}

struct ToolDefinition {
  name @0 :Text;
  description @1 :Text;
  inputJsonSchema @2 :C.ArtifactRef; # UTF-8 RFC 8259 JSON Schema object
}

struct ToolChoice {
  union {
    auto @0 :Void;
    none @1 :Void;
    required @2 :Void;
    specific @3 :Text;
  }
}

struct InferenceRequest {
  invocation @0 :C.Uuid;
  virtualModel @1 :Text;
  input @2 :List(InputItem);
  tools @3 :List(ToolDefinition);
  toolChoice @4 :ToolChoice;
  maxOutputTokens @5 :UInt32; # 0 = selected binding default
  temperature @6 :OptionalFloat64;
  topP @7 :OptionalFloat64;
  stopSequences @8 :List(Text);
  stream @9 :Bool;
}

struct ToolCall {
  id @0 :Text;
  name @1 :Text;
  argumentsJson @2 :Data; # UTF-8 RFC 8259 JSON object
}

struct Usage {
  inputTokens @0 :UInt64;
  outputTokens @1 :UInt64;
  cachedInputTokens @2 :UInt64;
}

enum FinishReason {
  stop @0;
  toolCalls @1;
  length @2;
  contentFilter @3;
  cancelled @4;
  failed @5;
}

struct InferenceResult {
  assistant @0 :Message;
  toolCalls @1 :List(ToolCall);
  usage @2 :Usage;
  finishReason @3 :FinishReason;
  providerResponse @4 :C.MaybeArtifactRef; # protected original response when retention allows
}

struct TextDelta {
  text @0 :Text;
}

struct ToolCallStart {
  index @0 :UInt32;
  id @1 :Text;
  name @2 :Text;
}

struct ToolCallArgumentsDelta {
  index @0 :UInt32;
  data @1 :Data; # UTF-8 JSON fragment; concatenate by index
}

struct ToolCallDone {
  index @0 :UInt32;
  call @1 :ToolCall;
}

struct Failure {
  error @0 :C.RpcError;
}

struct StreamEvent {
  union {
    textDelta @0 :TextDelta;
    toolCallStart @1 :ToolCallStart;
    toolCallArgumentsDelta @2 :ToolCallArgumentsDelta;
    toolCallDone @3 :ToolCallDone;
    usage @4 :Usage;
    completed @5 :InferenceResult;
    failed @6 :Failure;
  }
}

struct ModelBindingMetadata {
  binding @0 :C.Uuid;
  contextWindow @1 :UInt32;
  maxOutputTokens @2 :UInt32;
  tools @3 :Bool;
  images @4 :Bool;
  files @5 :Bool;
  streaming @6 :Bool;
}
