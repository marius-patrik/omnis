# ADR-0025 — Make Omnis v0 decision-complete

- **Status**: Accepted · **Date**: 2026-10-03
- **Depends on**: ADR-0023, ADR-0024

## Context

The graph-native architecture and v0 substrate were frozen, but an implementation worker could still
make consequential choices inside phrases such as ranking policy, context budget, graph layout,
retry behavior, queue sizing, recovery cadence, dependency bootstrap, remote graph behavior and
security defaults.

That discretion is incompatible with the goal that multiple agents implement one system rather than
independently designing variants of it.

## Decision

Adopt `docs/DECISION_COMPLETE_V0.md` as normative for all remaining v0 algorithms, constants,
defaults, ordering, fallback behavior and acceptance gates.

Implementation agents may choose only semantically invisible code expression. If the specification
does not answer a behaviorally observable choice, that is a specification defect rather than an
invitation to exercise judgment.

The initial upstream baselines are frozen to:

- nixpkgs `be5021eb406d32e8df6462a1c0986a70bdf03e02`;
- Nix `2ab29c63d3273d4e2b4d1346b1aefede9b5af350`;
- Rust 1.99.0;
- crates.io-index `cddab5f1c359539147959163142ff95a24995f6a`.

## Alternatives rejected

- **Let implementers choose conventional defaults.** Different workers would produce incompatible
  behavior and hidden architecture.
- **Specify only interfaces and leave algorithms replaceable.** That is appropriate after v0 exists,
  but it does not produce one deterministic initial system.
- **Encode every choice only in tests.** Tests are enforcement; documentation remains the human and
  agent implementation authority.
- **Freeze only library versions.** Behavioral choices such as retrieval, placement and layout remain
  more consequential than patch versions.

## Consequences

- v0 implementation becomes highly prescriptive.
- Some constants will later prove suboptimal; changing them is an explicit measured change rather than
  invisible worker discretion.
- Parallel coding agents can implement separate components against identical assumptions.
- Specification defects block an item instead of silently creating divergent architecture.
