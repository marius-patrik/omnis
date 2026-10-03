# Omnis — Contributor and Agent Rules

These rules are binding for human and automated contributors across the Omnis umbrella and component
repositories.

## 1. Architecture authority

`ARCHITECTURE.md` is normative. Supporting specs under `docs/` refine it. A change that contradicts
them requires an architecture/ADR change first.

Historical ADRs before the architecture reset are source material only where superseded.

## 2. Preserve the four authorities

Do not move responsibilities across product boundaries casually:

```text
OmnisOS      physical/system authority
OmnisManager resource/capability/binding authority
OmnisAgent   event/memory/cognitive authority
OmnisControl interaction/presentation authority
```

The shared graph is a substrate, not a fifth semantic authority.

## 3. One identity, one graph

Never create a component-local canonical shadow object for something already represented in the
shared graph.

Local caches/views are allowed only when:

- they retain the shared NodeId/EdgeId;
- they are explicitly derived;
- they can be rebuilt;
- they do not become a second source of truth.

## 4. Respect graph namespace ownership

A component writes canonical graph state only in its owned namespaces. Cross-authority changes go
through the owning API.

Graph core must enforce this rule; do not rely only on review convention.

## 5. Every meaningful transition becomes an event

First-party components must not make durable/meaningful state transitions invisible to OmnisAgent.

Do not add polling as the primary integration path when the producer can emit the event directly.

## 6. Bind before rebuilding

Before implementing a tool/runtime/service, ask whether a mature implementation already exists.
Prefer:

```text
bind existing tool
+ add graph identity
+ expose capabilities
+ preserve provenance
```

over a new Omnis implementation.

## 7. Deterministic first

Prefer exact mechanisms in this order where applicable:

```text
existing graph metadata
native APIs/reflection
protocol schemas
compiler/runtime/LSP metadata
CLI structured metadata
source/static analysis
deterministic probing
specialist learned model
general reasoning model
```

Do not use an LLM to rediscover information an exact interface already supplies.

## 8. Nix remains deterministic

Never call models from Nix evaluation/build semantics.

Agent reasoning may produce candidate inputs/configuration. Once candidate inputs are fixed, Nix
realization must be deterministic according to Nix semantics.

## 9. Persistent versus transient actions

Do not route every runtime action through Nix generations.

Use a generation for persistent structural system state. Use Manager execution for transient work.

## 10. Agent is not an LLM loop

Do not introduce a universal `while ask_model` executive loop.

Cognition is event-driven. Models are Manager resources used by workers. Worker outputs re-enter the
worldline as events.

## 11. Control is not a conventional GUI

Do not build separate application architectures for terminal, browser, graph, 3D, or AI output.

Control derives projections from the shared graph into one Control tree and renderer. Native apps are
delegated surfaces where appropriate.

2D and 3D must preserve the same identities/focus/selection/lens/frontier.

## 12. Agent gets structural Control access

If a first-party Control operation can only be performed by synthetic mouse/keyboard input, the API
is incomplete unless the operation is inherently physical input testing.

Agent must be able to manipulate Control structure directly.

## 13. Protected values are handles

Do not serialize credentials into:

- Agent model context;
- event payloads/history;
- graph properties visible outside allowed scope;
- Control output;
- logs.

Use protected handles and execution-time injection/brokering.

## 14. Effects must be honest

Unknown foreign operations are opaque/effectful.

Do not claim rollback of an external effect that already happened. Use idempotency, reconciliation,
compensation, or explicit failure state where supported.

## 15. Identity is not location

Do not use path, PID, store path, host, provider, window ID, or current version as semantic identity.
They are locators/properties/realizations.

## 16. Provenance is required

Discovered/inferred capabilities, graph relations, memories, and generated artifacts retain source,
method, version/hash, and confidence where available.

## 17. No compatibility baggage before compatibility exists

The new architecture supersedes the unimplemented old Omnis daemon architecture. Do not preserve
obsolete APIs, schemas, or package structures merely because they appeared in historical docs.

Compatibility work requires a real deployed contract/user dependency.

## 18. Upstream fork discipline

For Nix/nixpkgs-derived repositories:

- keep upstream remote and provenance;
- prefer patch stacks/small deltas;
- isolate Omnis-specific changes;
- regularly merge/rebase upstream according to repo policy;
- do not copy packages unnecessarily;
- preserve upstream license requirements.

## 19. Implementation quality

Every architectural guarantee should become at least one of:

- a type/property boundary;
- protocol validation;
- test;
- lint;
- process/authority boundary;
- integration test.

A principle enforced only by prose is unfinished.

## 20. Cross-component testing

Any change touching a shared protocol or graph semantic requires umbrella integration tests covering
all affected authorities.

Prefer real protocol/process tests over mocks once implementations exist.

## 21. Documentation changes

When implementation changes semantics, update the normative docs in the same change. Do not allow
README, architecture, protocol docs, and implementation to drift.

## 22. Completion behavior for coding agents

Before declaring work complete, an implementation agent must:

1. read applicable architecture/supporting specs;
2. identify the owning authority and graph namespaces;
3. preserve stable identities/provenance/events;
4. run unit/integration tests;
5. inspect the diff for duplicate semantic authorities;
6. update docs/contracts if behavior changed;
7. state any remaining incompatibility or unimplemented contract explicitly.