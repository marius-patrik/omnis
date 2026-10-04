# ADR-0026 — Keep exactly three core authorities and make every agent an external client

- **Status**: Accepted · **Date**: 2026-10-04
- **Supersedes:** ADR-0023's four-authority topology and the Agent/worldline/outbox portions of ADR-0024.
- **Narrows:** ADR-0025 to the current three-authority core contract.

## Context

The graph-native reset correctly made the operating system, resource manager and Control surface share
one semantic machine model, but it still made one particular cognitive implementation
(`OmnisAgent`) a first-party authority. It also pulled external coding-agent harnesses into Manager
and designed graph event delivery around one Agent-owned ACK/worldline consumer.

That is the wrong boundary.

Omnis must be intrinsically agent-operable without being intrinsically tied to one agent runtime. A
different agent should be able to attach tomorrow, consume the complete machine history, use the same
OS/Manager/Control operations and obtain the same structural Control access without an Omnis core
change. The reference agent can then evolve much faster than the operating system.

## Decision

Omnis v0 has exactly three core semantic authorities:

```text
OmnisOS       physical/system authority
OmnisManager  resource/capability/execution authority
OmnisControl  interaction/presentation authority
```

The shared multidimensional graph and append-only core event journal are common substrate, not
additional product authorities.

There is no core `OmnisAgent` service, repository, socket, NixOS user service, lifecycle state
machine, cognitive namespace, memory store or `code.agent` capability.

Every meaningful first-party OS/Manager/Control transition is appended durably to graphd's core event
journal. The journal is multi-consumer:
- monotonically increasing `ingest_seq`;
- replay from any retained cursor;
- live subscription after catch-up;
- no global ACK;
- no consumer may delete/advance another consumer's history;
- no automatic event deletion in v0.

All public Graph/OS/Manager/Control operations and all core events are projected with semantic parity
through:
- `omnis mcp` over stdio;
- the generated native `@omnis/agent-access` client/plugin SDK.

An agent is therefore a client with granted authority. Agent-owned worldline, memory, context,
goals/tasks, model sessions, worker state, procedures and learning live outside core. An authorized
agent may optionally publish selected semantic state into a granted `ext.<client-id>.*` namespace;
it cannot acquire first-party `omnis.*` write ownership.

Manager may still expose generic model/inference capabilities. It does not launch, pin, adapt or
fail over between Claude Code, Codex, OpenCode, DeepSeek Harness or other agent runtimes.

The separately released `marius-patrik/dsh-stack` project is the reference agent environment. Its
Omnis integration consumes exactly the same MCP/native-plugin surfaces available to any other agent.
Omnis releases never depend on or pin a DSH release.

## Alternatives rejected

- **Keep OmnisAgent as a privileged fourth service but also expose MCP.** This leaves two classes of
  agent: the privileged built-in one and everyone else. The OS would still encode one cognitive
  architecture as authority.
- **Put DSH Stack inside the Omnis release.** This couples fast-moving cognition/provider/UI work to
  OS releases and makes replacing the agent runtime a system migration.
- **Expose only MCP.** MCP is the portable boundary, but a local typed plugin client avoids
  unnecessary serialization and gives native integrations exact schema parity. Both must project one
  semantic API.
- **Expose only a native SDK.** This excludes arbitrary existing agents and recreates a proprietary
  harness boundary.
- **Keep one global Agent ACK queue.** A slow/disconnected consumer would become a system retention
  authority and newly installed agents could not independently replay history.
- **Treat external agents as screen automation.** Omnis already owns structured state and Control
  tree semantics; throwing them away and re-inferring pixels is less capable and less reliable.

## Consequences

- Core boot, recovery, package management, execution and Control work with no agent installed.
- Multiple independent agents can attach concurrently without changing core semantics.
- The event journal grows monotonically in v0; retention/archival requires a later explicit protocol
  that preserves replay guarantees rather than an implicit GC policy.
- Event-referenced CAS artifacts remain GC roots while their core events are retained.
- OmnisControl must expose enough typed structure that agents never need screenshot/synthetic-input
  automation for first-party UI when an equivalent structural operation exists.
- DSH Stack becomes the place for the removed cognitive worldline/memory/task/learning architecture,
  but remains independently deployable and replaceable.
- ADR-0004 remains valid only as repository **delivery automation**; its coding-CLI harness chain is
  not Omnis product architecture.
