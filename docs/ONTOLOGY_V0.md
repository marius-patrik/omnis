# Omnis v0 Ontology and Event Registry

**Status: NORMATIVE.** This file freezes first-party graph names, capability names, event names and
core lifecycle states for v0. Implementers do not invent synonyms.

All identifiers below are lowercase ASCII dotted names. New first-party identifiers require a spec
change before implementation.

---

## 1. Kind registry

### 1.1 OmnisOS

```text
omnis.kind.host
omnis.kind.cpu
omnis.kind.gpu
omnis.kind.memory_device
omnis.kind.storage_device
omnis.kind.network_device
omnis.kind.input_device
omnis.kind.output_device
omnis.kind.process
omnis.kind.service
omnis.kind.user
omnis.kind.session
omnis.kind.filesystem
omnis.kind.mount
omnis.kind.network_interface
omnis.kind.network_route
omnis.kind.network_listener
omnis.kind.cgroup
omnis.kind.nix_generation
omnis.kind.nix_store_path
omnis.kind.system_invariant
```

### 1.2 OmnisManager

```text
omnis.kind.resource
omnis.kind.package
omnis.kind.derivation
omnis.kind.executable
omnis.kind.library
omnis.kind.endpoint
omnis.kind.container
omnis.kind.vm
omnis.kind.model
omnis.kind.inference_runtime
omnis.kind.agent_harness
omnis.kind.mcp_server
omnis.kind.repository
omnis.kind.worktree
omnis.kind.capability
omnis.kind.binding
omnis.kind.execution
omnis.kind.credential_handle
omnis.kind.credential_lease
omnis.kind.remote_host_binding
```

### 1.3 OmnisAgent

```text
omnis.kind.activity
omnis.kind.goal
omnis.kind.commitment
omnis.kind.worker
omnis.kind.context_capsule
omnis.kind.hypothesis
omnis.kind.memory.episode
omnis.kind.memory.assertion
omnis.kind.memory.procedure
omnis.kind.memory.preference
omnis.kind.memory.expectation
omnis.kind.memory.decision
omnis.kind.memory.project_state
omnis.kind.memory.summary
```

### 1.4 OmnisControl

```text
omnis.kind.workspace
omnis.kind.view
omnis.kind.projection
omnis.kind.lens
omnis.kind.control_node
omnis.kind.native_surface
omnis.kind.terminal
omnis.kind.notification
omnis.kind.input_surface
omnis.kind.chart
omnis.kind.table
omnis.kind.document
omnis.kind.editor
```

A node can have multiple kinds. `omnis.kind.resource` is added to concrete Manager resource kinds.

---

## 2. Relation registry

### 2.1 physical/system

```text
omnis.relation.physical.attached_to
omnis.relation.physical.runs_on
omnis.relation.physical.parent_process
omnis.relation.physical.member_of_cgroup
omnis.relation.physical.mounts
omnis.relation.physical.listens_on
omnis.relation.system.active_generation
omnis.relation.system.parent_generation
omnis.relation.system.realized_as
omnis.relation.system.declares
omnis.relation.system.satisfies
omnis.relation.system.violates
```

### 2.2 Manager

```text
omnis.relation.resource.installed_on
omnis.relation.resource.realized_as
omnis.relation.resource.depends_on
omnis.relation.resource.contains
omnis.relation.capability.provides
omnis.relation.capability.requires
omnis.relation.binding.resource
omnis.relation.binding.capability
omnis.relation.binding.requires
omnis.relation.execution.binding
omnis.relation.execution.placed_on
omnis.relation.execution.uses
omnis.relation.execution.produced
omnis.relation.execution.consumed
omnis.relation.execution.spawned
omnis.relation.execution.authorized_by
omnis.relation.foreign.identity
```

### 2.3 Agent

```text
omnis.relation.activity.goal
omnis.relation.activity.worker
omnis.relation.activity.execution
omnis.relation.activity.repository
omnis.relation.worker.context
omnis.relation.worker.parent
omnis.relation.cognitive.about
omnis.relation.cognitive.evidence
omnis.relation.cognitive.derived_from
omnis.relation.cognitive.supersedes
omnis.relation.cognitive.contradicts
omnis.relation.cognitive.supports
omnis.relation.cognitive.refutes
omnis.relation.cognitive.procedure_for
omnis.relation.cognitive.expectation_about
omnis.relation.context.includes
```

### 2.4 Control

```text
omnis.relation.presentation.contains
omnis.relation.presentation.represents
omnis.relation.presentation.focus
omnis.relation.presentation.selection
omnis.relation.presentation.lens
omnis.relation.presentation.native_surface
omnis.relation.presentation.terminal_execution
omnis.relation.presentation.notification_source
omnis.relation.navigation.previous
omnis.relation.navigation.next
```

### 2.5 provenance/causal/authority

```text
omnis.relation.provenance.source
omnis.relation.provenance.derived_from
omnis.relation.causal.parent
omnis.relation.authority.may_read
omnis.relation.authority.may_write
omnis.relation.authority.may_invoke
omnis.relation.authority.protected_by
```

---

## 3. Required property keys

Common:

```text
omnis.identity.display_name        text
omnis.identity.owner_uid           u64
omnis.identity.created_at          i64 nanoseconds UTC
omnis.state.status                 text enum per state machine
omnis.state.valid_from             i64 nanoseconds UTC
omnis.state.valid_until            i64 nanoseconds UTC or absent
omnis.provenance.confidence        f64 [0,1]
omnis.provenance.method            text
omnis.provenance.foreign_system    text
omnis.provenance.foreign_id        text
```

Physical:

```text
omnis.physical.pid                 u64
omnis.physical.uid                 u64
omnis.physical.gid                 u64
omnis.physical.cpu_percent         f64
omnis.physical.memory_bytes        u64
omnis.physical.device_path         text
omnis.physical.address             text
```

Manager:

```text
omnis.resource.version             text
omnis.resource.locator             text
omnis.capability.name              text
omnis.binding.effect_class         text
omnis.binding.memory_coverage      text
omnis.execution.exit_code          i64
omnis.execution.started_at         i64
omnis.execution.finished_at        i64
omnis.placement.locality           text
omnis.credential.purpose           text
omnis.credential.expires_at        i64
```

Agent:

```text
omnis.cognitive.confidence         f64 [0,1]
omnis.cognitive.salience           f64 [0,1]
omnis.cognitive.valid_from         i64
omnis.cognitive.valid_until        i64 or absent
omnis.cognitive.text               text
omnis.cognitive.status             text
omnis.goal.priority                f64 [0,1]
omnis.goal.deadline                i64 or absent
omnis.worker.priority              f64
omnis.worker.checkpoint            ArtifactRef or absent
omnis.context.token_budget         u64
omnis.context.model_binding        NodeId or absent
```

Control:

```text
omnis.presentation.mode            "2d"|"3d"
omnis.presentation.visible         bool
omnis.presentation.pinned          bool
omnis.presentation.position2       list[f64,f64]
omnis.presentation.position3       list[f64,f64,f64]
omnis.presentation.size2           list[f64,f64]
omnis.presentation.zoom            f64
omnis.presentation.theme           text
omnis.presentation.timeline_event  EventId or absent
```

---

## 4. Capability registry

Core capability names:

```text
omnis.capability.shell.execute
omnis.capability.process.execute
omnis.capability.package.realize
omnis.capability.package.install.user
omnis.capability.package.install.system
omnis.capability.system.generation.plan
omnis.capability.system.generation.build
omnis.capability.system.generation.activate
omnis.capability.system.generation.rollback
omnis.capability.vcs.status
omnis.capability.vcs.diff
omnis.capability.vcs.commit
omnis.capability.vcs.push
omnis.capability.code.format
omnis.capability.code.test
omnis.capability.code.agent
omnis.capability.model.classify
omnis.capability.model.embed
omnis.capability.model.rerank
omnis.capability.model.generate
omnis.capability.model.reason
omnis.capability.model.vision
omnis.capability.model.audio.transcribe
omnis.capability.browser.navigate
omnis.capability.browser.inspect
omnis.capability.browser.interact
omnis.capability.http.request
omnis.capability.mcp.invoke
omnis.capability.container.run
omnis.capability.vm.run
omnis.capability.graph.query
omnis.capability.control.materialize
omnis.capability.control.mutate
omnis.capability.ingest
omnis.capability.host.pairing_code
omnis.capability.host.pair
omnis.capability.host.unpair
```

A provider-specific capability does not replace these semantic names; it binds to them.

---

## 5. Event registry

Every event uses `EventEnvelope` plus the payload fields listed here.

### 5.1 graph

```text
omnis.event.graph.committed
  transaction_id, previous_revision, new_revision, changed_ids
```

### 5.2 OS

```text
omnis.event.os.reconciled
  source, revision

omnis.event.os.observation_gap
  source, lost_count, recovery_revision

omnis.event.os.process.started
  process, parent_process?, executable?, pid

omnis.event.os.process.exec
  process, executable, argv_artifact?

omnis.event.os.process.exited
  process, exit_code?, signal?

omnis.event.os.service.changed
  service, old_state, new_state

omnis.event.os.device.added
omnis.event.os.device.removed
  device

omnis.event.os.network.changed
  identity, change_kind

omnis.event.os.invariant.violated
  invariant, identity, enforcement_action

omnis.event.os.generation.proposed
omnis.event.os.generation.evaluated
omnis.event.os.generation.built
omnis.event.os.generation.activating
omnis.event.os.generation.activated
omnis.event.os.generation.failed
omnis.event.os.generation.rolled_back
  generation, parent, evidence[]
```

### 5.3 Manager

```text
omnis.event.manager.resource.discovered
  resource, provenance

omnis.event.manager.binding.discovered
  binding, resource, capability, provenance

omnis.event.manager.resolution.completed
  capability, selected_binding?, candidates_artifact

omnis.event.manager.execution.created
omnis.event.manager.execution.started
omnis.event.manager.execution.waiting
omnis.event.manager.execution.succeeded
omnis.event.manager.execution.failed
omnis.event.manager.execution.cancelled
omnis.event.manager.execution.lost
  execution, binding, placement, status, evidence[]

omnis.event.inference.request
  invocation, execution, model_role, request_artifact

omnis.event.inference.response
  invocation, binding, response_artifact, input_tokens?, output_tokens?, latency_ns?, cost?

omnis.event.inference.failed
  invocation, binding?, error

omnis.event.manager.credential.lease.created
omnis.event.manager.credential.lease.expired
  handle, lease, execution

omnis.event.manager.host.paired
omnis.event.manager.host.unpaired
  identity
```

### 5.4 Agent

```text
omnis.event.agent.activity.created
omnis.event.agent.activity.completed
omnis.event.agent.activity.failed
  activity, goal?

omnis.event.agent.worker.created
omnis.event.agent.worker.started
omnis.event.agent.worker.waiting
omnis.event.agent.worker.succeeded
omnis.event.agent.worker.failed
omnis.event.agent.worker.cancelled
  worker, activity, context?, checkpoint?, evidence[]

omnis.event.agent.memory.created
omnis.event.agent.memory.updated
omnis.event.agent.memory.superseded
omnis.event.agent.memory.retracted
omnis.event.agent.memory.erased
  memory, evidence[]

omnis.event.agent.context.compiled
  context, trigger, source_count, token_budget

omnis.event.agent.procedure.promoted
  procedure, evidence[]

omnis.event.agent.competence_gap
  candidate=capability, target=worker-class identity, evidence[]=last terminal attempts

omnis.event.agent.candidate.proposed
omnis.event.agent.candidate.evaluated
omnis.event.agent.candidate.promoted
omnis.event.agent.candidate.rejected
  candidate, target, evidence[]
```

### 5.5 Control

```text
omnis.event.control.input.submitted
  workspace, input_surface, text_artifact

omnis.event.control.focus.changed
  workspace, old?, new?

omnis.event.control.selection.changed
  workspace, selected[]

omnis.event.control.mode.changed
  workspace, old_mode, new_mode

omnis.event.control.lens.changed
  workspace, lens[]

omnis.event.control.tree.mutated
  workspace, transaction

omnis.event.control.native_surface.created
omnis.event.control.native_surface.closed
  surface, process?

omnis.event.control.terminal.created
omnis.event.control.terminal.closed
  terminal, execution?

omnis.event.control.navigation
  workspace, address, resolved_identity?

omnis.event.control.notification.created
omnis.event.control.notification.dismissed
  notification, source?
```

### 5.6 timers

```text
omnis.event.timer.minute
omnis.event.timer.hour
```

The one-second timer is an internal reducer tick and is not durably enqueued unless a registered
commitment requires durable second resolution.

---

## 6. Execution state machine

States:

```text
created -> starting -> running
running -> waiting -> running
running|waiting -> succeeded
running|waiting|starting -> failed
created|starting|running|waiting -> cancelling -> cancelled
running|waiting -> lost
```

Terminal states: succeeded, failed, cancelled, lost.

Illegal transition => Conflict error + `omnis.event.os.invariant.violated` for the Execution node.

Exit-code mapping:

- process exit 0 => succeeded unless binding postcondition says otherwise;
- non-zero => failed;
- SIGTERM/SIGKILL after requested cancel => cancelled;
- process disappears without authoritative exit observation after reconciliation => lost.

---

## 7. Worker state machine

```text
created -> ready -> running
running -> waiting -> ready
running -> succeeded
running -> failed
created|ready|running|waiting -> cancelling -> cancelled
running|waiting -> suspended
suspended -> ready
```

Terminal: succeeded, failed, cancelled.

A Worker can have multiple Manager Executions over its life but one current ContextCapsule per
activation attempt.

---

## 8. Activity state machine

```text
active -> waiting
waiting -> active
active|waiting -> completed
active|waiting -> failed
active|waiting -> cancelled
```

No `idle` state exists.

An Activity remains active while any nonterminal Worker, Commitment or required Execution belongs to
it.

---

## 9. Generation state machine

```text
proposed -> evaluated -> building -> built -> activating -> active
proposed|evaluated|building -> failed
built|activating -> failed
active -> rolling_back -> rolled_back
failed activation -> rolling_back -> rolled_back
```

Only one Generation can be active per Host at a time.

---

## 10. Memory ontology

### 10.1 episode

Represents a bounded experienced sequence.

Required:

```text
kind: omnis.kind.memory.episode
omnis.cognitive.text
omnis.cognitive.salience
omnis.cognitive.valid_from
omnis.cognitive.valid_until
cognitive.evidence -> EventIds
cognitive.about -> relevant NodeIds
```

Episode boundary rule:

- explicit Activity completion/failure closes its Activity episode;
- otherwise gap >=30 minutes between related salient events closes an episode;
- a new explicit user request on a different Project/Repository closes the previous conversational
  episode.

### 10.2 assertion

Required:

```text
kind: omnis.kind.memory.assertion
subject NodeId
predicate dotted text
object typed Value or NodeId
confidence [0,1]
valid_from
valid_until?
evidence EventIds/ArtifactIds
status current|superseded|retracted|erased
```

Do not overwrite contradictory assertions. Create both and connect with
`omnis.relation.cognitive.contradicts`.

A newer assertion supersedes an older assertion only when:
- same subject+predicate semantic slot; and
- evidence establishes temporal replacement rather than unresolved disagreement.

### 10.3 procedure

```text
kind: omnis.kind.memory.procedure
procedure_for -> Capability
preconditions artifact/schema
ordered steps artifact
postconditions artifact/schema
success_count
failure_count
mean_cost
status candidate|active|retired
```

### 10.4 preference

Always scope preference to user + domain/context. No global preference is inferred from one isolated
choice.

Required fields: value, scope NodeIds, confidence, evidence.

### 10.5 expectation

Required: subject, predicted predicate/value, deadline?, confidence, evidence.
Resolution produces support/refute relation and prediction-error event when appropriate.

### 10.6 project state

Represents durable active facts/commitments about one Project/Repository and links directly to its
shared graph identity.

### 10.7 decision

Stores selected option, alternatives artifact, reasons artifact, actor and evidence.

---

## 11. Memory extraction/update rule

For each event after deterministic reducers:

1. update exact current operational facts in owning graph namespace;
2. if event closes/changes a durable user/project fact, create/update Agent assertion;
3. if event belongs to an active Activity, attach to its episode;
4. if event contains explicit user preference, create scoped preference at confidence 0.9;
5. if preference is inferred from behavior, initial confidence 0.6;
6. if a model extracts a semantic assertion, initial confidence is
   `model_confidence * provenance_quality`, capped 0.9;
7. user explicit correction creates assertion confidence 1.0 and contradicts/supersedes the prior
   interpretation as temporally appropriate;
8. no derived memory can exist without evidence relation(s).

Provenance quality multipliers:

```text
native-authoritative  1.00
user-declared         1.00
nix-evaluation        0.99
kernel-observation    0.99
protocol-descriptor   0.95
structured-tooling    0.95
foreign-api           0.90
source-analysis       0.90
deterministic-probe   0.85
agent-derived         0.80
learned-inference     0.70
```

---

## 12. Procedure induction

Normalize successful execution traces into capability-name sequences with semantic input/output
schema IDs, ignoring concrete ExecutionIds and timing.

Create a candidate procedure when the same normalized sequence reaches the same postcondition in at
least 3 independent episodes.

Candidate evaluation:

1. replay against all matching historical episodes;
2. require 100% postcondition success on at least 3 episodes;
3. run 5 sandbox executions on fixture/test inputs where the capability provides fixtures;
4. require 5/5 success;
5. require mean normalized cost <= 0.8 of the original model-mediated path.

Then promote automatically to active procedure and emit
`omnis.event.agent.procedure.promoted`.

Any later 2 failures within the last 10 uses retires the procedure and falls back to the original
capability resolution path.

---

## 13. Self-evolution state machine

Self-evolution always produces a candidate artifact/branch first.

Targets:

```text
Agent procedure/config
Agent code
Control code/config
Manager code/config
OmnisOS code/config
```

Evaluation gates for code/config candidates:

1. build succeeds;
2. owning repo full tests pass;
3. umbrella protocol/integration tests pass;
4. replay corpus has no regression >1% in required success metrics;
5. resource-cost regression <=10% unless success metric improves >=5%;
6. no new authority/protection violation;
7. candidate Nix artifact is reproducible twice with identical output hash when expected deterministic.

Automatic promotion defaults:

- learned Agent procedure: yes after §12;
- Agent user-level configuration: yes if all gates pass and rollback exists;
- Agent code: no;
- Control code: no;
- Manager code: no;
- OmnisOS code/config: no.

Non-automatic candidates remain graph-visible and can be activated by an actor holding the relevant
promotion capability. This is a physical authority rule, not a semantic approval workflow.

---

## 14. Direct ingest capability

`omnis.capability.ingest` provides deterministic bootstrap of arbitrary user data without models.

CLI:

```text
omnis ingest <path> [<path>...]
```

Algorithm:

1. lstat without following symlink;
2. allocate Resource NodeId per filesystem object;
3. record path, file type, size, mode, mtime, owner and symlink target;
4. regular file bytes -> BLAKE3 CAS ArtifactId;
5. recursively enumerate directories in raw filename-byte lexical order;
6. never execute ingested files;
7. detect Git repository from `.git` metadata and bind Repository identity;
8. parse deterministic formats only when a registered parser exists;
9. attach provenance `user-declared + deterministic-probe`;
10. enqueue ingest event;
11. Agent semantic reinterpretation can happen later and never rewrites original artifact/provenance.

Default recursion:
- recurse directories;
- stay on same filesystem;
- skip `.git/objects` content bodies but retain Git object identity through Git plumbing;
- maximum individual file 10 GiB;
- larger files create metadata node but are not copied to CAS unless explicitly requested.

---

## 15. Multi-user graph access

System graph is shared, but user-private cognitive/presentation state is owner-scoped.

Read rules:

- root/system services read all except secret bytes, which are never graph values;
- a user reads public/system/Manager state plus nodes whose `omnis.identity.owner_uid` equals their
  UID;
- one ordinary user cannot read another user's Agent cognitive or Control presentation nodes;
- remote host peers read only namespaces granted during pairing.

Write rules:

```text
omnis-os UID       physical.*, system.*, enforcement.*
omnis-manager UID  resource.*, capability.*, binding.*, execution.*, placement.*, foreign.*
user Agent          cognitive.*, memory.*, goal.*, context.*, judgement.*, worker.*, learning.*
user Control        presentation.*, interaction.*, scene.*, navigation.*
```

System services authenticate by dedicated UID + socket peer credentials.
Agent and Control share user UID; graphd additionally requires their per-unit 256-bit random service
token delivered as a systemd credential. Token rotates on unit restart. This prevents accidental
cross-component writes; the owning user remains a trust boundary and can ultimately impersonate
their own services.

Cross-namespace mutation goes through owning RPC, never direct graph commit.

---

## 16. Memory erasure

Worldline causal envelopes are immutable, but user-requested erasure can remove payload content.

Erasure algorithm:

1. create `omnis.event.agent.memory.erased`;
2. end validity of derived memory graph nodes;
3. delete/revoke protected ArtifactRef roots requested for erasure;
4. keep original EventId/type/time/causal edges and ArtifactId hash as an `erased` placeholder;
5. CAS GC physically deletes unreferenced payload after the normal tombstone interval;
6. rebuild retrieval indexes excluding erased content.

Do not fabricate or rewrite earlier event metadata.

---

## 17. Control semantic source components

### 17.1 text/document/editor

Plain text storage uses UTF-8 and a rope data structure through `ropey`.
Syntax trees use Tree-sitter when a language grammar binding exists.
LSP actions/completions/diagnostics come through Manager LSP bindings.

Editor defaults:

```text
tab width              4 display columns
insert spaces          inherit project editorconfig; otherwise 4 spaces
line endings           preserve existing; new files LF
encoding               UTF-8
undo history           10000 operations per document
autosave               off
syntax highlighting    Tree-sitter query when present
```

User/Agent save is an explicit filesystem effect event.

### 17.2 Markdown

Markdown parses with `pulldown-cmark` CommonMark + tables + task lists + strikethrough.
It lowers to ordinary Control text/image/link primitives.

### 17.3 table

Virtualize rows when row count >200.
Default visible overscan: 20 rows above and below.
Sort is stable; missing/null sorts last ascending and first descending.
Column width defaults to min(max(content estimate, 80px), 400px).

### 17.4 charts

Charts are custom Control scene projections, not a second renderer.

v0 chart types:

```text
line
scatter
bar
histogram
heatmap
```

Default numeric axis scale is linear.
Time data uses UTC internally and local timezone labels.
Downsample >10000 visible points per series using Largest-Triangle-Three-Buckets to 5000 points.
Raw source identity remains attached so selection resolves to original data.

### 17.5 images/media

Static image decoding uses `image` crate formats enabled by the pinned build.
Video/audio playback binds GStreamer/PipeWire as Manager resources; Control receives texture/audio
stream handles rather than implementing codecs.

---

## 18. Error presentation

Errors are graph/event identities, not modal-string-only failures.

Control behavior:

- effect/query error tied to focused action -> inline error on originating view;
- security/credential denial -> inline explanation + available remediation capability;
- system invariant violation -> persistent critical notification;
- background worker failure -> Activity indicator + event, no focus theft;
- protocol incompatibility of core local service -> persistent system banner and recovery action.

Error details include TraceId and a copyable `omnis://trace/<TraceId>` URI.

---

## 19. URI registry

Canonical URIs:

```text
omnis://node/<uuid>
omnis://event/<uuid>
omnis://activity/<uuid>
omnis://worker/<uuid>
omnis://execution/<uuid>
omnis://generation/<uuid>
omnis://artifact/<64-hex-blake3>
omnis://trace/<uuid>
omnis://capability/<percent-encoded-dotted-name>
omnis://host/<uuid>
```

Parsing is strict. Unknown authority/path returns NotFound; it does not become a web search.

---

## 20. State-machine enforcement

Execution, Worker, Activity, Generation and Memory status transitions in this document are enforced by
typed transition functions. Direct string/property writes to `omnis.state.status` for these kinds
are rejected by the owning authority.

Every rejected illegal transition produces a typed Conflict response and a diagnostic event.

---

## 21. Ontology extension rule

Implementation code may consume unknown third-party kinds/relations/properties as opaque namespaced
data.

It may **not create a new `omnis.*` identifier** unless that identifier is first added to this
registry or another active normative spec in the same change.
