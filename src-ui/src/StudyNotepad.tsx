import { useMemo, useState } from "react";

import { api } from "./api";
import { friendlyStatus, safeJsonObject, text } from "./helpers";
import type { Dict } from "./types";


type StudyNotepadProps = {
  session: Dict;
  onUpdated: (result: Dict) => void;
};

const OPEN_CLARIFICATION_STATES = new Set(["unclear", "question_forming", "question_ready", "reopened"]);

function noteKindLabel(value: unknown) {
  const labels: Record<string, string> = {
    notice: "Something noticed",
    connection: "Connection",
    idea: "Emerging idea",
    uncertainty: "Uncertainty",
    revisit: "Worth revisiting",
  };
  return labels[text(value)] || friendlyStatus(value);
}

function clarificationLabel(value: unknown) {
  const labels: Record<string, string> = {
    not_needed: "No clarification needed",
    unclear: "Unclear",
    question_forming: "Question forming",
    question_ready: "Question ready",
    answered: "Answered",
    clarified_for_now: "Clear for now",
    reopened: "Reopened",
  };
  return labels[text(value)] || friendlyStatus(value);
}

export default function StudyNotepad({ session, onUpdated }: StudyNotepadProps) {
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");
  const [questionDrafts, setQuestionDrafts] = useState<Record<string, string>>({});
  const sessionItem = safeJsonObject(session.item);
  const sessionId = Number(sessionItem.id || 0);
  const notes = (session.notes || []) as Dict[];
  const clarificationNotes = useMemo(
    () => notes.filter((item) => text(item.clarification_state) !== "not_needed"),
    [notes],
  );

  async function formNote(attentionMode: "anything" | "clarification") {
    if (!sessionId || busy) return;
    setBusy(attentionMode);
    setMessage("");
    try {
      const result = await api<Dict>("/api/study/notes/form", {
        method: "POST",
        body: JSON.stringify({ session_id: sessionId, attention_mode: attentionMode }),
      });
      setMessage(text(result.message || (result.created ? "Selene added a note." : "Nothing new needed a note.")));
      onUpdated(result);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "The Study note could not be formed.");
    } finally {
      setBusy("");
    }
  }

  async function updateClarification(note: Dict, action: string, extra: Dict = {}) {
    const noteId = Number(note.id || 0);
    if (!noteId || busy) return;
    setBusy(`${noteId}:${action}`);
    setMessage("");
    try {
      const result = await api<Dict>("/api/study/notes/clarification", {
        method: "POST",
        body: JSON.stringify({ note_id: noteId, action, ...extra }),
      });
      setMessage("The clarification path was updated.");
      if (action === "form_question") {
        setQuestionDrafts((current) => ({ ...current, [text(noteId)]: "" }));
      }
      onUpdated(result);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "The clarification state could not be updated.");
    } finally {
      setBusy("");
    }
  }

  return (
    <div className="studyNotepadGrid">
      <section className="panel studyNotepadPanel">
        <div className="panelHeader">
          <div>
            <h3>Selene&apos;s Notepad</h3>
            <p className="plainHelp">What catches her attention, in her own language, with the supported meaning kept underneath.</p>
          </div>
          <span>{notes.length} notes</span>
        </div>
        <div className="reviewActions studyNoteActions">
          <button className="primary" disabled={Boolean(busy)} onClick={() => formNote("anything")}>What stands out?</button>
          <button disabled={Boolean(busy)} onClick={() => formNote("clarification")}>Check for clarification</button>
        </div>
        <p className="plainHelp">Clarification is formed only from uncertainty already recorded in this Study session. Selene will not invent confusion to fill the page.</p>
        {message ? <p className="studyNotebookMessage" role="status" aria-live="polite">{message}</p> : null}
        <div className="studyNoteStack">
          {notes.map((note) => {
            const noteId = text(note.id);
            const state = text(note.clarification_state);
            return (
              <article className="studyNoteCard" key={`study-note-${noteId}`}>
                <div className="packetHeader">
                  <strong>Selene</strong>
                  <span>{noteKindLabel(note.note_kind)}</span>
                </div>
                <p className="studyNoteVoice">{text(note.note_text)}</p>
                <div className="chips">
                  <span>{clarificationLabel(state)}</span>
                  <span>source: {friendlyStatus(note.source_field)}</span>
                </div>
                <details className="studyNoteBasis">
                  <summary>Supported meaning and provenance</summary>
                  <p>{text(note.meaning_summary)}</p>
                  <ul>
                    {((note.source_refs || []) as unknown[]).map((source, index) => <li key={`${noteId}-source-${index}`}>{text(source)}</li>)}
                  </ul>
                </details>
                {state === "not_needed" ? (
                  <button disabled={Boolean(busy)} onClick={() => updateClarification(note, "needs_clarification")}>Something here needs clarification</button>
                ) : null}
              </article>
            );
          })}
          {!notes.length ? <p className="emptyState">The notepad is empty. Nothing is written merely to make Study look busy.</p> : null}
        </div>
      </section>

      <section className="panel studyClarificationPanel">
        <div className="panelHeader">
          <div>
            <h3>Clarification Lane</h3>
            <p className="plainHelp">Uncertainty can exist before Selene has a complete question.</p>
          </div>
          <span>{clarificationNotes.filter((item) => OPEN_CLARIFICATION_STATES.has(text(item.clarification_state))).length} open</span>
        </div>
        <div className="studyClarificationStack">
          {clarificationNotes.map((note) => {
            const noteId = text(note.id);
            const state = text(note.clarification_state);
            const draft = questionDrafts[noteId] || "";
            return (
              <article className="studyClarificationCard" key={`clarification-${noteId}`}>
                <div className="packetHeader">
                  <strong>{noteKindLabel(note.note_kind)}</strong>
                  <span>{clarificationLabel(state)}</span>
                </div>
                <p>{text(note.note_text)}</p>
                {state === "unclear" || state === "reopened" ? (
                  <div className="reviewActions">
                    <button className="primary" disabled={Boolean(busy)} onClick={() => updateClarification(note, "develop_question")}>Let the question develop</button>
                    <button disabled={Boolean(busy)} onClick={() => updateClarification(note, "clarified_for_now")}>Clear for now</button>
                  </div>
                ) : null}
                {state === "question_forming" ? (
                  <div className="studyQuestionComposer">
                    <label>
                      <span>The question, when the words arrive</span>
                      <textarea value={draft} onChange={(event) => setQuestionDrafts((current) => ({ ...current, [noteId]: event.target.value }))} placeholder="What does Selene want to ask about this?" />
                    </label>
                    <div className="reviewActions">
                      <button className="primary" disabled={Boolean(busy) || !draft.trim()} onClick={() => updateClarification(note, "form_question", { formation_state: "ready", question_text: draft })}>Question ready</button>
                      <button disabled={Boolean(busy)} onClick={() => updateClarification(note, "form_question", { formation_state: "question_without_words" })}>No words yet</button>
                      <button disabled={Boolean(busy)} onClick={() => updateClarification(note, "clarified_for_now")}>Clear for now</button>
                    </div>
                  </div>
                ) : null}
                {state === "question_ready" ? <p className="plainHelp">The formed question is waiting in Open Questions and Answers.</p> : null}
                {state === "answered" || state === "clarified_for_now" ? (
                  <button disabled={Boolean(busy)} onClick={() => updateClarification(note, "reopen")}>Reopen this</button>
                ) : null}
              </article>
            );
          })}
          {!clarificationNotes.length ? <p className="emptyState">No clarification is waiting. A note can still be interesting without being a question.</p> : null}
        </div>
      </section>
    </div>
  );
}
