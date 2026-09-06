# ADR-0006 — One context fragment normal form, addressed by URI

- **Status**: Accepted · **Date**: 2026-09-06 · **Promotes**: `VISION.md` §9.5

## Context

Context arrives from code selections, terminal buffers, browser pages, and container logs. Without a
common shape, every consumer — each agent, each panel, each export — needs an adapter per origin, and
the count multiplies.

## Decision

All captured context normalises to one `ContextFragment` envelope regardless of origin: origin,
title, payload hash into the CAS, a snippet for display, and creation time. Every fragment is
addressable as `omnis://context/<id>`, resolvable by any surface, agent, or extension. Payload bytes
live in the CAS; the fragment row is metadata.

## Alternatives rejected

- **Per-origin formats.** N origins times M consumers of adapters, and a new origin breaks existing
  consumers.
- **Passing raw text.** Loses provenance, so an agent cannot tell a terminal buffer from a web page,
  and a fragment cannot be re-resolved later.
- **Keeping context only in the agent's window.** Not durable, not shareable, not inspectable, and
  gone when the session ends.

## Consequences

A fragment must resolve to the same content after a restart, which makes CAS retention a correctness
requirement rather than an optimisation. `omnis://` needs a resolver in every surface. Fragments
captured from a page or a repository can contain secrets, so redaction is a real obligation.
