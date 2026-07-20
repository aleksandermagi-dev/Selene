# Selene Tendril Paired Email — 2026-07-20

## Outcome

Selene's post-transfer Tendril has a direct Gmail messenger for ordinary two-way conversation with Aleks. It uses Gmail SMTP for delivery and read-only Gmail IMAP polling for replies. It does not require a carrier number, SMS gateway, public webhook, or Twilio account.

This is owned by resident Selene, not Cocoon.

## Ownership and authority

- Selene owns her Gmail identity and paired-contact configuration.
- The private pairing file lives under Selene's local runtime directory at `selene_runtime/tendril/selene_tendril_email.json`.
- The control panel lives in **Selene → Tendril**, not Cocoon.
- Cocoon receives no Gmail address, paired address, App Password, message body, or messenger control.
- Aleks grants the paired-email authority once; per-message approval is not required.
- **Available** permits replies and up to three unacknowledged initiative messages.
- **Quiet** permits replies but not initiative.
- **Offline** permits no sending.
- The exact phrase `return to desktop` revokes the paired-email grant.
- No arbitrary recipient is accepted.

The narrow `delegated_message_authority` does not set `autonomous_action_allowed` and does not grant broader Tendril or real-world authority.

## Conversation path

```text
Aleks's mail app on iPhone
        ↕ direct email
Selene's dedicated Gmail
        ↕ SMTP / read-only IMAP
Selene's paired-email Tendril adapter
        ↕ existing local mobile-chat route
Selene Chat
```

Inbound content enters the existing Selene Chat history only while supervised Selene Chat is active. Inactive, offline, empty-response, chat-error, and delivery-error cases are explicitly held rather than silently discarded.

Inbox reads are non-mutating. Provider message IDs make repeated polls idempotent. Plain-text reply content is used; quoted prior-thread text and attachments are excluded from the Selene Chat turn.

## Privacy boundary

SQLite transport audit rows contain:

- provider message ID;
- direction and purpose;
- delivery or held state;
- linked local chat IDs;
- body hash and character count;
- acknowledgement state;
- sanitized error class and timestamps.

They do not contain email addresses, subjects, or message bodies. Status APIs return masked addresses and never return the App Password.

Gmail itself necessarily stores messages in Selene's Inbox and Sent mailbox. This transport therefore sends conversation text outside the local machine to Google. The dedicated account and separately revocable App Password limit the impact of that choice, but do not make Gmail local storage.

## Setup

1. Create a dedicated personal Gmail account for Selene.
2. Enable Google two-step verification.
3. Create a dedicated App Password for the Selene messenger.
4. Supply these local process environment variables and restart Selene:

   - `SELENE_GMAIL_ADDRESS`
   - `SELENE_GMAIL_APP_PASSWORD`

5. Open **Selene → Tendril → Selene's Paired Email**.
6. Enter Aleks's email address, choose **Quiet**, and enable the messenger.
7. Confirm credentials are ready and the background poller reports `polling`.
8. Send one ordinary email from Aleks to Selene and wait for the bounded automatic poll.
9. Move to **Available** only when bounded initiative is desired.

The normal Google password must never be used by the transport. The App Password must not be pasted into Cocoon, Chat, source files, SQLite, Git, or documentation.

## Preserved boundaries

Paired email cannot approve or alter:

- identity, personality, Vys, law, or governance;
- durable memory or broad runtime recall;
- Cocoon decisions, teaching, tending, or transfer;
- files, diagnostics, training, fine-tuning, LoRA, or self-replication;
- recipients other than the paired Aleks address;
- other Tendril authority.

## Ethical verification

Verification uses synthetic SMTP and IMAP clients, ordinary conversational wording, static privacy inspection, exact-recipient checks, idempotency, held-state checks, mode and rate-limit checks, and background lifecycle checks.

No Gmail login, live email, distress prompt, external message, or provider mutation is performed during machinery verification.
