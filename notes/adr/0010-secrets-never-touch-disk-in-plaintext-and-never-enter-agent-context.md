# ADR-0010 — Secrets never touch disk in plaintext, and never enter agent context

- **Status**: Accepted · **Date**: 2026-09-06 · **Promotes**: `VISION.md` §9.4

## Context

Terminals, VCS pushes, package installs, and agents all need credentials. The usual answer is a
`.env` file on disk and environment variables inherited broadly, which puts plaintext at rest and
inside every child process. With autonomous agents in the loop there is a second exposure the
transcript names explicitly: secrets landing in an agent's context window, and from there in a model
provider's logs.

## Decision

- The master key derives via Argon2id; the key-encryption key is held in a zeroising buffer with
  `mlock`, never serialised.
- Device secrets bridge to the OS keychain (Apple Keychain, DPAPI, Secret Service).
- Secrets reach child processes by injection into the spawned process's environment at spawn time —
  never written to disk, and never to a file the child reads.
- **Secrets are never placed in agent context.** An agent may reference a secret by name and cause it
  to be injected; it may not read its value.
- Git, forge, and SSH authentication go through `omnis-ssh-agent` over a local socket, so private
  keys are decrypted on demand and never handed out.

## Alternatives rejected

- **`.env` files on disk.** Plaintext at rest, trivially readable by anything running as the user,
  and routinely committed by accident.
- **OS keychain as the only store.** Not portable across the sync mesh, and inconsistent APIs make
  the behaviour differ per platform in ways users notice.
- **Passing secrets through agent context.** Leaks them to the model provider, into logs, and into
  any transcript the user later shares.
- **A long-lived decrypted cache.** Convenient, and it converts a memory-disclosure bug into full
  credential compromise.

## Consequences

Every subsystem needing credentials goes through the vault, so the vault is on the critical path for
terminals, VCS, packages, and agents — arguing for building it early (E11). Injection at spawn time
means a child that re-executes or daemonises may outlive the grant; process lifetime is part of the
threat surface.

**Scope limit:** as with ADR-0009, this fixes the *shape*. Argon2id parameters, what `mlock`
genuinely defends against on each platform, whether environment injection is acceptable against the
intended adversary, and the revocation story for in-flight secrets are D10's, and D10 may constrain
this ADR without superseding it.
