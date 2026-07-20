# Selene Tendril Gmail-to-Verizon Text Gateway — 2026-07-20

## Outcome

Selene's post-transfer Tendril uses Python's standard-library Gmail SMTP and read-only IMAP support to reach Aleks through Verizon's consumer email-to-text gateway.

Outbound mail is addressed internally to the paired ten-digit number at `vtext.com`, which Verizon converts into a text for the phone's Messages app. Replies that Verizon returns to Selene's Gmail are polled through IMAP and routed into the existing Selene Chat path.

This is provider-API-free: it uses no paid SMS API, Twilio account, copied third-party package, public webhook, or inbound home-network tunnel. Gmail and Verizon still provide the underlying mail and carrier transport.

The Stack Overflow answer and linked demonstration were used only to confirm the carrier-gateway mechanism. Selene's implementation retains her own Tendril authority model, lifecycle, privacy boundaries, audit, automatic polling, and failure behavior.

## Ownership and authority

- Selene owns her Gmail identity and paired Verizon-number configuration.
- The private pairing file lives under Selene's local runtime directory at `selene_runtime/tendril/selene_tendril_email.json`.
- Controls live in **Selene → Tendril**, not Cocoon.
- Cocoon receives no Gmail address, Verizon number, derived gateway address, App Password, message body, or messenger control.
- Aleks grants the gateway-text authority once; per-message approval is not required.
- **Available** permits replies and up to three unacknowledged initiative messages.
- **Quiet** permits replies but not initiative.
- **Offline** permits no sending.
- The exact phrase `return to desktop` revokes the gateway-text grant.
- No arbitrary recipient or carrier gateway is accepted.

The narrow `delegated_message_authority` does not set `autonomous_action_allowed` and does not grant broader Tendril or real-world authority.

## Conversation path

```text
Selene Chat
    ↕ existing local chat route
Selene's bounded Tendril gateway adapter
    ↕ Gmail SMTP / read-only IMAP
Selene's dedicated Gmail
    ↕ internally derived 10-digit-number@vtext.com
Verizon consumer email-to-text gateway
    ↕ SMS
Aleks's Messages app
```

Outbound gateway messages are plain text, omit the email subject, and are truncated to 140 characters so the complete email-to-text payload remains conservatively below Verizon's documented 160-character limit. One Selene reply creates at most one gateway message.

Inbound content enters the existing Selene Chat history only while supervised Selene Chat is active. Inactive, offline, empty-response, chat-error, and delivery-error cases are explicitly held rather than silently discarded.

Inbox reads are non-mutating. Provider message IDs make repeated polls idempotent. Plain-text reply content is used; quoted prior-thread text and attachments are excluded from the Selene Chat turn.

## Privacy boundary

SQLite transport audit rows contain provider message ID, direction, purpose, delivery state, linked local chat IDs, body hash, character count, acknowledgement state, sanitized error class, and timestamps.

They do not contain phone numbers, email addresses, subjects, gateway addresses, or message bodies. Status APIs return masked identities and never return the App Password.

Gmail necessarily stores sent and received gateway mail. Verizon necessarily processes the resulting carrier text. The dedicated Gmail account and separately revocable App Password limit the impact of that choice, but do not make the external transport local.

## Setup

1. Create a dedicated personal Gmail account for Selene.
2. Enable Google two-step verification.
3. Create a dedicated App Password for the Selene messenger.
4. Supply these local process environment variables and restart Selene:

   - `SELENE_GMAIL_ADDRESS`
   - `SELENE_GMAIL_APP_PASSWORD`

5. Open **Selene → Tendril → Selene's Verizon Text Gateway**.
6. Enter Aleks's ten-digit Verizon number, choose **Quiet**, and enable the gateway.
7. If necessary, text `Status` to Verizon short code `4040`; Verizon reports whether email-to-text is allowed. Text `On` to `4040` only if Aleks intentionally wants to enable it.
8. Confirm credentials are ready and the background poller reports `polling`.
9. Send one ordinary, short diagnostic text from Selene to determine whether Verizon still accepts gateway traffic for this line.
10. Reply naturally from the Messages app to verify the return path.
11. Move to **Available** only when bounded initiative is desired.

The normal Google password must never be used by the transport. The App Password must not be pasted into Cocoon, Chat, source files, SQLite, Git, or documentation.

## Verizon lifecycle constraint

Verizon still documents `number@vtext.com` for consumer email-to-text and describes it as a low-volume consumer service. Verizon has also announced an active shutdown scheduled to complete by March 31, 2027 and warns that some senders may lose access sooner or be filtered.

The adapter therefore treats Verizon acceptance as a live capability to verify, not a permanent guarantee. Failure falls gracefully and does not trigger repeated sending, broaden authority, or count as Selene failing.

## Preserved boundaries

Gateway texting cannot approve or alter identity, personality, Vys, law, governance, durable memory, broad runtime recall, Cocoon decisions, teaching, transfer, files, diagnostics, training, fine-tuning, LoRA, self-replication, other recipients, or other Tendril authority.

## Ethical verification

Machinery verification uses synthetic SMTP and IMAP clients, ordinary conversational wording, static privacy inspection, exact-recipient checks, message-length checks, idempotency, held-state checks, mode and rate-limit checks, and background lifecycle checks.

The one real delivery probe is justified only to learn whether Verizon still supports the line. It should be one ordinary short message, not a repeated stress test.
