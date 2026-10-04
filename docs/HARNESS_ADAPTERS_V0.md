# Omnis v0 Harness Adapters and Inference Gateway

**Status: NORMATIVE.** This document freezes the three built-in external coding-agent adapters and
the model gateway they use. Implementers do not choose alternate CLI modes, model-routing behavior,
session transport, inner permission modes, or coverage tiers.

The exact release fixtures are:

| Harness | v0 version | Control surface |
|---|---:|---|
| Claude Code | 2.1.289 | print mode + stream-json stdin/stdout |
| Codex | 0.160.0 (`rust-v0.160.0`) | app-server over stdio JSON-RPC |
| OpenCode | 1.18.34 | `opencode serve` HTTP + SSE |

`spec/harnesses.toml` is the machine-readable adapter manifest.
`spec/inference_gateway.toml` is the machine-readable gateway contract.

## 1. Common execution contract

Every built-in `omnis.capability.code.agent` binding has one hard dependency on
`omnis.capability.model.reason`.

Manager resolves the code-agent Binding first, then resolves exactly one reason-model Binding under
the same Activity authority/privacy/locality constraints. If no reason-model Binding is feasible,
the built-in harness Binding is infeasible. The harness never chooses a provider.

The selected model binding is locked to the harness Execution for its lifetime and is exposed to the
harness only as virtual model:

```text
omnis-reason
```

A request authenticated by a harness token that names any other model is rejected.

## 2. Execution-scoped gateway authentication

Before launching a built-in harness, Manager generates 32 CSPRNG bytes and serializes:

```text
omnis1.<base64url-without-padding(random32)>
```

Only BLAKE3-256(token bytes) is retained in Manager memory. The record contains:

```text
ExecutionId
WorkerId
ActivityId
selected model BindingId
protection/provider constraints
creation monotonic time
```

The plaintext token is injected only as `OMNIS_GATEWAY_TOKEN` and, when a harness requires it, its
provider-specific bearer-token variable.

HTTP requests must send:

```http
Authorization: Bearer <OMNIS_GATEWAY_TOKEN>
```

There is no persistent gateway-token database. Token lifetime equals Execution lifetime. On terminal
Execution state it is erased immediately. After managerd restart all old tokens are invalid; live
harness processes are stopped, restarted with new tokens, and resumed through their recorded foreign
session/thread identity.

A gateway token is never accepted as an upstream provider credential and never leaves the local
machine.

## 3. Gateway network envelope

A built-in harness does not receive broad network access merely to reach a model.

Its base network requirement is `loopback-gateway`:

```text
PrivateNetwork=no
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
IPAddressDeny=any
IPAddressAllow=127.0.0.1
IPAddressAllow=::1
cgroup connect eBPF: TCP destination port must equal 7331 for loopback gateway traffic
```

If the coding task requires other network access, Manager unions only the destinations already
granted by the selected code-agent Binding/Activity. Gateway access never implies public network.

## 4. Canonical inference path

The inference gateway accepts only the endpoint set in `spec/inference_gateway.toml`.

Every request becomes `protocol/inference.capnp::InferenceRequest`. Model provider adapters consume
that canonical request and emit `InferenceResult` / `StreamEvent`. Provider-specific request
translation exists only at the Manager adapter boundary.

The canonical subset supports:

- system/developer/user/assistant messages;
- text, image ArtifactRef and file ArtifactRef content;
- tool definitions using UTF-8 JSON Schema artifacts;
- tool results keyed by call ID;
- automatic/none/required/specific tool choice;
- max output tokens;
- finite temperature/top-p;
- stop sequences;
- streaming text/tool-call deltas;
- final usage and finish reason.

Unsupported hosted-provider-only features are rejected with `InvalidArgument`; they are never
silently approximated.

### 4.1 OpenAI Responses mapping

`POST /v1/responses` maps:
- `instructions` -> first developer Message;
- input message items -> Message;
- function-call-output items -> ToolResult;
- function/custom function tool definitions -> ToolDefinition;
- function tool choice -> ToolChoice;
- `max_output_tokens`, `temperature`, `top_p` -> canonical scalar fields;
- streaming response events -> canonical StreamEvent -> OpenAI-compatible SSE.

Hosted web/file-search/computer/code-interpreter/image tools are rejected for this local gateway.
The harness must use its own local tools.

### 4.2 OpenAI Chat Completions mapping

`POST /v1/chat/completions` maps system/developer/user/assistant/tool roles, function tools and
tool-choice directly to the canonical structures. Unknown top-level request fields are rejected
except metadata fields explicitly documented as nonsemantic and ignored by the compatibility parser.

### 4.3 Anthropic Messages mapping

`POST /anthropic/v1/messages` maps:
- top-level `system` -> system Message;
- user/assistant messages -> Message;
- `tool_use` -> ToolCall;
- `tool_result` -> ToolResult;
- `tools[].input_schema` -> ToolDefinition;
- `tool_choice` -> ToolChoice;
- `max_tokens`, `temperature`, `top_p`, `stop_sequences` -> canonical fields.

Known Anthropic cache-control annotations are ignored as nonsemantic cache hints after being retained
in the protected original-request artifact. Unknown beta features that alter semantics are rejected.

`/anthropic/v1/messages/count_tokens` tokenizes the mapped canonical request using the selected
model Binding tokenizer when advertised; otherwise it uses the same conservative byte estimator as
Agent context compilation.

## 5. Context injection

For every model request authenticated by a Worker-attached harness token:

1. gateway parses the request;
2. stores the protected original request artifact;
3. asks Agent to compile a ContextCapsule for the Worker and current inference call;
4. caps injected content at `min(25% input budget, 16384 tokens)`;
5. excludes material prohibited for the selected concrete provider;
6. adds stable NodeId/EventId evidence citations;
7. injects exactly one tagged Omnis context segment;
8. emits `omnis.event.inference.request`;
9. invokes the locked reason-model Binding;
10. streams result and emits response/failure event.

Injection representation:
- Responses: prepend one developer input message;
- Chat Completions: prepend one developer message;
- Anthropic Messages: append one `<omnis-context>...</omnis-context>` block to the system content.

The tag is recognized on future interception and is not re-ingested as new source evidence.

## 6. Coverage contract

Coverage is dimensional:

```text
model_interception
context_injection
structured_lifecycle
structured_tool_events
session_resume
permission_control
```

A built-in adapter is `full` only when all six are true. Claude Code, Codex and OpenCode are all
`full` for the pinned v0 versions.

This supersedes the older rule that `full` necessarily required a native pre-model hook. Gateway
interception plus the harness's structured control/event surface is sufficient. Native hooks may
supply additional evidence but are not a correctness dependency.

## 7. Claude Code 2.1.289

Discovery requires executable `claude` and exact parsed version `2.1.289`. Any other version is
reported as a Resource but this built-in Binding is `incompatible`.

Each Agent Worker turn launches one process in the Worker worktree:

```text
claude -p
  --input-format stream-json
  --output-format stream-json
  --verbose
  --dangerously-skip-permissions
  --model omnis-reason
  [--resume <foreign_session_id>]
```

Prompt text never appears in argv. Manager writes one NDJSON user envelope from
`spec/harnesses.toml` to stdin.

Environment is exact:

```text
OMNIS_GATEWAY_TOKEN=<execution token>
ANTHROPIC_BASE_URL=http://127.0.0.1:7331/anthropic
ANTHROPIC_AUTH_TOKEN=<execution token>
ANTHROPIC_MODEL=omnis-reason
DISABLE_AUTOUPDATER=1
```

`ANTHROPIC_API_KEY` is removed from the environment.

Output parsing:
- every non-empty stdout line must be a JSON object or the Execution fails as incompatible output;
- retain the raw NDJSON as an Execution artifact;
- first non-empty `session_id` becomes the foreign session alias;
- `assistant.message.content[].type=tool_use` records a tool-call semantic event;
- `user.message.content[].type=tool_result` records its result;
- `system` messages record session/compaction/lifecycle evidence;
- terminal `type=result, subtype=success` means turn success;
- any result error subtype or non-zero process exit means failure;
- unknown JSON message types are preserved as evidence and produce a compatibility diagnostic, not
  silently discarded.

Claude's inner permission layer is deliberately bypassed. OmnisOS ExecutionEnvelope is the sole
physical authority boundary for this Worker.

## 8. Codex 0.160.0

Discovery requires exact `codex --version` semver `0.160.0`.

Manager starts one app-server per Worker using the exact argv in `spec/harnesses.toml`:
- stdio transport;
- strict config;
- provider `omnis`;
- base URL `http://127.0.0.1:7331/v1`;
- bearer token from `OMNIS_GATEWAY_TOKEN`;
- Responses wire API;
- WebSockets off;
- approvals `never`;
- Codex sandbox `danger-full-access`.

OmnisOS remains the sole physical sandbox; Codex is not allowed to add a divergent inner sandbox.

At package build time, run:

```text
codex app-server generate-json-schema --out <build-output>/share/omnis/codex-app-server-schema
```

with **no** `--experimental`. The generated stable schema for 0.160.0 is the adapter parser
authority.

RPC sequence:

1. send `initialize` with clientInfo name `omnis`, title `Omnis`, system release version and
   `experimentalApi=false`;
2. wait for successful response;
3. send `initialized`;
4. new Worker session: `thread/start` with cwd = Worker worktree, model = `omnis-reason`;
5. resumed session: `thread/resume` with recorded thread ID;
6. persist returned `thread.id` as foreign session alias;
7. send `turn/start` with text input containing the expanded code-worker prompt;
8. consume all typed notifications and store unknown stable-schema notifications as evidence;
9. `turn/completed` is terminal for the turn; only status `completed` succeeds. `failed` or
   `interrupted` fails/cancels accordingly.

## 9. OpenCode 1.18.34

Discovery requires exact `opencode --version` semver `1.18.34`.

Each Worker starts a dedicated headless server:

```text
opencode serve --hostname 127.0.0.1 --port 0
```

It is not the user's shared OpenCode service. Manager parses the selected ephemeral port from the
startup line and immediately verifies `GET /global/health`.

The server has independent random 32-byte Basic Auth password
`OMNIS_HARNESS_SERVER_TOKEN`; username is `omnis`. This token exists only in Manager memory and
the child environment.

Manager supplies `OPENCODE_CONFIG_CONTENT` as canonical minified JSON:

```json
{
  "$schema":"https://opencode.ai/config.json",
  "autoupdate":false,
  "model":"omnis/omnis-reason",
  "small_model":"omnis/omnis-reason",
  "permission":"allow",
  "provider":{
    "omnis":{
      "npm":"@ai-sdk/openai",
      "name":"Omnis",
      "options":{
        "baseURL":"http://127.0.0.1:7331/v1",
        "apiKey":"{env:OMNIS_GATEWAY_TOKEN}"
      },
      "models":{
        "omnis-reason":{
          "name":"Omnis Reason",
          "limit":{
            "context":<selected_binding_context_window>,
            "output":<selected_binding_max_output>
          }
        }
      }
    }
  }
}
```

Also set `OPENCODE_DISABLE_AUTOUPDATE=1` and `OPENCODE_DISABLE_MODELS_FETCH=1`.

Control sequence:

1. open authenticated `GET /event` SSE stream;
2. `POST /session` to create a session, or reuse the recorded session ID after process restart if
   the server instance can resolve it;
3. persist returned session ID as foreign session alias;
4. `POST /session/<id>/message` with model
   `{"providerID":"omnis","modelID":"omnis-reason"}` and one text part containing the expanded
   code-worker prompt;
5. consume the synchronous response plus SSE lifecycle/tool/message events;
6. use `GET /session/status` to reconcile after reconnect;
7. cancel through `POST /session/<id>/abort`;
8. collect `GET /session/<id>/diff` at terminal state.

OpenCode's permission config is `allow` because OmnisOS is the physical authority boundary.
Its server binds only loopback and is protected by Basic Auth.

On Worker terminal state Manager calls `POST /instance/dispose`, terminates the server process,
erases both local tokens and records the session/diff artifacts.

## 10. No direct provider escape

For all three built-ins:
- remove inherited provider API key/token variables not explicitly required by the adapter;
- physical network policy allows the inference gateway but not provider endpoints unless an unrelated
  task capability explicitly grants them;
- model identity presented to the harness is always `omnis-reason`;
- the concrete provider/model never enters harness configuration;
- provider credential bytes never enter harness environment, argv, config, graph or Agent context.

## 11. Adapter upgrade rule

A different harness version is not "close enough."

To support it:
1. update `spec/harnesses.toml`;
2. update version-specific fixtures/schema snapshots;
3. run adapter conformance tests;
4. verify gateway routing, structured events, resume and permission behavior;
5. change this document in the same commit;
6. only then mark the new version compatible.

There is no best-effort flag guessing.


## 12. Upstream interface evidence

These references support the exact pinned adapter fixtures above. They are evidence only and do not
weaken the version pins.

- Claude Code CLI: https://docs.anthropic.com/en/docs/claude-code/cli-usage
- Claude Code gateway configuration: https://docs.anthropic.com/en/docs/claude-code/llm-gateway
- Codex exec/app-server source surface: https://github.com/openai/codex
- OpenCode CLI: https://opencode.ai/v2/docs/cli/commands/
- OpenCode providers: https://opencode.ai/v2/docs/providers

## 13. Descriptor-driven generic harness

The v0 generic harness adapter is intentionally narrower than the three built-ins. It supports one
process-per-turn executable described by a JSON document that validates against
`spec/generic_harness.schema.json`.

Exact behavior:

1. descriptor is supplied by an explicitly registered Resource; Manager never invents one from help text;
2. run `probe.versionArgs`, then `probe.helpArgs`, each with the normal 2-second discovery timeout;
3. normalize help output as UTF-8 with replacement, CRLF->LF, ASCII whitespace collapse, ASCII lowercase;
4. every `probe.requiredTokens` token must occur after normalization or Binding is incompatible;
5. expand only `{worktree}`, `{gateway}`, and `{model}` argv placeholders;
6. prompt transport `last_arg` appends expanded `prompts/code_worker.md`; `stdin_utf8` writes those UTF-8 bytes then closes stdin;
7. working directory is always the assigned Worktree path;
8. `process_only` receives no model-provider credential or gateway grant;
9. `gateway` receives exactly the descriptor gateway/model environment plus one execution-scoped gateway token; the credential variable value is that token;
10. output `text` retains stdout bytes; `json` requires one RFC 8259 JSON value; `jsonl` requires every non-empty line to be one RFC 8259 JSON value;
11. exit 0 plus valid declared output is success; non-zero or invalid declared output is failure;
12. generic adapters expose process lifecycle only; they do not claim structured tool/session events or session resume.

The generic descriptor cannot claim `full` or `hook` coverage in v0. Rich integration requires a
first-party/versioned adapter contract.
