# ADR-0005 — Configuration lives in files, data lives in PGlite

- **Status**: Accepted · **Date**: 2026-09-06 · **Resolves**: D2

## Context

The transcript puts appearance profiles in a `brand_appearance_profiles` table *and* the same
settings in `settings.json`, with no stated precedence. It also names the store: a "Serialized PGlite
Mailbox" — embedded Postgres, not a server, which settles the local-first tension but not the overlap.

## Decision

**Configuration** — themes, icon themes, profiles, keymaps, layouts, feature flags, settings — lives
in versioned files and resolves through `defaults → profile → user → workspace → runtime`. It is
diffable, shareable, reviewable, and survives losing the database.

**User data** — workspaces, tabs, chat threads, audit entries, CAS metadata, VCS state, context
fragments, escrow tickets — lives in PGlite.

The transcript's `brandAppearanceProfiles` table is **not adopted**. The test: *would a user want
this in version control, or be alarmed to find it there?* Config is the first, data the second.

## Alternatives rejected

- **Everything in the database.** Profiles stop being shareable artifacts, configuration becomes
  unreviewable, and a corrupt store takes the user's setup with it.
- **Everything in files.** Chat history, audit streams, and CAS metadata as flat files means no
  queries, no transactions, and a synchronisation problem per file.
- **A server Postgres.** Contradicts local-first; makes a background service a hard dependency for a
  desktop application.
- **SQLite instead of PGlite.** Defensible and lighter. Rejected to keep one dialect across the
  eventual sync and mailbox work. Worth revisiting if PGlite's footprint proves unacceptable — that
  would supersede this ADR.

## Consequences

Two persistence mechanisms and two backup stories, with a boundary that will be argued at the edges
(a pinned context fragment is data, because the user did not author it as a setting). Config writes
must be atomic and attributable in the same way database mutations are. The sync boundary (E19) must
handle both, and they have different conflict semantics: config merges textually, data through the
CRDT.
