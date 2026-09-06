# ADR-0002 — Themes are VS Code colour themes; profiles bundle them

- **Status**: Accepted · **Date**: 2026-09-06

## Context

The transcript escalates "theme" from colour tokens to a `SystemPersonalityPackage` that changes the
renderer, layout, keymap, input routing, extension compatibility, and the agent persona. One word
covering all of that is useless: someone reading "switch theme" will not expect their keymap to
change.

But collapsing colours *into* the larger concept is equally wrong — it discards the single largest
piece of ecosystem compatibility available to this project.

## Decision

Two distinct concepts, and colours keep the name.

**A theme is colours, in the VS Code colour-theme format.** `colors` (workbench keys),
`tokenColors` (TextMate scopes), `semanticTokenColors`, and `type: dark | light | hc`. Existing VS
Code colour themes load directly, unmodified. The VS Code colour key namespace is the canonical
token namespace, **extended** where Omnis needs tokens VS Code lacks — material-layer inputs, and
cell-grid specifics beyond the `terminal.ansi*` keys the format already provides.

**File and product icon themes** use the VS Code icon-theme format for the same reason.

**A profile is a bundle**: a theme reference, an icon theme reference, the five axis values
(presentation, layout, input routing, keymap), window chrome, app icon and its state animations,
typography and density, audio pack, material-layer backdrops, and settings overrides. Profiles are
the transcript's `SystemPersonalityPackage`.

No product code branches on a theme name or a profile name. Adding either requires zero code changes.

**Agent persona is not part of a profile.** A profile may *suggest* a persona; it never sets a
provider, model, or reasoning effort behind the user's back.

## Alternatives rejected

- **One concept called "theme"** (the transcript). Hides that selecting one changes behaviour.
- **One concept called "profile", colours folded in.** Throws away compatibility with thousands of
  existing themes, and forces every user to re-author colours they already have.
- **An Omnis-native colour format.** Marginally cleaner, and it would mean nobody's existing theme
  works on day one. The VS Code format is verbose and editor-shaped, and that is worth paying: it
  also hands us the 16 ANSI terminal colours the cell-grid renderer and `omnis-tui` both need.
- **Binding persona to the bundle** (the transcript's `aiPersona`). Selecting a *look* would silently
  select a model provider and reasoning effort.

## Consequences

- A documented mapping from VS Code colour keys onto scene-tree primitives is required, and gaps in
  that mapping are a compatibility surface with its own versioning obligation.
- Themes authored for a DOM editor will not exercise every Omnis token; unmapped tokens need
  defined fallbacks rather than undefined colour.
- Two lints, not one: no branching on theme name, no branching on profile name.
- Third-party trade dress becomes a data and licensing question (D3), not a code question.
