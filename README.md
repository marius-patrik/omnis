# Omnis

**A graph-native operating environment built on Linux, Nix and NixOS, designed to be fully operable
by humans and arbitrary agents.**

Omnis core has exactly three authorities:

| Component | Authority |
|---|---|
| **OmnisOS** | physical/system state, NixOS generations, enforcement, observation |
| **OmnisManager** | resources, capabilities, bindings, execution, placement, generic model/inference resources |
| **OmnisControl** | graph desktop, 2D/3D interaction, ControlTree, renderer, shell and native app surfaces |

They share one multidimensional graph, one append-only core event journal and one stable identity
space.

## Agents are clients, not a core subsystem

Omnis does **not** ship or depend on an OmnisAgent daemon, Claude Code, Codex, OpenCode, DeepSeek
Harness, or another coding-agent harness.

Any authorized agent can use the same three core surfaces through:
- `omnis mcp` — stdio MCP projection;
- `@omnis/agent-access` — generated native plugin client.

Both expose the same typed OS/Manager/Control/graph operations. The event journal is replayable from
sequence 0 and streams every first-party transition, so an agent never needs to infer first-party
state changes from screenshots.

The separately developed `marius-patrik/dsh-stack` project is the reference agent environment. It
owns its own memory, cognition, tasks/workers, models/providers and agent UX; from Omnis' perspective
it is an ordinary plugin/MCP client.

## Core thesis

- **One world, one graph.** Processes, packages, services, resources, executions and Control views use
  stable shared identities.
- **Every event is explicit.** OS, Manager and Control append every meaningful transition to the core
  event journal.
- **Nix realizes persistent state.** AI never participates in Nix evaluation/build semantics.
- **Bind existing software.** Unmodified Linux applications and mature tools remain real resources.
- **Control is the graph made interactive.** 2D and 3D are projections over the same identities.
- **Agents get structural access.** An authorized agent can mutate the Control tree directly instead
  of observing screenshots or simulating clicks.
- **Agent runtime is replaceable.** Removing or changing the agent does not change core semantics.

## Repositories

```text
marius-patrik/omnis          umbrella contracts/integration
marius-patrik/omnis-os       NixOS/nixpkgs-derived system
marius-patrik/omnis-manager  Nix-derived universal manager
marius-patrik/omnis-control  graph desktop/compositor/control
marius-patrik/dsh-stack      separate reference agent environment
```

## Architecture documents

- [Architecture](ARCHITECTURE.md)
- [Implementation blueprint](docs/IMPLEMENTATION.md)
- [Decision-complete v0 core](docs/DECISION_COMPLETE_V0.md)
- [Shared graph](docs/GRAPH.md)
- [Core ontology/events](docs/ONTOLOGY_V0.md)
- [Agent access](docs/AGENT_ACCESS_V0.md)
- [OmnisOS](docs/OMNIS_OS.md)
- [OmnisManager](docs/OMNIS_MANAGER.md)
- [OmnisControl](docs/OMNIS_CONTROL.md)
- [Control renderer](docs/CONTROL_RENDER_V0.md)
- [Nix control](docs/NIX_CONTROL_V0.md)
- [NixOS options](docs/NIX_OPTIONS_V0.md)
- [Protocols](docs/PROTOCOLS.md)
- [Implementation roadmap](ROADMAP.md)
- [Contributor rules](AGENTS.md)

`spec/contract.toml` is the machine-readable root of the complete core v0 contract.
