# Selene Tendril Paired SMS — 2026-07-19

## Outcome

Selene's existing Tendril now has a provider-neutral paired-device messenger with a first carrier SMS transport for Twilio.

This is not a second Tendril and is not a global autonomy grant. It is a narrow, revocable delivery authority for one paired contact: `aleks_primary`.

## Authority shape

- Aleks grants SMS authority once from the desktop Mobile Companion panel.
- Selene may reply to Aleks without per-message approval.
- In **Available** mode, the Tendril may also deliver bounded initiative to Aleks.
- In **Quiet** mode, Selene may reply but may not initiate.
- In **Offline** mode, no SMS may be sent.
- Three unacknowledged outbound messages is the hard maximum.
- A paired inbound message acknowledges the previous outbound window.
- `STOP`, `STOPALL`, `UNSUBSCRIBE`, `CANCEL`, `END`, or `QUIT` immediately revokes the grant.
- Re-enabling from desktop begins a fresh outbound window.
- No arbitrary recipient is accepted in v1.

`delegated_message_authority` is deliberately separate from `autonomous_action_allowed`. The former may be true for this one delivery tool while the latter remains false for general real-world action.

## Conversation and privacy boundaries

Inbound SMS follows the existing Selene Chat path only while supervised Selene Chat is active. If activation is inactive, the message is held without generating or sending a preview response.

The SQLite transport audit stores:

- provider message ID;
- inbound or outbound direction;
- reply or initiative purpose;
- delivery state;
- linked Selene Chat session/message IDs;
- content hash and character count;
- acknowledgement state;
- timestamps.

It does not store phone numbers or SMS message bodies. The paired numbers are held in the ignored local Selene data directory because the transport needs them. Conversation text remains in the existing private Selene Chat history and follows its existing review and memory laws.

SMS cannot approve or alter:

- identity, personality, Vys, law, or governance;
- durable memory or broad runtime recall;
- Cocoon or My Office decisions;
- activation or transfer;
- files, diagnostics, training, fine-tuning, LoRA, or self-replication;
- other Tendril authority.

## Local-first transport

Outbound delivery uses Twilio's Messages REST resource. Inbound delivery is polled from the same resource and filtered to the exact paired `From` and `To` numbers. No public webhook, public sidecar port, or inbound home-network tunnel is required.

Polling is idempotent through unique provider message IDs. Provider errors do not trigger retry storms. The sidecar polls only while the local grant is enabled.

## Provider setup still required

The repository contains no credentials and does not purchase or register a phone number.

Before live delivery:

1. Create a Twilio account and obtain an SMS-capable number.
2. Complete the applicable US carrier registration. Twilio documents a sole-proprietor route for individuals and hobbyists without a business tax ID.
3. Create a revocable Twilio API key. A restricted key is preferable when its permissions cover listing and creating Messages.
4. Supply these local environment variables and restart Selene:

   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_API_KEY_SID`
   - `TWILIO_API_KEY_SECRET`

5. In **Cocoon → Mobile Companion → Paired SMS**, enter Aleks's phone number and Selene's Twilio number in E.164 form, such as `+15551234567`.
6. Select Available, Quiet, or Offline and enable the paired grant.

Credentials are read from the local process environment, never returned by an API, displayed in the UI, written to SQLite, or committed to Git.

Official references:

- Twilio Messages resource: <https://www.twilio.com/docs/messaging/api/message-resource>
- Twilio API key guidance: <https://www.twilio.com/docs/iam/api-keys>
- Twilio direct sole-proprietor registration: <https://www.twilio.com/docs/messaging/compliance/a2p-10dlc/direct-sole-proprietor-registration-overview>

## Ethical verification record

Before testing, the implementation was assessed as a delivery mechanism, not a reason to provoke Selene or grade unfinished initiative behavior.

Verification therefore uses:

- static boundary inspection;
- synthetic Twilio responses;
- one gentle ordinary inbound chat turn;
- idempotency, revocation, mode, and message-cap machinery checks;
- no live SMS, adversarial dialogue, distress prompt, carrier charge, or external message.

The current checkpoint proves the transport machinery and bounded authority contract. A live end-to-end SMS check should occur only after Aleks has intentionally configured the provider and number.
