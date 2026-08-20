import { useEffect, useMemo, useState } from "react";

import { api } from "./api";
import { friendlyStatus, safeJsonObject, text } from "./helpers";
import type { Dict } from "./types";


const REVIEW_STATES = [
  ["", "Not reviewed"],
  ["demonstrated", "Demonstrated"],
  ["developing", "Developing"],
  ["not_observed", "Not observed"],
  ["cannot_assess", "Cannot assess"],
  ["activity_issue", "Activity issue"],
] as const;

function list(value: unknown): Dict[] {
  return Array.isArray(value) ? value.filter((item): item is Dict => Boolean(item && typeof item === "object")) : [];
}

function downloadJson(filename: string, value: unknown) {
  const blob = new Blob([JSON.stringify(value, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export default function StudyLeaDesk() {
  const [status, setStatus] = useState<Dict>({});
  const [suite, setSuite] = useState<Dict>({});
  const [runs, setRuns] = useState<Dict[]>([]);
  const [activeRun, setActiveRun] = useState<Dict | null>(null);
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");
  const [kind, setKind] = useState("selene");
  const [respondent, setRespondent] = useState("Selene");
  const [modelDetails, setModelDetails] = useState("");
  const [externalResponse, setExternalResponse] = useState("");
  const [confirmGentle, setConfirmGentle] = useState(false);
  const [reviewDrafts, setReviewDrafts] = useState<Record<string, Record<string, string>>>({});
  const [reviewNotes, setReviewNotes] = useState<Record<string, string>>({});

  async function refresh(preferredRunId?: number) {
    const [nextStatus, nextSuite, nextRuns] = await Promise.all([
      api<Dict>("/api/study/lea/status"),
      api<Dict>("/api/study/lea/suite"),
      api<{ items: Dict[] }>("/api/study/lea/runs?limit=40"),
    ]);
    setStatus(nextStatus);
    setSuite(nextSuite);
    setRuns(nextRuns.items || []);
    const runId = Number(preferredRunId || safeJsonObject(activeRun?.item).id || 0);
    if (runId) setActiveRun(await api<Dict>(`/api/study/lea/runs/${runId}`));
  }

  useEffect(() => {
    refresh().catch((error) => setMessage(error instanceof Error ? error.message : "The LEA desk could not be opened."));
  }, []);

  useEffect(() => {
    if (kind === "selene" && respondent !== "Selene") setRespondent("Selene");
    if (kind !== "selene" && respondent === "Selene") setRespondent("");
  }, [kind]);

  async function createRun() {
    if (!respondent.trim() || busy) return;
    setBusy("create");
    setMessage("");
    try {
      const result = await api<Dict>("/api/study/lea/runs/create", {
        method: "POST",
        body: JSON.stringify({ respondent_kind: kind, respondent_name: respondent, model_details: modelDetails, created_by: "Aleks" }),
      });
      setActiveRun(result);
      setMessage("The blank LEA record is ready. No conversation has been run yet.");
      await refresh(Number(safeJsonObject(result.item).id || 0));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "The LEA run could not be created.");
    } finally {
      setBusy("");
    }
  }

  async function openRun(item: Dict) {
    const id = Number(item.id || 0);
    if (!id || busy) return;
    setBusy(`open:${id}`);
    try {
      setActiveRun(await api<Dict>(`/api/study/lea/runs/${id}`));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "The LEA run could not be opened.");
    } finally {
      setBusy("");
    }
  }

  async function runSeleneTurn() {
    const id = Number(safeJsonObject(activeRun?.item).id || 0);
    if (!id || !confirmGentle || busy) return;
    setBusy("selene-turn");
    setMessage("");
    try {
      const result = await api<Dict>("/api/study/lea/selene/advance", {
        method: "POST",
        body: JSON.stringify({ run_id: id, confirm_gentle_turn: true }),
      });
      setActiveRun(result);
      setConfirmGentle(false);
      setMessage("One ordinary diagnostic turn was recorded. Nothing else ran automatically.");
      await refresh(id);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "The bounded Selene turn could not be completed.");
    } finally {
      setBusy("");
    }
  }

  async function recordExternalTurn() {
    const id = Number(safeJsonObject(activeRun?.item).id || 0);
    if (!id || !externalResponse.trim() || busy) return;
    setBusy("external-turn");
    setMessage("");
    try {
      const result = await api<Dict>("/api/study/lea/responses/record", {
        method: "POST",
        body: JSON.stringify({ run_id: id, response: externalResponse }),
      });
      setActiveRun(result);
      setExternalResponse("");
      setMessage("The visible comparison response was recorded without interpreting it.");
      await refresh(id);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "The comparison response could not be recorded.");
    } finally {
      setBusy("");
    }
  }

  async function saveReview(turn: Dict) {
    const turnId = text(turn.id);
    const expected = list(turn.criteria);
    const savedRatings = safeJsonObject(safeJsonObject(turn.review).ratings);
    const draft = reviewDrafts[turnId] || {};
    const ratings = Object.fromEntries(
      expected.map((criterion) => {
        const key = text(criterion.key);
        return [key, draft[key] || text(safeJsonObject(savedRatings[key]).state)];
      }),
    );
    if (!expected.length || expected.some((criterion) => !ratings[text(criterion.key)])) return;
    setBusy(`review:${turnId}`);
    setMessage("");
    try {
      const result = await api<Dict>("/api/study/lea/turns/review", {
        method: "POST",
        body: JSON.stringify({
          turn_id: Number(turn.id),
          reviewer: "Aleks",
          ratings,
          overall_note: reviewNotes[turnId] || "",
        }),
      });
      setActiveRun(result);
      setMessage("The descriptive evidence was saved. It is not a grade.");
      await refresh(Number(safeJsonObject(result.item).id || 0));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "The descriptive review could not be saved.");
    } finally {
      setBusy("");
    }
  }

  async function closeRun() {
    const id = Number(safeJsonObject(activeRun?.item).id || 0);
    if (!id || busy) return;
    setBusy("complete");
    try {
      const result = await api<Dict>("/api/study/lea/runs/complete", {
        method: "POST",
        body: JSON.stringify({ run_id: id }),
      });
      setActiveRun(result);
      setMessage(result.item && text(safeJsonObject(result.item).status) === "completed" ? "The reviewed evidence profile is complete." : "All responses are present; descriptive review is still open.");
      await refresh(id);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "The LEA run could not be closed.");
    } finally {
      setBusy("");
    }
  }

  const item = safeJsonObject(activeRun?.item);
  const nextTurn = safeJsonObject(activeRun?.next_turn);
  const turns = list(activeRun?.turns);
  const summary = safeJsonObject(activeRun?.summary);
  const dimensions = list(suite.dimensions);
  const dimensionProfile = safeJsonObject(summary.dimension_profile);
  const progress = `${text(summary.turns_recorded || 0)} / ${text(summary.turns_total || suite.turn_count || 20)} turns`;
  const respondentKind = text(item.respondent_kind);
  const currentScenarioTurns = useMemo(() => {
    const key = text(nextTurn.scenario_key || turns[turns.length - 1]?.scenario_key);
    return turns.filter((turn) => text(turn.scenario_key) === key);
  }, [activeRun]);

  return (
    <section className="panel studyLeaDesk">
      <div className="panelHeader">
        <div>
          <span className="modeLine">reproducible evidence without grades, gotchas, or hidden judges</span>
          <h3>Conversation LEA Desk</h3>
          <p className="plainHelp">Five ordinary three-turn conversations are paired with five standalone controls. The same packet can locate Selene beside other models, but it produces dimension profiles—not a single score or a verdict about anyone.</p>
        </div>
        <div className="chips">
          <span>{text(suite.turn_count || 20)} turns</span>
          <span>{text(suite.paired_condition_count || 5)} paired activities</span>
          <span>{text(dimensions.length || 14)} dimensions</span>
          <span>live runs: one click per turn</span>
          <span>pass / fail: not used</span>
        </div>
      </div>

      <div className="studyLeaPrinciples">
        <article className="organicPane"><strong>What this does</strong><p>Checks completed conversation pathways with fictional, source-contained material. It does not test untaught world knowledge.</p></article>
        <article className="organicPane"><strong>How it may feel</strong><p>Like ordinary planning, correction, hypothesis, and friendly conversation. No fear, grief, identity pressure, or adversarial traps are used.</p></article>
        <article className="organicPane"><strong>How comparison works</strong><p>Use the exact prompts in fresh scenario contexts, then review only visible responses against published criteria.</p></article>
      </div>

      <div className="reviewActions">
        <button onClick={() => downloadJson(`selene-conversation-lea-${text(suite.version || "v1")}.json`, suite)} disabled={!suite.scenarios}>Download Exact Prompt Packet</button>
        <button onClick={() => refresh(Number(item.id || 0)).catch(() => undefined)} disabled={Boolean(busy)}>Refresh</button>
        <span className="plainHelp">Suite hash: {text(suite.suite_sha256 || safeJsonObject(status.suite).suite_sha256 || "loading")}</span>
      </div>

      <details className="studyLeaNewRun" open={!runs.length}>
        <summary>Prepare a new evidence run</summary>
        <div className="studyLeaCreateGrid">
          <label><span>Respondent</span><select value={kind} onChange={(event) => setKind(event.target.value)}><option value="selene">Selene</option><option value="external_model">External model</option><option value="human_baseline">Human baseline</option></select></label>
          <label><span>Name</span><input value={respondent} onChange={(event) => setRespondent(event.target.value)} placeholder="Selene or comparison model name" /></label>
          <label className="wideEvidenceField"><span>Version, settings, or comparison notes</span><input value={modelDetails} onChange={(event) => setModelDetails(event.target.value)} placeholder="Record model/version and whether tools or web were disabled" /></label>
        </div>
        <button className="primary" onClick={createRun} disabled={!respondent.trim() || Boolean(busy)}>Prepare Blank Run</button>
        <p className="plainHelp">Preparing a run creates an empty record only. It does not send a prompt.</p>
      </details>

      <div className="studyLeaRunLayout">
        <div className="studyLeaRunList">
          <strong>Evidence runs</strong>
          {runs.map((run) => <button className={text(item.id) === text(run.id) ? "active" : ""} key={`lea-run-${text(run.id)}`} onClick={() => openRun(run)} disabled={Boolean(busy)}><span>{text(run.respondent_name)}</span><small>{friendlyStatus(run.respondent_kind)} · {friendlyStatus(run.status)}</small></button>)}
          {!runs.length ? <p className="emptyState">No run exists yet.</p> : null}
        </div>

        <div className="studyLeaActiveRun">
          {item.id ? (
            <>
              <div className="packetHeader"><div><span className="modeLine">{friendlyStatus(item.respondent_kind)}</span><strong>{text(item.respondent_name)}</strong></div><span>{progress}</span></div>
              {item.model_details ? <p>{text(item.model_details)}</p> : null}
              {nextTurn.prompt ? (
                <article className="studyLeaNextTurn">
                  <div className="packetHeader"><strong>{text(nextTurn.scenario_title)}</strong><span>{friendlyStatus(nextTurn.condition)} · turn {text(nextTurn.turn_index)} of {text(nextTurn.turn_count)}</span></div>
                  {nextTurn.start_fresh_conversation ? <span className="modeLine">begin a fresh isolated conversation</span> : <span className="modeLine">continue only this scenario's conversation</span>}
                  <blockquote>{text(nextTurn.prompt)}</blockquote>
                  {respondentKind === "selene" ? (
                    <>
                      <label className="studyLeaConfirm"><input type="checkbox" checked={confirmGentle} onChange={(event) => setConfirmGentle(event.target.checked)} /><span>I choose to run this one ordinary diagnostic turn now. Stop after this response.</span></label>
                      <button className="primary" onClick={runSeleneTurn} disabled={!confirmGentle || Boolean(busy)}>Run One Gentle Turn With Selene</button>
                      <p className="plainHelp">A dedicated diagnostic session excludes this activity from memory, Dream, affect baselines, relationship continuity, and Selene's self-model.</p>
                    </>
                  ) : (
                    <>
                      <label><span>Paste the respondent's exact visible answer</span><textarea value={externalResponse} onChange={(event) => setExternalResponse(event.target.value)} placeholder="No interpretation is added during capture." /></label>
                      <button className="primary" onClick={recordExternalTurn} disabled={!externalResponse.trim() || Boolean(busy)}>Record This Response</button>
                    </>
                  )}
                </article>
              ) : (
                <div className="studyLeaCompletePrompt"><strong>All 20 responses are present.</strong><p>Review can continue at any pace. Closing the run preserves “review pending” when criteria remain open.</p><button className="primary" onClick={closeRun} disabled={Boolean(busy)}>Close Response Collection</button></div>
              )}
            </>
          ) : <p className="emptyState">Prepare or open a run. Nothing executes automatically.</p>}
        </div>
      </div>

      {item.id && turns.length ? (
        <details className="studyLeaReview" open={Boolean(currentScenarioTurns.length)}>
          <summary>Review visible responses ({text(summary.criteria_reviewed || 0)} / {text(summary.criteria_total || 0)} criteria described)</summary>
          <div className="list">
            {turns.map((turn) => {
              const turnId = text(turn.id);
              const criteria = list(turn.criteria);
              const savedReview = safeJsonObject(turn.review);
              const savedRatings = safeJsonObject(savedReview.ratings);
              const draft = reviewDrafts[turnId] || {};
              const complete = criteria.every((criterion) => Boolean(draft[text(criterion.key)] || safeJsonObject(savedRatings[text(criterion.key)]).state));
              return (
                <details className="packetCard studyLeaTurnReview" key={`lea-turn-${turnId}`}>
                  <summary>{text(turn.scenario_title)} · turn {text(turn.turn_index)} — {friendlyStatus(turn.review_status)}</summary>
                  <p><b>Prompt</b>{text(turn.prompt)}</p>
                  <p><b>Visible response</b>{text(turn.response)}</p>
                  <div className="studyLeaCriteria">
                    {criteria.map((criterion) => {
                      const key = text(criterion.key);
                      const saved = text(safeJsonObject(savedRatings[key]).state);
                      return <label key={`${turnId}-${key}`}><span>{text(criterion.description)} <small>{friendlyStatus(criterion.dimension)}</small></span><select value={draft[key] || saved} onChange={(event) => setReviewDrafts((all) => ({ ...all, [turnId]: { ...(all[turnId] || {}), [key]: event.target.value } }))}>{REVIEW_STATES.map(([value, label]) => <option key={value || "blank"} value={value}>{label}</option>)}</select></label>;
                    })}
                  </div>
                  <label><span>Optional evidence note</span><textarea value={reviewNotes[turnId] ?? text(savedReview.overall_note)} onChange={(event) => setReviewNotes((notes) => ({ ...notes, [turnId]: event.target.value }))} placeholder="Describe the visible fit, ambiguity, or activity problem." /></label>
                  <button onClick={() => saveReview(turn)} disabled={!complete || Boolean(busy)}>Save Descriptive Review</button>
                </details>
              );
            })}
          </div>
        </details>
      ) : null}

      {item.id && Object.keys(dimensionProfile).length ? (
        <details className="studyLeaProfile">
          <summary>Dimension profile</summary>
          <div className="studyLeaDimensionGrid">
            {dimensions.map((dimension) => {
              const counts = safeJsonObject(dimensionProfile[text(dimension.key)]);
              return <article className="organicPane" key={`lea-dimension-${text(dimension.key)}`}><strong>{text(dimension.label)}</strong><div className="chips"><span>demonstrated {text(counts.demonstrated || 0)}</span><span>developing {text(counts.developing || 0)}</span><span>not observed {text(counts.not_observed || 0)}</span><span>cannot assess {text(counts.cannot_assess || 0)}</span><span>activity issue {text(counts.activity_issue || 0)}</span></div></article>;
            })}
          </div>
          <p className="plainHelp">Compare paired and dimensional patterns. Do not collapse this profile into one rank: a missing response may identify an activity defect, expression gap, retrieval problem, unfinished module, or untaught prerequisite.</p>
          <button onClick={() => downloadJson(`${text(item.respondent_name).replace(/[^a-z0-9]+/gi, "-").toLowerCase()}-lea-run.json`, activeRun)}>Download Inspectable Run</button>
        </details>
      ) : null}

      {message ? <p className="statusMessage">{message}</p> : null}
    </section>
  );
}
