# OmnisOS

**Status: normative supporting specification.**

OmnisOS is the physical and persistent-system authority of Omnis. It is initially implemented as a
maintained NixOS/nixpkgs-derived Linux distribution. Linux remains the hardware kernel; OmnisOS owns
the system composition, graph integration, enforcement, and persistent generation semantics above
it.

---

## 1. Upstream relationship

OmnisOS is implemented as a fork/patch stack over `NixOS/nixpkgs`, preserving nixpkgs package
compatibility and upstream mergeability.

The fork exists for changes that require system-wide integration which cannot cleanly live as an
ordinary downstream NixOS module, especially:

- graph-native service/process/device publication;
- generation metadata and semantic diffs;
- Omnis boot/session integration;
- capability/authority enforcement hooks;
- Manager/Control core subsystem composition;
- event-producing lifecycle integration.

Ordinary packages remain upstream nixpkgs packages unless an Omnis-specific patch/package definition is required by a normative contract or failing acceptance test.

---

## 2. Boot target

The initial boot chain is conceptually:

```text
UEFI/firmware
  -> Linux kernel + initrd
  -> NixOS activation
  -> omnis-graphd
  -> {omnis-osd, nix-daemon, omnis-managerd}
  -> user session
  -> omnis-control
```

OmnisControl is the default local interactive environment. A headless target may omit Control while
retaining OS, Manager, graph, agent-access APIs, and remote-control capability.

systemd is the v0 service supervisor and transient-service execution mechanism. `omnis-osd` is the
only Omnis component allowed to create restricted `omnis-exec-*.service` units. It is a physical
mechanism, not a
second semantic system model; desired service semantics remain represented in NixOS + graph.

---

## 3. Graph publication

OmnisOS adapters publish authoritative physical facts to the shared graph.

Initial producers:

- host identity and hardware inventory;
- CPUs, memory, GPUs, storage, network devices;
- mounts/filesystems;
- active processes and process ancestry;
- services/units;
- users/session identities;
- network interfaces/routes/listeners;
- devices/hotplug;
- active Nix generation;
- store-path realization links;
- cgroups/resource envelopes;
- isolation/authority metadata.

OS facts MUST reference an existing Manager Resource NodeId when exact foreign/realization identity
resolves uniquely. If none exists yet, OS publishes the physical identity and Manager later attaches
its Resource through the normal exact-alias/provenance path; OS never guesses a fuzzy match.

Example:

```text
Resource:Firefox
  --system.realized_as--> StorePath:/nix/store/...
  --execution.spawned--> Process:812
  --presentation.surface--> WaylandSurface:41
```

---

## 4. Generation model

An OmnisOS generation extends ordinary NixOS generation identity with graph-visible metadata:

```text
Generation
  parent
  configuration source revision
  Nix derivation/system closure
  closure diff
  semantic graph diff
  actor
  causal event/intention
  build result
  activation result
  observed post-activation effects
```

Generation metadata must not require embedding model output into Nix derivations. Model reasoning is
stored as external-client/graph provenance; Nix receives deterministic configuration inputs.

---

## 5. Candidate generation workflow

Persistent mutation path:

```text
1. caller proposes persistent intent
2. Manager resolves package/resource/binding implications
3. produce candidate Nix configuration revision
4. evaluate configuration
5. compute dependency/closure/system graph diff
6. build candidate
7. validate machine invariants possible before switch
8. activate atomically using NixOS mechanisms
9. observe actual runtime state
10. publish graph changes + Agent events
```

Failures before activation do not alter active persistent state. Failures after external/activation
effects must be reported honestly and reconciled rather than described as impossible rollback.

---

## 6. Invariants

OmnisOS supports two invariant classes.

### 6.1 Evaluation invariants

Pure assertions over desired system/configuration graph state that can be checked before activation.

Examples:

- selected host provides required GPU capability;
- persistent service dependency resolves;
- protected local-only model is not placed remotely;
- conflicting implementation bindings are rejected.

### 6.2 Runtime physical invariants

Assertions over current physical state which may require ongoing enforcement/monitoring.

Examples:

- execution remains inside cgroup resource limits;
- execution cannot access filesystem outside mounts;
- network scope remains restricted;
- credential handle remains unavailable outside execution scope.

Runtime invariant violation emits a high-salience Agent event and invokes the declared physical
enforcement response without requiring an LLM decision in the critical path.

---

## 7. Authority and isolation

OmnisOS exposes an execution-envelope primitive sufficient for Manager to instantiate scoped work.

An envelope can constrain:

```text
filesystem/mount visibility
network namespace/reachability
process namespace
user/group identity
CPU quota/affinity
memory limit
GPU/device access
secret handle availability
IPC endpoints
lifetime/cancellation relationship
```

The Linux implementation composes existing primitives instead of inventing parallel isolation:

- cgroup v2;
- namespaces;
- seccomp;
- eBPF only for the frozen process-observation and constrained-network filters; no Omnis-specific LSM/Landlock layer in v0;
- Unix credentials/capabilities;
- container/VM runtimes when stronger isolation is required.

---

## 8. Hosts

Every Omnis installation has a stable Host graph identity.

Remote hosts can participate through Manager placement. A host advertises authoritative physical
capabilities and availability into the graph.

Native Omnis remote RPC uses QUIC with TLS 1.3 mutual host authentication. SSH remains an ordinary
Manager binding and Tailscale may carry QUIC traffic, but neither transport identity is host semantic
identity.

Remote execution must preserve:

- activity/execution ID;
- graph resource IDs;
- Agent causal parents;
- provenance;
- authority envelope.

---

## 9. Files and paths

Linux filesystems remain real and fully supported. Omnis does not replace POSIX paths.

Paths are locators for resources/artifacts and may change without changing graph semantic identity.

OS publishes file metadata/events sufficient for Agent/Manager to connect files to:

- packages/derivations;
- repositories/projects;
- processes;
- open handles;
- artifacts;
- Control views.

High-volume watched-filesystem observation uses the exact inotify batching/reconciliation contract in `DECISION_COMPLETE_V0.md §70` while
retaining enough causal evidence for Agent reconstruction.

---

## 10. Services and processes

Processes are physical executions, not the highest-level unit of work.

Manager/Agent activities may own multiple processes. OS publishes process facts and enforcement; it
does not infer high-level activity meaning.

Service supervisors remain bound mechanisms. Their state must be reflected into the graph rather
than becoming invisible side configuration.

---

## 11. Recovery

OmnisOS must recover independently of model availability.

On reboot:

1. restore graph service current-state database/recover its WAL;
2. identify active Nix generation;
3. republish/reconcile physical state;
4. start Manager;
6. start Control;
7. emit reconciliation events for differences between expected and observed state.

The machine must remain bootable with no model credentials and no network access.

---

## 12. Required implementation interfaces

OmnisOS must expose to Manager/Agent/Control:

```text
Graph API
Host inventory API
Execution envelope API
Generation evaluate/build/switch/rollback API
Physical observation/event API
Protected-handle broker API
Native surface/compositor prerequisites
```

The exact wire protocol is defined in `PROTOCOLS.md`.

---

Agent runtimes are not started, supervised or recovered by OmnisOS. They attach as ordinary clients.

## 13. Non-goals

Initial OmnisOS does not:

- replace the Linux kernel;
- replace system drivers;
- replace all systemd functionality immediately;
- create an alternate package universe;
- implement cognition;
- own model-provider semantics;
- own Control layout/presentation.

A future custom kernel is only justified by measured limitations of Linux against Omnis requirements.

---

## 14. v0 process and persistence binding

`omnis-graphd`, `omnis-osd` and `omnis-managerd` are system services. `omnis-control` is the per-user
session process. No agent daemon is generated or boot-critical; external agents attach as clients.

OmnisOS adds the `omnis.*` NixOS module family and two concrete configuration files:

```text
/etc/omnis/configuration.nix
/etc/omnis/managed.nix
```

The first imports the ordinary user NixOS configuration plus the second. OmnisManager edits only
`managed.nix` through the forked Nix parser/AST. Candidate files live under
`/var/lib/omnis/candidates/<GenerationId>/` until build/invariant checks succeed.

`omnis-osd` publishes exact Linux facts from systemd D-Bus, udev, rtnetlink, `/proc`, process eBPF
tracepoints, watched-scope fanotify/inotify, logind and cgroup v2. Startup reconciliation precedes
incremental event handling.

On graph corruption or unrecoverable startup failure, OmnisOS enters `omnis-recovery.target` with a
conventional TTY, Nix generation rollback and graph restore/rebuild tools. No model is required for
boot, recovery or enforcement.


---

## 15. Physical launch API

Manager owns semantic Execution resolution. OmnisOS owns the physical launch.

`omnis-osd` exposes:

```text
execution_envelope.create/destroy
physical_process.launch
physical_process.get
physical_process.signal
physical_process.stop
```

Launch creates one `omnis-exec-<ExecutionId>.service` through systemd with the exact sandbox
properties in `DECISION_COMPLETE_V0.md §§53-55`. osd creates pipes/PTY before unit start and returns
typed stream capabilities. No arbitrary string shell command is accepted: executable, argv,
environment and working directory are separate typed fields.
