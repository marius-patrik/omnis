# ADR-0019 — Native surfaces are delegated regions the compositor does not own

- **Status**: Proposed · **Date**: 2026-09-06
- **Extends**: [ADR-0001](0001-one-scene-tree-two-renderer-backends.md) §9.2 · **Answers**: D13
- **Enables**: [ADR-0014](0014-guest-environments-are-host-level-siblings-of-the-core.md), [ADR-0018](0018-services-are-backends-of-domain-subsystems.md)

## Context

ADR-0014 states that a guest application window is "a pixel source composited into the scene tree",
riding the existing `texture` primitive. ADR-0018 then hits a wall with it: **DRM-protected playback
cannot be captured**. Widevine and its equivalents require a protected output path, and capturing
protected output yields black frames by design. Netflix in a guest environment fails exactly as
Netflix in a browser canvas fails, because both are capture.

The same wall, less obviously, applies to anything the platform composites better than we can:
hardware-decoded video, and third-party webviews (D13), where a per-frame readback is both a
performance cost and a fidelity loss.

Capture is the wrong verb.

## Decision

Add a sixth primitive: a **native surface** — a region the scene tree **delegates** rather than
draws.

Omnis declares the geometry, the clip, and the z-order. The **platform** composites someone else's
content there, through its own path. **We never receive the pixels**, which is precisely why it is
permitted where capture is not.

| Platform | Mechanism |
|---|---|
| Linux/Wayland | Subsurface, or an overlay plane |
| macOS | `CALayer` / `AVSampleBufferDisplayLayer` |
| Windows | DirectComposition visual, swapchain overlay |

Used by: DRM playback, guest environment windows, hardware-decoded video, and third-party webviews.

**This is the sixth primitive class.** §9.2 says adding one is a design conversation rather than a
patch; this is that conversation, and the justification is that no combination of the existing five
can express "content we are not allowed to look at".

### What it costs, and these are not small

- **We cannot style, theme, colour-correct, or post-process it.** A profile does not reach inside a
  native surface. It is someone else's rectangle.
- **We cannot screenshot or record it.** Which is the point, and also means our own capture features
  have a hole in them that must be reported honestly rather than producing a black rectangle.
- **Z-ordering is constrained.** On several platforms an overlay is above or below the scene, not
  freely interleaved. Effects, popovers, and modals over a native surface may be impossible rather
  than merely awkward, and layout has to be designed knowing that.
- **It does not cross the network.** The web surface (ADR-0015) hosts the compositor in a browser
  canvas; a native surface cannot be delegated through it. **Remote access to DRM playback does not
  work**, and the remote surface must say so rather than showing a blank region.
- **It is a per-platform implementation** — four mechanisms, not one — in a project that otherwise
  keeps platform differences to how the core is hosted.

### The rule

**Delegate as little as possible, and only where capture is impossible or wasteful.** A native
surface is an escape hatch from our own rendering, and every use of one is a region of the interface
we no longer control. If content can be a texture, it should be.

## Alternatives rejected

- **Capture the guest window into a texture** (ADR-0014 as written). Works for ordinary applications
  and fails precisely where it was needed: protected content captures black. It also pays a readback
  per frame for content the platform would composite for free.
- **Accept that DRM services cannot be presented at all.** Honest, and it removes a large part of the
  point of ADR-0018's streaming domain. Search, metadata, and queue can be unified even when playback
  cannot — but only if playback has somewhere to go.
- **Ship a separate player window outside Omnis.** Solves DRM by leaving the product. The whole
  premise is composition.
- **Attempt to defeat the protected path.** Not a design option.

## Consequences

- ADR-0014's "guest windows ride the `texture` primitive" is refined: they ride `texture` where
  capture works, and a native surface where it does not or where the platform composites better.
- **D13 is answered**: webviews use a native subsurface, not readback — the same mechanism, reached
  from a different direction, which is evidence it is the right one.
- The parity contract is not violated, because ADR-0017 removed the TUI. A native surface could not
  have degraded to a terminal under any definition, so this primitive and the TUI were mutually
  exclusive. Dropping the TUI is what makes it available.
- The accessibility obligation (§9.5) does not extend inside a native surface: its contents are
  opaque to us, so whatever accessibility it has is the platform's and the content's. The region must
  still be *described* in our tree, or a screen reader encounters an unexplained gap.
