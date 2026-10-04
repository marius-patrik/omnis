# Omnis machine-readable v0 specification

These files are canonical inputs for generated constants/registries.

- `v0.toml` — scalar baselines, paths, ports, limits, weights, schedules and defaults.
- `ontology.toml` — first-party kind/relation/capability/event/state names.
- `events.toml` — event name -> `events.capnp::Payload` union variant.
- `capabilities.toml` — capability name -> input/output Cap'n Proto types + effect class.
- `properties.toml` — first-party property key types/constraints.
- `state_machines.toml` — legal lifecycle transitions.
- `harnesses.toml` — exact external coding-harness versions, commands, transports and coverage.
- `inference_gateway.toml` — local gateway listener/auth/model/network/context constants.
- `nix_control.toml` — exact evaluator/store control transports, configuration roots, fingerprints and recovery.
- `control_render.toml` — ControlTree layout, render, clipping, hit-test, text/native-surface and animation constants.

Component repositories pin an umbrella commit and generate language-specific constants from these
files during Nix builds. They must not copy values into independent handwritten registries.

Human explanations live in `docs/DECISION_COMPLETE_V0.md` and `docs/ONTOLOGY_V0.md`. When a
machine-readable scalar/name and prose disagree, the machine-readable manifest controls the scalar or
identifier and the contradiction is a specification defect that must be fixed immediately.
