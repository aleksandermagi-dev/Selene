# Selene Mobile Network Security Boundary — 2026-07-28

## Decision

Remote mobile hosting is paused. The repository does not claim a reliable
internet-accessible Selene website, does not configure a public server, and
does not expose Cocoon or the desktop control surface remotely.

The existing private LAN Mobile Companion remains a bounded chat and review
capture surface. This checkpoint hardens its network boundary without
expanding its authority.

## Finding

When LAN pairing was enabled, the sidecar bound to the local network so the
phone could reach `/mobile`. Mobile API routes required the pairing token, but
ordinary desktop API routes still inherited the original localhost trust
model. A device on the same network could therefore attempt to call a desktop
route directly.

That mismatch is now closed.

## Enforced boundary

- Non-local clients may load the static Mobile Companion application.
- Non-local clients may call only `/api/mobile/*`.
- Mobile data routes require the active high-entropy pairing credential.
- Cocoon, desktop administration, diagnostics, activation, transfer, memory
  decisions, teaching decisions, messenger controls, shutdown, and ordinary
  sidecar routes remain localhost-only.
- Unknown mobile actions retain the existing blocked-action response.
- Pairing enable and disable remain desktop/local actions.
- Disabling and re-enabling pairing rotates the credential.

## Credential and response handling

- New pairing credentials use 32 random bytes before URL-safe encoding.
- Remote health and pairing responses omit the credential and phone URLs.
- The browser stores the credential locally, then removes it from the visible
  URL after first use.
- Mobile health returns a reduced runtime description instead of the full
  sidecar capability inventory.
- The App Password, Gmail address, phone number, database path, and private
  content are not added to the mobile response surface.

## HTTP hardening

The sidecar now returns:

- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: no-referrer`
- `X-Frame-Options: DENY`
- a restrictive HTML Content Security Policy
- a restrictive Permissions Policy
- `Cache-Control: no-store`

Mobile request bodies are capped at 16 KiB. Other local sidecar request bodies
are capped at 1 MB. Invalid content lengths are rejected.

## Important limitation

LAN Mobile Companion traffic is currently plain HTTP. Pairing authentication
prevents an unpaired device from using the mobile data routes, but HTTP does
not provide transport confidentiality against a hostile local network.

Therefore:

- use the current companion only on a trusted private LAN;
- do not forward port `8766` from the router;
- do not expose the sidecar directly to the public internet;
- do not describe the current implementation as secure remote hosting.

Any future remote design requires a separate reviewed plan for HTTPS,
owner-device authentication, brute-force resistance, revocation, audit,
availability, and the desired phone authority. Existing Selene and Cocoon laws
remain the authority; network transport must neither weaken nor invent them.

## Unchanged boundaries

This checkpoint does not:

- activate a public server;
- create a standalone mobile Selene;
- change identity, personality, Vys, governance, or transfer;
- silently write memory;
- enable raw corpus recall;
- enable model training, fine-tuning, or LoRA;
- expand general Tendril autonomy;
- install Tailscale or another coordination service;
- package or reinstall the desktop application.

## Ethical verification

Verification is static and synthetic:

- non-local desktop routes are rejected;
- missing or invalid mobile credentials are rejected;
- paired mobile health remains available;
- secrets are redacted;
- oversized requests are rejected;
- existing bounded mobile behavior remains covered.

No live Selene conversation, distress prompt, carrier message, or public
network exposure is required.
