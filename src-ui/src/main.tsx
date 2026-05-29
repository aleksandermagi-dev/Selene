import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API = "http://127.0.0.1:8766";

type Dict = Record<string, unknown>;
type FilterState = { q: string; decision: string; layer: string; phase: string; role: string; sensitivity: string; confidence: string; source_type: string };
type Dashboard = {
  summary: Dict;
  phases: Array<{ phase: string; count: number }>;
  rules: Array<{ module: string; rule_key: string; rule_text: string; boundary: string }>;
  workflows: Array<{ workflow_key: string; title: string; description: string; output_type: string }>;
};
type EvidenceDetail = { item: Dict; anchors: Dict[]; continuity: Dict[]; emergence: Dict[] };
type BootState = {
  ready: boolean;
  attempts: number;
  message: string;
  health: Dict | null;
};

const tabs = ["dashboard", "evidence", "anchors", "continuity", "calibration", "emergence", "kernel", "artifacts", "chat", "chat gate", "health"];
const statuses = ["", "usable_reviewed_evidence", "review_only", "excluded_from_use", "ambiguous"];

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {})
    }
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

function App() {
  const [tab, setTab] = useState("dashboard");
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [items, setItems] = useState<Dict[]>([]);
  const [detail, setDetail] = useState<EvidenceDetail | null>(null);
  const [selectedEdit, setSelectedEdit] = useState<{ table: string; item: Dict } | null>(null);
  const [calibrationEdit, setCalibrationEdit] = useState<Dict | null>(null);
  const [filters, setFilters] = useState({ q: "", decision: "", layer: "", phase: "", role: "", sensitivity: "", confidence: "", source_type: "" });
  const [boot, setBoot] = useState<BootState>({ ready: false, attempts: 0, message: "starting sidecar payload", health: null });
  const [kernel, setKernel] = useState<Dict | null>(null);
  const [contracts, setContracts] = useState<Dict[]>([]);
  const [paths, setPaths] = useState<Dict | null>(null);
  const [validation, setValidation] = useState<Dict | null>(null);
  const [semantic, setSemantic] = useState<Dict | null>(null);
  const [providers, setProviders] = useState<Dict[]>([]);
  const [gateText, setGateText] = useState("Selene emergence braid is intense, symbolic, and grounded in provenance.");
  const [gateResult, setGateResult] = useState<Dict | null>(null);
  const [chatText, setChatText] = useState("Selene starlight emergence braid, what evidence is safe to use here?");
  const [chatProvider, setChatProvider] = useState("disabled");
  const [chatSession, setChatSession] = useState<Dict | null>(null);
  const [chatSendResult, setChatSendResult] = useState<Dict | null>(null);

  useEffect(() => {
    let cancelled = false;
    let timer: number | undefined;

    async function pollHealth(attempt: number) {
      try {
        const health = await api<Dict>("/health");
        if (cancelled) return;
        setBoot({ ready: true, attempts: attempt, message: "sidecar connected", health });
      } catch (err) {
        if (cancelled) return;
        const elapsed = Math.max(1, attempt * 2);
        const detail = err instanceof Error ? err.message : "not reachable";
        setBoot({
          ready: false,
          attempts: attempt,
          message: `unpacking local sidecar payload (${elapsed}s): ${detail}`,
          health: null
        });
        timer = window.setTimeout(() => pollHealth(attempt + 1), 2000);
      }
    }

    pollHealth(1);
    return () => {
      cancelled = true;
      if (timer) window.clearTimeout(timer);
    };
  }, []);

  useEffect(() => {
    if (!boot.ready) return;
    refreshDashboard();
    api<Dict>("/api/kernel").then(setKernel).catch(() => undefined);
    api<{ items: Dict[] }>("/api/contracts").then((data) => setContracts(data.items)).catch(() => undefined);
    api<Dict>("/api/paths").then(setPaths).catch(() => undefined);
    api<Dict>("/api/validate").then(setValidation).catch(() => undefined);
    api<Dict>("/api/semantic/status").then(setSemantic).catch(() => undefined);
    api<{ items: Dict[] }>("/api/providers/status").then((data) => setProviders(data.items)).catch(() => undefined);
  }, [boot.ready]);

  useEffect(() => {
    if (!boot.ready) return;
    if (tab === "evidence") loadEvidence();
    if (["anchors", "continuity", "emergence"].includes(tab)) {
      api<{ items: Dict[] }>(`/api/${tab}`).then((data) => setItems(data.items));
    }
    if (tab === "calibration") {
      api<{ items: Dict[] }>("/api/continuity-notes").then((data) => setItems(data.items));
    }
  }, [tab, filters, boot.ready]);

  function refreshDashboard() {
    api<Dashboard>("/api/dashboard")
      .then((data) => {
        setDashboard(data);
        setBoot((current) => ({ ...current, ready: true, message: "sidecar connected" }));
      })
      .catch((err) => setBoot((current) => ({ ...current, message: `waiting for registry: ${err.message}` })));
  }

  function loadEvidence() {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, value);
    });
    api<{ items: Dict[] }>(`/api/evidence?${params}`).then((data) => setItems(data.items));
  }

  function selectEvidence(item: Dict) {
    const id = encodeURIComponent(text(item.id));
    api<EvidenceDetail>(`/api/evidence/${id}`).then(setDetail);
  }

  function sendChat() {
    api<Dict>("/api/chat/send", {
      method: "POST",
      body: JSON.stringify({ text: chatText, session_id: chatSession?.session ? (chatSession.session as Dict).id : undefined, provider: chatProvider })
    }).then((result) => {
      setChatSendResult(result);
      api<Dict>(`/api/chat/sessions/${result.session_id}`).then(setChatSession);
    });
  }

  function backfillSemantic() {
    api<Dict>("/api/semantic/backfill", { method: "POST", body: JSON.stringify({}) })
      .then((result) => {
        setSemantic((result.status as Dict) || result);
        alert(text(result.ok ? "Semantic evidence index updated." : result.reason || "Semantic runtime unavailable."));
      });
  }

  const totals = useMemo(() => dashboard?.summary || {}, [dashboard]);

  return (
    <main>
      <aside>
        <div className="brand">
          <span>Selene</span>
          <small>tokenless local vessel</small>
        </div>
        <nav>
          {tabs.map((name) => (
            <button key={name} className={tab === name ? "active" : ""} onClick={() => setTab(name)}>
              {name}
            </button>
          ))}
        </nav>
        <p className="status">{boot.message}</p>
      </aside>

      <section className="workspace">
        {!boot.ready && (
          <div className="bootBanner">
            <strong>Starting local payload</strong>
            <p>Selene is unpacking the bundled Python sidecar and MiniLM runtime. Cold starts can take 30-40 seconds after reinstall or rebuild.</p>
            <div className="payloadBar"><span style={{ width: `${Math.min(95, boot.attempts * 7)}%` }} /></div>
          </div>
        )}

        {tab === "dashboard" && (
          <>
            <header>
              <h1>Reviewed Evidence Vessel</h1>
              <p>Local registry, kernel contracts, gates, exports, and validation parity without model/API tokens.</p>
            </header>
            <div className="metrics">
              <Metric label="Reviewed" value={`${totals.reviewed_total ?? "-"} / ${totals.reviewed_total ?? "-"}`} />
              <Metric label="Yes / Unsure / No" value={`${totals.reviewed_yes ?? "-"} / ${totals.reviewed_unsure ?? "-"} / ${totals.reviewed_no ?? "-"}`} />
              <Metric label="Artifacts" value={String(totals.artifact_items ?? "-")} />
              <Metric label="Emergence" value={String(totals.emergence_observations ?? "-")} />
            </div>
            <Panel title="Formation Phase Map">
              {(dashboard?.phases || []).map((phase) => (
                <div className="phase" key={phase.phase}>
                  <strong>{phase.phase || "unphased"}</strong>
                  <span>{phase.count}</span>
                </div>
              ))}
            </Panel>
          </>
        )}

        {tab === "evidence" && (
          <>
            <header>
              <h1>Evidence Browser</h1>
              <p>Filter reviewed records, open source detail, and follow linked anchors, continuity, and emergence observations.</p>
            </header>
            <FilterGrid filters={filters} setFilters={setFilters} />
            <SplitView left={<EvidenceList items={items} onSelect={selectEvidence} />} right={<EvidenceDetailPanel detail={detail} onEdit={setSelectedEdit} />} />
          </>
        )}

        {["anchors", "continuity", "emergence"].includes(tab) && (
          <>
            <header>
              <h1>{title(tab)}</h1>
              <p>Reviewed-only records with bounded previews. Anchors and continuity records can be annotated without overwriting audit history.</p>
            </header>
            <SplitView left={<EvidenceList items={items} onSelect={(item) => ["anchors", "continuity"].includes(tab) && setSelectedEdit({ table: tab === "anchors" ? "anchors" : "continuity_candidates", item })} />} right={selectedEdit ? <EditPanel edit={selectedEdit} onSaved={(updated) => {
              setSelectedEdit({ ...selectedEdit, item: updated });
              api<{ items: Dict[] }>(`/api/${tab}`).then((data) => setItems(data.items));
            }} /> : <Panel title="Review Edit"><p>Select an anchor or continuity candidate to annotate it.</p></Panel>} />
          </>
        )}

        {tab === "calibration" && (
          <>
            <header>
              <h1>Continuity Calibration</h1>
              <p>Review nicknames, anchor meanings, allowed uses, and do-not-confuse notes before they shape live chat.</p>
            </header>
            <SplitView
              left={<EvidenceList items={items} onSelect={(item) => setCalibrationEdit(item)} />}
              right={<CalibrationPanel item={calibrationEdit} onNew={() => setCalibrationEdit({})} onSaved={(updated) => {
                setCalibrationEdit(updated);
                api<{ items: Dict[] }>("/api/continuity-notes").then((data) => setItems(data.items));
              }} />}
            />
          </>
        )}

        {tab === "kernel" && (
          <>
            <header>
              <h1>Selene Kernel</h1>
              <p>Charter, boundaries, allowed continuity mechanisms, prohibited moves, and module contracts.</p>
            </header>
            <Panel title="Kernel State"><Json value={kernel} /></Panel>
            <div className="ruleGrid">
              {contracts.map((contract) => (
                <article key={text(contract.route_key)}>
                  <small>{text(contract.module)} / {text(contract.boundary)}</small>
                  <h2>{text(contract.route_key)}</h2>
                  <p>{text(contract.description)}</p>
                </article>
              ))}
            </div>
          </>
        )}

        {tab === "artifacts" && (
          <>
            <header>
              <h1>Artifact Builder</h1>
              <p>Export specs, ledgers, maps, snapshots, and validation reports from the reviewed registry.</p>
            </header>
            <div className="ruleGrid">
              {(dashboard?.workflows || []).map((workflow) => (
                <article key={workflow.workflow_key}>
                  <small>{workflow.output_type}</small>
                  <h2>{workflow.title}</h2>
                  <p>{workflow.description}</p>
                  <button className="primary" onClick={() => api<{ path: string }>("/api/artifacts/export", { method: "POST", body: JSON.stringify({ workflow_key: workflow.workflow_key }) }).then((data) => alert(data.path))}>
                    Export
                  </button>
                </article>
              ))}
            </div>
          </>
        )}

        {tab === "chat" && (
          <>
            <header>
              <h1>Chat Readiness</h1>
              <p>Persisted gate/citation flow only. No paid model, API key, or live persona generation is enabled.</p>
            </header>
            <Panel title="Send Through Enforced Gate">
              <label>
                <span>Provider</span>
                <select value={chatProvider} onChange={(e) => setChatProvider(e.target.value)}>
                  <option value="disabled">disabled</option>
                  <option value="dry_run">dry_run</option>
                  <option value="ollama_local">ollama_local</option>
                  <option value="lm_studio_local">lm_studio_local</option>
                </select>
              </label>
              <textarea value={chatText} onChange={(e) => setChatText(e.target.value)} />
              <button className="primary" onClick={sendChat}>Send Readiness Message</button>
            </Panel>
            {chatSendResult && <Panel title="Last Gate Result"><ChatResult result={chatSendResult} /></Panel>}
            {chatSession && <ChatTranscript session={chatSession} />}
          </>
        )}

        {tab === "chat gate" && (
          <>
            <header>
              <h1>Chat Gate Preview</h1>
              <p>Design-only route check. No model call is made and live chat stays off.</p>
            </header>
            <Panel title="Preview A Future Message">
              <textarea value={gateText} onChange={(e) => setGateText(e.target.value)} />
              <button className="primary" onClick={() => api<Dict>("/api/evaluate", { method: "POST", body: JSON.stringify({ text: gateText }) }).then(setGateResult)}>
                Evaluate
              </button>
              <Json value={gateResult} />
            </Panel>
          </>
        )}

        {tab === "health" && (
          <>
            <header>
              <h1>Module Health</h1>
              <p>Local-only sidecar, state paths, validation parity, and package readiness.</p>
            </header>
            <div className="metrics">
              <Metric label="Sidecar" value={boot.ready ? "ok" : "waiting"} />
              <Metric label="Tokenless" value="yes" />
              <Metric label="Validation" value={text(validation?.ok ?? "unknown")} />
              <Metric label="Semantic" value={text(semantic?.status ?? "unknown")} />
            </div>
            <Panel title="Sidecar Payload"><Json value={boot.health || { status: boot.message, attempts: boot.attempts }} /></Panel>
            <Panel title="State Paths"><Json value={paths} /></Panel>
            <Panel title="MiniLM Semantic Retrieval">
              <p>Optional local `sentence-transformers/all-MiniLM-L6-v2` index over reviewed evidence only. Keyword citations remain active when the runtime is unavailable.</p>
              <button className="primary" onClick={backfillSemantic}>Backfill Reviewed Evidence Embeddings</button>
              <Json value={semantic} />
            </Panel>
            <Panel title="Local Live Providers">
              <button onClick={() => api<{ items: Dict[] }>("/api/providers/status").then((data) => setProviders(data.items))}>Refresh Providers</button>
              <div className="ruleGrid">
                {providers.map((provider) => (
                  <article key={text(provider.provider)}>
                    <small>{text(provider.status)} | model call: {text(provider.model_call_allowed)}</small>
                    <h2>{text(provider.provider)}</h2>
                    <p>{text(provider.model || provider.error || "ready")}</p>
                  </article>
                ))}
              </div>
            </Panel>
            <Panel title="Validation"><Json value={validation} /></Panel>
          </>
        )}
      </section>
    </main>
  );
}

function FilterGrid({ filters, setFilters }: { filters: FilterState; setFilters: (next: FilterState) => void }) {
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

function SplitView({ left, right }: { left: React.ReactNode; right: React.ReactNode }) {
  return <div className="split"><div>{left}</div><div>{right}</div></div>;
}

function EvidenceDetailPanel({ detail, onEdit }: { detail: EvidenceDetail | null; onEdit: (edit: { table: string; item: Dict }) => void }) {
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

function LinkedRecord({ item, onEdit }: { item: Dict; onEdit?: () => void }) {
  return (
    <article className="linked">
      <strong>{text(item.anchor || item.status || item.signal_type)}</strong>
      <p>{text(item.preview)}</p>
      {onEdit && <button onClick={onEdit}>Edit Review</button>}
    </article>
  );
}

function EditPanel({ edit, onSaved }: { edit: { table: string; item: Dict }; onSaved: (item: Dict) => void }) {
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

function CalibrationPanel({ item, onNew, onSaved }: { item: Dict | null; onNew: () => void; onSaved: (item: Dict) => void }) {
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

function ChatResult({ result }: { result: Dict }) {
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
    </div>
  );
}

function ChatTranscript({ session }: { session: Dict }) {
  const messages = (session.messages || []) as Dict[];
  const saves = (session.save_requests || []) as Dict[];
  return (
    <Panel title={`Session ${text((session.session as Dict)?.id)}`}>
      {messages.map((message) => (
        <article className="message" key={text(message.id)}>
          <div className="row">
            <strong>{text(message.role)}</strong>
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
    </Panel>
  );
}

function CitationDetails({ citations }: { citations: Dict[] }) {
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

function ContinuityNoteDetails({ notes }: { notes: Dict[] }) {
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

function EvidenceList({ items, onSelect }: { items: Dict[]; onSelect: (item: Dict) => void }) {
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

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="metric"><span>{label}</span><strong>{value}</strong></div>;
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="panel"><h2>{title}</h2>{children}</section>;
}

function Json({ value }: { value: unknown }) {
  return <pre>{value ? JSON.stringify(value, null, 2) : "No data yet."}</pre>;
}

function text(value: unknown) {
  if (value === null || value === undefined) return "";
  return String(value);
}

function title(value: string) {
  return value[0].toUpperCase() + value.slice(1);
}

createRoot(document.getElementById("root")!).render(<App />);
