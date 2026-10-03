# OmnisManager

**Status: normative supporting specification.**

OmnisManager is the resource, capability, binding, execution, and placement authority of Omnis. It
is implemented as a maintained fork/extension of `NixOS/nix` plus the Rust `omnis-managerd` service.

Nix remains a package/build/store system. OmnisManager extends its reach so the same machine can
reason uniformly about packages, programs, models, agent harnesses, services, devices, remote hosts,
and arbitrary foreign capabilities.

---

## 1. Principles

1. **Packages are resources, not the whole universe.**
2. **Capabilities describe meaning; bindings describe realizations.**
3. **Stable resource identity survives physical replacement.**
4. **Discovery is deterministic-first.**
5. **Existing tools are bound, not reimplemented.**
6. **Provider-specific details do not leak into Agent cognition.**
7. **Resolution and placement are inspectable.**
8. **Protected values are handles.**
9. **Unknown foreign effects are treated conservatively.**
10. **Nix evaluation remains deterministic and model-free.**

---

## 2. Resource model

`Resource` is any concrete or realizable thing that may provide capabilities or participate in an
execution.

Initial categories include:

```text
package / derivation / store artifact
executable
library
service
CLI
API endpoint
protocol endpoint
container
VM
host
CPU / GPU / accelerator
device
model artifact
inference engine
model provider binding
agent harness
MCP server/client
repository/workspace
credential handle
database
network resource
native handle
```

Categories are graph kinds, not separate manager architectures.

---

## 3. Capability model

A capability is an addressable semantic action contract.

Examples:

```text
shell.execute
vcs.commit
vcs.push
code.agent
code.format
model.classify
model.embed
model.rerank
model.reason
browser.navigate
browser.inspect
container.run
gpu.compute
image.render
system.build-generation
```

A capability may define:

- input/output schema;
- required resource features;
- effect classification;
- hard constraints;
- optional quality/cost metadata;
- discoverable documentation.

Capabilities are not tied to a provider.

---

## 4. Bindings

A Binding states that a resource can realize a capability under known conditions.

```text
Binding
  resource
  capability
  constraints
  invocation descriptor
  effect metadata
  provenance
  version/environment requirements
```

Bindings may be:

```text
native-declared
Nix/package-derived
deterministically discovered
adapter-declared
semantically inferred
user-declared
```

The provenance category remains visible.

---

## 5. Resolution

`resolve(capability, constraints, context)` returns candidate bindings plus an inspectable selection.

Hard constraints eliminate candidates. Remaining candidates can be ordered by explicit policy over:

- compatibility;
- availability;
- locality;
- latency;
- quality/capability tier;
- CPU/GPU/RAM demand;
- privacy;
- monetary/token cost;
- energy;
- provider quota;
- warm state/cache;
- user preferences;
- Agent learned performance estimates.

Learned estimates are input data, not hidden control flow. Given the same graph revision, policy,
and estimates, resolution should be reproducible.

Callers can request a specific binding when implementation identity is semantically relevant.

---

## 6. Nix extensions

The maintained Nix fork exposes structured observer/query APIs for:

- derivation/resource identity mapping;
- why a package/store path exists;
- dependency/closure provenance;
- what a candidate configuration changes;
- build/download/rebuild plans;
- generation/store realization events;
- graph publication hooks;
- resource metadata discovery;
- execution environment realization.

Omnis-specific semantic metadata lives alongside, not inside, core derivation semantics. The normal
Nix daemon/client worker protocol remains compatible. Omnis-specific control and observation use the
separate `/run/omnis/nix-control.sock` Cap'n Proto endpoint.

The fork patches the current upstream evaluator/store boundaries rather than creating another Nix
implementation. Required hook points include `EvalState::forceValue` in `src/libexpr`, derivation
creation, `src/libstore` realization/substitution/closure operations, build lifecycle code under
`src/libstore/build`, and daemon-operation correlation in `src/libstore/daemon.cc`. Upstream-compatible
behavior remains the default.

---

## 7. Arbitrary bindings

Manager must make it easy to bind things it has never seen before.

Minimum generic binding locators:

```text
command
path
library/native symbol
process/service
HTTP/API endpoint
Unix socket / named pipe
D-Bus interface
MCP server
LSP/DAP endpoint
model endpoint
container/VM
host/device
credential handle
custom foreign handle
```

A generic binding may start weak and become semantically richer as discovery produces evidence.

---

## 8. Discovery pipeline

When a resource appears, Manager attempts enrichment in this order when applicable:

```text
1. Nix/resource metadata
2. native descriptors and reflection
3. protocol schemas
4. desktop/service registration metadata
5. LSP/DAP/compiler/runtime metadata
6. CLI completion / --help / man / structured help
7. source/debug symbols/config schemas
8. deterministic probing
9. specialist classifier/parser/model
10. general reasoning worker
```

Discovery results become graph relations with provenance and confidence.

The system may revisit older resources when better tooling/models become available.

---

## 9. External agent harnesses

Agent harnesses are normal resources that provide capabilities.

Initial target bindings:

```text
Claude Code
Codex
OpenCode
Agents-compatible runtimes
arbitrary CLI harnesses
MCP-capable agents
```

A harness binding should expose, when possible:

- binary/package identity;
- supported model/provider configuration;
- tool/permission controls;
- repository/workspace requirements;
- session/resume semantics;
- lifecycle hooks/events;
- context interception endpoint or model proxy integration;
- cost/quota status;
- structured output/protocol capabilities.

OmnisAgent can use harnesses as workers without encoding harness-specific behavior into its core.

---

## 10. Inference engines and models

Inference is resolved like any other capability.

Manager graph identities distinguish:

```text
model artifact
model logical role
inference runtime
provider endpoint
hardware
execution
```

Example:

```text
Model:Qwen32B
  runnable_by -> Runtime:vLLM
  runnable_by -> Runtime:llama.cpp

Runtime:vLLM
  requires -> Capability:cuda.compute

GPU:5090
  provides -> Capability:cuda.compute
```

Logical roles such as `model.classify`, `model.embed`, `model.reason`, and `model.vision` may resolve
to different models/runtimes.

---

## 11. Protected values

Secrets are resources/handles with disclosure restrictions.

Manager may expose to Agent:

```text
identity
purpose/capabilities authorized
scope
availability
expiry
```

It does not expose plaintext unless a specifically authorized capability requires disclosure to the
calling process.

Execution receives the narrowest viable handle/injection scope.

---

## 12. Execution

An `Execution` binds together:

```text
requested capability
selected binding/resource
input references
host/placement
execution envelope
actor/activity
causal parents
lifecycle
outputs/artifacts
resource use
external effects
```

Execution lifecycle state is reflected in the graph and durably enqueued through graphd's event
outbox for Agent delivery.

---

## 13. Effect semantics

Manager attaches the strongest justified contract to a binding/execution:

```text
pure
read_only
idempotent
retry_safe
reversible
compensatable
transactional
persistent_external
opaque
```

Default for an unknown foreign operation is `opaque` and effectful.

Retries after ambiguous external writes require reconciliation where possible.

---

## 14. Placement

Placement is a resolution dimension, not an installation detail.

A capability may execute on:

```text
local native host
local container
local VM
remote Omnis host
remote generic host
cloud runner/GPU
```

Placement constraints are explicit and graph-queryable. Failure to find a satisfying host is a
resolution error with explanation, not silent fallback.

---

## 15. Manager CLI/API

The v0 Manager CLI surface supports:

```text
omnis manager resource list/inspect
omnis manager capability list/inspect
omnis manager bind
omnis manager discover
omnis manager resolve
omnis manager execute
omnis manager placement explain
omnis manager model list/status
omnis manager harness list/status
omnis manager protected list
omnis manager nix explain
```

CLI, Agent, Control, and MCP projections must call the same underlying Manager operations.

---

## 16. Non-goals

Manager does not:

- own Agent memory/cognition;
- become another package language;
- reimplement existing agent harnesses;
- reimplement model inference engines;
- replace Nix derivation semantics with learned resolution;
- own OS-level enforcement;
- own presentation.
---

## 17. v0 daemon architecture

`omnis-managerd` is a Rust 2024/Tokio process. It owns semantic resource/capability state and talks
to the patched C++ `nix-daemon` over `/run/omnis/nix-control.sock`.

Internal modules:

```text
registry      graph-backed resources/capabilities/bindings
discovery     deterministic enrichment and provenance
resolver      hard filtering + inspectable stable scoring
placement     host/runtime/device choice
executor      systemd transient-scope lifecycle
nix_bridge    Nix control/observer client
secrets       protected HandleId broker
adapters      subprocess/native binding providers
```

Local executions launch as systemd transient scopes under the Omnis cgroup hierarchy. ExecutionId is
the idempotency key and is embedded in the unit/scope metadata so restart reconciliation can discover
already-running work instead of duplicating it.

Third-party Manager adapters are subprocesses speaking the typed Cap'n Proto adapter protocol. They
are not arbitrary shared libraries loaded into the privileged daemon.

## 18. v0 binding providers

The first implementation ships providers for:

```text
Nix package/store/derivation
PATH executable + CLI metadata
systemd service/D-Bus
HTTP/OpenAPI
MCP
OpenAI-compatible model APIs
Anthropic model APIs
llama.cpp/local GGUF
ONNX Runtime classifiers/embeddings
Claude Code
Codex
OpenCode
generic PTY agent harness
container runtime
SSH generic remote host
native Omnis QUIC remote host
```

Provider-specific configuration is Manager state/Nix configuration. OmnisAgent asks only for
semantic capabilities such as `model.embed` or `code.agent`.

## 19. v0 protected-handle realization

Persistent secret bytes are systemd encrypted credentials and may be TPM2-sealed by OmnisOS.
Manager publishes only HandleId/purpose/scope/availability into the graph. At execution time the
handle is materialized into a private credential file or sealed memory handle; environment
injection is used only when the foreign program requires it.
