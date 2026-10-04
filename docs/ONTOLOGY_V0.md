# Omnis v0 Core Ontology and Event Registry

**Status: NORMATIVE.** This file freezes first-party names owned by the three core authorities.
External agents do not extend the `omnis.*` namespace; optional agent-owned graph data uses granted
`ext.<client-id>.*` namespaces.

## 1. Authorities

```text
OmnisOS       physical system / enforcement
OmnisManager  resources / capabilities / bindings / executions
OmnisControl  presentation / interaction / navigation
```

The shared graph/event journal is substrate, not a fourth authority.

## 2. Machine-readable registry

`spec/ontology.toml` is canonical for:
- dimensions;
- kinds;
- relations;
- semantic capability names;
- first-party core event names;
- Execution and Generation states.

`spec/properties.toml` freezes core property types.
`spec/state_machines.toml` freezes legal state transitions.
`spec/events.toml` maps every core event to one `events.capnp::Payload` variant.
`spec/capabilities.toml` maps every semantic capability to one typed input/output/effect contract.

No first-party `omnis.kind.agent_*`, `omnis.event.agent.*`, Worker, Activity, Memory, ContextCapsule
or cognitive relation exists in core v0.

## 3. Extension namespaces

An authorized external plugin may publish its own semantic state only under:

```text
ext.<client-id>.*
```

It may reference core NodeIds/EventIds but cannot redefine their first-party kinds/properties or write
another owner's namespace.

## 4. Core event classes

The journal contains graph, OS, Manager/inference, Control and timer events listed in
`spec/events.toml`. All are durable and replayable.

## 5. Core capability classes

The registry includes shell/process/package/system/VCS/code-tool/model/browser/HTTP/MCP/container/VM/
graph/Control/ingest/host capabilities.

There is deliberately no `omnis.capability.code.agent`: an agent runtime is a caller, not a Manager
resource class.

## 6. State machines

Only core-owned lifecycle state machines are normative here:
- Execution;
- Generation.

Agent runtimes define their own task/worker/memory lifecycle outside core.
