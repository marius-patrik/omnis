# Vision capture — provenance and how to finish it

`VISION.md` is a partial transcript of the scoping conversation that produced Omnis. This note
records where it came from, what is missing, and how to complete it.

## Source

- **Conversation**: Google Gemini, "App Scoping Technical Specifications Discussion"
- **URL**: `https://gemini.google.com/app/545cf54445afcd33`
- **Account**: the maintainer's Google account
- **Captured**: 2026-09-06, via browser automation against the live page DOM
- **Size**: 20 turns, 79,891 characters of rendered text

## What was captured

| Turns | Content | Status |
|---|---|---|
| 0–1 | App icon configuration; Brand Parity & Dynamic Appearance Subsystem | Complete |
| 2–3 | Window styling; the "5 Pillars" | Pillar 1 and the schema only — pillars 2–5 lost |
| 4–5 | Typography, audio cues, icon state machines, `BrandProfileSpecification` | Mostly complete — two gaps |
| 6–7 | `SystemPersonalityPackage` | Interface complete, opening prose lost |
| 8–9 | The Zed terminal-native UI engine | Complete |
| 10–11 | The settings switchboard | Complete |
| 12–13 | Terminal-grid web browser | Complete |
| 14–15 | Master specification, section 1 | ~2,500 of ~19,500 characters |
| 16–19 | Two further exchanges, including a 19,000-character final compilation | **Not captured at all** |

Roughly 45,000 characters — the entire master compilation past its first section — are missing.

## Why it is incomplete

Extraction ran through the page's rendered DOM in chunks because the tooling truncates each read at
1,000 characters. Partway through the master compilation the browser extension lost its connection
to the automation host and did not reconnect. Clipboard and CDP fallbacks were both unavailable: the
page rejected programmatic clipboard writes without focus, and the only reachable debugging port
belonged to an unrelated application.

## How to finish the capture

1. Open the conversation in Chrome with the automation extension connected and the window focused.
2. Extract turn by turn rather than in fixed-size slices — `document.querySelectorAll('user-query,
   model-response')` returns 20 elements; turns 15 and 19 are the large ones.
3. Prefer a route that writes to disk over one that returns text through a tool result, since tool
   output is truncated at 1,000 characters and content-inspection guards reject some code-dense
   chunks outright. Focusing the tab first and copying to the clipboard, then reading the clipboard
   locally, is the shortest path that avoids both limits.
4. Append the recovered sections to `VISION.md`, replacing the corresponding `[GAP]` callouts.
5. Re-run the gap audit: every `[GAP]` still standing must name what is missing and how large it is.

## Ground rules for the recovered material

`VISION.md` stays non-normative no matter how complete it becomes. Anything in the recovered
sections that should bind the implementation must be promoted deliberately into `ARCHITECTURE.md`
through an ADR — never by editing the vision document and treating it as a specification.
