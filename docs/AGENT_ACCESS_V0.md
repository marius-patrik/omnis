# Omnis v0 Agent Access Contract

**Status: NORMATIVE.** Omnis core has no built-in agent runtime. This document defines how arbitrary
agents access OmnisOS, OmnisManager, OmnisControl, the shared graph, and the complete core event
journal without harness-specific integration.

## 1. Principle

There are exactly three core semantic authorities:

```text
OmnisOS
OmnisManager
OmnisControl
```

Graphd is shared substrate. Agent-access adapters are projections, not authorities.

An agent is a client. Removing every agent client must not change boot, recovery, package management,
execution, Control rendering or graph/event correctness.

## 2. Canonical source of truth

Canonical semantics remain the Cap'n Proto service APIs:

```text
protocol/os.capnp
protocol/manager.capnp
protocol/control.capnp
protocol/graph.capnp
```

`spec/agent_access.toml` maps every public operation/event to:
- MCP name/resource;
- native plugin client method;
- effect/read classification.

CI requires exact parity. An MCP/plugin-only operation is invalid.

## 3. MCP projection

Command:

```text
omnis mcp
```

Transport: MCP over stdio. It opens no listening network socket.

The process runs as the invoking Unix user, connects to the normal local Omnis sockets, and receives
exactly that caller's authority. It never runs setuid/root and never stores credentials.

Tool names are stable dotted names:

```text
omnis.os.*
omnis.manager.*
omnis.control.*
omnis.graph.*
```

Read-only graph/event objects are additionally exposed as MCP resources under:

```text
omnis://graph/node/<uuid>
omnis://graph/revision/<u64>
omnis://event/<event-uuid>
omnis://events/core
omnis://artifact/<blake3>
```

The `omnis://events/core` resource supports cursor replay from `ingest_seq` and resource-change
notifications for newly appended events. The MCP adapter never samples or semantically summarizes
events.

## 4. Native plugin SDK

The umbrella repository generates a native agent-access client from the same manifest and Cap'n Proto
schemas.

The v0 reference package is:

```text
@omnis/agent-access
```

It exposes four clients:

```text
os
manager
control
graph
```

and one lossless event iterator:

```text
events({ afterIngestSeq })
```

The package contains no cognition, memory, provider routing or agent lifecycle. Runtime-specific
plugins wrap this client.

The DSH reference integration is owned by `marius-patrik/dsh-stack`; it is not implemented inside
Omnis core.

## 5. Event contract

Every first-party event is appended durably to graphd's core event journal before publication is
considered complete.

Consumers:
- choose an initial `after_ingest_seq`;
- receive strictly increasing `ingest_seq`;
- persist their own cursor;
- reconnect from that cursor;
- deduplicate by EventId if desired.

There is no global ACK and no consumer-owned deletion.

v0 performs **no automatic deletion of core event-journal rows or referenced event artifacts**.
Archival/compaction is a future explicit feature, not implicit GC.

This guarantees that a newly attached authorized agent can replay every core event since system
initialization.

## 6. Agent-owned state

An agent owns its own:
- conversations;
- causal/cognitive worldline;
- memory/indexes;
- goals/tasks/workers;
- model/provider sessions;
- procedures/skills;
- self-model and learning.

It may store these outside Omnis or publish selected semantic state to a granted extension graph
namespace. Core never requires or interprets those structures.

Extension namespace convention:

```text
ext.<client-id>.*
```

Core-owned `omnis.*` namespaces remain write-protected.

## 7. Control structural access

Agent clients get the full typed ControlService, including:
- materialize;
- tree transactions;
- focus/selection;
- lens/mode;
- navigation;
- input submission;
- Control-node reads.

This is intentionally more structural access than normal end-user pointer/keyboard gestures expose.
The agent operates the tree directly and receives resulting Control events from the journal.

First-party automation MUST NOT use screenshots/synthetic input when the typed Control operation
exists.

## 8. No external harness architecture

Omnis core contains no:
- Claude Code adapter;
- Codex adapter;
- OpenCode adapter;
- DeepSeek Harness adapter;
- generic PTY coding-harness adapter;
- harness version pin;
- harness failover chain;
- harness-specific model gateway.

An external agent runtime may itself use any models/providers/harness machinery it wants. From Omnis'
perspective it is still only a client of the same three surfaces.

## 9. DSH reference direction

`dsh-stack` is the reference agent environment and is upgraded independently toward:
- durable event ingestion from `omnis://events/core`;
- DSH-owned memory/cognition/task state;
- one Omnis integration plugin exposing all MCP/native operations to DSH tools;
- direct Control-tree mutation;
- shared NodeId/EventId references;
- optional publication of cognitive dimensions under an extension namespace.

DSH/Cordis remains an agent-runtime implementation detail, never an Omnis core dependency.
