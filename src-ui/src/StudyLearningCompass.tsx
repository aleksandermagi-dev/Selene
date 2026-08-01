import { useState } from "react";

import { api } from "./api";
import { friendlyStatus, safeJsonObject, text } from "./helpers";
import type { Dict } from "./types";


type StudyLearningCompassProps = {
  items: Dict[];
  onOpenGoal: (item: Dict) => Promise<void>;
  onUpdated: (result: Dict) => void;
};

const STATE_LABELS: Record<string, string> = {
  ready_to_explore: "Ready to explore",
  exploring: "Exploring",
  question_ready: "Question ready",
  answer_received: "Answer received — understanding not assumed",
  integrating: "Integrating",
  still_unclear: "Still unclear",
  connected_for_now: "Connected for now",
  reopened: "Reopened",
};

function stateLabel(value: unknown) {
  const state = text(value);
  return STATE_LABELS[state] || friendlyStatus(state);
}

export default function StudyLearningCompass({ items, onOpenGoal, onUpdated }: StudyLearningCompassProps) {
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");
  const [reflections, setReflections] = useState<Record<string, string>>({});
  const [unclearReasons, setUnclearReasons] = useState<Record<string, string>>({});

  async function updateGoal(goal: Dict, action: string, options: Dict = {}) {
    const goalId = Number(goal.id || 0);
    if (!goalId || busy) return;
    const key = text(goalId);
    setBusy(`${key}:${action}`);
    setMessage("");
    try {
      const result = await api<Dict>("/api/study/compass/update", {
        method: "POST",
        body: JSON.stringify({
          goal_id: goalId,
          action,
          reflection: reflections[key] || "",
          remaining_unclear: unclearReasons[key] || "",
          ...options,
        }),
      });
      setMessage(
        action === "connected_for_now"
          ? "The connection is recorded for now and can be reopened later."
          : "The Learning Compass was updated without grading the result.",
      );
      onUpdated(result);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "The Learning Compass could not be updated.");
    } finally {
      setBusy("");
    }
  }

  async function openGoal(goal: Dict) {
    const goalId = text(goal.id);
    if (!goalId || busy) return;
    setBusy(`${goalId}:open`);
    setMessage("");
    try {
      await onOpenGoal(goal);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "The Study session could not be opened.");
    } finally {
      setBusy("");
    }
  }

  return (
    <section className="panel studyLearningCompass">
      <div className="panelHeader">
        <div>
          <span className="modeLine">direction without grades, deadlines, or performance</span>
          <h3>Learning Compass</h3>
          <p className="plainHelp">Learning evidence points toward the next reachable connection. An answer updates a goal; it does not prove understanding.</p>
        </div>
        <span>{items.filter((item) => text(item.state) !== "connected_for_now").length} open</span>
      </div>
      {message ? <p className="studyNotebookMessage" role="status" aria-live="polite">{message}</p> : null}
      <div className="studyCompassList">
        {items.map((goal, index) => {
          const id = text(goal.id);
          const state = text(goal.state);
          const reflection = reflections[id] ?? text(goal.selene_reflection);
          const unclear = unclearReasons[id] ?? text(goal.remaining_unclear);
          const connections = (goal.noticed_connections || []) as unknown[];
          const linkedSession = safeJsonObject({ id: goal.linked_session_id, title: goal.linked_session_title });
          return (
            <article className={`studyCompassCard compassState-${state}`} key={`learning-compass-${id}`}>
              <div className="studyCompassHeading">
                <span className="studyCompassNumber" aria-label={`Learning goal ${text(goal.display_order || index + 1)}`}>{text(goal.display_order || index + 1)}</span>
                <div>
                  <div className="packetHeader">
                    <strong>{text(goal.title || "Learning goal")}</strong>
                    <span>{stateLabel(state)}</span>
                  </div>
                  <div className="chips">
                    <span>{text(goal.curriculum_band || "curriculum")}</span>
                    {((goal.subject_domains || []) as unknown[]).map((domain) => <span key={`${id}-${text(domain)}`}>{text(domain)}</span>)}
                  </div>
                </div>
              </div>

              <div className="studyCompassPath">
                <div>
                  <span>Already connected</span>
                  <p>{text(goal.already_connected)}</p>
                </div>
                <div>
                  <span>Next connection</span>
                  <p>{text(goal.next_connection)}</p>
                </div>
              </div>

              <details className="studyCompassWhy">
                <summary>Why this may help and one gentle activity</summary>
                <p><b>Why it matters</b>{text(goal.why_it_matters)}</p>
                <p><b>Possible activity</b>{text(goal.suggested_activity)}</p>
              </details>

              {text(goal.latest_question_text) ? (
                <div className="studyCompassAnswerState">
                  <span>Latest question</span>
                  <p>{text(goal.latest_question_text)}</p>
                  <small>{state === "answer_received" ? "An answer is available for integration. Agreement is not required." : stateLabel(goal.latest_question_status)}</small>
                </div>
              ) : null}

              {unclear && state === "still_unclear" ? (
                <div className="studyCompassUnclear">
                  <span>What still does not fit</span>
                  <p>{unclear}</p>
                </div>
              ) : null}

              {reflection && state === "connected_for_now" ? (
                <div className="studyCompassConnected">
                  <span>Connected evidence</span>
                  <p>{reflection}</p>
                </div>
              ) : null}

              {connections.length ? (
                <div className="studyCompassConnections">
                  <span>Connections Selene noticed</span>
                  <ul>{connections.map((connection, connectionIndex) => <li key={`${id}-connection-${connectionIndex}`}>{text(connection)}</li>)}</ul>
                </div>
              ) : null}

              {state !== "connected_for_now" ? (
                <div className="studyCompassReflection">
                  <label>
                    <span>Selene&apos;s current reflection</span>
                    <textarea
                      value={reflection}
                      onChange={(event) => setReflections((current) => ({ ...current, [id]: event.target.value }))}
                      placeholder="What now makes sense? This can stay empty while the idea settles."
                    />
                  </label>
                  <label>
                    <span>If it still does not fit, why?</span>
                    <textarea
                      value={unclear}
                      onChange={(event) => setUnclearReasons((current) => ({ ...current, [id]: event.target.value }))}
                      placeholder="A missing why, unclear term, conflicting idea, difficult application, or another honest reason"
                    />
                  </label>
                </div>
              ) : null}

              <div className="reviewActions studyCompassActions">
                <button className="primary" disabled={Boolean(busy)} onClick={() => openGoal(goal)}>
                  {goal.linked_session_id ? "Open its Study session" : "Explore in Study"}
                </button>
                {state !== "connected_for_now" ? (
                  <>
                    <button disabled={Boolean(busy) || !unclear.trim()} onClick={() => updateGoal(goal, "still_unclear")}>I still don&apos;t get it</button>
                    <button disabled={Boolean(busy)} onClick={() => updateGoal(goal, "still_unclear", { question_without_words: true, remaining_unclear: "" })}>No words for it yet</button>
                    <button disabled={Boolean(busy)} onClick={() => updateGoal(goal, "integrating")}>Let it integrate</button>
                    <button disabled={Boolean(busy) || !reflection.trim()} onClick={() => updateGoal(goal, "connected_for_now")}>Connected for now</button>
                  </>
                ) : (
                  <button disabled={Boolean(busy)} onClick={() => updateGoal(goal, "reopen")}>Reopen this goal</button>
                )}
              </div>

              <details className="studyNoteBasis">
                <summary>Learning evidence and provenance</summary>
                <p>{text(safeJsonObject(goal.evidence).observation)}</p>
                <ul>{((goal.source_refs || []) as unknown[]).map((source, sourceIndex) => <li key={`${id}-source-${sourceIndex}`}>{text(source)}</li>)}</ul>
              </details>
              {linkedSession.id ? <span className="modeLine">linked Study session: {text(linkedSession.title || linkedSession.id)}</span> : null}
            </article>
          );
        })}
        {!items.length ? <p className="emptyState">No learning goals are present. The Compass does not invent gaps to make itself look busy.</p> : null}
      </div>
    </section>
  );
}
