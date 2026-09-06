# ADR-0021 — One input bar, one navigation model, everything addressable

- **Status**: Accepted · **Date**: 2026-09-06
- **Depends on**: ADR-0001, ADR-0006 · **Applies**: P10

## Context

Every comparable product ships the same widget five times: a chat box, a search field, a terminal
prompt, a command palette, and an address bar. Each has its own completion, its own history, its own
keybindings, and its own bugs. The transcript's "omni-bar" gestures at fixing this for chat and
search; the problem is larger.

Separately, navigation is treated as a browser feature. Back, forward, and reload exist in the web
view and nowhere else, so moving between a settings page, a file, and a documentation page has no
history at all.

Both are symptoms of the same gap: nothing has an address.

## Decision

**One input bar.** Not five widgets — one control, bound to whatever has focus. Chat, quick search,
terminal input, a web address, a settings filter, and a documentation query all reach the user
through it.

Panes do not ship input widgets. A pane declares an **input contract** — what it accepts, where
completions come from, what history it draws on, and what submitting means — and the bar renders and
routes accordingly (P10).

This clarifies the `inputBar` axis: `global-hud` and `per-pane` are two **placements** of the same
bar, floating or anchored into the focused pane, not two implementations.

**Everything is addressable.** Panes, files, settings pages, documentation, chats, repositories,
tasks, context fragments, and guest environments all have an `omnis://` address. Addressability is
what the input bar navigates to, what the CLI takes as an argument, what an agent cites in a
proposal, and what a documentation link points at.

**Navigation is global.** Because everything is addressed, **back, forward, and reload** are system
controls over one history stack across every surface.

**Reload re-materialises; it never re-executes.** Reload re-reads the file, re-queries the schema,
re-fetches the page. Reloading a task view must not run the task. Conflating those two turns a
navigation control into a destructive one, and a user pressing a familiar button will not expect it.

## Alternatives rejected

- **A widget per pane** — the default everywhere. Five implementations, five sets of keybindings,
  and completion quality that varies by which box you are in.
- **One input bar, but only for chat and search** (the transcript's omni-bar). Draws the line
  arbitrarily and leaves the terminal and address bar separate, so the unification never pays off.
- **Browser-style navigation only inside the browser pane.** Keeps the history model where it is
  least needed; moving between settings, docs, and a file remains untracked.
- **Reload meaning "re-run" for executable views.** Superficially useful and dangerous: one control
  whose meaning changes with focus, where one meaning destroys work.
- **Addresses for navigable things only.** Then the CLI and agent need a second addressing scheme for
  everything else, and the two drift.

## Consequences

- Every pane type must define its input contract and its address, which is a real per-pane cost paid
  once instead of a widget built each time.
- The `omnis://` scheme becomes a compatibility surface: addresses appear in documentation, agent
  proposals, and user bookmarks, so they cannot be casually renamed.
- History across heterogeneous surfaces raises questions a browser does not face — what "back" means
  after a pane closes, or when a target no longer exists. Those need answers before this ships, not
  after.
- Completion quality becomes a single shared concern rather than five separate mediocre ones, which
  is the main payoff.
