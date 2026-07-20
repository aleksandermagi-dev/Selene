import { useEffect, useState } from "react";

import { api } from "./api";
import { friendlyStatus, text } from "./helpers";
import type { Dict } from "./types";


type SubjectDefinition = {
  key: string;
  label: string;
  description: string;
  endpoint?: string;
};

const SUBJECTS: SubjectDefinition[] = [
  {
    key: "language_conversation",
    label: "Language & Conversation",
    description: "Uncertainty, back-and-forth, explanation, repair, register, humor, and natural endings.",
    endpoint: "/api/language-teaching/items",
  },
  {
    key: "mathematics",
    label: "Mathematics",
    description: "Ordered foundations, operations, measurement, geometry, language, and later verified reasoning.",
    endpoint: "/api/curriculum-authorization/items",
  },
  {
    key: "science",
    label: "Science",
    description: "Observation, evidence, systems, biology, physical science, and uncertainty built in order.",
  },
  {
    key: "history_civics",
    label: "History & Civics",
    description: "Chronology, causation, sources, perspective, institutions, and contested interpretations.",
  },
  {
    key: "cross_subject",
    label: "Cross-Subject Integration",
    description: "Approved concepts that connect multiple subjects without turning teaching into identity or governance.",
    endpoint: "/api/teaching-lifecycle/items?limit=50",
  },
];


export default function CocoonSubjectClassrooms() {
  const [selected, setSelected] = useState<SubjectDefinition | null>(null);
  const [items, setItems] = useState<Dict[]>([]);
  const [state, setState] = useState<Dict>({ status: "subject_classrooms_standby" });

  useEffect(() => {
    if (!selected) {
      setItems([]);
      setState({ status: "subject_classrooms_standby" });
      return;
    }
    let cancelled = false;
    setItems([]);
    setState({ status: "loading", subject: selected.key });
    api<Dict>("/api/cocoon/bridge/wake", {
      method: "POST",
      body: JSON.stringify({
        channel: "teaching",
        subject_key: selected.key,
        reason: `${selected.label} classroom opened.`,
      }),
    }).catch(() => undefined);
    if (!selected.endpoint) {
      setState({ status: "subject_foundation_not_prepared", subject: selected.key });
      return () => { cancelled = true; };
    }
    api<{ items?: Dict[] }>(selected.endpoint)
      .then((result) => {
        if (cancelled) return;
        setItems(result.items || []);
        setState({ status: "subject_classroom_active", subject: selected.key });
      })
      .catch((err) => {
        if (cancelled) return;
        setState({ status: "subject_classroom_load_warning", error: err instanceof Error ? err.message : "Subject shelf could not load." });
      });
    return () => { cancelled = true; };
  }, [selected]);

  return (
    <section className="panel">
      <div className="panelHeader">
        <div>
          <h3>Subject Classrooms</h3>
          <p className="plainHelp">Each classroom stays in standby until opened. Leaving Teaching unmounts this module and releases its temporary subject state.</p>
        </div>
        <span>{selected ? `${selected.label} active` : "all subjects standby"}</span>
      </div>
      <div className="reviewActions">
        {SUBJECTS.map((subject) => (
          <button
            className={selected?.key === subject.key ? "primary" : ""}
            key={subject.key}
            onClick={() => setSelected((current) => current?.key === subject.key ? null : subject)}
          >
            {subject.label}
          </button>
        ))}
      </div>
      {selected ? (
        <div className="packetCard">
          <div className="packetHeader">
            <strong>{selected.label}</strong>
            <span>{friendlyStatus(state.status)}</span>
          </div>
          <p>{selected.description}</p>
          {state.status === "subject_foundation_not_prepared" ? (
            <p className="plainHelp">No reviewed classroom group is prepared yet. This is a curriculum gap, not Selene failing a subject.</p>
          ) : null}
          {items.length ? (
            <div className="list compactList packetList">
              {items.slice(0, 12).map((item, index) => (
                <article className="packetCard" key={`${selected.key}-${text(item.id || item.lesson_key || item.authorization_key || index)}`}>
                  <div className="packetHeader">
                    <strong>{text(item.title || item.lesson_title || item.lesson_key || item.authorization_key || "Reviewed lesson")}</strong>
                    <span>{friendlyStatus(item.status || item.review_status || "reviewed")}</span>
                  </div>
                  <p>{text(item.summary || item.description || item.scope || "Source-linked teaching item.")}</p>
                </article>
              ))}
            </div>
          ) : null}
        </div>
      ) : (
        <p className="emptyState">Choose a subject only when teaching or review is needed.</p>
      )}
    </section>
  );
}
