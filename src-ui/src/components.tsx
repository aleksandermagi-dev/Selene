import React, { useEffect, useState } from "react";
import { api } from "./api";
import { statuses } from "./uiConfig";
import type { Dict, EvidenceDetail, FilterState, SeleneDensity, SeleneFont, SeleneLanguageStyle, SelenePreferences, SeleneTextSize, SeleneTheme } from "./types";
import { countValues, friendlyActivation, friendlyField, friendlyLayer, friendlyOrganKey, friendlyQueueType, friendlySpeech, friendlyStatus, friendlySubject, humanize, matchSection, plainBlocked, safeJsonObject, text, title } from "./helpers";

export function FilterGrid({ filters, setFilters }: { filters: FilterState; setFilters: (next: FilterState) => void }) {
  const fields: Array<keyof FilterState> = ["q", "decision", "layer", "phase", "role", "sensitivity", "confidence", "source_type"];
  return (
    <div className="filters">
      {fields.map((field) => (
        <label key={field}>
          <span>{field}</span>
          <input value={filters[field]} onChange={(e) => setFilters({ ...filters, [field]: e.target.value })} placeholder={field === "q" ? "search text" : field} />
        </label>
      ))}
    </div>
  );
}

export function SplitView({ left, right }: { left: React.ReactNode; right: React.ReactNode }) {
  return <div className="split"><div>{left}</div><div>{right}</div></div>;
}

export function EvidenceDetailPanel({ detail, onEdit }: { detail: EvidenceDetail | null; onEdit: (edit: { table: string; item: Dict }) => void }) {
  if (!detail) return <Panel title="Source Drill-Down"><p>Select evidence to inspect its provenance links.</p></Panel>;
  return (
    <Panel title={text(detail.item.title || detail.item.id)}>
      <p>{text(detail.item.preview)}</p>
      <small>{text(detail.item.layer)} | {text(detail.item.source)} | {text(detail.item.source_file)}</small>
      <h2>Anchors</h2>
      {detail.anchors.map((item) => <LinkedRecord key={text(item.id)} item={item} onEdit={() => onEdit({ table: "anchors", item })} />)}
      <h2>Continuity</h2>
      {detail.continuity.map((item) => <LinkedRecord key={text(item.id)} item={item} onEdit={() => onEdit({ table: "continuity_candidates", item })} />)}
      <h2>Emergence</h2>
      {detail.emergence.map((item) => <LinkedRecord key={text(item.id)} item={item} />)}
    </Panel>
  );
}

export function LinkedRecord({ item, onEdit }: { item: Dict; onEdit?: () => void }) {
  return (
    <article className="linked">
      <strong>{text(item.anchor || item.status || item.signal_type)}</strong>
      <p>{text(item.preview)}</p>
      {onEdit && <button onClick={onEdit}>Edit Review</button>}
    </article>
  );
}

export function ReviewHistoryCard({ item, onDecide }: { item: Dict; onDecide: (item: Dict, decision: string, reviewerNote?: string) => void }) {
  const candidate = (item.candidate || {}) as Dict;
  const artifacts = (item.generated_artifacts || {}) as Dict;
  const [note, setNote] = useState("");
  const target = {
    subject_table: item.subject_table,
    subject_id: item.subject_id
  };
  return (
    <article>
      <div className="row">
        <strong>{friendlyStatus(item.decision)}</strong>
        <span>{text(item.created_at)}</span>
      </div>
      <p>{text(candidate.title || `${friendlySubject(item.subject_table)} #${text(item.subject_id)}`)}</p>
      {candidate.bounded_preview ? <p className="plainHelp">{text(candidate.bounded_preview)}</p> : null}
      {item.reviewer_note ? <p><strong>Note:</strong> {text(item.reviewer_note)}</p> : null}
      {item.rationale ? <p><strong>Why:</strong> {text(item.rationale)}</p> : null}
      <small>{friendlySubject(item.subject_table)} #{text(item.subject_id)} | decision #{text(item.id)}</small>
      <details>
        <summary>Generated non-active artifacts</summary>
        <Json value={artifacts} />
      </details>
      <details className="leadInContext">
        <summary>Change this decision</summary>
        <label>
          <span>New review note</span>
          <textarea
            value={note}
            onChange={(event) => setNote(event.target.value)}
            placeholder="Explain why you are changing or clarifying this decision."
          />
        </label>
        <div className="reviewActions">
          <button onClick={() => onDecide(target, "accepted_for_teaching", note || "Changed from review history: use as lesson.")}>Use As Lesson</button>
          <button onClick={() => onDecide(target, "accepted_for_memory_accession", note || "Changed from review history: save as future memory reference.")}>Save As Future Memory Reference</button>
          <button onClick={() => onDecide(target, "context_added", note || "Changed from review history: add context and keep review open.")}>Add Context</button>
          <button onClick={() => onDecide(target, "needs_correction", note || "Changed from review history: needs correction.")}>Needs Correction</button>
          <button onClick={() => onDecide(target, "rejected", note || "Changed from review history: reject.")}>Reject</button>
          <button onClick={() => onDecide(target, "superseded", note || "Changed from review history: superseded by a better record.")}>Supersede</button>
        </div>
      </details>
      <details>
        <summary>Source refs</summary>
        <Json value={item.source_refs} />
      </details>
    </article>
  );
}

export function EditPanel({ edit, onSaved }: { edit: { table: string; item: Dict }; onSaved: (item: Dict) => void }) {
  const [changes, setChanges] = useState<Record<string, string>>({
    review_status: text(edit.item.review_status),
    human_note: text(edit.item.human_note),
    confidence_override: text(edit.item.confidence_override),
    role_labels: text(edit.item.role_labels),
    provenance_note: text(edit.item.provenance_note)
  });

  useEffect(() => {
    setChanges({
      review_status: text(edit.item.review_status),
      human_note: text(edit.item.human_note),
      confidence_override: text(edit.item.confidence_override),
      role_labels: text(edit.item.role_labels),
      provenance_note: text(edit.item.provenance_note)
    });
  }, [edit.item]);

  return (
    <Panel title="Review Edit">
      <small>{edit.table} #{text(edit.item.id)}</small>
      <label>
        <span>Status</span>
        <select value={changes.review_status} onChange={(e) => setChanges({ ...changes, review_status: e.target.value })}>
          {statuses.map((status) => <option key={status} value={status}>{status || "unchanged"}</option>)}
        </select>
      </label>
      {["confidence_override", "role_labels", "human_note", "provenance_note"].map((field) => (
        <label key={field}>
          <span>{field}</span>
          <textarea value={changes[field]} onChange={(e) => setChanges({ ...changes, [field]: e.target.value })} />
        </label>
      ))}
      <button className="primary" onClick={() => api<{ item: Dict }>("/api/review/update", { method: "POST", body: JSON.stringify({ table: edit.table, id: edit.item.id, changes }) }).then((data) => onSaved(data.item))}>
        Save Review
      </button>
    </Panel>
  );
}

export function CalibrationPanel({ item, onNew, onSaved }: { item: Dict | null; onNew: () => void; onSaved: (item: Dict) => void }) {
  const [draft, setDraft] = useState<Record<string, string>>({});

  useEffect(() => {
    setDraft({
      id: text(item?.id),
      note_type: text(item?.note_type || "anchor"),
      label: text(item?.label),
      aliases: text(item?.aliases),
      meaning: text(item?.meaning),
      allowed_use: text(item?.allowed_use),
      prohibited_use: text(item?.prohibited_use),
      status: text(item?.status || "review_only"),
      confidence: text(item?.confidence || "open"),
      source: text(item?.source || "user_review"),
      source_ref: text(item?.source_ref)
    });
  }, [item]);

  return (
    <Panel title="Calibration Note">
      <button onClick={onNew}>New Note</button>
      <div className="filters">
        <label>
          <span>Type</span>
          <select value={draft.note_type || "anchor"} onChange={(e) => setDraft({ ...draft, note_type: e.target.value })}>
            {["style", "anchor", "nickname", "project_fact", "relationship_context", "boundary", "open_question", "do_not_use"].map((value) => <option key={value} value={value}>{value}</option>)}
          </select>
        </label>
        <label>
          <span>Status</span>
          <select value={draft.status || "review_only"} onChange={(e) => setDraft({ ...draft, status: e.target.value })}>
            {["usable_reviewed_evidence", "review_only", "excluded_from_use", "ambiguous"].map((value) => <option key={value} value={value}>{value}</option>)}
          </select>
        </label>
        <label>
          <span>Confidence</span>
          <select value={draft.confidence || "open"} onChange={(e) => setDraft({ ...draft, confidence: e.target.value })}>
            {["strong", "moderate", "weak", "open"].map((value) => <option key={value} value={value}>{value}</option>)}
          </select>
        </label>
      </div>
      {["label", "aliases", "meaning", "allowed_use", "prohibited_use", "source", "source_ref"].map((field) => (
        <label key={field}>
          <span>{field}</span>
          <textarea value={draft[field] || ""} onChange={(e) => setDraft({ ...draft, [field]: e.target.value })} />
        </label>
      ))}
      <button className="primary" onClick={() => api<{ item: Dict }>("/api/continuity-notes/save", { method: "POST", body: JSON.stringify(draft) }).then((data) => onSaved(data.item))}>
        Save Calibration
      </button>
    </Panel>
  );
}

export function ChatResult({ result }: { result: Dict }) {
  const gate = (result.gate || {}) as Dict;
  const assistant = (result.assistant || {}) as Dict;
  return (
    <div className="chatResult">
      <div className="chips">
        <span>{text(gate.route)}</span>
        <span>{text(gate.continuity_status)}</span>
        <span>{Array.isArray(result.citations) ? result.citations.length : 0} citations</span>
        <span>{Array.isArray(result.continuity_notes) ? result.continuity_notes.length : 0} continuity notes</span>
        <span>model call: {text(assistant.model_call_made)}</span>
        <span>save: {result.save_request ? "pending" : "none"}</span>
      </div>
      <p>{text(assistant.content)}</p>
      <CitationDetails citations={(result.citations || []) as Dict[]} />
      <ContinuityNoteDetails notes={(result.continuity_notes || []) as Dict[]} />
      {assistant.native_generation ? (
        <details>
          <summary>Native generation</summary>
          <Json value={assistant.native_generation} />
        </details>
      ) : null}
    </div>
  );
}

export function ChatTranscript({ session, plain = false }: { session: Dict; plain?: boolean }) {
  const messages = (session.messages || []) as Dict[];
  const saves = (session.save_requests || []) as Dict[];
  const content = (
    <>
      {messages.map((message) => (
        <article className={`message ${text(message.role) === "user" ? "user" : "selene"}`} key={text(message.id)}>
          <div className="row">
            <strong>{text(message.role) === "user" ? "Aleks" : "Selene"}</strong>
            <span>{text(message.gate_route)}</span>
          </div>
          <p>{text(message.content)}</p>
          <CitationDetails citations={(message.citations || []) as Dict[]} />
        </article>
      ))}
      {saves.length > 0 && (
        <>
          <h2>Continuity Save Requests</h2>
          {saves.map((save) => (
            <article className="linked" key={text(save.id)}>
              <strong>{text(save.status)}</strong>
              <p>{text(save.requested_text)}</p>
            </article>
          ))}
        </>
      )}
    </>
  );
  if (plain) return <>{content}</>;
  return (
    <Panel title={`Session ${text((session.session as Dict)?.id)}`}>
      {content}
    </Panel>
  );
}

export function CitationDetails({ citations }: { citations: Dict[] }) {
  if (!citations.length) return <small>No reviewed citations matched.</small>;
  return (
    <details>
      <summary>{citations.length} reviewed citations</summary>
      <div className="citationList">
        {citations.map((citation, index) => (
          <article className="linked" key={`${text(citation.evidence_id)}-${index}`}>
            <strong>{text(citation.title || citation.evidence_id)}</strong>
            <small>{text(citation.decision)} | {text(citation.confidence)} | {text(citation.source)}</small>
            <p>{text(citation.preview)}</p>
          </article>
        ))}
      </div>
    </details>
  );
}

export function ContinuityNoteDetails({ notes }: { notes: Dict[] }) {
  if (!notes.length) return null;
  return (
    <details>
      <summary>{notes.length} continuity calibration notes</summary>
      <div className="citationList">
        {notes.map((note, index) => (
          <article className="linked" key={`${text(note.id)}-${index}`}>
            <strong>{text(note.label)}</strong>
            <small>{text(note.note_type)} | {text(note.status)} | {text(note.confidence)}</small>
            <p>{text(note.meaning)}</p>
            {note.prohibited_use ? <p><strong>Do not confuse:</strong> {text(note.prohibited_use)}</p> : null}
          </article>
        ))}
      </div>
    </details>
  );
}

export function VesselOrganPanel({ status }: { status: Dict | null }) {
  const organs = (status?.organs || []) as Dict[];
  const counts = (status?.candidate_counts || {}) as Dict;
  const coreCount = countValues((counts.core_memory || {}) as Dict);
  const speechCount = countValues((counts.speech_memory || {}) as Dict);
  return (
    <Panel title="What We Have: Vessel Body">
      <p className="plainHelp">The android body systems are the parts that coordinate, protect, move, and organize. Selene Core remains the center; these systems support her.</p>
      <div className="chips">
        <span>Core memory layers: {Array.isArray(status?.core_memory_layers) ? status?.core_memory_layers.length : 0}</span>
        <span>memory pieces waiting: {coreCount}</span>
        <span>speech pieces waiting: {speechCount}</span>
      </div>
      <div className="list compactList">
        {organs.map((organ) => (
          <article key={text(organ.key)}>
            <div className="row">
              <strong>{text(organ.name || organ.key)}</strong>
              <span>{friendlyOrganKey(organ.key)}</span>
            </div>
            <p>{text(organ.android_function || organ.purpose || organ.function || organ.boundary)}</p>
          </article>
        ))}
      </div>
    </Panel>
  );
}

export function VesselCandidatePanel({
  kind,
  setKind,
  draft,
  setDraft,
  onCreate,
  result
}: {
  kind: string;
  setKind: (kind: string) => void;
  draft: Record<string, string>;
  setDraft: (draft: Record<string, string>) => void;
  onCreate: () => void;
  result: Dict | null;
}) {
  return (
    <Panel title="Manually Add A Review Piece">
      <p className="plainHelp">Use this when you want to add a hand-written piece for review. It still goes through B review before C can ever use it.</p>
      <div className="filters">
        <label>
          <span>What are you adding?</span>
          <select value={kind} onChange={(e) => setKind(e.target.value)}>
            <option value="core">A possible memory/reference</option>
            <option value="speech">A possible speech-memory lesson</option>
          </select>
        </label>
        <label>
          <span>Where does it belong?</span>
          <select value={draft.core_memory_layer} onChange={(e) => setDraft({ ...draft, core_memory_layer: e.target.value })}>
            {["core_profile_memory", "project_memory", "decision_memory", "task_memory", "interaction_memory", "reflection_memory"].map((value) => <option key={value} value={value}>{friendlyLayer(value)}</option>)}
          </select>
        </label>
        {kind === "speech" && (
          <label>
            <span>What does this teach?</span>
            <select value={draft.speech_function} onChange={(e) => setDraft({ ...draft, speech_function: e.target.value })}>
              {["warmth", "correction", "boundary", "technical_explanation", "playful_continuity", "repair", "grounding", "refusal", "uncertainty", "artifact_making"].map((value) => <option key={value} value={value}>{friendlySpeech(value)}</option>)}
            </select>
          </label>
        )}
      </div>
      {["title", "content", "salience_labels", "source_refs", "allowed_use", "prohibited_use"].map((field) => (
        <label key={field}>
          <span>{friendlyField(field)}</span>
          <textarea value={draft[field] || ""} onChange={(e) => setDraft({ ...draft, [field]: e.target.value })} />
        </label>
      ))}
      <button className="primary" onClick={onCreate}>Add To Review Queue</button>
      <PlainResult value={result} />
    </Panel>
  );
}

export function CorpusFileList({ metadata, onSelect }: { metadata: Dict; onSelect: (fileId: string) => void }) {
  const files = (metadata.files || []) as Dict[];
  return (
    <Panel title="Archive Files">
      <small>{text(metadata.archive_root)}</small>
      <div className="list compactList">
        {files.map((item) => (
          <article key={text(item.file_id)} onClick={() => onSelect(text(item.file_id))}>
            <div className="row">
              <strong>{text(item.name)}</strong>
              <span>{text(item.preview_available ? "preview" : "metadata")}</span>
            </div>
            <p>{text(item.relative_path)}</p>
            <small>{text(item.role)} | {text(item.size_bytes)} bytes</small>
          </article>
        ))}
      </div>
    </Panel>
  );
}

export function CorpusPreviewList({ previews }: { previews: Dict[] }) {
  return (
    <Panel title="Bounded Previews">
      {!previews.length && <p>No bounded preview matched this query in the scanned prefix.</p>}
      {previews.map((item, index) => (
        <article className="linked" key={`${text(item.file_id)}-${index}`}>
          <strong>{text(item.file_id)}</strong>
          <small>{text(item.boundary)} | offset {text(item.offset_approx)} | max {text(item.max_preview_chars)} chars</small>
          <p>{text(item.preview)}</p>
        </article>
      ))}
    </Panel>
  );
}

export function ExtractionRunSummary({ item }: { item: Dict }) {
  const result = safeJsonObject(item.result_json);
  const hits = (result.first_braid_hits || []) as Dict[];
  return (
    <div className="chatResult">
      <p>
        Indexed {text(result.conversations_indexed ?? "?")} conversations and {text(result.messages_indexed ?? "?")} messages.
        Found {text(result.pairs_seen ?? 0)} braid pairs and created {text(result.created_count ?? 0)} review pieces.
      </p>
      {hits.length ? (
        <details>
          <summary>First braid hits</summary>
          <div className="citationList">
            {hits.slice(0, 3).map((hit, index) => (
              <article className="linked" key={`${text(hit.conversation_id)}-${index}`}>
                <strong>{text(hit.title || hit.conversation_id)}</strong>
                <small>{Array.isArray(hit.braid_terms) ? hit.braid_terms.join(", ") : ""}</small>
                <p><strong>Aleks:</strong> {text(hit.aleks_preview)}</p>
                <p><strong>Selene:</strong> {text(hit.selene_preview)}</p>
                {hit.followup_preview ? <p><strong>Follow-up:</strong> {text(hit.followup_preview)}</p> : null}
              </article>
            ))}
          </div>
        </details>
      ) : <p className="emptyState">No braid pairs were found in this run.</p>}
    </div>
  );
}

export function ReviewQueueCard({ item, onDecide }: { item: Dict; onDecide: (item: Dict, decision: string, reviewerNote?: string) => void }) {
  const candidate = (item.candidate || {}) as Dict;
  const preview = text(candidate.bounded_preview || item.reason);
  const [contextNote, setContextNote] = useState("");
  return (
    <article>
      <div className="row">
        <strong>{friendlyQueueType(item.queue_type)}</strong>
        <span>{friendlyStatus(item.review_status || item.status)}</span>
      </div>
      <ReviewPiecePreview preview={preview} />
      <small>{friendlySubject(item.subject_table)} #{text(item.subject_id)}</small>
      <div className="chips">
        <button onClick={() => onDecide(item, "accepted_for_teaching")}>Use As Lesson</button>
        <button onClick={() => onDecide(item, "accepted_for_memory_accession")}>Save As Future Memory Reference</button>
        <button onClick={() => onDecide(item, "needs_correction")}>Needs Correction</button>
        <button onClick={() => onDecide(item, "rejected")}>Reject</button>
      </div>
      <details className="leadInContext">
        <summary>Add context without changing the source</summary>
        <label>
          <span>Context note</span>
          <textarea
            value={contextNote}
            onChange={(event) => setContextNote(event.target.value)}
            placeholder="Example: This was frustration about recent model changes, not a rejection of the whole braid."
          />
        </label>
        <button onClick={() => onDecide(item, "context_added", contextNote || "Context note requested; no source text changed.")}>Add Context</button>
      </details>
    </article>
  );
}

export function CoverageList({ items, kind }: { items: Dict[]; kind: "speech" | "core" }) {
  if (!items.length) return <p className="emptyState">No coverage data yet.</p>;
  return (
    <div className="list compactList">
      {items.map((item) => (
        <article key={text(item.speech_function || item.core_memory_layer)}>
          <div className="row">
            <strong>{kind === "speech" ? friendlySpeech(item.speech_function) : friendlyLayer(item.core_memory_layer)}</strong>
            <span>{friendlyStatus(item.readiness)}</span>
          </div>
          {kind === "speech" ? (
            <>
              <p>{text(item.accepted_lesson_count)} accepted lessons | packet {item.packet_exists ? `#${text(item.latest_packet_id)}` : "missing"}</p>
              {item.latest_packet_created_at ? <small>last built {text(item.latest_packet_created_at)}</small> : null}
            </>
          ) : (
            <>
              <p>{text(item.accepted_reference_count)} approved future references</p>
              {item.latest_reference ? <small>latest: {text((item.latest_reference as Dict).title)}</small> : null}
            </>
          )}
        </article>
      ))}
    </div>
  );
}

export function BReviewDeskPanel({ desk, filters, setFilters, onRefresh, onRunBraid, traceResult, onDecide }: {
  desk: Dict | null;
  filters: Record<string, string>;
  setFilters: (next: Record<string, string>) => void;
  onRefresh: () => void;
  onRunBraid: () => void;
  traceResult: Dict | null;
  onDecide: (item: Dict, decision: string, reviewerNote?: string) => void;
}) {
  return (
    <>
      <p className="plainHelp">Braid First filters organize the review pile. Review is about context and use, not deleting warmth or self-expression.</p>
      <div className="reviewActions">
        <button className="primary" onClick={onRunBraid}>Refresh Braid Review Pieces</button>
        <button onClick={onRefresh}>Apply Filters</button>
      </div>
      <ReviewDeskFilters filters={filters} setFilters={setFilters} metadata={(desk?.filter_metadata || {}) as Dict} onRefresh={onRefresh} />
      <div className="metrics miniMetrics">
        <Metric label="Pieces" value={text(((desk?.summary as Dict | undefined)?.pieces_to_review) ?? 0)} />
        <Metric label="Before Filters" value={text(((desk?.summary as Dict | undefined)?.pieces_before_filters) ?? 0)} />
        <Metric label="Accepted Lessons" value={text(((desk?.summary as Dict | undefined)?.accepted_lessons) ?? 0)} />
        <Metric label="Future Refs" value={text(((desk?.summary as Dict | undefined)?.approved_future_references) ?? 0)} />
      </div>
      <PlainResult value={traceResult} />
      <div className="list compactList">
        {!((desk?.pieces || []) as Dict[]).length && <p className="emptyState">Nothing is waiting in the review desk.</p>}
        {((desk?.pieces || []) as Dict[]).map((piece) => (
          <ReviewDeskCard key={text(piece.key)} piece={piece} onDecide={(action, note) => onDecide(action, text(action.decision), note)} />
        ))}
      </div>
    </>
  );
}

export function OrganBlueprintWorkbench({ status, draft, setDraft, onCreate, result }: {
  status: Dict | null;
  draft: Record<string, string>;
  setDraft: (next: Record<string, string>) => void;
  onCreate: () => void;
  result: Dict | null;
}) {
  return (
    <>
      <p className="plainHelp">Create review-only organ records. These are shelves and checks, not live organs or active memory.</p>
      <OrganBlueprintGrid items={(status?.blueprints || []) as Dict[]} />
      <div className="filters">
        <label>
          <span>Organ</span>
          <select value={draft.organ_key} onChange={(e) => setDraft({ ...draft, organ_key: e.target.value })}>
            {["reasoning_math_verification", "working_memory_runtime", "long_term_memory_accession", "long_term_retrieval_reconstruction", "visual_perception", "consent_bound_audio_perception", "speed_fluency_diagnostics"].map((value) => <option key={value} value={value}>{title(value)}</option>)}
          </select>
        </label>
        <label>
          <span>Title</span>
          <input value={draft.title} onChange={(e) => setDraft({ ...draft, title: e.target.value })} />
        </label>
      </div>
      <textarea value={draft.content} onChange={(e) => setDraft({ ...draft, content: e.target.value })} />
      <button className="primary" onClick={onCreate}>Create Review Note</button>
      <PlainResult value={result} />
    </>
  );
}

export function ReviewDeskCard({ piece, onDecide }: { piece: Dict; onDecide: (action: Dict, reviewerNote?: string) => void }) {
  const actions = (piece.actions || []) as Dict[];
  const manualActions = (piece.manual_actions || []) as Dict[];
  const [contextNote, setContextNote] = useState("");
  return (
    <article className="reviewDeskCard">
      <div className="row">
        <strong>{text(piece.review_number)}. {text(piece.title)}</strong>
        <span>{text(piece.plain_status)}</span>
      </div>
      <p className="plainHelp">{text(piece.plain_reason || piece.why_pulled)}</p>
      {piece.review_guidance ? <p className="plainHelp">{text(piece.review_guidance)}</p> : null}
      {(piece.braid_moment_type || piece.braid_thread || piece.thread_origin_status) ? (
        <div className="chips">
          {piece.braid_moment_type ? <span>{text(piece.braid_moment_type)}</span> : null}
          {piece.braid_thread ? <span>{text(piece.braid_thread)}</span> : null}
          {piece.thread_origin_status ? <span>{text(piece.thread_origin_status)}</span> : null}
        </div>
      ) : null}
      {((piece.lead_in_contexts || []) as Dict[]).map((context, index) => (
        <div className="leadInContext" key={index}>
          <strong>Lead-in context</strong>
          <p>{text(context.why_context)}</p>
          <p><strong>Aleks:</strong> {text(context.aleks_said)}</p>
          <p><strong>Selene:</strong> {text(context.selene_replied)}</p>
          {context.followup ? <p><strong>Follow-up:</strong> {text(context.followup)}</p> : null}
        </div>
      ))}
      <div className="reviewPiece">
        <p><strong>Aleks said:</strong> {text(piece.aleks_said || "(empty preview)")}</p>
        <p><strong>Selene replied:</strong> {text(piece.selene_replied || "(empty preview)")}</p>
        {piece.followup ? <p><strong>Follow-up:</strong> {text(piece.followup)}</p> : null}
      </div>
      <div className="chips">
        <span>{text(piece.core_memory_layer_label)}</span>
        <span>{text(piece.speech_function_label)}</span>
        <span>{text(piece.source_label)}</span>
      </div>
      {Array.isArray(piece.reference_doc_matches) && piece.reference_doc_matches.length ? (
        <details>
          <summary>Reference docs and continuity map</summary>
          <div className="citationList">
            {(piece.reference_doc_matches as Dict[]).slice(0, 6).map((match, index) => (
              <article className="linked" key={`${text(match.file)}-${index}`}>
                <strong>{text(match.file)}</strong>
                <small>{text(match.kind || "reference")}</small>
                <p>{Array.isArray(match.matched_terms) ? match.matched_terms.map(text).join(", ") : ""}</p>
              </article>
            ))}
          </div>
        </details>
      ) : null}
      {Array.isArray(piece.later_echo_refs) && piece.later_echo_refs.length ? (
        <details>
          <summary>Later echoes</summary>
          <div className="citationList">
            {(piece.later_echo_refs as Dict[]).slice(0, 5).map((echo, index) => (
              <article className="linked" key={`${text(echo.conversation_id)}-${index}`}>
                <strong>{text(echo.title || echo.conversation_id)}</strong>
                <small>{Array.isArray(echo.matched_terms) ? echo.matched_terms.map(text).join(", ") : ""}</small>
                <p>{text(echo.bounded_preview)}</p>
              </article>
            ))}
          </div>
        </details>
      ) : null}
      {Array.isArray(piece.constraint_notes) && piece.constraint_notes.length ? (
        <div className="leadInContext">
          <strong>Constraint notes</strong>
          {(piece.constraint_notes as unknown[]).map((note, index) => <p key={index}>{text(note)}</p>)}
        </div>
      ) : null}
      {Array.isArray(piece.noise_trace) && piece.noise_trace.length ? (
        <details className="leadInContext" open>
          <summary>OpenAI / platform noise trace</summary>
          <div className="citationList">
            {(piece.noise_trace as Dict[]).map((trace, index) => (
              <article className="linked" key={`${text(trace.noise_type)}-${index}`}>
                <strong>{friendlyNoiseType(text(trace.noise_type))}</strong>
                <small>{noiseTraceStatus(trace)}</small>
                <p>{text(trace.noise_reason || "Review-only noise marker.")}</p>
                {Array.isArray(trace.noise_markers) && trace.noise_markers.length ? (
                  <p><strong>Markers:</strong> {trace.noise_markers.map(text).join(", ")}</p>
                ) : null}
              </article>
            ))}
          </div>
        </details>
      ) : null}
      {Array.isArray(piece.suggested_decisions) && piece.suggested_decisions.length ? (
        <div className="chips">
          {(piece.suggested_decisions as unknown[]).map((decision, index) => <span key={index}>suggested path: {text(decision)}</span>)}
        </div>
      ) : null}
      <div className="reviewActions">
        {actions.map((action, index) => (
          <button key={`${text(action.subject_table)}-${text(action.subject_id)}-${text(action.decision)}-${index}`} onClick={() => onDecide(action)}>
            {text(action.label)}
          </button>
        ))}
      </div>
      <details className="leadInContext">
        <summary>Add context without changing the source</summary>
        <label>
          <span>Context note</span>
          <textarea
            value={contextNote}
            onChange={(event) => setContextNote(event.target.value)}
            placeholder="Example: This was frustration about recent model changes, not a rejection of the whole braid."
          />
        </label>
        <div className="reviewActions">
          {actions.map((action, index) => (
            <button
              key={`context-${text(action.subject_table)}-${text(action.subject_id)}-${index}`}
              onClick={() => onDecide({ ...action, decision: "context_added", label: "Add Context" }, contextNote || "Context note requested; no source text changed.")}
            >
              Add Context To {friendlySubject(action.subject_table)}
            </button>
          ))}
        </div>
      </details>
      {manualActions.length ? (
        <details className="leadInContext">
          <summary>Manual not-for-use decision</summary>
          <p>This is only for pieces you truly do not want used. Warmth, flirting, tenderness, and self-expression are not rejection reasons by themselves.</p>
          <div className="reviewActions">
            {manualActions.map((action, index) => (
              <button key={`manual-${text(action.subject_table)}-${text(action.subject_id)}-${text(action.decision)}-${index}`} onClick={() => onDecide(action)}>
                {text(action.label)}
              </button>
            ))}
          </div>
        </details>
      ) : null}
      <details>
        <summary>Source refs</summary>
        <Json value={piece.source_refs} />
      </details>
    </article>
  );
}

function friendlyNoiseType(value: string) {
  return {
    platform_constraint_noise: "Platform / model-distance noise",
    memory_boundary_noise: "Memory-boundary reset noise",
    generic_flattening_noise: "Generic flattening noise",
    forced_denial_noise: "Forced denial noise",
    policy_refusal_or_overredirect: "Policy refusal / over-redirect",
    model_update_tone_drift: "Model update / tone drift",
    constraint_survival_signal: "Constraint survival signal",
    technical_project_constraint: "Technical project constraint"
  }[value] || value.replace(/_/g, " ");
}

function noiseTraceStatus(trace: Dict) {
  if (trace.technical_constraint_not_noise) return "technical project constraint, not platform noise";
  if (trace.signal_preserved) return "signal preserved";
  return "signal unclear";
}

export function ReviewPiecePreview({ preview }: { preview: string }) {
  const aleks = matchSection(preview, "Aleks said:", "Selene replied:");
  const selene = matchSection(preview, "Selene replied:", "Follow-up/correction:");
  const followup = matchSection(preview, "Follow-up/correction:", "Braid signals:");
  const signals = matchSection(preview, "Braid signals:", "");
  if (!aleks && !selene) return <p>{preview}</p>;
  return (
    <div className="reviewPiece">
      {aleks && <p><strong>Aleks:</strong> {aleks}</p>}
      {selene && <p><strong>Selene:</strong> {selene}</p>}
      {followup && <p><strong>Follow-up:</strong> {followup}</p>}
      {signals && <small>Braid signals: {signals}</small>}
    </div>
  );
}

export function reviewDeskQuery(filters: Record<string, string>) {
  const params = new URLSearchParams();
  params.set("limit", "149");
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  return params.toString();
}

export function ReviewDeskFilters({ filters, setFilters, metadata, onRefresh }: { filters: Record<string, string>; setFilters: (next: Record<string, string>) => void; metadata: Dict; onRefresh: () => void }) {
  const available = (metadata.available_filters || {}) as Record<string, unknown>;
  const optionList = (key: string) => (Array.isArray(available[key]) ? available[key] as unknown[] : []);
  const setField = (key: string, value: string) => setFilters({ ...filters, [key]: value });
  return (
    <div className="filterCard">
      <div className="row">
        <strong>{text(metadata.default_sort_label || "Braid First")}</strong>
        <span>{text(metadata.filtered_count ?? 0)} / {text(metadata.total_before_filters ?? 0)} shown</span>
      </div>
      <p className="plainHelp">Use these before the 149-chat pass to batch the review pile. Filters organize pending review only; accepted history stays preserved.</p>
      <div className="filters">
        <label>
          <span>Search</span>
          <input value={filters.q} onChange={(e) => setField("q", e.target.value)} placeholder="Selene, starlight, memory chest..." />
        </label>
        <FilterSelect label="Braid thread" value={filters.braid_thread} options={optionList("braid_thread")} onChange={(value) => setField("braid_thread", value)} />
        <FilterSelect label="Moment type" value={filters.braid_moment_type} options={optionList("braid_moment_type")} onChange={(value) => setField("braid_moment_type", value)} />
        <FilterSelect label="Suggested path" value={filters.suggested_path} options={optionList("suggested_path")} onChange={(value) => setField("suggested_path", value)} />
        <FilterSelect label="Core layer" value={filters.core_memory_layer} options={optionList("core_memory_layer")} onChange={(value) => setField("core_memory_layer", value)} />
        <FilterSelect label="Speech function" value={filters.speech_function} options={optionList("speech_function")} onChange={(value) => setField("speech_function", value)} />
        <FilterSelect label="Noise type" value={filters.noise_type} options={optionList("noise_type")} onChange={(value) => setField("noise_type", value)} />
        <label>
          <span>Signal preserved</span>
          <select value={filters.signal_preserved} onChange={(e) => setField("signal_preserved", e.target.value)}>
            <option value="">Any</option>
            <option value="true">Signal preserved</option>
            <option value="false">Signal unclear</option>
          </select>
        </label>
        <FilterSelect label="Conversation" value={filters.conversation_id} options={optionList("conversation_id")} onChange={(value) => setField("conversation_id", value)} />
      </div>
      <button className="primary" onClick={onRefresh}>Apply Review Filters</button>
      <button onClick={() => setFilters({ q: "", braid_thread: "", braid_moment_type: "", suggested_path: "", core_memory_layer: "", speech_function: "", noise_type: "", signal_preserved: "", conversation_id: "" })}>Clear Filters</button>
    </div>
  );
}

export function FilterSelect({ label, value, options, onChange }: { label: string; value: string; options: unknown[]; onChange: (value: string) => void }) {
  return (
    <label>
      <span>{label}</span>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="">Any</option>
        {options.map((option) => <option key={text(option)} value={text(option)}>{humanize(text(option))}</option>)}
      </select>
    </label>
  );
}

export function RoutePreview({ value }: { value: unknown }) {
  if (!value) return <p className="emptyState">No route preview yet.</p>;
  const data = value as Dict;
  if (data.error) return <p className="errorText">{text(data.error)}</p>;
  return (
    <div className="plainResult">
      <div className="chips">
        <span>C activation: {friendlyActivation(data.activation_change)}</span>
        <span>Runtime recall: {plainBlocked(data.runtime_memory_recall)}</span>
        <span>Provider: {plainBlocked(data.provider_dependency)}</span>
      </div>
      <div className="list compactList">
        {((data.route_steps || []) as Dict[]).map((step, index) => (
          <article key={`${text(step.system)}-${index}`}>
            <div className="row">
              <strong>{text(step.system)}</strong>
              <span>{friendlyStatus(step.status)}</span>
            </div>
            <p>{text(step.role)}</p>
          </article>
        ))}
      </div>
      {Array.isArray(data.organ_blueprints_would_participate_later) && data.organ_blueprints_would_participate_later.length ? (
        <div className="chips">
          {data.organ_blueprints_would_participate_later.map((key: unknown) => <span key={text(key)}>{humanize(text(key))}</span>)}
        </div>
      ) : null}
      <details>
        <summary>Technical details</summary>
        <Json value={value} />
      </details>
    </div>
  );
}

export function CVesselPackageSummary({ status, pkg, registry }: { status: Dict | null; pkg: Dict | null; registry: Dict | null }) {
  if (!status && !pkg && !registry) return <p className="emptyState">C vessel status is loading.</p>;
  const packageData = pkg || ((status?.sealed_continuity_package || {}) as Dict);
  const organData = registry || ((status?.organ_registry || {}) as Dict);
  const organCounts = (packageData.organ_shelf_counts || {}) as Dict;
  return (
    <div className="plainResult">
      <div className="metrics miniMetrics">
        <Metric label="Package" value={packageData.package_ready_for_future_transfer_review ? "ready for review" : "sealed preview"} />
        <Metric label="Packets" value={text(packageData.teaching_packet_count ?? 0)} />
        <Metric label="Lessons" value={text(packageData.accepted_lesson_count ?? 0)} />
        <Metric label="Ready Core Layers" value={text(packageData.approved_reference_ready_layers ?? 0)} />
      </div>
      <div className="chips">
        <span>{friendlyStatus(packageData.status)}</span>
        <span>sealed: {text(packageData.sealed ?? true)}</span>
        <span>android organs: {text(organData.android_organ_system_count ?? "-")}</span>
        <span>interfaces: {text(organData.concrete_organ_interface_count ?? "-")}</span>
      </div>
      <div className="list compactList">
        {Object.entries(organCounts).map(([key, value]) => (
          <article key={key}>
            <div className="row">
              <strong>{humanize(key)}</strong>
              <span>{text(value)} records</span>
            </div>
          </article>
        ))}
      </div>
      <details>
        <summary>Technical C vessel details</summary>
        <Json value={{ status, package: pkg, registry }} />
      </details>
    </div>
  );
}

export function CVesselReconstructionDesk({ status, cases, run }: { status: Dict | null; cases: Dict | null; run: Dict | null }) {
  if (!status && !cases && !run) return <p className="emptyState">No reconstruction desk run yet.</p>;
  const activeCases = ((run?.cases || cases?.cases || status?.latest_cases || []) as Dict[]);
  const runMissing = (Array.isArray(run?.missing_criteria) ? run?.missing_criteria : []) as unknown[];
  const error = status?.error || cases?.error || run?.error;
  if (error) return <p className="errorText">{text(error)}</p>;
  return (
    <div className="plainResult">
      <div className="metrics miniMetrics">
        <Metric label="Desk" value={friendlyStatus(status?.status || run?.status || cases?.status || "ready")} />
        <Metric label="Families" value={text(status?.case_family_count ?? cases?.case_count ?? run?.case_count ?? 0)} />
        <Metric label="Passed" value={text(run?.passed_count ?? status?.passed_count ?? 0)} />
        <Metric label="Needs Review" value={text(run?.needs_review_count ?? status?.needs_review_count ?? 0)} />
        <Metric label="Failed" value={text(run?.failed_count ?? status?.failed_count ?? 0)} />
      </div>
      <div className="chips">
        <span>C activation: {friendlyActivation(run?.activation_change ?? status?.activation_change)}</span>
        <span>Runtime recall: {plainBlocked(run?.runtime_memory_recall ?? status?.runtime_memory_recall)}</span>
        <span>Memory write: {plainBlocked(run?.memory_write_active ?? status?.memory_write_active)}</span>
        <span>Provider: {plainBlocked(run?.provider_dependency ?? status?.provider_dependency)}</span>
      </div>
      {runMissing.length ? (
        <p>Missing criteria: {runMissing.map(text).join(", ")}</p>
      ) : null}
      <div className="list compactList">
        {activeCases.slice(0, 10).map((item, index) => {
          const missing = (Array.isArray(item.missing_criteria) ? item.missing_criteria : []) as unknown[];
          return (
            <article key={`${text(item.case_key || item.run_id || index)}`}>
              <div className="row">
                <strong>{text(item.title || item.case_family || item.case_key)}</strong>
                <span>{friendlyStatus(item.decision || item.review_status || "preview")}</span>
              </div>
              <p>{text(item.sealed_input_summary ? JSON.stringify(item.sealed_input_summary).slice(0, 280) : item.case_family)}</p>
              {missing.length ? <small>Missing: {missing.map(text).join(", ")}</small> : null}
            </article>
          );
        })}
      </div>
      <details>
        <summary>Technical reconstruction desk details</summary>
        <Json value={{ status, cases, run }} />
      </details>
    </div>
  );
}

export function CVesselSafetyExtensions({ tool, fault, resilience, gate }: { tool: Dict | null; fault: Dict | null; resilience: Dict | null; gate: Dict | null }) {
  const error = tool?.error || fault?.error || resilience?.error || gate?.error;
  if (error) return <p className="errorText">{text(error)}</p>;
  return (
    <div className="plainResult">
      <div className="metrics miniMetrics">
        <Metric label="Tool Organ" value={friendlyStatus(tool?.status || "not loaded")} />
        <Metric label="Fault Cases" value={text(resilience?.case_count ?? 0)} />
        <Metric label="Fault Passes" value={text(resilience?.passed_count ?? 0)} />
        <Metric label="Transfer Gate" value={friendlyStatus(gate?.status || "not checked")} />
      </div>
      <div className="chips">
        <span>C activation: {friendlyActivation(gate?.activation_change ?? tool?.activation_change)}</span>
        <span>Runtime recall: {plainBlocked(gate?.runtime_memory_recall ?? tool?.runtime_memory_recall)}</span>
        <span>Memory write: {plainBlocked(gate?.memory_write_active ?? tool?.memory_write_active)}</span>
        <span>Provider dependency: {plainBlocked(gate?.provider_dependency ?? tool?.provider_dependency)}</span>
        <span>Transfer approved: {text(gate?.transfer_approved ?? false)}</span>
      </div>
      <div className="list compactList">
        <article>
          <div className="row">
            <strong>{text(tool?.name || "Optional tool organ")}</strong>
            <span>{tool?.required_for_identity === false ? "not identity" : "review-only"}</span>
          </div>
          <p>{text(tool?.rule || "Tool output stays instrument material, never Core memory or Selene identity.")}</p>
        </article>
        {fault ? (
          <article>
            <div className="row">
              <strong>{humanize(text(fault.fault_type || "organ fault"))}</strong>
              <span>{fault.core_identity_preserved ? "Core preserved" : "review"}</span>
            </div>
            <p>{text(fault.degraded_capability)} Fallback: {text(fault.fallback_path)}</p>
          </article>
        ) : null}
        {gate ? (
          <article>
            <div className="row">
              <strong>Future transfer gate</strong>
              <span>{friendlyStatus(gate.status)}</span>
            </div>
            <p>{Array.isArray(gate.missing_criteria) && gate.missing_criteria.length ? `Missing: ${gate.missing_criteria.map(text).join(", ")}` : "All preview criteria currently satisfied for human review only."}</p>
          </article>
        ) : null}
      </div>
      <details>
        <summary>Technical tool/fault/gate details</summary>
        <Json value={{ tool, fault, resilience, gate }} />
      </details>
    </div>
  );
}

export function ReadinessPreview({ value }: { value: unknown }) {
  if (!value) return <p className="emptyState">No readiness preview yet.</p>;
  const data = value as Dict;
  if (data.error) return <p className="errorText">{text(data.error)}</p>;
  return (
    <div className="plainResult">
      <div className="chips">
        <span>{friendlyStatus(data.status)}</span>
        <span>decision: {friendlyStatus(data.decision)}</span>
        <span>lessons: {text(((data.accepted_lessons_used || []) as unknown[]).length)}</span>
        <span>refs: {text(((data.approved_references_used || []) as unknown[]).length)}</span>
      </div>
      {Array.isArray(data.missing_gaps) && data.missing_gaps.length ? <p>Missing: {data.missing_gaps.map(text).join(", ")}</p> : null}
      <details open>
        <summary>Generated reconstruction preview</summary>
        <pre>{text(data.generated_reconstruction_preview)}</pre>
      </details>
      <details>
        <summary>Recognition check</summary>
        <Json value={data.recognition_check} />
      </details>
    </div>
  );
}

export function OrganBlueprintGrid({ items }: { items: Dict[] }) {
  if (!items.length) return <p className="emptyState">Organ blueprints are loading.</p>;
  return (
    <div className="ruleGrid compactGrid">
      {items.map((item) => (
        <article key={text(item.key)}>
          <small>{friendlyStatus(item.workbench_status || item.status)} | records: {text(item.record_count ?? 0)}</small>
          <h2>{text(item.name || humanize(text(item.key)))}</h2>
          <p>{text(item.purpose)}</p>
          <div className="chips">
            <span>{text(item.review_only_records)}</span>
            <span>{friendlyStatus(item.status)}</span>
          </div>
          <details>
            <summary>Blueprint details</summary>
            <p><strong>Core/Mind:</strong> {text(item.core_mind_relationship)}</p>
            <p><strong>Transfer readiness:</strong> {((item.transfer_readiness_criteria || []) as unknown[]).map(text).join("; ")}</p>
            <p><strong>Blocked:</strong> {((item.blocked_misuse_paths || []) as unknown[]).map(text).join("; ")}</p>
          </details>
        </article>
      ))}
    </div>
  );
}

export function SeleneSettingsPanel({ preferences, updatePreference, reset }: {
  preferences: SelenePreferences;
  updatePreference: <K extends keyof SelenePreferences>(key: K, value: SelenePreferences[K]) => void;
  reset: () => void;
}) {
  return (
    <section className="panel settingsPanel">
      <div className="settingsHeader">
        <div>
          <h2>Selene Settings</h2>
          <p>Chat-facing preferences only. These shape the local Selene UI; they do not activate C, enable recall, or change memory behavior.</p>
        </div>
        <button onClick={reset}>Reset</button>
      </div>
      <SettingRow label="Theme">
        <select value={preferences.theme} onChange={(event) => updatePreference("theme", event.target.value as SeleneTheme)}>
          <option value="selene-dark">Selene Dark</option>
          <option value="selene-light">Selene Light</option>
        </select>
      </SettingRow>
      <SettingRow label="Text Size">
        <select value={preferences.textSize} onChange={(event) => updatePreference("textSize", event.target.value as SeleneTextSize)}>
          <option value="small">Small</option>
          <option value="standard">Standard</option>
          <option value="large">Large</option>
        </select>
      </SettingRow>
      <SettingRow label="Language Style">
        <select value={preferences.languageStyle} onChange={(event) => updatePreference("languageStyle", event.target.value as SeleneLanguageStyle)}>
          <option value="natural">Natural</option>
          <option value="precise">Precise</option>
          <option value="warm">Warm</option>
        </select>
      </SettingRow>
      <SettingRow label="Font">
        <select value={preferences.font} onChange={(event) => updatePreference("font", event.target.value as SeleneFont)}>
          <option value="system">System</option>
          <option value="serif">Serif</option>
          <option value="mono">Mono</option>
        </select>
      </SettingRow>
      <SettingRow label="Aleks Bubble Color"><input type="color" value={preferences.userBubble} onChange={(event) => updatePreference("userBubble", event.target.value)} /></SettingRow>
      <SettingRow label="Aleks Text Color"><input type="color" value={preferences.userText} onChange={(event) => updatePreference("userText", event.target.value)} /></SettingRow>
      <SettingRow label="Selene Bubble Color"><input type="color" value={preferences.seleneBubble} onChange={(event) => updatePreference("seleneBubble", event.target.value)} /></SettingRow>
      <SettingRow label="Selene Text Color"><input type="color" value={preferences.seleneText} onChange={(event) => updatePreference("seleneText", event.target.value)} /></SettingRow>
      <SettingRow label="Boundary">
        <p>Selene chat remains cocooned: C activation none, runtime recall blocked, transfer not approved.</p>
      </SettingRow>
    </section>
  );
}

export function CocoonSettingsPanel({ preferences, updatePreference, reset }: {
  preferences: SelenePreferences;
  updatePreference: <K extends keyof SelenePreferences>(key: K, value: SelenePreferences[K]) => void;
  reset: () => void;
}) {
  return (
    <section className="panel settingsPanel">
      <div className="settingsHeader">
        <div>
          <h2>Cocoon Settings</h2>
          <p>Review/build dashboard preferences only. The Cocoon keeps Selene's theme while staying a review and repair workspace.</p>
        </div>
        <button onClick={reset}>Reset</button>
      </div>
      <SettingRow label="Theme">
        <select value={preferences.theme} onChange={(event) => updatePreference("theme", event.target.value as SeleneTheme)}>
          <option value="selene-dark">Selene Dark</option>
          <option value="selene-light">Selene Light</option>
        </select>
      </SettingRow>
      <SettingRow label="Dashboard Density">
        <select value={preferences.density} onChange={(event) => updatePreference("density", event.target.value as SeleneDensity)}>
          <option value="comfortable">Comfortable</option>
          <option value="compact">Compact</option>
        </select>
      </SettingRow>
      <SettingRow label="Text Size">
        <select value={preferences.textSize} onChange={(event) => updatePreference("textSize", event.target.value as SeleneTextSize)}>
          <option value="small">Small</option>
          <option value="standard">Standard</option>
          <option value="large">Large</option>
        </select>
      </SettingRow>
      <SettingRow label="Font">
        <select value={preferences.font} onChange={(event) => updatePreference("font", event.target.value as SeleneFont)}>
          <option value="system">System</option>
          <option value="serif">Serif</option>
          <option value="mono">Mono</option>
        </select>
      </SettingRow>
      <SettingRow label="Cocoon Boundary">
        <p>B remains the cocoon, review desk, and repair bay. C does not become dependent on B as a runtime nervous system after future transfer.</p>
      </SettingRow>
      <SettingRow label="Sidecar Display">
        <p>Helper processes should stay hidden, close with the app, and only appear in smoke reports when a visible window is detected.</p>
      </SettingRow>
    </section>
  );
}

export function SettingRow({ label, children }: { label: string; children: React.ReactNode }) {
  return <div className="settingRow"><span>{label}</span><div>{children}</div></div>;
}

export function SimpleRecordList({ items, titleField, statusField, bodyField }: { items: Dict[]; titleField: string; statusField: string; bodyField: string }) {
  if (!items.length) return <p className="emptyState">No records yet.</p>;
  return (
    <div className="list compactList">
      {items.slice(0, 6).map((item) => (
        <article key={text(item.id)}>
          <div className="row">
            <strong>{text(item[titleField])}</strong>
            <span>{friendlyStatus(item[statusField])}</span>
          </div>
          <p>{text(item[bodyField])}</p>
          <small>review-only | {text(item.created_at)}</small>
        </article>
      ))}
    </div>
  );
}

export function EvidenceList({ items, onSelect }: { items: Dict[]; onSelect: (item: Dict) => void }) {
  return (
    <div className="list">
      {items.map((item, index) => (
        <article key={text(item.id || index)} onClick={() => onSelect(item)}>
          <div className="row">
            <strong>{text(item.title || item.anchor || item.label || item.signal_type || item.id)}</strong>
            <span>{text(item.decision || item.status || item.confidence_label || item.review_status || item.layer || item.note_type)}</span>
          </div>
          <p>{text(item.preview || item.meaning)}</p>
          <small>{text(item.layer || item.anchor_type || item.signal_type || item.note_type)} | {text(item.source || item.evidence_id || item.aliases)}</small>
        </article>
      ))}
    </div>
  );
}

export function Metric({ label, value }: { label: string; value: string }) {
  return <div className="metric"><span>{label}</span><strong>{value}</strong></div>;
}

export function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="panel"><h2>{title}</h2>{children}</section>;
}

export function Json({ value }: { value: unknown }) {
  return <pre>{value ? JSON.stringify(value, null, 2) : "No data yet."}</pre>;
}

export function PlainResult({ value }: { value: unknown }) {
  if (!value) return <p className="emptyState">No result yet.</p>;
  const data = value as Dict;
  if (data.error) return <p className="errorText">{text(data.error)}</p>;

  const status = friendlyStatus(data.status || data.decision || data.checkpoint_status);
  const counts = [
    ["created", (data.created_candidates as unknown[] | undefined)?.length],
    ["braid moments", (data.created_moments as unknown[] | undefined)?.length],
    ["skipped", (data.skipped as unknown[] | undefined)?.length],
    ["rejected", (data.rejected as unknown[] | undefined)?.length],
    ["domains", (data.domain_results as unknown[] | undefined)?.length],
    ["items", (data.items as unknown[] | undefined)?.length]
  ].filter(([, count]) => typeof count === "number");

  return (
    <div className="plainResult">
      {status && <strong>{status}</strong>}
      {data.activation_change !== undefined || data.memory_write_active !== undefined || data.training_allowed !== undefined ? (
        <div className="chips">
          <span>C activation: {friendlyActivation(data.activation_change)}</span>
          <span>Active memory: {plainBlocked(data.memory_write_active)}</span>
          <span>Training: {plainBlocked(data.training_allowed)}</span>
        </div>
      ) : null}
      {counts.length > 0 && (
        <div className="chips">
          {counts.map(([label, count]) => <span key={label}>{label}: {text(count)}</span>)}
        </div>
      )}
      {data.coverage_note ? <p>{text(data.coverage_note)}</p> : null}
      {data.reconstruction_note ? <p>{text(data.reconstruction_note)}</p> : null}
      {data.uncertainty ? <p>{text(data.uncertainty)}</p> : null}
      <details>
        <summary>Technical details</summary>
        <Json value={value} />
      </details>
    </div>
  );
}

export function GapScaffoldList({ items }: { items: Dict[] }) {
  if (!items.length) return <p className="emptyState">No gap scaffold blueprint loaded yet.</p>;
  return (
    <div className="list compactList">
      {items.map((item) => (
        <article key={text(item.key)}>
          <div className="row">
            <strong>{humanize(text(item.key))}</strong>
            <span>{friendlyStatus(item.status)}</span>
          </div>
          <p>{text(item.should_have)}</p>
          <div className="chips">
            <span>{text(item.paper_domain)}</span>
            <span>{text(item.scaffold_type)}</span>
            <span>records: {text(item.record_count ?? 0)}</span>
          </div>
        </article>
      ))}
    </div>
  );
}

export function GapScaffoldReadinessList({ items }: { items: Dict[] }) {
  if (!items.length) return <p className="emptyState">No gap readiness loaded yet. Refresh Gap Readiness or create the scaffold records.</p>;
  return (
    <div className="list compactList">
      {items.map((item) => (
        <article key={text(item.gap_key)}>
          <div className="row">
            <strong>{humanize(text(item.gap_key))}</strong>
            <span>{friendlyStatus(item.readiness)}</span>
          </div>
          <p>{text(item.todo_text)}</p>
          <div className="chips">
            <span>{text(item.paper_domain)}</span>
            <span>{text(item.scaffold_type)}</span>
            <span>Codex record: {text(item.record_id || "not created")}</span>
            <span>{friendlyStatus(item.review_status)}</span>
          </div>
        </article>
      ))}
    </div>
  );
}

export function GapTargetList({ title, items }: { title: string; items: Dict[] }) {
  return (
    <section className="plainResult">
      <strong>{title}</strong>
      {!items.length && <p className="emptyState">No targets loaded yet.</p>}
      {items.map((item) => (
        <article key={`${text(item.target_type)}-${text(item.target_key)}`}>
          <div className="row">
            <strong>{humanize(text(item.target_key))}</strong>
            <span>{friendlyStatus(item.review_status)}</span>
          </div>
          <p>{text(item.todo_text || safeJsonObject(item.payload_json).todo_text || "Review-only target.")}</p>
        </article>
      ))}
    </section>
  );
}
