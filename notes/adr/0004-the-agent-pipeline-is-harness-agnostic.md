# ADR-0004 — The agent pipeline is harness-agnostic

- **Status**: Accepted · **Date**: 2026-09-06

## Context

The delivery pipeline was hardcoded to Antigravity's `agy`, with fallback only between models inside
that one CLI. On this repository's first real run, Antigravity exhausted both tiers mid-implementation
and two approved plans stalled at `Blocked` with nothing else to try.

## Decision

Coding-agent CLIs are declared in `.github/scripts/harnesses.py` as a binary, an argv template, a
model chain, and credential keys — Antigravity, Claude Code, Codex, Kimi, Grok, Cursor, opencode.
Fallback escalates **across harnesses**, not only across models. Missing binaries and missing
credentials are **skipped, not failed**. `AGENT_HARNESS_CHAIN` and `AGENT_HARNESS_CONFIG` override
order and every field at runtime. Prompts pass as argv elements, never through a shell.

## Alternatives rejected

- **Stay single-vendor.** Demonstrated to halt delivery on one provider's quota — observed, not
  hypothetical.
- **`if`/`elif` per CLI in the runner.** Every new CLI edits the core retry loop, and each upstream
  flag rename becomes a code change and a container rebuild.
- **A wrapper script per CLI.** Moves invocation into shell, where prompt quoting becomes an
  injection risk, and puts it beyond unit tests.
- **An LLM API abstraction instead of CLIs.** These are agents, not completion endpoints: they carry
  their own tool loops, permissions, and repository awareness. Reimplementing that is the project.

## Consequences

Invocation flags are a maintenance surface, mitigated by runtime overrides. The container is larger
and tolerates per-CLI build failure, printing a manifest of what landed. Harness behaviour differs,
so prompts must not assume any one CLI's habits.
