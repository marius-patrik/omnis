# ADR-0007 — Every mutating VCS operation is invertible from an operation log

- **Status**: Accepted · **Date**: 2026-09-06 · **Promotes**: `notes/transcript.md` §9.5

## Context

Version control is where autonomous agents do the most damage, and where a user's confidence is
hardest won. Git's own safety net is partial: the reflog covers ref movements but not index or
worktree state, is not queryable, and does not exist for Sapling.

## Decision

Every mutating VCS operation appends an entry to an atomic operation log (`vcs_op_log`) that carries
enough state to invert it. Undo is a first-class operation over that log, not a reconstruction from
git internals. This holds identically for Git and Sapling — the log is Omnis's, not the backend's.

The backends themselves are `git` and `sl`, driven as they are. The abstraction exists so they are
**interchangeable and removable** (ADR-0011, ADR-0013) — so Sapling can stand where Git stands, and a
user who wants only one can remove the other along with its entire installation and system integration — not so that either
is reimplemented.

## Alternatives rejected

- **Rely on `git reflog`.** Does not cover index or worktree operations, is not queryable, and has no
  Sapling equivalent — so the undo story would differ per backend.
- **Snapshot the worktree before each operation.** Correct and far too expensive at repository scale;
  CAS deduplication helps but does not make it free.
- **No undo.** The status quo of most tools, and unacceptable once an agent is doing the committing.

## Consequences

Every new VCS operation must ship with its inverse, which makes adding operations more expensive on
purpose. The log is data (ADR-0005) and must survive backup and sync. Some operations are not
losslessly invertible — a hard reset over uncommitted changes — and those must either capture the
discarded state into the CAS first, or refuse.
