# OmnisAgent v0 Learning and Self-Optimization Contract

**Status: NORMATIVE.** This document freezes the algorithms behind ROADMAP Phase 10. Implementers do
not choose alternate learning rules, smoothing, thresholds, promotion gates, or routing updates.

Machine-readable constants live in `spec/learning.toml`.

## 1. Memory utility learning

Each retrievable memory identity maintains:

```text
recalled_count
selected_count
useful_count
last_recalled_at_ns
```

The counters in `schema/index.sql::retrieval_stats` are derived and rebuildable.

Update rules:

- recalled_count += 1 when the identity enters the merged retrieval candidate set;
- selected_count += 1 when the identity is included in a ContextCapsule;
- useful_count += 1 at most once per Worker activation when:
  - the Worker structured result cites that memory identity or one of its evidence IDs; or
  - a deterministic postcondition evaluator attributes a successful required fact/procedure to that
    memory identity.
- no usefulness credit is inferred from mere temporal proximity.

Smoothed utility:

```text
posterior_usefulness = (useful_count + 1) / (selected_count + 2)
utility_multiplier   = 0.75 + 0.50 * posterior_usefulness
```

Range is [0.75, 1.25].

Retrieval integration:

1. compute ordinary RRF score;
2. multiply by utility_multiplier;
3. sort descending by learned score, then identity bytes;
4. take top 32 for model rerank when available;
5. if reranker exists, its order is final;
6. otherwise learned score order is final.

New/unselected memories therefore start at multiplier 1.0.

## 2. Binding performance learning

Manager maintains derived statistics keyed by:

```text
(capability canonical name, BindingId, placement class)
```

Fields:

```text
attempts
successes
failures
ewma_latency_ns
ewma_cost_micros
last_success_ns
last_failure_ns
```

Terminal success increments attempts+successes.
Terminal failed/lost increments attempts+failures.
Cancelled executions do not update quality.
A provider rejection before execution starts counts as failure only when the binding was selected and
the rejection establishes that the binding cannot satisfy its advertised contract.

Quality posterior:

```text
learned_quality = (successes + 2) / (attempts + 4)
```

Prior mean = 0.5.

Manager §14 quality feature is:

```text
attempts < 3:
  advertised_quality if present else 0.5
attempts >= 3:
  0.25 * (advertised_quality if present else 0.5)
  + 0.75 * learned_quality
```

Latency/cost EWMA:

```text
first successful observation -> observed value
later successful observation -> 0.20 * observed + 0.80 * previous
```

Failed/cancelled observations do not update latency/cost EWMA.

The §14 candidate normalization uses EWMA when available, otherwise advertised estimate, otherwise
the documented missing-value fallback.

Statistics are derived from Execution events and can be rebuilt from worldline/graph history.

## 3. Agent competence self-model

Competence is tracked per semantic capability and Worker class.

```text
competence = (successes + 2) / (attempts + 4)
```

with the same terminal accounting as §2.

Labels:

```text
attempts < 5            unknown
attempts >=5, <0.60     weak
attempts >=5, <0.80     developing
attempts >=5, >=0.80    competent
```

This self-model is evidence for intention cost/risk estimation; it is not an authority gate.

When candidate intention normalized_cost is model-estimated, Agent adjusts it:

```text
unknown     +0.00
weak        +0.20
developing  +0.10
competent   -0.05
```

then clamp to [0,1].

## 4. Competence-gap event

Agent emits one `omnis.event.agent.competence_gap` when either condition becomes true for a
capability/Worker class:

```text
A. >= 3 failures among last 10 terminal attempts
B. attempts >= 5 and competence < 0.60
```

Deduplication:
- one open gap per capability + Worker class;
- close it after 5 consecutive successes and competence >=0.80;
- emit a new gap only after a closed gap regresses again.

Gap payload includes capability, Worker class, last 10 terminal Execution/Worker IDs, competence and
failure count.

## 5. Endogenous improvement candidate trigger

A competence gap does **not** force self-modification.

It creates one ordinary candidate intention:

```text
postcondition:
  improve measured success/cost for the affected semantic capability without weakening invariants
```

Candidate feature defaults:

```text
goal_progress      0.50
information_gain   0.70
urgency            0.20
risk_reduction     0.50
novelty            0.50
user_relevance     0.30
normalized_cost    0.70
```

Normal scheduler rules, active user work, budgets and NullIntention decide whether it runs.

If selected, improvement search order is fixed:

1. inspect binding/discovery/procedure evidence;
2. try deterministic configuration/binding fix;
3. try new/updated learned Procedure;
4. if source-level defect remains and `omnis.capability.code.agent` is available, create a candidate
   code worktree against the owning component;
5. otherwise defer.

No direct live-code mutation exists.

## 6. Procedure induction

The algorithm is exactly `docs/ONTOLOGY_V0.md §12`.

Additional normalization rules:

- capability names remain semantic canonical names;
- omit ExecutionId/WorkerId/TraceId/EventId;
- replace concrete file paths inside the active Worktree with `$WORKTREE/<relative>`;
- replace CAS ArtifactIds with media-type + semantic role;
- preserve literal user-specified values that affect the postcondition;
- preserve ordered step sequence.

Sequence equality is exact after this normalization.

## 7. Learned routing estimates and decay

No time decay is applied to success counts in v0.

EWMA latency/cost naturally adapts with alpha=0.20.

When a Binding executable/model artifact identity changes:
- retain historical statistics under old realization;
- start a fresh statistics key for the new realization;
- advertised quality applies until 3 new attempts exist.

A remote placement HostId change is a distinct placement class.

## 8. Candidate source/config/code evolution

Targets and promotion policy remain `docs/ONTOLOGY_V0.md §13`.

Candidate generation is always performed by an ordinary capability:
- Nix/config candidate -> system generation planning capability;
- Procedure candidate -> deterministic procedure induction;
- source-code candidate -> `omnis.capability.code.agent`.

The candidate branch/worktree rules are the normal repository worker rules.

Every candidate records:

```text
candidate NodeId
target NodeId
parent realization/generation
trigger competence-gap/event
creating Worker
source ArtifactIds
test/eval ArtifactIds
metric baseline
metric candidate
promotion result
rollback/revert identity when applicable
```

## 9. Replay corpus

Each component has a CAS-backed replay corpus of successful and failed historical fixtures.

Fixture admission:
- explicit acceptance test fixture: always;
- user-visible Activity with deterministic postcondition: after terminal state;
- security/invariant failure: always;
- raw conversation without deterministic evaluator: not a regression fixture.

Maximum v0 corpus per component:
- newest 1000 ordinary fixtures;
- plus all security/invariant fixtures;
- plus all fixtures referenced by an active candidate.

When >1000 ordinary fixtures, evict oldest by terminal event ingest sequence.

Candidate evaluation runs the complete retained corpus, not a sampled subset.

## 10. Metrics

Required success metric:

```text
success_fraction = successful deterministic postconditions / evaluable fixtures
```

Required resource cost metric:

```text
normalized_cost =
  0.25 * normalized_wall_time
+ 0.20 * normalized_cpu_time
+ 0.15 * normalized_peak_memory
+ 0.15 * normalized_model_tokens
+ 0.15 * normalized_provider_cost
+ 0.10 * normalized_network_bytes
```

Each component is normalized against baseline median per fixture. Missing dimensions contribute 0
weight and remaining weights are renormalized to sum 1.

The self-evolution gates in `ONTOLOGY_V0.md §13` use these exact metrics.

## 11. Preference learning

Only explicit user preference and repeated behavioral evidence can update Preference memory.

Explicit:
- confidence = 0.90 on first declaration;
- direct correction/reaffirmation = 1.00.

Behavioral:
- require same scoped choice in >=3 independent Activities;
- initial confidence = 0.60;
- each additional consistent independent Activity adds 0.05 to max 0.85;
- one contradictory explicit user statement immediately supersedes the inferred preference;
- contradictory behavior alone creates competing evidence and reduces confidence by 0.10, floor 0.50;
- below 0.50 the inferred preference is retracted.

Preferences never change system authority/security policy.

## 12. Prediction error

For an Expectation with confidence >=0.60:
- matching observed outcome -> `cognitive.supports`;
- incompatible observed outcome -> `cognitive.refutes` and an internal prediction-error event;
- deadline passes with no observable resolution -> mark unresolved, do not count as refutation.

Prediction-error salience:

```text
abs(expected_probability - observed_outcome)
```

where observed_outcome is 1 for match and 0 for contradiction.

Prediction error can create an ordinary candidate intention but does not directly mutate memory
strategy/code.

## 13. No hidden optimizer

There is no separate reinforcement-learning daemon, online weight training loop, genetic optimizer,
or background hyperparameter search in v0.

All adaptation is:
- derived counter/statistics updates;
- memory preference/assertion updates;
- deterministic Procedure induction;
- ordinary candidate intentions;
- candidate code/config generations evaluated by frozen gates.
