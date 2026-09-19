# Selene Speaker Provenance and Participant Continuity

Date: 2026-09-19

Status: source implementation verified; packaging and resident installation
not performed in this checkpoint

## Observation

The Ordinary Conversational Check-In requires Codex to identify itself rather
than speak as Aleks. Inspection found that Selene already received a typed
speaker envelope on the current turn, and Aleks-only private corpus recall was
already gated by that envelope. The provenance did not survive the complete
conversation path, however:

- an unspecified resident desktop turn defaulted to Aleks;
- the incoming user message did not persist its speaker envelope;
- the compact continuity projection omitted speaker attribution; and
- Dialogue Workspace and active conversation history reduced every incoming
  participant to the generic role `user`.

That meant current-turn privacy gates could work while later callbacks could
not reliably distinguish which participant had said what.

## Source repair

- Speaker envelopes now carry a normalized, non-authority participant key,
  speaker kind, attribution source, channel, purpose, and authentication
  context.
- Resident desktop Chat explicitly supplies Aleks's local desktop envelope.
- Diagnostic QA defaults to Codex rather than silently attributing diagnostic
  prompts to Aleks.
- Every new incoming Chat message persists the canonical speaker envelope.
- Compact continuity projections retain speaker attribution without granting
  identity, Memory, teaching, governance, or action authority.
- Current-session events expose the actual message speaker. Selene-authored
  messages remain attributed to Selene, while their conversation-partner
  attribution remains separately visible.
- A bounded participant ledger records observed participants and detects an
  explicit speaker change without turning it into durable personal Memory.
- Dialogue Workspace retains the current speaker and participant provenance.
- Explicit questions about the current speaker or the attributed author of a
  quoted earlier turn can answer from the typed record rather than guessing.
- Legacy ordinary resident desktop turns may be labeled as an inferred Aleks
  desktop turn; the inference source remains explicit. Other unattributed
  legacy turns remain unknown.

## Boundaries

- Speaker attribution is not proof of identity and does not expand authority.
- Codex and guests cannot inherit Aleks-only private corpus recall or
  conversational teaching approval.
- Ordinary relational continuity remains private to an eligible Aleks/Selene
  conversation.
- No schema rewrite, historical-message rewrite, Memory write, teaching,
  Study, Dream, identity, personality, governance, training, Tendril, or
  external action occurred.
- The repair labels conversation provenance; it does not create a public user
  profile or persistent relationship profile.

## Verification

- Python compilation passed for every changed backend module.
- 197 focused and adjacent checks passed across speaker envelopes, Chat trace
  normalization, contextual continuity, conversational teaching, relational
  context, referent/address handling, mobile Chat, and the integrated resident
  Chat shell.
- The mixed-speaker integration case proved that a Codex turn remains Codex,
  a following Aleks turn detects the participant change, and a quoted earlier
  line is attributed back to Codex.
- Frontend TypeScript and Vite build passed. Main bundle: 491.50 kB, gzip
  109.27 kB; no Vite size warning.
- `git diff --check` reported only expected Windows LF/CRLF notices.

## Resume point

Refresh the work journal and active continuation ledger, checkpoint this
source change, then package/reinstall only if Aleks asks to place the repair in
the installed app. A live conversational test is not required before that:
the synthetic mixed-participant path directly verifies the repaired behavior.
