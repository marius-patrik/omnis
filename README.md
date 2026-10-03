# Omnis

**A graph-native, agentic operating system built on Linux and Nix.**

Omnis is not an assistant application running on top of a conventional desktop. It is an operating
system in which the machine, its software, its resources, its agent, and its interface share one
addressable model of reality.

The system is organized around four first-class products:

| Component | Role |
|---|---|
| **OmnisOS** | Linux/NixOS-derived system substrate. Owns physical machine state, system invariants, generations, enforcement, and the shared graph substrate. |
| **OmnisManager** | Nix-derived universal resource manager. Owns packages, resources, capabilities, bindings, placement, inference engines, external agent harnesses, and arbitrary foreign integrations. |
| **OmnisAgent** | Persistent cognitive subsystem. Owns the causal event worldline, memory, context compilation, judgement, workers, internal dynamics, and learning. |
| **OmnisControl** | Universal control surface. Projects the shared graph into an interactive 2D/3D graph desktop, shell, native application regions, inspectors, and arbitrary visualizations. |

The unifying substrate is a **shared multidimensional graph**. OmnisOS contributes physical and
system state; OmnisManager contributes resources, capabilities, bindings, and executions;
OmnisAgent contributes cognitive and memory state; OmnisControl contributes presentation and
interaction state. Every object keeps one stable identity across those dimensions.

A separate immutable **worldline** in OmnisAgent records causal experience. The graph describes the
current structured world; the worldline records how that world changed.

```text
                              USER
                                │
                                ▼
                         ┌──────────────┐
                         │ OmnisControl │
                         │ graph desktop│
                         └──────┬───────┘
                                │
                                ▼
                SHARED MULTIDIMENSIONAL GRAPH
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
          ▼                     ▼                     ▼
      OmnisOS              OmnisManager           OmnisAgent
  physical reality       possibility/action    meaning/cognition
          │                     │                     │
          └─────────────────────┼─────────────────────┘
                                │
                                ▼
                              Linux

Every meaningful transition ───────────────────────▶ Agent worldline
```

## The core idea

Omnis deliberately separates four questions:

- **What physically is?** — OmnisOS.
- **What can be done, and what can realize it?** — OmnisManager.
- **What does it mean, and what should happen next?** — OmnisAgent.
- **How is that reality exposed and manipulated interactively?** — OmnisControl.

The graph connects the answers without collapsing them into one implementation.

This design takes several ideas from Invariant-Oriented Engineering while dropping the custom
language: stable semantic identity, capability/binding separation, deterministic-first discovery,
host-independent placement, protected values, causal history, graph projections, and replacement of
physical realizations without changing meaning. Linux, Nix, existing applications, model runtimes,
and external agent harnesses remain real software; Omnis binds and composes them rather than
requiring them to be rewritten.

## Nix foundation

Omnis intentionally forks both major Nix layers:

- **OmnisOS** tracks a fork of `nixpkgs`/NixOS for complete system-level integration while retaining
  compatibility with the nixpkgs package ecosystem.
- **OmnisManager** tracks a fork of `NixOS/nix` and extends the evaluator/store/package-manager layer
  into a universal resource, binding, capability, execution, and placement manager.

Nix remains deterministic machinery. AI does not run inside Nix evaluation. OmnisAgent may decide
*what* should change; OmnisManager resolves *how*; OmnisOS/Nix deterministically builds and realizes
persistent system state.

## Interface

OmnisControl provides a desktop, but not a traditional desktop environment. The desktop is an
interactive projection of the shared graph.

It has two equivalent spatial modes:

- **2D** — Airgraph/Blueprint-like graph interaction optimized for precision, editing, inspection,
  workflow manipulation, and dense information.
- **3D** — spatial graph interaction optimized for large-scale navigation, clusters, causal depth,
  temporal structure, and multidimensional relationships.

Switching modes preserves identity, focus, selection, lens, and timeline position. A terminal,
browser, editor, system monitor, memory explorer, or application window is not a separate UI
architecture; each is a projection or delegated region inside the same control environment.

The shell remains a first-class default interaction surface. Exact shell syntax and known commands
execute directly. URLs, graph identities, capabilities, and semantic requests resolve through the
same input surface without requiring a mode switch into an "AI chat".

## Agent

OmnisAgent is not a single LLM loop. It is a persistent event-driven cognitive system.

Every meaningful system event reaches it directly. Its worldline, memory, world model, context
compiler, judgement mechanisms, and workers persist independently of any one model or process.
LLMs, classifiers, embedding models, rerankers, vision/audio models, coding agents, and deterministic
algorithms are resources resolved through OmnisManager.

The Agent never needs to periodically inspect the UI to learn what happened. OmnisControl, OmnisOS,
and OmnisManager emit their events directly. The Agent also has direct structural access to the
Control graph and can create, replace, rebind, reorganize, or remove interactive projections without
simulating user clicks.

## Status

This repository is the **umbrella architecture and integration specification** for the Omnis system.
The previous daemon/workspace architecture is superseded by the graph-native four-component
architecture defined in [ARCHITECTURE.md](ARCHITECTURE.md).

Implementation specifications:

- [Shared graph](docs/GRAPH.md)
- [OmnisOS](docs/OMNIS_OS.md)
- [OmnisManager](docs/OMNIS_MANAGER.md)
- [OmnisAgent](docs/OMNIS_AGENT.md)
- [OmnisControl](docs/OMNIS_CONTROL.md)
- [Protocols and contracts](docs/PROTOCOLS.md)
- [Implementation roadmap](ROADMAP.md)
- [Contributor/agent rules](AGENTS.md)

Historical ADRs remain useful source material but are non-normative where they conflict with the
architecture reset in `notes/adr/0023-graph-native-os-architecture-reset.md`.