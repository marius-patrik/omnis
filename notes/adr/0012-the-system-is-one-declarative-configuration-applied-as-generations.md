# ADR-0012 — The system is one declarative configuration, applied as generations

- **Status**: Accepted · **Date**: 2026-09-06
- **Refines**: ADR-0005 · **Completes**: ADR-0003, ADR-0006

## Context

`notes/transcript.md` §7 treats `settings.json` as a switchboard: a bag of keys the UI writes and the daemon
reads. ADR-0005 put configuration in versioned files, which is right but says nothing about *shape*.

Two problems remain unsolved by a settings bag. First, once subsystems, packages, profiles, and
guest environments are all configuration, an unstructured key-value file cannot express the
dependencies between them. Second — and more seriously — ADR-0003 promises every modification is
**reversible** and ADR-0006 promises every agent action is **attributable**, and neither record says
by what mechanism. Both are currently aspirations.

## Decision

**The configuration is a single declarative specification the system converges toward**, in the
NixOS sense: you describe the desired state, evaluation produces a system, and applying it creates a
**generation**.

- **One declaration, in Nix.** Not a format of our own that compiles to Nix — that means owning a
  language and a compiler, which ADR-0011 forbids. Using the Nix module system directly gives typed
  options, merge semantics, `mkDefault`/`mkForce`, imports, and nixpkgs for nothing.
- **It declares the whole system**: enabled subsystems, packages and toolchains, profiles and themes,
  guest environments, remote access, and secret *references* — never secret values (ADR-0010).
- **Applying it produces a generation** with a parent, a diff, and an author. Generations are
  listable, diffable, and roll back.
- **Runtime mutations write the declaration.** A change made through the modification surface
  (ADR-0003) is staged into the specification and applied by convergence. It is not an overlay and
  not a side-channel.

## Why this completes two earlier records

**ADR-0003's reversibility becomes a mechanism.** "Any change an agent makes can be inspected,
diffed, and rolled back" stops being a design intention and becomes `omnis rollback` — the same
operation for a typo, a bad profile, and a misbehaving agent.

**ADR-0006's attribution gets a natural unit.** A generation has an author. An agent reconfiguring
your system produces a reviewable change with a parent commit, not an untraceable mutation. Audit
answers *what happened*; generations answer *what the system now is, and who made it so*.

This is the reason to prefer declarative here. It is not tidiness — it is that the safety properties
already promised have no other credible implementation.

## Alternatives rejected

- **A settings bag (`settings.json`), as the transcript proposes.** Cannot express dependencies
  between subsystems, packages, and environments; cannot roll back; gives attribution nowhere to
  live. It is adequate for appearance and inadequate for a system definition.
- **Our own declarative format compiled to Nix.** Friendlier syntax, and it costs a language, a
  parser, a type system, an error-reporting story, and a compiler — to reach a place the Nix module
  system already occupies. The friendliness belongs in the GUI editing structured options, not in a
  second language.
- **Imperative configuration with a snapshot/undo layer.** Snapshots capture state without capturing
  intent, so a rollback cannot explain what it undid, and two concurrent changes cannot be merged.
- **Declarative base with runtime overlays that are never written back.** The tempting middle. It
  guarantees drift: the running system stops matching the declaration, and the declaration stops
  being the source of truth exactly when you need it to be.

## Consequences

- **Nix is a hard dependency and a real learning curve.** Users who never open the file are served by
  the GUI writing structured options for them; users who do open it meet Nix. That cost is accepted
  in exchange for the module system and nixpkgs.
- Convergence is not instant. Some changes apply live; others need a subsystem restart. The
  configuration schema has to say which, or the UI will lie about when a change took effect.
- Every setting needs a typed option definition — which ADR-0003's introspection requirement demands
  anyway, so the two land together.
- Secrets stay outside the declaration, referenced by name only. A declaration is diffable,
  shareable, and frequently pasted into an issue.
