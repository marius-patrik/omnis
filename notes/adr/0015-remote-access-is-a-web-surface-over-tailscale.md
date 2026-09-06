# ADR-0015 — Remote access is a web surface over Tailscale

- **Status**: Proposed · **Date**: 2026-09-06
- **Depends on**: ADR-0001, ADR-0003, ADR-0011

## Context

The daemon holds everything durable and the surfaces are thin (`ARCHITECTURE.md` §2), so reaching a
workspace from another device should be a matter of attaching another surface. Doing that over the
open internet normally means port forwarding, a reverse proxy, certificate management, and an
authentication system — four things nobody wants to own.

## Decision

**Remote access is a first-class web surface, served over Tailscale at the device's HTTPS name**
(`https://<device>.<tailnet>.ts.net`).

- **Transport, naming, and certificates are Tailscale's.** `tailscale serve` provides the stable
  name and a valid certificate with no port forwarding and no public exposure. We write none of it
  (ADR-0011).
- **Identity comes from the tailnet.** The caller's identity is established by Tailscale rather than
  by an account system of ours, which is what makes ADR-0003's attribution requirement satisfiable
  for a remote caller.
- **The web surface is a surface, not a new renderer backend.** The GPU compositor is wgpu-based and
  wgpu targets WebGPU, so a browser hosts the *same* backend in a canvas. ADR-0001's two backends
  still hold; this adds a third *host*, not a third renderer.
- **It is optional.** Tailscale is an integration, never a dependency. The daemon must start, run,
  and be fully usable with no network at all, and with Tailscale absent.

## Alternatives rejected

- **Our own remote access: reverse proxy, certificates, accounts.** Four hard problems, one of them
  security-critical, all solved better elsewhere. This is the clearest possible case for ADR-0011.
- **Public exposure through a tunnel service.** Reaches more devices and makes a developer workspace
  — with shell access, secrets, and an agent runtime — internet-reachable. The tailnet boundary is
  doing real work here, and giving it up for reach is a bad trade at this blast radius.
- **Streaming the compositor's frames, remote-desktop style.** Works over a LAN, degrades badly over
  a WAN, and discards text selection, copy, and accessibility — the same objection ADR-0001 raises
  against rasterising for the terminal.
- **A separate DOM implementation for the web surface.** A third renderer backend, with everything
  built a third time. The WebGPU path exists precisely so this is unnecessary.
- **Making Tailscale a hard dependency.** Simplifies the code and makes a local-first tool require a
  third-party network service to start. Not acceptable.

## Consequences

- The accessibility cost of a canvas-rendered UI (§4.5) applies to the web surface too, and browsers
  are where users most expect assistive technology to work. This raises the priority of publishing an
  accessibility tree rather than lowering it.
- WebGPU availability varies by browser and platform; the surface needs a stated floor and an honest
  failure message, not a blank canvas.
- Tailnet identity is coarse — it identifies a device and a user, not a role. Anything finer stays
  with the capability broker and the escrow (ADR-0003, ADR-0006).
- A remote surface makes latency visible in a way local ones do not. The input-to-frame path becomes
  a budget question (D7) rather than an implementation detail.
