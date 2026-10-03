# OmnisOS v0 NixOS Option Contract

**Status: NORMATIVE.** These are the exact public v0 NixOS option paths, types and defaults.
Implementers must not rename, duplicate or invent competing configuration surfaces.

Unless stated otherwise, options are declared under `options.omnis`.

## 1. Root

| Option | Type | Default |
|---|---|---|
| `omnis.enable` | bool | `false` |

When false, no Omnis service/module side effect is enabled.

## 2. Graph

| Option | Type | Default |
|---|---|---|
| `omnis.graph.enable` | bool | `config.omnis.enable` |
| `omnis.graph.dataDir` | path | `/var/lib/omnis/graph` |
| `omnis.graph.socket` | str | `/run/omnis/graph.sock` |
| `omnis.graph.writerQueue` | unsigned int | `4096` |
| `omnis.graph.inlinePayloadMax` | unsigned int | `65536` |
| `omnis.graph.query.defaultLimit` | unsigned int | `1000` |
| `omnis.graph.query.hardLimit` | unsigned int | `10000` |
| `omnis.graph.query.maxDepth` | unsigned int | `8` |
| `omnis.graph.casDir` | path | `/var/lib/omnis/cas/blake3` |
| `omnis.graph.backupDir` | path | `/var/lib/omnis/backups/graph` |

SQLite journal/synchronous modes are not public options in v0: WAL/FULL are fixed contracts.

## 3. OS observation

| Option | Type | Default |
|---|---|---|
| `omnis.os.enable` | bool | `config.omnis.enable` |
| `omnis.os.socket` | str | `/run/omnis/os.sock` |
| `omnis.os.observe.systemd` | bool | `true` |
| `omnis.os.observe.udev` | bool | `true` |
| `omnis.os.observe.rtnetlink` | bool | `true` |
| `omnis.os.observe.processes` | bool | `true` |
| `omnis.os.observe.sessions` | bool | `true` |
| `omnis.os.observe.cgroups` | bool | `true` |
| `omnis.os.observe.watchedFileScopes` | list of paths | `[]` |

## 4. Manager

| Option | Type | Default |
|---|---|---|
| `omnis.manager.enable` | bool | `config.omnis.enable` |
| `omnis.manager.socket` | str | `/run/omnis/manager.sock` |
| `omnis.manager.nixControlSocket` | str | `/run/omnis/nix-control.sock` |
| `omnis.manager.discovery.enable` | bool | `true` |
| `omnis.manager.discovery.concurrency` | unsigned int | `16` |
| `omnis.manager.inferenceGateway.enable` | bool | `true` |
| `omnis.manager.inferenceGateway.port` | port | `7331` |
| `omnis.manager.remote.listen` | bool | `false` |
| `omnis.manager.remote.port` | port | `7443` |

Provider toggles all default false except exact local-system providers:

```text
omnis.manager.providers.nix.enable = true
omnis.manager.providers.cli.enable = true
omnis.manager.providers.systemd.enable = true
omnis.manager.providers.http.enable = true
omnis.manager.providers.mcp.enable = true

omnis.manager.providers.models.openaiCompatible.enable = false
omnis.manager.providers.models.anthropic.enable = false
omnis.manager.providers.models.llamaCpp.enable = false
omnis.manager.providers.models.onnx.enable = false

omnis.manager.providers.harnesses.claude.enable = false
omnis.manager.providers.harnesses.codex.enable = false
omnis.manager.providers.harnesses.opencode.enable = false
```

A provider can additionally become available through deterministic discovery even when its built-in
adapter toggle is false; the toggle controls the first-party adapter, not resource visibility.

## 5. Agent users

`omnis.agent.users` is an attrsOf submodule keyed by existing NixOS username. No users are generated.

Per user:

| Option | Type | Default |
|---|---|---|
| `enable` | bool | `false` |
| `memory.fts5` | bool | `true` |
| `memory.vectorIndex` | enum `none|sqlite-vec` | `sqlite-vec` |
| `models.providers` | list of strings | `[]` |
| `retention.modelContextDays` | unsigned int | `30` |
| `retention.modelOutputDays` | unsigned int | `30` |

If `vectorIndex=sqlite-vec` and no `model.embed` binding exists, the extension/index remains
available but contains no vectors; retrieval falls back exactly as specified.

## 6. Control users

`omnis.control.users` is attrsOf existing username submodule.

| Option | Type | Default |
|---|---|---|
| `enable` | bool | `false` |
| `defaultMode` | enum `2d|3d` | `2d` |
| `shell` | package | user's login shell package if known, else `pkgs.bashInteractive` |
| `xwayland.enable` | bool | `true` |
| `scrollbackLines` | unsigned int | `100000` |
| `theme` | str | `Omnis Dark` |

## 7. Hosts

| Option | Type | Default |
|---|---|---|
| `omnis.hosts.nativeRemote.enable` | bool | `true` |
| `omnis.hosts.quic.enable` | bool | `true` |
| `omnis.hosts.quic.port` | port | `7443` |
| `omnis.hosts.peers` | attrsOf peer submodule | `{}` |

Peer:

```text
hostId         UUID string, required
publicKey      string, required
fingerprint    string, required
address        string, required
grants         list of strings, default []
```

## 8. Security

| Option | Type | Default |
|---|---|---|
| `omnis.security.protectedHandles.enable` | bool | `true` |
| `omnis.security.systemdCredentials.enable` | bool | `true` |
| `omnis.security.executionIsolation.enable` | bool | `true` |
| `omnis.security.defaultWorkerNetwork` | enum `deny|user` | `deny` |
| `omnis.security.selfModification.agentProceduresAutoPromote` | bool | `true` |
| `omnis.security.selfModification.agentConfigAutoPromote` | bool | `true` |
| `omnis.security.selfModification.codeAutoPromote` | bool | `false` |
| `omnis.security.selfModification.systemAutoPromote` | bool | `false` |

## 9. Generated service dependencies

Exact system ordering:

```text
omnis-graphd.service
  after = local-fs.target
  before = omnis-osd.service omnis-managerd.service

omnis-osd.service
  requires = omnis-graphd.service
  after = omnis-graphd.service systemd-udevd.service

omnis-managerd.service
  requires = omnis-graphd.service nix-daemon.service
  after = omnis-graphd.service nix-daemon.service

user omnis-agentd.service
  after = graphical-session-pre.target
  wants network-online.target only when a configured binding needs it
  requires no Control service

user omnis-control.service
  after = graphical-session-pre.target
  requires no Agent service
```

Agent and Control both reconnect indefinitely with the fixed retry schedule; neither creates a hard
boot dependency on the other.

## 10. Invalid combinations

Evaluation fails for:

- `omnis.enable=false` with any child `enable=true`;
- Agent/Control user key that does not exist in `users.users`;
- remote listen=true while nativeRemote/quic=false;
- security protected handles disabled while any configured provider references a credential handle;
- writerQueue < 64;
- graph hardLimit < defaultLimit;
- port collisions among configured Omnis listeners.

These are NixOS module assertions, not runtime warnings.
