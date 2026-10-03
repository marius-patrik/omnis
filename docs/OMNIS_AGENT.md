# OmnisAgent

**Status: normative supporting specification.**

OmnisAgent is the persistent cognitive subsystem of Omnis. It owns the machine's causal event
worldline, derived memory, judgement, context compilation, cognitive workers, internal dynamics, and
learning.

It is not a chat process and not an LLM loop. Models and external agent harnesses are resources
resolved through OmnisManager.

---

## 1. Identity and continuity

Agent identity survives:

- process restart;
- model/provider replacement;
- Control restart;
- host placement changes;
- network loss;
- individual worker failure.

Durable continuity consists of worldline, memory, active durable work, graph references, and
reconstructable internal state.

The Agent can be alive while consuming zero model tokens and zero active worker CPU.

---

## 2. Event kernel

Every meaningful first-party event enters one canonical gateway and receives stable identity,
provenance, causal parents, and graph references.

Event sources include OmnisOS, OmnisManager, OmnisControl, workers, external harness hooks,
inference interception, timers, external services, and endogenous cognition.

The Agent does not periodically "observe" OmnisControl. Input and structural changes are events.

The worldline is append-only historical truth. Events may be moved to colder storage but may not be
silently rewritten into newer interpretations.

---

## 3. Judgement

Every meaningful event receives cheap deterministic handling first and a judgement sufficient to
decide whether further cognition is useful.

Judgement may estimate:

```text
semantic domain
event role
entities
salience
novelty
uncertainty
urgency
causal relevance
goal/project relevance
capability demand
context demand
expected information value
resource cost
dispatch topology
```

The judgement stack may contain deterministic rules, classifiers, embedding/graph models, specialist
models, and strong reasoning models. There is no mandatory single executive classifier.

The null action is valid.

---

## 4. Memory

### 4.1 Ground truth

Event memory/worldline is immutable source evidence.

Derived memory may change, merge, become stale, contradict another memory, or be superseded.

### 4.2 Required memory forms

```text
episode
assertion
entity
relationship
concept
decision
goal
commitment
preference
procedure
skill
artifact
expectation
project-state
self-model
competence estimate
```

Every derived memory retains evidence/provenance whenever source evidence exists.

### 4.3 Temporal semantics

Memory distinguishes:

```text
event time
observation time
knowledge time
validity interval
```

Changing truth is represented as temporal state rather than destructive text replacement.

### 4.4 Multiple representations

A memory may simultaneously have:

- structured semantics;
- graph relations;
- lexical representation;
- embedding(s);
- structural/AST representation;
- source artifacts;
- abstraction hierarchy.

Vectors are rebuildable indexes, never memory truth.

---

## 5. Working memory and context

Four states remain distinct:

```text
long-term memory   durable derived state
working memory     currently activated state
scratch state      transient computation
model context      serialized projection for one inference
```

Context is compiled per event × worker × purpose.

A context capsule may contain:

- direct causal ancestors;
- relevant current graph subgraph;
- project/goal state;
- episodic/semantic/procedural memory;
- artifacts/code structure;
- previous attempts/failures;
- negative evidence and contradictions;
- available capabilities;
- privacy/disclosure constraints;
- token/latency budgets.

The compiler should initially include the cheapest sufficient abstraction and retain references that
allow workers to expand details explicitly.

---

## 6. Universal inference interception

Because Omnis can run arbitrary external harnesses, native hooks are not sufficient for complete
memory coverage.

Manager should support an inference-boundary interception binding for common model protocols. Agent
uses it to:

1. observe context about to enter inference;
2. deduplicate already observed context items;
3. record new source events;
4. retrieve/compile relevant Agent memory;
5. inject a tagged memory projection where configured;
6. observe the generated result.

Native harness hooks enrich this with stronger semantics such as tool calls, file edits, compaction,
permissions, subagent results, and session transitions.

Memory projections are tagged so their future retransmission does not become recursive source
evidence.

---

## 7. Workers

Workers are durable cognitive activations, not separate agent identities.

Initial families:

```text
judgement
retrieval
reasoning/planning
research
code
verification
simulation
memory/reflection
learning
evolution
domain specialists
```

A worker receives a compiled context capsule and resource/capability grants. It may use deterministic
code, local models, remote models, external agent harnesses, or combinations thereof.

Worker outputs always return as events/artifacts.

---

## 8. Workflows

The Agent supports explicit durable causal workflows composed from general primitives such as:

```text
sequence
parallel
map
fork
join
race
quorum
retry
wait-event
timeout
cancel
spawn
branch
merge
yield
delegate
compensate
```

"Planner/executor", debate, research fan-out, speculative coding, reflection, and similar patterns
are workflows built from primitives rather than privileged architecture modes.

The Agent itself is not one giant workflow.

---

## 9. Internal dynamics

External requests do not define when cognition exists.

Endogenous event sources may include:

```text
memory association
unresolved contradiction
prediction error
uncertainty
novelty
competence gap
standing commitment
hypothesis
reflection
consolidation
self-observation
self-evolution proposal
```

These mechanisms generate candidate intentions. They do not hard-code activities such as "when idle,
read documentation".

The Agent may choose to do nothing.

---

## 10. Sleep/consolidation

Sleep is a resource-allocation regime, not a binary identity state.

During low external demand the Agent may allocate more resources toward:

- consolidation;
- replay;
- contradiction resolution;
- memory abstraction;
- procedure induction;
- maintenance;
- self-evaluation.

A high-salience event can immediately alter that allocation.

---

## 11. Procedures and learning

Repeated successful experience can become procedural memory:

```text
repeated episodes
  -> pattern candidate
  -> procedure hypothesis
  -> validation
  -> durable procedure/skill
```

Repeated expensive model-mediated behavior should preferentially compile toward cheaper structured
or deterministic capabilities when possible.

Learning may update retrieval utility, routing estimates, worker selection, competence estimates, or
procedural knowledge without rewriting historical events.

---

## 12. Self-evolution

Agent structural changes use candidate variants rather than mutating the only live implementation in
place.

A candidate retains lineage and may be evaluated through replay, benchmarks, sandbox experiments,
and real-world outcomes before promotion.

OmnisAgent may propose changes to itself, Manager, Control, or OS, but physical realization still
flows through the owning component and its execution/generation mechanisms.

---

## 13. Control integration

Agent receives all OmnisControl events directly and references the same graph identities Control
renders.

Agent has direct structural capability over presentation state, including:

- creating projections;
- changing focus/lens;
- rearranging layout;
- materializing resources as views;
- binding interactions;
- opening delegated native surfaces;
- selecting 2D/3D representations.

Agent should not resort to screenshot-based clicking for first-party Control content.

---

## 14. Manager integration

Agent requests semantic capabilities from Manager rather than provider names whenever implementation
identity is not itself relevant.

Examples:

```text
model.classify
model.embed
model.reason
code.agent
web.search
browser.navigate
code.test
system.inspect
```

Manager returns concrete bindings/execution handles and publishes execution lifecycle back into graph
and event stream.

---

## 15. Persistence

Initial local implementation should use an embedded durable database for:

```text
worldline events
causal edges
memories
entities/relations
sessions/activities
worker/workflow state
context activations
model invocations
procedures/skills
expectations
lineage
```

SQLite/WAL is acceptable initially. Large immutable artifacts belong in content-addressed storage and
are referenced from events/memory.

The persistence implementation must support snapshot + replay/reconciliation and must not make model
availability a recovery dependency.

---

## 16. Hard invariants

1. Event is the basic durable cognitive unit.
2. Every event has identity, provenance, and causal relationships.
3. Worldline is never replaced by summaries.
4. Derived memory remains connected to source evidence where available.
5. Context is compiled, not accumulated globally.
6. Worker outputs re-enter the event stream.
7. LLMs/models are replaceable resources, not Agent identity.
8. External agent harnesses are workers/resources, not privileged cognition.
9. Endogenous and exogenous events use the same cognitive pipeline.
10. No semantic `IDLE` state exists.
11. Null/no work is valid.
12. Agent does not need to observe Control/OS snapshots to know first-party transitions.