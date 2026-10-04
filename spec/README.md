# Omnis machine-readable v0 specification

These files are canonical inputs for generated constants/registries.

`contract.toml` is the root manifest enumerating the complete v0 implementation contract. Tools and
implementation agents begin there rather than discovering authority ad hoc.

- `contract.toml` — complete authoritative-source manifest and component ownership.
- `v0.toml` — scalar baselines, paths, ports, limits, weights, schedules and defaults.
- `ontology.toml` — first-party kind/relation/capability/event/state names.
- `events.toml` — event name -> `events.capnp::Payload` union variant.
- `capabilities.toml` — capability name -> input/output Cap'n Proto types + effect class.
- `properties.toml` — first-party property key types/constraints.
- `state_machines.toml` — legal lifecycle transitions.
- `inference_gateway.toml` — local gateway listener/auth/model/network/context constants.
- `nix_control.toml` — exact evaluator/store control transports, configuration roots, fingerprints and recovery.
- `agent_access.toml` — exact MCP/native-plugin projection and parity contract.
- `control_render.toml` — ControlTree layout, render, clipping, hit-test, text/native-surface and animation constants.

Component repositories pin an umbrella commit and generate language-specific constants from these
files during Nix builds. They must not copy values into independent handwritten registries.

Human explanations live in `docs/DECISION_COMPLETE_V0.md` and `docs/ONTOLOGY_V0.md`. When a
machine-readable scalar/name and prose disagree, the machine-readable manifest controls the scalar or
identifier and the contradiction is a specification defect that must be fixed immediately.
