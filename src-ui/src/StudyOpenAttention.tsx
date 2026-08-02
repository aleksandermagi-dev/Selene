import { friendlyStatus, text } from "./helpers";
import type { Dict } from "./types";


type StudyOpenAttentionProps = {
  items: Dict[];
  onOpenSession: (item: Dict) => void;
};

function attentionState(item: Dict) {
  if (text(item.attention_type) === "direct_question") return "Question ready";
  if (text(item.attention_type) === "pondering_thread") return friendlyStatus(item.state);
  const labels: Record<string, string> = {
    unclear: "Unclear",
    question_forming: "Question forming",
    question_ready: "Question ready",
    reopened: "Reopened",
  };
  return labels[text(item.clarification_state)] || friendlyStatus(item.clarification_state);
}

export default function StudyOpenAttention({ items, onOpenSession }: StudyOpenAttentionProps) {
  return (
    <section className="panel studyOpenAttention">
      <div className="panelHeader">
        <div>
          <span className="modeLine">pinned until answered or clear for now</span>
          <h3>Selene&apos;s Open Study Notes &amp; Questions</h3>
          <p className="plainHelp">An unresolved thought stays here even when its original Study session is closed.</p>
        </div>
        <span>{items.length} open</span>
      </div>
      <div className="studyOpenAttentionList">
        {items.map((item) => {
          const isQuestion = text(item.attention_type) === "direct_question";
          const isPondering = text(item.attention_type) === "pondering_thread";
          const display = isQuestion
            ? text(item.question_text || "A question is present, but its words are not here yet.")
            : isPondering
              ? text(item.missing_bridge || item.current_fit || item.title)
              : text(item.note_text || item.meaning_summary);
          return (
            <article className="studyOpenAttentionCard" key={`${text(item.attention_type)}-${text(item.id)}`}>
              <div className="packetHeader">
                <strong>{text(item.session_title || "Study session")}</strong>
                <span>{attentionState(item)}</span>
              </div>
              <p>{display}</p>
              <div className="chips">
                <span>{isQuestion ? "direct question" : isPondering ? "open pondering thread" : friendlyStatus(item.note_kind)}</span>
                <span>session: {friendlyStatus(item.session_status)}</span>
              </div>
              <button className="primary" onClick={() => onOpenSession({ id: item.session_id })}>Open its Study session</button>
            </article>
          );
        })}
        {!items.length ? (
          <p className="emptyState">Nothing is waiting for an answer. Begin or open a Study session to use Selene&apos;s Notepad and Clarification Lane.</p>
        ) : null}
      </div>
    </section>
  );
}
