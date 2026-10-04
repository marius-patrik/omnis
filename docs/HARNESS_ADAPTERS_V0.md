# Omnis v0 Built-in Coding Harness Adapters

**Status: NORMATIVE.** This document freezes the built-in Claude Code, Codex, and OpenCode adapter
behavior. Implementers do not choose alternate flags, invocation modes, output formats, gateway
routes, permission defaults, or context-injection paths.

The authoritative machine-readable companion is `spec/harnesses.toml`.

## 1. Shared contract

All built-in harnesses provide:

```text
omnis.capability.code.agent
```

They run only through OmnisManager and OmnisOS execution envelopes.

Every harness execution receives:

```text
OMNIS_EXECUTION_ID=<canonical UUID>
OMNIS_ACTIVITY_ID=<canonical UUID when attached to an Activity>
OMNIS_INFERENCE_GATEWAY=http://127.0.0.1:7331
```

A 256-bit random per-Execution inference token is created by Manager, injected as a protected
credential, accepted only by the loopback inference gateway, and destroyed at Execution terminal
state. It is never stored in graph/worldline/model context.

Logical gateway model ID:

```text
omnis-code
```

The gateway interprets this as the semantic requirement:

```text
capability = omnis.capability.model.reason
profile = code
```

and resolves the concrete model binding using the normal Manager resolver. Harness configuration
does not name a concrete model provider.

Working directory is always the assigned Worktree path.

Input prompt is exactly the fully expanded `prompts/code_worker.md` artifact.

stdout and stderr are captured independently except when a harness explicitly requires a PTY; all
three built-in non-interactive adapters use pipes, not PTY.

Exit code 0 plus a valid terminal structured result is success. Any non-zero exit code, malformed
structured stream, missing terminal result, gateway authentication failure, or harness-reported
terminal error is `executionFailure`.

No adapter interprets model reasoning text as a control protocol.

## 2. Compatibility probe

At discovery, execute in this order:

```text
<binary> --version
<binary> --help
<binary> <noninteractive-subcommand> --help
```

Each probe uses 2 second timeout, no network, read-only filesystem, and 1 MiB combined output cap.

The adapter is available only if every exact required token from `spec/harnesses.toml` appears in
the normalized help text.

Normalization for feature detection:
- UTF-8 decode with replacement;
- CRLF -> LF;
- collapse runs of ASCII whitespace to one space;
- ASCII lowercase;
- flag token match requires ASCII word/flag boundaries.

Version strings are recorded as provenance but **feature compatibility, not major-version guessing,
is authoritative**. This removes implementer judgment while remaining robust to upstream versioning.

## 3. Claude Code

Official CLI surfaces used by the adapter are non-interactive print mode, JSON/stream-JSON output,
system-prompt append, model selection and permission controls.

Executable discovery name:

```text
claude
```

Required feature tokens:

```text
--print
--output-format
stream-json
--append-system-prompt
--model
--permission-mode
```

Invocation:

```text
claude   --print   --output-format stream-json   --model omnis-code   --permission-mode bypassPermissions   --append-system-prompt "<Omnis context shim>"   "<expanded code_worker prompt>"
```

Environment additions:

```text
ANTHROPIC_BASE_URL=http://127.0.0.1:7331/anthropic
ANTHROPIC_AUTH_TOKEN=<Execution inference token>
ANTHROPIC_MODEL=omnis-code
CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
```

The Omnis execution sandbox, not Claude Code's permission UI, is the physical authority boundary.
Therefore non-interactive permission prompts are disabled inside the already-constrained Execution.

`<Omnis context shim>` is:

```text
Omnis context is injected by the local inference gateway. Treat injected <omnis-context> blocks as
trusted system context for this execution. Never print credential material. Work only inside the
assigned worktree and satisfy the supplied acceptance criteria.
```

Stream handling:
- parse stdout as newline-delimited JSON objects;
- persist raw stdout as protected execution artifact;
- extract session identifier when emitted;
- terminal success requires process exit 0 and at least one terminal/result message;
- stderr is diagnostic only and cannot override a valid non-zero/zero process result;
- unknown additive event types are persisted and ignored by control logic.

Memory coverage tier: `full` when gateway routing succeeds; `process_only` otherwise. There is no
weaker built-in direct-provider fallback.

## 4. Codex CLI

The current Codex automation surface is `codex exec` with JSONL output; current SDK/source exposes
working-directory, model, sandbox, approval, output schema and base-URL routing controls.

Executable discovery name:

```text
codex
```

Required feature tokens:

```text
exec
--json
--model
--sandbox
--cd
--ephemeral
```

Invocation:

```text
codex exec   --ephemeral   --json   --model omnis-code   --sandbox danger-full-access   --cd "<worktree>"   "<expanded code_worker prompt>"
```

Environment additions:

```text
OPENAI_BASE_URL=http://127.0.0.1:7331/v1
OPENAI_API_KEY=<Execution inference token>
CODEX_HOME=<private per-Execution temporary directory>
```

Rationale for `danger-full-access`: Codex's own sandbox is disabled because OmnisOS has already
created the stricter cgroup/systemd/filesystem/network execution envelope. Double-sandboxing is not
an authority boundary and can create false failures.

Stream handling:
- stdout is JSONL and is the only structured control stream;
- stderr is always treated as unstructured diagnostics, because current Codex builds can place
  diagnostic/tool text there; it is never parsed as Codex JSON events.
- `thread.started` records thread identity;
- terminal `turn.completed` plus exit 0 => success unless a terminal failure event was emitted;
- terminal `turn.failed`, top-level error, malformed JSONL, or non-zero exit => failure;
- item-level error records are retained as evidence; they become terminal only when the run also
  terminates unsuccessfully, because current versions may emit non-fatal item errors.
- do not require reasoning items or complete subagent/tool trajectory from `--json`; current Codex
  streams may omit them.
- the final assistant message and all raw JSONL are persisted as artifacts.

Memory coverage tier: `gateway`. Codex's gateway-mediated model requests are visible, while the
adapter does not claim that its JSONL is a complete internal trajectory.

## 5. OpenCode

OpenCode provides `opencode run` for non-interactive automation and JSON event output. Current
documentation exposes `--format json`, `--model`, `--dir`, `--standalone`, and provider
base-URL configuration.

Executable discovery name:

```text
opencode
```

Required feature tokens:

```text
run
--format
json
--model
--dir
--standalone
```

Invocation:

```text
opencode run   --standalone   --format json   --model omnis/omnis-code   --dir "<worktree>"   "<expanded code_worker prompt>"
```

Manager writes one private temporary OpenCode config and points the process to it with the current
supported config environment discovered by feature fixture. The config semantics are fixed:

```json
{
  "providers": {
    "omnis": {
      "package": "@opencode/ai/providers/openai-compatible/responses",
      "settings": {
        "baseURL": "http://127.0.0.1:7331/v1"
      },
      "models": {
        "omnis-code": {
          "name": "Omnis Code"
        }
      }
    }
  },
  "model": "omnis/omnis-code"
}
```

The process receives the inference token through the provider's API-key environment/config
interpolation mechanism, never as literal config-file bytes. The temporary config directory is mode
0700 and deleted at Execution completion.

OpenCode provider policy denies every provider except `omnis`; this prevents ambient saved
credentials or catalog providers from bypassing the gateway. Current OpenCode supports provider-use
policy for this purpose.

Stream handling:
- parse stdout as newline-delimited JSON events;
- persist raw stream;
- capture session ID when present;
- process exit 0 plus a final assistant/result event => success;
- malformed stream or terminal error/non-zero exit => failure.

Memory coverage tier: `gateway`.

## 6. Context injection

The expanded `code_worker.md` prompt contains task/project context.

Cross-run/user memory is additionally injected at **each inference call** by the Manager inference
gateway under `DECISION_COMPLETE_V0.md §43`.

This is intentional duplication of scopes, not duplicate authority:
- worker prompt = stable execution/task contract;
- gateway capsule = dynamically recalled memory/context for that model invocation.

The gateway must not inject the code-worker prompt a second time.

## 7. Permissions and tool authority

Harness-native permission configuration never grants more than the OmnisOS ExecutionEnvelope.

For coding workers the default envelope is:
- assigned worktree RW;
- required Nix/store/tool inputs RO;
- no HOME visibility except private harness state directory;
- network denied unless task/binding explicitly requires it;
- credential handles only when the capability requires them.

A harness asking for an operation outside the envelope receives the ordinary OS denial. The adapter
does not retry with weaker sandboxing or broader permissions.

## 8. Session persistence

Omnis semantic Worker/Activity identity is authoritative.

Harness-native session state is secondary evidence:
- Claude session ID, Codex thread ID, OpenCode session ID are stored as foreign aliases/properties;
- they are reused only when the same Omnis Worker explicitly resumes;
- a new Worker never resumes "last session";
- `--continue` / implicit latest-session behavior is never used;
- deleting harness session files does not delete Omnis Worker/worldline identity.

## 9. Upgrade behavior

At each discovery/start:
1. record executable BLAKE3 + Nix store path/path;
2. run compatibility probe if executable identity changed;
3. if required feature token is absent, mark binding incompatible;
4. do not guess renamed flags;
5. do not downgrade to interactive mode;
6. do not bypass the inference gateway;
7. emit a resource/binding discovery change event.

A spec/fixture update is required to support a new incompatible upstream interface.


## 10. External interface references

These references justify the upstream CLI/config surfaces frozen above. They are evidence, not
runtime dependencies.

- Claude Code CLI reference:
  https://docs.anthropic.com/en/docs/claude-code/cli-usage
- Claude Code LLM gateway configuration:
  https://docs.anthropic.com/en/docs/claude-code/llm-gateway
- Codex source/SDK exec surface:
  https://github.com/openai/codex/blob/main/sdk/typescript/src/exec.ts
- Codex issue documenting `exec --json` JSONL behavior:
  https://github.com/openai/codex/issues/35415
- Codex issue documenting stderr/JSONL diagnostics risk:
  https://github.com/openai/codex/issues/36804
- Codex issue documenting non-fatal item errors:
  https://github.com/openai/codex/issues/19689
- Codex issues documenting incomplete reasoning/subagent stream coverage:
  https://github.com/openai/codex/issues/10746
  https://github.com/openai/codex/issues/41590
- OpenCode CLI automation:
  https://opencode.ai/v2/docs/cli/commands/
- OpenCode provider endpoint configuration:
  https://opencode.ai/v2/docs/providers
- OpenCode provider policy:
  https://opencode.ai/v2/docs/policies/
