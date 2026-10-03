# Omnis protocol schemas

These Cap'n Proto files are the canonical v0 cross-component wire schema sources described in
`docs/PROTOCOLS.md` and `docs/IMPLEMENTATION.md`.

Rules:

- all services generate Rust/C++ bindings from the same pinned schema revision;
- field ordinals are append-only and never reused;
- UUID values are exactly 16 bytes; ArtifactId values are exactly 32 BLAKE3 bytes;
- protocol major mismatch fails the handshake;
- minor revisions may add optional fields/operations with capability negotiation;
- JSON/debug projections are not alternate wire contracts.

The first implementation should add a CI job that runs `capnp compile` plus language binding
generation/golden compatibility tests once component source repositories are created.
