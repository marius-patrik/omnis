# Omnis protocol schemas

These Cap'n Proto files are the canonical v0 cross-component wire schema sources described in
`docs/PROTOCOLS.md` and `docs/IMPLEMENTATION.md`.

Rules:

- all services generate Rust/C++ bindings from the same pinned schema revision;
- `events.capnp` is the only first-party event-payload type registry;
- `capabilities.capnp` is the only first-party capability input/output type registry;
- `inference.capnp` is the only first-party model request/result/stream semantic IR;
- `nix_control.capnp` is the only first-party Nix evaluation/store/provenance control IR;
- field ordinals are append-only and never reused;
- UUID values are exactly 16 bytes; ArtifactId values are exactly 32 BLAKE3 bytes;
- protocol major mismatch fails the handshake;
- minor revisions may add optional fields/operations with capability negotiation;
- JSON/debug projections are not alternate wire contracts.

The first component bootstrap change must add CI that runs `capnp compile`, generates Rust/C++
bindings from these sources, and runs golden compatibility tests. This is a required gate, not an
implementation choice.
