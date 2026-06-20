# Selene iOS Chat Companion

The iOS companion is a private chat doorway, not a mobile control room.

## Shape

- Desktop Selene remains the vessel host.
- The phone view uses `/mobile` or `?mobile=1`.
- Mobile can send gated chat messages, view session history, and save a review-only capture for desktop My Office.
- Mobile cannot decide reviews, run cocoon/build actions, run diagnostics, sync public release material, browse files, approve transfer, activate C, write live memory, import raw A, or run autonomous actions.

## Backend

Mobile routes live under `/api/mobile/*`:

- `GET /api/mobile/health`
- `GET /api/mobile/chat/sessions`
- `GET /api/mobile/chat/sessions/:id`
- `POST /api/mobile/chat/send`
- `POST /api/mobile/review-capture`

Every mobile response carries guard flags showing no activation, no transfer approval, no live memory write, no runtime recall, no raw A import, no autonomous action, and no self-replication.

## iOS Access

The default sidecar remains local-only on `127.0.0.1`. This pass does not expose Selene publicly and does not create an App Store app.

Future iPhone access should use a private LAN/Tailscale-style plan with authentication before any real on-the-go use.

## Rule

Phone is conversation and capture. Desktop is governance, review, build, diagnostics, evidence, and transfer boundary.
