# ADR-0009 — Content-addressed storage: BLAKE3, FastCDC, convergent encryption

- **Status**: Accepted · **Date**: 2026-09-06 · **Promotes**: `VISION.md` §9.5

## Context

CAS underpins task caching (ADR-0008), context fragments (ADR-0006), virtual files, and the sync
mesh. Its shape has to be fixed before those are built.

## Decision

Content-defined chunking with FastCDC (declared min/average/max sizes), chunks keyed by their BLAKE3
hash, and convergent encryption deriving each chunk's key from a master secret plus that chunk's
hash. Reflink-based deduplication across workspaces where the filesystem supports it.

## Alternatives rejected

- **Fixed-size chunking.** An insertion near the start of a file shifts every subsequent boundary and
  defeats deduplication entirely.
- **SHA-256 keys.** Slower with no benefit here; content addressing needs collision resistance, not
  a specific standard's pedigree.
- **Per-file random keys.** No deduplication at all once encrypted, which removes the reason for
  content addressing.
- **Unkeyed convergent encryption.** Identical plaintext produces an identical ciphertext *globally*,
  letting anyone confirm whether a known file exists. Keying the derivation with a per-user master
  secret confines that to a single user's own store.

## Consequences

Convergent encryption still leaks equality **within** one user's store: an attacker with store access
who can guess a plaintext can confirm its presence. That is an accepted, bounded property of the
design, not an oversight.

**Scope limit:** this ADR fixes the *structure*. It asserts no threat model — what this defends
against, and against whom, is D10. Argon2id parameters, key rotation, and the sync-mesh exposure of
convergent keys are all D10's to settle, and D10 may constrain this ADR without superseding it.
