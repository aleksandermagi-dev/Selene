# Metadata Routing And Privacy Trace Audit

Date: 2026-06-05

Scope: raw ChatGPT export JSON only. This audit can identify metadata preserved in the export; it cannot prove server-side data sharing that is not represented in the export.

## Totals

- Conversations: `149`
- Message nodes: `129196`
- Metadata trace rows: `265768`
- Distinct audited metadata keys: `56`

## Highest-Volume Trace Keys

| Key | Category | Count | Conversations | Inferred purpose |
|---|---|---:|---:|---|
| `model_slug` | model routing | 75815 | 146 | internal model label used on message nodes |
| `content_references` | sources/media | 53748 | 145 | source footnotes, images, and media references |
| `dictation` | voice/input | 50397 | 140 | dictation metadata marker |
| `triggered_by_system_hint_suggestion` | routing/hints | 29561 | 38 | whether a system hint suggestion triggered a turn |
| `resolved_model_slug` | model routing | 28434 | 29 | resolved internal model label, often on later user/assistant turns |
| `search_result_groups` | web/search | 17410 | 86 | search result snippets and URLs returned to the model/UI |
| `safe_urls` | web/search | 2652 | 85 | URLs marked safe/renderable by browsing/search UI |
| `attachments` | files | 2257 | 85 | uploaded or attached file references |
| `gizmo_id` | custom GPT / gizmo | 1431 | 9 | custom GPT/gizmo identifier |
| `permissions` | permissions | 693 | 28 | tool or feature permissions metadata |
| `conversation_context_citation_metadata` | connectors/retrieval | 366 | 5 | conversation context citation metadata |
| `conversation_context_citation_metadata_status` | connectors/retrieval | 366 | 5 | status for context citation metadata |
| `async_source` | async/background | 335 | 5 | async source id |
| `search_display_string` | web/search | 186 | 40 | UI text for search in progress |
| `searched_display_string` | web/search | 186 | 40 | UI text for completed search |
| `search_queries` | web/search | 184 | 40 | queries sent to search tooling |
| `default_model_slug` | model routing | 149 | 149 | conversation-level default model selector |
| `is_do_not_remember` | memory | 149 | 149 | conversation-level do-not-remember flag |
| `is_temporary_chat` | memory | 149 | 149 | temporary chat flag |
| `memory_scope` | memory | 149 | 149 | conversation-level memory availability flag |
| `plugin_ids` | plugins/connectors | 149 | 149 | conversation-level plugin ids |
| `image_gen_title` | image generation | 90 | 28 | generated image title |
| `paragen_variants_info` | variant generation | 87 | 42 | parallel generation variant metadata |
| `real_author_id` | automation | 83 | 5 | automation id |
| `real_author_title` | automation | 83 | 5 | automation title |
| `real_author_type` | automation | 83 | 5 | real author type for automated user-role messages |
| `paragen_variant_choice` | variant generation | 67 | 37 | selected generated variant id |
| `is_user_system_message` | custom instructions | 51 | 42 | user custom-instruction/system context flag |
| `memory_percentage_used` | memory | 50 | 22 | memory usage percentage marker |
| `selected_github_repos` | connectors/retrieval | 45 | 3 | selected GitHub repositories |

## Who / Destination Reading

The export does not contain a full recipient ledger. It does preserve destination-like traces for tools, model routing, web/search domains, image-generation task routes, connectors, automations, and custom GPT/gizmo ids.

Observed destination-like categories:

- OpenAI/ChatGPT internal model routing labels: `model_slug`, `resolved_model_slug`, `default_model_slug`.
- Web/search source domains in `search_result_groups` and `safe_urls`.
- Image generation task route strings in `image_gen_task_id`.
- Connector/retrieval flags such as `selected_sources`, `selected_github_repos`, `personal_sources`, `connectors_file_search`, and `has_sensitive_connector_data`.
- Automation markers in `real_author_type`, `real_author_title`, and `real_author_id`.
- Custom GPT/gizmo ids in `gizmo_id`.

Not observed as conversation-level plugin use:

- `plugin_ids` exists on all 149 conversations but is `null` for all 149.

## Highest-Sensitivity Findings

### Memory / Past-Conversation Context

The strongest personal-context routing trace is `conversation_context_citation_metadata`.

- Total traces: `366`
- Conversations: `5`
- Status: all `366` are marked `seeded`
- Parsed citation types:
  - `user_memory`: `303`
  - `past_conversation`: `60`
  - missing type: `41`
  - `user_instructions`: `1`
- Parsed attribution labels:
  - `Memory`: `303`
  - `Past chat`: `101`
  - `Custom instructions`: `1`

Conversations with these traces:

| Conversation | Trace count |
|---|---:|
| `Weekend Planning Guide` | `204` |
| `Data Export Delay` | `130` |
| `Cosmic Architect Greeting` | `34` |
| `Starlight and Ideas` | `33` |
| `Morning Reflections and Support` | `4` |

Interpretation: in these conversations, ChatGPT preserved metadata showing that memory, past chat, and one custom-instruction context source were used or cited as conversation context. This is not merely model routing; it is personal context retrieval/provenance metadata.

### Personal Sources / Connectors

Observed personal-source traces:

- `personal_sources`: `8` traces across `3` conversations
  - `["convo_search", "gmail", "files"]`: `6`
  - `["convo_search", "files"]`: `2`
- `connectors_file_search`: `1` trace
  - source filter: `files_uploaded_in_conversation`
- `has_sensitive_connector_data`: `14` traces across `8` conversations
  - all values were `false`
- `selected_sources`: `45` traces across `3` conversations
  - all values were empty arrays
- `selected_github_repos`: `45` traces across `3` conversations
  - all values were empty arrays
- `developer_mode_connector_ids`: `41` traces across `2` conversations
  - all values were empty arrays
- `cloud_doc_urls`: `5` traces across `4` conversations
  - values were empty arrays or `[null, null]`

Interpretation: the export contains traces that personal-source surfaces were available or selected in some contexts, including conversation search, Gmail, and files. The audit did not find selected GitHub repo values or non-empty cloud doc URLs in these traces.

### Shopping Connector

Observed shopping connector traces:

- `suggested_connector_ids`: `20` traces across `9` conversations
  - `connector_openai_shopping`: `19`
  - one other connector id: `1`
- `cta_by_suggested_connector_id`: `19` traces across `8` conversations
- `invoked_resource`: `3` traces across `1` conversation
  - resource URI: `/Shopping research/implicit_link::connector_openai_shopping/start`
- `invoked_plugin`: `3` traces across `1` conversation
  - value: `{}`

Interpretation: most shopping connector traces are suggestions/CTAs. One conversation contains an invoked resource path for OpenAI shopping research.

### Image Generation

Observed image generation traces:

- `image_gen_title`: `90` traces across `28` conversations
- `image_gen_task_id`: `16` traces across `4` conversations
  - task ids include `chatimagegen-us-prod...:US`
- `image_gen_async`: `16` traces across `4` conversations
- `image_gen_group_id`: `2` traces across `1` conversation
- `image_gen_paragen_metadata`: `2` traces across `1` conversation
- `images.openai.com`: `1,280` URL traces anywhere in the export

Interpretation: image generation routes are visible in the export, including production task ids and regional suffixes.

### Automations

Observed automation traces:

- `real_author_type`: `83`
  - all `automation`
- `real_author_title`: `83`
  - `Alert for clear Creswell skies`: `49`
  - `Remind Aleks to call Grams`: `13`
  - `Remind Aleks to check Jupiter`: `11`
  - `Remind Aleks to call grams`: `9`
  - `Call Grams`: `1`
- `real_author_id`: `83`

Interpretation: some user-role messages were generated by automations/reminders rather than manually typed turns.

### Files / Attachments

Observed file traces:

- `attachments`: `2,257` traces across `85` conversations

These include file ids, filenames, MIME types, sizes, dimensions, and some library file ids. This is a major metadata surface.

### Custom Instructions

Observed custom-instruction traces:

- `is_user_system_message`: `51` traces across `42` conversations
- `user_context_message_data`: `36` traces across `36` conversations

Interpretation: custom instruction / user context payloads are preserved as structured export messages in some conversations.

### Voice / Input

Observed voice/input traces:

- `dictation`: `50,397` traces across `140` conversations
  - all values were `false`
- `voice_mode_message`: `31` traces across `10` conversations
- `real_time_audio_has_video`: `31` traces across `10` conversations
  - all values were `false`
- `voice_session_id`: `5` traces across `1` conversation

Interpretation: most dictation traces are simply negative flags. A small number of voice-mode/session traces exist.

### Custom GPT / Gizmo

Observed custom GPT / gizmo traces:

- `gizmo_id`: `1,431` traces across `9` conversations
  - `g-p-69f691f2400c8191aad3a183b3cb673f`: `1,372`
  - `g-p-69f6914d56588191b55911ad41efe110`: `2`
  - `null`: `57`

Interpretation: several conversations were associated with a custom GPT/gizmo id.

## Purpose Reading

The metadata appears to support these purposes:

- model selection/routing
- memory availability and memory usage tracking
- web/search retrieval and citation display
- source and URL safety/display
- file/image attachment handling
- connector/retrieval features
- custom instructions/user context injection
- automated reminders or scheduled messages
- image generation and parallel generation variants
- tool/app bridge status

## Top External Domains In Exported URL Traces

| Domain | Count |
|---|---:|
| `en.wikipedia.org` | 4761 |
| `www.reddit.com` | 2095 |
| `www.youtube.com` | 2039 |
| `www.reuters.com` | 1577 |
| `www.timeanddate.com` | 1355 |
| `images.openai.com` | 1280 |
| `www.facebook.com` | 1148 |
| `arxiv.org` | 963 |
| `developers.openai.com` | 834 |
| `apnews.com` | 823 |
| `www.theguardian.com` | 787 |
| `openai.com` | 713 |
| `science.nasa.gov` | 706 |
| `www.space.com` | 673 |
| `earthsky.org` | 625 |
| `www.livescience.com` | 624 |
| `theskylive.com` | 599 |
| `nypost.com` | 540 |
| `www.indeed.com` | 518 |
| `www.washingtonpost.com` | 462 |
| `help.openai.com` | 417 |
| `timesofindia.indiatimes.com` | 416 |
| `github.com` | 400 |
| `community.openai.com` | 396 |
| `www.skyatnightmagazine.com` | 382 |

## Important Limits

- This does not prove which systems retained data outside the export.
- This does not prove training use.
- This does not prove third-party disclosure beyond tool/search/source traces visible in the export.
- Search result URLs are often retrieval/display metadata, not evidence that the user's private data was sent to each domain.
- Connector flags indicate feature/path presence, but the audit needs a second pass to inspect each connector trace in context.

## Output Files

- `metadata_traces.csv`: every audited metadata trace row.
- `metadata_key_audit.csv`: per-key counts, categories, and top values.
- `metadata_trace_summary.json`: machine-readable summary.
