import { type CSSProperties, useEffect, useState } from "react";

import { api } from "./api";
import { friendlyStatus, safeJsonObject, text } from "./helpers";
import type { Dict } from "./types";


type StudyPonderingLabProps = {
  session: Dict;
  onUpdated: (result: Dict) => void;
};

const REPRESENTATION_LABELS: Record<string, string> = {
  objects: "Visible objects",
  tallies: "Tally marks",
  groups: "Equal groups",
  place_value: "Place value",
  spatial_object: "Move or rotate an object",
  sentence_roles: "Sentence meaning-role cards",
  sentence_transform: "Before and after sentence",
  sentence_scene: "Statement, question, and callback",
};

const NUMERIC_REPRESENTATIONS = new Set(["objects", "tallies", "groups", "place_value"]);
const SENTENCE_REPRESENTATIONS = new Set(["sentence_roles", "sentence_transform", "sentence_scene"]);

const PONDERING_LABELS: Record<string, string> = {
  active: "Actively pondering",
  needs_representation: "Try another representation",
  needs_prerequisite: "Needs an earlier foundation",
  question_forming: "Question forming",
  waiting_for_answer: "Waiting for an answer",
  return_later: "Return later",
  integrated_for_now: "Connected for now",
  reopened: "Reopened",
};

type ThreadDraft = {
  state: string;
  current_fit: string;
  missing_bridge: string;
  prerequisite_needed: string;
  revisit_cue: string;
};

type RepresentationDraft = {
  kind: string;
  quantity: string;
  group_size: string;
  shape: string;
  label: string;
  rotation: string;
  rotate_degrees: string;
  x: string;
  y: string;
  move_x: string;
  move_y: string;
  subject: string;
  predicate: string;
  object: string;
  subject_number: string;
  tense: string;
  polarity: string;
  subject_modifier: string;
  object_modifier: string;
  relation: string;
  second_subject: string;
  second_predicate: string;
  second_object: string;
  place: string;
  time: string;
  callback_pronoun: string;
  question_role: string;
  observation: string;
};

const DEFAULT_REPRESENTATION: RepresentationDraft = {
  kind: "objects",
  quantity: "12",
  group_size: "4",
  shape: "square",
  label: "object",
  rotation: "0",
  rotate_degrees: "90",
  x: "50",
  y: "50",
  move_x: "0",
  move_y: "0",
  subject: "the lesson",
  predicate: "remain",
  object: "available",
  subject_number: "singular",
  tense: "present",
  polarity: "positive",
  subject_modifier: "",
  object_modifier: "",
  relation: "",
  second_subject: "",
  second_predicate: "",
  second_object: "",
  place: "near the window",
  time: "",
  callback_pronoun: "it",
  question_role: "place",
  observation: "",
};

function representationVisual(attempt: Dict) {
  const kind = text(attempt.representation_kind);
  const output = safeJsonObject(attempt.output);
  if (kind === "objects") {
    const items = (output.items || []) as Dict[];
    return (
      <div className="representationObjectField" aria-label={`${text(output.quantity)} represented objects`}>
        {items.map((item) => (
          <span
            className={`representationObject representationShape-${text(item.shape)}`}
            key={`object-${text(item.id)}`}
            style={{ left: `${Number(item.x || 0)}%`, top: `${Number(item.y || 0)}%` }}
          />
        ))}
      </div>
    );
  }
  if (kind === "tallies") {
    return <div className="representationTallies">{((output.groups || []) as unknown[]).map((group, index) => <span key={`tally-${index}`}>{text(group)}</span>)}</div>;
  }
  if (kind === "groups") {
    return (
      <div className="representationGroups">
        {((output.groups || []) as unknown[]).map((group, index) => (
          <span key={`group-${index}`}>{Array.from({ length: Number(group || 0) }, (_, itemIndex) => <i key={`group-${index}-${itemIndex}`} />)}</span>
        ))}
        {Number(output.remainder || 0) ? <span className="remainderGroup">{Array.from({ length: Number(output.remainder || 0) }, (_, index) => <i key={`remainder-${index}`} />)}</span> : null}
      </div>
    );
  }
  if (kind === "place_value") {
    return (
      <div className="representationPlaceValue">
        <span><b>{text(output.hundreds)}</b>hundreds</span>
        <span><b>{text(output.tens)}</b>tens</span>
        <span><b>{text(output.ones)}</b>ones</span>
        <em>{text(output.expanded)}</em>
      </div>
    );
  }
  if (kind === "sentence_roles") {
    const roles = (output.roles || []) as Dict[];
    return (
      <div className="representationSentenceShape">
        <div className="sentenceRoleCards">
          {roles.map((role, index) => (
            <span key={`sentence-role-${index}`}><small>{text(role.label)}</small><b>{text(role.value)}</b></span>
          ))}
        </div>
        <p>{text(output.sentence)}</p>
      </div>
    );
  }
  if (kind === "sentence_transform") {
    return (
      <div className="representationSentenceShape">
        <div className="sentenceBeforeAfter">
          <span><small>Before</small><b>{text(output.before_sentence)}</b></span>
          <span><small>After the visible change</small><b>{text(output.sentence)}</b></span>
        </div>
        <div className="chips">
          <span>{text(output.subject_number)}</span>
          <span>{text(output.tense)}</span>
          <span>{text(output.polarity)}</span>
          {text(output.relation) ? <span>{text(output.relation)}</span> : null}
          <span>{output.original_claim_unchanged ? "same claim" : "claim changed by visible controls"}</span>
        </div>
      </div>
    );
  }
  if (kind === "sentence_scene") {
    const roles = (output.roles || []) as Dict[];
    return (
      <div className="representationSentenceShape">
        <div className="sentenceRoleCards">
          {roles.map((role, index) => <span key={`scene-role-${index}`}><small>{text(role.label)}</small><b>{text(role.value)}</b></span>)}
        </div>
        <div className="sentenceBeforeAfter">
          <span><small>Statement</small><b>{text(output.statement)}</b></span>
          <span><small>Useful question · missing {text(output.missing_role)}</small><b>{text(output.question)}</b></span>
          <span><small>Clear callback · {text(output.callback_pronoun)} refers to {text(output.pronoun_antecedent)}</small><b>{text(output.callback)}</b></span>
        </div>
      </div>
    );
  }
  const style = {
    left: `${Number(output.x || 0)}%`,
    top: `${Number(output.y || 0)}%`,
    transform: `translate(-50%, -50%) rotate(${Number(output.rotation || 0)}deg)`,
  } as CSSProperties;
  return (
    <div className="representationSpatialField">
      <span className={`spatialSimObject spatialShape-${text(output.shape)}`} style={style}>{text(output.label || "object")}</span>
      <small>{text(output.rotation)}° · x {text(output.x)} · y {text(output.y)}</small>
    </div>
  );
}

export default function StudyPonderingLab({ session, onUpdated }: StudyPonderingLabProps) {
  const item = safeJsonObject(session.item);
  const sessionId = Number(item.id || 0);
  const threads = (session.pondering_threads || []) as Dict[];
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");
  const [newThread, setNewThread] = useState<ThreadDraft & { title: string }>({
    title: "",
    state: "needs_representation",
    current_fit: "",
    missing_bridge: "",
    prerequisite_needed: "",
    revisit_cue: "",
  });
  const [threadDrafts, setThreadDrafts] = useState<Record<string, ThreadDraft>>({});
  const [representationDrafts, setRepresentationDrafts] = useState<Record<string, RepresentationDraft>>({});

  useEffect(() => {
    setNewThread((current) => ({ ...current, title: text(item.focus || item.title) }));
  }, [sessionId, item.focus, item.title]);

  function threadDraft(thread: Dict): ThreadDraft {
    const id = text(thread.id);
    return threadDrafts[id] || {
      state: text(thread.state || "active"),
      current_fit: text(thread.current_fit),
      missing_bridge: text(thread.missing_bridge),
      prerequisite_needed: text(thread.prerequisite_needed),
      revisit_cue: text(thread.revisit_cue),
    };
  }

  function representationDraft(thread: Dict) {
    return representationDrafts[text(thread.id)] || DEFAULT_REPRESENTATION;
  }

  function setThreadField(thread: Dict, field: keyof ThreadDraft, value: string) {
    const id = text(thread.id);
    setThreadDrafts((current) => ({ ...current, [id]: { ...threadDraft(thread), [field]: value } }));
  }

  function setRepresentationField(thread: Dict, field: keyof RepresentationDraft, value: string) {
    const id = text(thread.id);
    setRepresentationDrafts((current) => ({ ...current, [id]: { ...representationDraft(thread), [field]: value } }));
  }

  async function holdThread() {
    if (!sessionId || !newThread.title.trim() || busy) return;
    setBusy("create");
    setMessage("");
    try {
      const result = await api<Dict>("/api/study/pondering/create", {
        method: "POST",
        body: JSON.stringify({ session_id: sessionId, ...newThread }),
      });
      setMessage("The thought remains open and inspectable. It is not a grade or hidden memory.");
      onUpdated(result);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "The pondering thread could not be held.");
    } finally {
      setBusy("");
    }
  }

  async function updateThread(thread: Dict, overrideState?: string) {
    const id = Number(thread.id || 0);
    if (!id || busy) return;
    const draft = threadDraft(thread);
    setBusy(`${id}:update`);
    setMessage("");
    try {
      const result = await api<Dict>("/api/study/pondering/update", {
        method: "POST",
        body: JSON.stringify({ thread_id: id, ...draft, state: overrideState || draft.state }),
      });
      setMessage(overrideState === "integrated_for_now" ? "Connected for now. It can be reopened later." : "The open thought was updated without judging it.");
      onUpdated(result);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "The pondering thread could not be updated.");
    } finally {
      setBusy("");
    }
  }

  async function tryRepresentation(thread: Dict) {
    const id = Number(thread.id || 0);
    if (!id || busy) return;
    const draft = representationDraft(thread);
    setBusy(`${id}:representation`);
    setMessage("");
    try {
      const result = await api<Dict>("/api/study/representations/try", {
        method: "POST",
        body: JSON.stringify({
          thread_id: id,
          representation_kind: draft.kind,
          quantity: Number(draft.quantity),
          group_size: Number(draft.group_size),
          shape: draft.shape,
          label: draft.label,
          rotation: Number(draft.rotation),
          rotate_degrees: Number(draft.rotate_degrees),
          x: Number(draft.x),
          y: Number(draft.y),
          move_x: Number(draft.move_x),
          move_y: Number(draft.move_y),
          subject: draft.subject,
          predicate: draft.predicate,
          object: draft.object,
          subject_number: draft.subject_number,
          tense: draft.tense,
          polarity: draft.polarity,
          subject_modifier: draft.subject_modifier,
          object_modifier: draft.object_modifier,
          relation: draft.relation,
          second_subject: draft.second_subject,
          second_predicate: draft.second_predicate,
          second_object: draft.second_object,
          place: draft.place,
          time: draft.time,
          callback_pronoun: draft.callback_pronoun,
          question_role: draft.question_role,
          observation: draft.observation,
        }),
      });
      setMessage("A visible representation was added. Trying a form does not claim that the concept is understood.");
      onUpdated(result);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "The representation could not be formed.");
    } finally {
      setBusy("");
    }
  }

  async function formRepresentationReflection(attempt: Dict) {
    const attemptId = Number(attempt.id || 0);
    if (!attemptId || busy) return;
    setBusy(`${attemptId}:reflection`);
    setMessage("");
    try {
      const result = await api<Dict>("/api/study/representations/reflect", {
        method: "POST",
        body: JSON.stringify({ attempt_id: attemptId, connect_for_now: true }),
      });
      setMessage("Selene formed a visible L1 reflection from this scene and connected it for now. It can be reopened later.");
      onUpdated(result);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "The visible reflection could not be formed.");
    } finally {
      setBusy("");
    }
  }

  return (
    <section className="panel studyPonderingLab">
      <div className="panelHeader">
        <div>
          <span className="modeLine">hold · represent · inspect · revisit</span>
          <h3>Pondering &amp; Representation Lab</h3>
          <p className="plainHelp">Confusion can remain open while Selene tries another form or learns an earlier foundation. Only visible learning state is recorded—never hidden chain-of-thought.</p>
        </div>
        <span>{threads.filter((thread) => text(thread.state) !== "integrated_for_now").length} open</span>
      </div>
      {message ? <p className="studyNotebookMessage" role="status" aria-live="polite">{message}</p> : null}

      <details className="ponderingThreadCreator" open={!threads.length}>
        <summary>Hold a thought open</summary>
        <div className="ponderingCreatorGrid">
          <label className="wideEvidenceField">
            <span>What are we holding?</span>
            <input value={newThread.title} onChange={(event) => setNewThread({ ...newThread, title: event.target.value })} placeholder="The question or connection worth returning to" />
          </label>
          <label>
            <span>Current learning state</span>
            <select value={newThread.state} onChange={(event) => setNewThread({ ...newThread, state: event.target.value })}>
              {Object.entries(PONDERING_LABELS).map(([value, label]) => <option value={value} key={value}>{label}</option>)}
            </select>
          </label>
          <label><span>What already fits?</span><textarea value={newThread.current_fit} onChange={(event) => setNewThread({ ...newThread, current_fit: event.target.value })} placeholder="This may stay empty while the idea settles." /></label>
          <label><span>What bridge is missing?</span><textarea value={newThread.missing_bridge} onChange={(event) => setNewThread({ ...newThread, missing_bridge: event.target.value })} placeholder="A why, term, representation, relationship, or something not yet expressible" /></label>
          <label><span>Possible prerequisite</span><input value={newThread.prerequisite_needed} onChange={(event) => setNewThread({ ...newThread, prerequisite_needed: event.target.value })} placeholder="An earlier concept that may help" /></label>
          <label><span>When might this be useful to revisit?</span><input value={newThread.revisit_cue} onChange={(event) => setNewThread({ ...newThread, revisit_cue: event.target.value })} placeholder="For example: after place value" /></label>
        </div>
        <button className="primary" disabled={Boolean(busy) || !newThread.title.trim()} onClick={holdThread}>Keep This Open</button>
      </details>

      <div className="ponderingThreadList">
        {threads.map((thread) => {
          const id = text(thread.id);
          const draft = threadDraft(thread);
          const representation = representationDraft(thread);
          const attempts = (thread.representation_attempts || []) as Dict[];
          const numericRepresentation = NUMERIC_REPRESENTATIONS.has(representation.kind);
          const sentenceRepresentation = SENTENCE_REPRESENTATIONS.has(representation.kind);
          return (
            <article className={`ponderingThreadCard ponderingState-${text(thread.state)}`} key={`pondering-${id}`}>
              <div className="packetHeader">
                <strong>{text(thread.title)}</strong>
                <span>{PONDERING_LABELS[text(thread.state)] || friendlyStatus(thread.state)}</span>
              </div>
              <div className="ponderingThreadFields">
                <label><span>State</span><select value={draft.state} onChange={(event) => setThreadField(thread, "state", event.target.value)}>{Object.entries(PONDERING_LABELS).map(([value, label]) => <option value={value} key={`${id}-${value}`}>{label}</option>)}</select></label>
                <label><span>What currently fits?</span><textarea value={draft.current_fit} onChange={(event) => setThreadField(thread, "current_fit", event.target.value)} /></label>
                <label><span>What bridge is missing?</span><textarea value={draft.missing_bridge} onChange={(event) => setThreadField(thread, "missing_bridge", event.target.value)} /></label>
                <label><span>Earlier foundation that may help</span><input value={draft.prerequisite_needed} onChange={(event) => setThreadField(thread, "prerequisite_needed", event.target.value)} /></label>
                <label><span>Return cue</span><input value={draft.revisit_cue} onChange={(event) => setThreadField(thread, "revisit_cue", event.target.value)} /></label>
              </div>
              <div className="reviewActions">
                <button className="primary" disabled={Boolean(busy)} onClick={() => updateThread(thread)}>Save Pondering State</button>
                {text(thread.state) === "integrated_for_now"
                  ? <button disabled={Boolean(busy)} onClick={() => updateThread(thread, "reopened")}>Reopen</button>
                  : <button disabled={Boolean(busy) || !draft.current_fit.trim()} onClick={() => updateThread(thread, "integrated_for_now")}>Connected for Now</button>}
              </div>

              <details className="representationWorkbench" open={!attempts.length}>
                <summary>Try another representation</summary>
                <div className="representationControls">
                  <label><span>Representation</span><select value={representation.kind} onChange={(event) => setRepresentationField(thread, "kind", event.target.value)}>{Object.entries(REPRESENTATION_LABELS).map(([value, label]) => <option value={value} key={`${id}-${value}`}>{label}</option>)}</select></label>
                  {numericRepresentation ? <label><span>Quantity</span><input type="number" min="0" max="200" value={representation.quantity} onChange={(event) => setRepresentationField(thread, "quantity", event.target.value)} /></label> : null}
                  {representation.kind === "groups" ? <label><span>Items per group</span><input type="number" min="1" max="50" value={representation.group_size} onChange={(event) => setRepresentationField(thread, "group_size", event.target.value)} /></label> : null}
                  {representation.kind === "objects" ? <label><span>Object shape</span><select value={representation.shape} onChange={(event) => setRepresentationField(thread, "shape", event.target.value)}><option value="circle">Circle</option><option value="square">Square</option><option value="triangle">Triangle</option></select></label> : null}
                  {representation.kind === "spatial_object" ? (
                    <>
                      <label><span>Object label</span><input value={representation.label} onChange={(event) => setRepresentationField(thread, "label", event.target.value)} /></label>
                      <label><span>Shape</span><select value={representation.shape === "circle" ? "arrow" : representation.shape} onChange={(event) => setRepresentationField(thread, "shape", event.target.value)}><option value="arrow">Arrow</option><option value="rectangle">Rectangle</option><option value="square">Square</option><option value="triangle">Triangle</option></select></label>
                      <label><span>Start rotation</span><input type="number" value={representation.rotation} onChange={(event) => setRepresentationField(thread, "rotation", event.target.value)} /></label>
                      <label><span>Rotate by degrees</span><input type="number" min="-360" max="360" value={representation.rotate_degrees} onChange={(event) => setRepresentationField(thread, "rotate_degrees", event.target.value)} /></label>
                      <label><span>Move sideways</span><input type="number" min="-100" max="100" value={representation.move_x} onChange={(event) => setRepresentationField(thread, "move_x", event.target.value)} /></label>
                      <label><span>Move vertically</span><input type="number" min="-100" max="100" value={representation.move_y} onChange={(event) => setRepresentationField(thread, "move_y", event.target.value)} /></label>
                    </>
                  ) : null}
                  {sentenceRepresentation ? (
                    <>
                      <label><span>Who or what</span><input value={representation.subject} onChange={(event) => setRepresentationField(thread, "subject", event.target.value)} /></label>
                      <label><span>Action, state, or relation</span><input value={representation.predicate} onChange={(event) => setRepresentationField(thread, "predicate", event.target.value)} /></label>
                      <label><span>Affected or completing part</span><input value={representation.object} onChange={(event) => setRepresentationField(thread, "object", event.target.value)} /></label>
                      <label><span>Subject number</span><select value={representation.subject_number} onChange={(event) => setRepresentationField(thread, "subject_number", event.target.value)}><option value="singular">Singular</option><option value="plural">Plural</option></select></label>
                    </>
                  ) : null}
                  {representation.kind === "sentence_transform" ? (
                    <>
                      <label><span>Time</span><select value={representation.tense} onChange={(event) => setRepresentationField(thread, "tense", event.target.value)}><option value="present">Present</option><option value="past">Past</option><option value="future">Future</option></select></label>
                      <label><span>Claim form</span><select value={representation.polarity} onChange={(event) => setRepresentationField(thread, "polarity", event.target.value)}><option value="positive">Positive</option><option value="negative">Negative</option></select></label>
                      <label><span>Optional subject description</span><input value={representation.subject_modifier} onChange={(event) => setRepresentationField(thread, "subject_modifier", event.target.value)} placeholder="reviewed" /></label>
                      <label><span>Optional object description</span><input value={representation.object_modifier} onChange={(event) => setRepresentationField(thread, "object_modifier", event.target.value)} placeholder="clearly" /></label>
                      <label><span>Relationship to a second clause</span><select value={representation.relation} onChange={(event) => setRepresentationField(thread, "relation", event.target.value)}><option value="">No second clause</option><option value="support">Addition or support</option><option value="contrast">Contrast</option><option value="cause">Reason or result</option><option value="sequence">Sequence</option></select></label>
                      {representation.relation ? (
                        <>
                          <label><span>Second who or what</span><input value={representation.second_subject} onChange={(event) => setRepresentationField(thread, "second_subject", event.target.value)} /></label>
                          <label><span>Second action or state</span><input value={representation.second_predicate} onChange={(event) => setRepresentationField(thread, "second_predicate", event.target.value)} /></label>
                          <label><span>Second completing part</span><input value={representation.second_object} onChange={(event) => setRepresentationField(thread, "second_object", event.target.value)} /></label>
                        </>
                      ) : null}
                    </>
                  ) : null}
                  {representation.kind === "sentence_scene" ? (
                    <>
                      <label><span>Where (optional unless asked)</span><input value={representation.place} onChange={(event) => setRepresentationField(thread, "place", event.target.value)} /></label>
                      <label><span>When (optional unless asked)</span><input value={representation.time} onChange={(event) => setRepresentationField(thread, "time", event.target.value)} /></label>
                      <label><span>Clear callback pronoun</span><select value={representation.callback_pronoun} onChange={(event) => setRepresentationField(thread, "callback_pronoun", event.target.value)}><option value="it">It</option><option value="she">She</option><option value="he">He</option><option value="they">They</option></select></label>
                      <label><span>Role the useful question asks for</span><select value={representation.question_role} onChange={(event) => setRepresentationField(thread, "question_role", event.target.value)}><option value="object">Affected or completing part</option><option value="place">Where</option><option value="time">When</option><option value="reason">Why</option><option value="manner">How</option></select></label>
                    </>
                  ) : null}
                  <label className="wideEvidenceField"><span>What does Selene notice?</span><textarea value={representation.observation} onChange={(event) => setRepresentationField(thread, "observation", event.target.value)} placeholder="Optional. The representation can exist before its meaning is clear." /></label>
                </div>
                <button className="primary" disabled={Boolean(busy)} onClick={() => tryRepresentation(thread)}>Try This Form</button>
              </details>

              {attempts.length ? (
                <div className="representationAttemptList">
                  {attempts.map((attempt) => (
                    <article className="representationAttempt" key={`attempt-${text(attempt.id)}`}>
                      <div className="packetHeader"><strong>{REPRESENTATION_LABELS[text(attempt.representation_kind)]}</strong><span>visible attempt {text(attempt.id)}</span></div>
                      {representationVisual(attempt)}
                      {text(attempt.observation) ? <p><b>Selene noticed</b>{text(attempt.observation)}</p> : <p className="plainHelp">No interpretation is required yet. This form can be revisited.</p>}
                      {text(attempt.representation_kind) === "sentence_scene" ? <div className="reviewActions"><button className="primary" disabled={Boolean(busy)} onClick={() => formRepresentationReflection(attempt)}>Form L1 Reflection &amp; Connect for Now</button></div> : null}
                    </article>
                  ))}
                </div>
              ) : null}
            </article>
          );
        })}
      </div>
    </section>
  );
}
