# ADR-0008 — Task identity is the hash of its inputs

- **Status**: Accepted · **Date**: 2026-09-06 · **Promotes**: `notes/transcript.md` §9.5

## Context

The transcript describes a cross-repository task DAG parsed from `package.json`, `Cargo.toml`,
`Makefile`, and `Taskfile.yaml`, using "CAS timestamps" to skip unchanged targets. Timestamps are the
wrong key: `mtime` changes on checkout, restore, and touch without the content changing, and fails to
change on same-second writes.

## Decision

A target's identity is the hash of its inputs — source content, dependency output hashes, the command
line, and the declared environment — not a timestamp. A target is skipped when the CAS already holds
an output for that input hash. Skips are explainable: the system can say which input changed.

## Alternatives rejected

- **Timestamp comparison.** Both false-negative and false-positive, and unusable across machines,
  containers, or a sync mesh where mtimes are meaningless.
- **Always rebuild.** Correct and unusable at repository scale.
- **Delegate caching to each tool.** No cross-repository graph, no shared cache, and every tool's
  cache is invalidated differently.

## Consequences

Input declaration must be complete, and an undeclared input produces a wrong cache hit — the classic
build-system failure. Undeclared-input detection (sandboxed execution, or filesystem tracing) is
therefore part of the epic, not an extra. Cache entries are CAS objects and share its retention
policy. Cycles must be reported *with the cycle*, not merely detected.
