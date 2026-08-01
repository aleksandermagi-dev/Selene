import { useMemo, useState } from "react";

import { text } from "./helpers";
import type { Dict } from "./types";


type StudyLibraryProps = {
  materials: Dict[];
  sessions: Dict[];
  selectedConceptId: string;
  onSelectMaterial: (item: Dict) => void;
  onOpenSession: (item: Dict) => void;
};

type SubjectShelf = {
  key: string;
  label: string;
  order: number;
  items: Dict[];
};

const SUBJECT_RULES = [
  { key: "language", label: "Language & Conversation", order: 10, terms: ["language", "conversation", "literacy", "english", "writing", "reading"] },
  { key: "mathematics", label: "Mathematics", order: 20, terms: ["math", "arithmetic", "fraction", "geometry", "algebra", "statistics", "number", "operation", "measurement", "time", "capacity", "mass", "data", "equal_group"] },
  { key: "science", label: "Science", order: 30, terms: ["science", "biology", "chemistry", "physics", "earth", "astronomy"] },
  { key: "history-civics", label: "History & Civics", order: 40, terms: ["history", "civic", "government", "geography", "community", "cooperation", "fairness", "rules"] },
  { key: "social-understanding", label: "Social Understanding", order: 50, terms: ["social", "psychology", "economics", "culture"] },
  { key: "philosophy-reasoning", label: "Philosophy & Reasoning", order: 60, terms: ["philosophy", "reasoning", "logic", "epistem"] },
  { key: "technology-engineering", label: "Technology & Engineering", order: 70, terms: ["technology", "engineering", "comput", "code"] },
  { key: "arts-humanities", label: "Arts & Humanities", order: 80, terms: ["art", "music", "literature", "poetry", "humanities"] },
] as const;

function subjectFor(item: Dict) {
  const domain = text(item.domain).toLowerCase();
  const match = SUBJECT_RULES.find((rule) => rule.terms.some((term) => domain.includes(term)));
  return match || { key: "cross-subject", label: "Cross-Subject & Other", order: 90, terms: [] };
}

function conceptIds(session: Dict) {
  const value = session.concept_ids;
  if (Array.isArray(value)) return value.map(Number).filter((item) => item > 0);
  return [];
}

function latestSessionFor(material: Dict, sessions: Dict[]) {
  const conceptId = Number(material.id || 0);
  return sessions.find((session) => conceptIds(session).includes(conceptId));
}

function materialState(material: Dict, sessions: Dict[]) {
  const session = latestSessionFor(material, sessions);
  if (!session) return { key: "new", label: "New" };
  if (Number(session.open_question_count || 0) > 0) return { key: "questions", label: "Questions" };
  if (Number(session.open_clarification_count || 0) > 0) return { key: "clarification", label: "Clarification" };
  const status = text(session.status);
  if (status === "active") return { key: "studying", label: "Studying" };
  if (status === "paused") return { key: "revisit", label: "Revisit" };
  if (status === "completed") return { key: "studied", label: "Studied" };
  return { key: "new", label: "New" };
}

function compareMaterials(left: Dict, right: Dict) {
  const leftSubject = subjectFor(left);
  const rightSubject = subjectFor(right);
  return leftSubject.order - rightSubject.order
    || text(left.domain).localeCompare(text(right.domain))
    || text(left.title).localeCompare(text(right.title));
}

function buildShelves(materials: Dict[]) {
  const grouped = new Map<string, SubjectShelf>();
  [...materials].sort(compareMaterials).forEach((item) => {
    const subject = subjectFor(item);
    const shelf = grouped.get(subject.key) || { key: subject.key, label: subject.label, order: subject.order, items: [] };
    shelf.items.push(item);
    grouped.set(subject.key, shelf);
  });
  return [...grouped.values()].sort((left, right) => left.order - right.order || left.label.localeCompare(right.label));
}

export default function StudyLibrary({
  materials,
  sessions,
  selectedConceptId,
  onSelectMaterial,
  onOpenSession,
}: StudyLibraryProps) {
  const [query, setQuery] = useState("");
  const [subjectFilter, setSubjectFilter] = useState("all");
  const [openSubject, setOpenSubject] = useState("");
  const [expandedMaterial, setExpandedMaterial] = useState("");

  const shelves = useMemo(() => buildShelves(materials), [materials]);
  const filteredShelves = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return shelves
      .filter((shelf) => subjectFilter === "all" || shelf.key === subjectFilter)
      .map((shelf) => ({
        ...shelf,
        items: shelf.items.filter((item) => !needle || [item.title, item.domain, item.central_claim]
          .some((value) => text(value).toLowerCase().includes(needle))),
      }))
      .filter((shelf) => shelf.items.length > 0);
  }, [query, shelves, subjectFilter]);

  const queue = useMemo(() => {
    const continuing = sessions
      .filter((session) => ["active", "paused"].includes(text(session.status)))
      .slice(0, 6)
      .map((session) => ({ kind: "session" as const, item: session }));
    const seenConcepts = new Set(sessions.flatMap(conceptIds));
    const available = [...materials]
      .sort(compareMaterials)
      .filter((item) => !seenConcepts.has(Number(item.id || 0)))
      .slice(0, Math.max(0, 6 - continuing.length))
      .map((item) => ({ kind: "material" as const, item }));
    return [...continuing, ...available];
  }, [materials, sessions]);

  return (
    <div className="studyLibraryGrid">
      <section className="panel studyQueuePanel">
        <div className="panelHeader">
          <div>
            <h3>Learning Queue</h3>
            <p className="plainHelp">Continue current work first, then choose from the next untouched foundations.</p>
          </div>
          <span>{queue.length} shown</span>
        </div>
        <div className="studyQueueList">
          {queue.map((entry) => {
            if (entry.kind === "session") {
              const session = entry.item;
              const status = Number(session.open_question_count || 0) > 0
                ? "Questions"
                : Number(session.open_clarification_count || 0) > 0
                  ? "Clarification"
                  : text(session.status) === "paused" ? "Revisit" : "Studying";
              return (
                <button className="studyQueueRow" key={`queue-session-${text(session.id)}`} onClick={() => onOpenSession(session)}>
                  <span><strong>{text(session.title || "Study session")}</strong><small>{text(session.focus || "Continue deliberate study")}</small></span>
                  <em>{status}</em>
                </button>
              );
            }
            const material = entry.item;
            return (
              <button className="studyQueueRow" key={`queue-material-${text(material.id)}`} onClick={() => onSelectMaterial(material)}>
                <span><strong>{text(material.title || "Approved material")}</strong><small>{subjectFor(material).label}</small></span>
                <em>Next available</em>
              </button>
            );
          })}
          {!queue.length ? <p className="emptyState">Nothing is waiting. The shelf remains available whenever study feels useful.</p> : null}
        </div>
      </section>

      <section className="panel studyBookshelfPanel">
        <div className="panelHeader">
          <div>
            <h3>Bookshelf</h3>
            <p className="plainHelp">All approved material remains available. Shelves are only visual organization.</p>
          </div>
          <span>{materials.length} materials</span>
        </div>
        <div className="studyShelfFilters">
          <label>
            <span>Find a topic</span>
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search titles, subjects, or concepts" />
          </label>
          <label>
            <span>Subject</span>
            <select value={subjectFilter} onChange={(event) => setSubjectFilter(event.target.value)}>
              <option value="all">All subjects</option>
              {shelves.map((shelf) => <option key={shelf.key} value={shelf.key}>{shelf.label} ({shelf.items.length})</option>)}
            </select>
          </label>
        </div>
        <div className="studyShelves">
          {filteredShelves.map((shelf) => {
            const isOpen = Boolean(query.trim()) || subjectFilter !== "all" || openSubject === shelf.key;
            return (
              <section className="studyShelf" key={shelf.key}>
                <button
                  className="studyShelfHeader"
                  aria-expanded={isOpen}
                  onClick={() => setOpenSubject((current) => current === shelf.key ? "" : shelf.key)}
                >
                  <span>{shelf.label}</span>
                  <small>{shelf.items.length} {shelf.items.length === 1 ? "material" : "materials"} · {isOpen ? "close" : "open"}</small>
                </button>
                {isOpen ? (
                  <div className="studyShelfRows">
                    {shelf.items.map((item) => {
                      const id = text(item.id);
                      const status = materialState(item, sessions);
                      const isExpanded = expandedMaterial === id;
                      const isSelected = selectedConceptId === id;
                      return (
                        <article className={`studyMaterialRow${isSelected ? " selected" : ""}`} key={`shelf-material-${id}`}>
                          <button className="studyMaterialSummary" onClick={() => setExpandedMaterial((current) => current === id ? "" : id)} aria-expanded={isExpanded}>
                            <span><strong>{text(item.title || "Approved material")}</strong><small>{text(item.domain || shelf.label)}</small></span>
                            <em className={`studyState ${status.key}`}>{status.label}</em>
                          </button>
                          {isExpanded ? (
                            <div className="studyMaterialDetail">
                              <p>{text(item.central_claim || "Approved source-linked knowledge material.")}</p>
                              <div className="chips">
                                <span>{text(item.confidence || "reviewed confidence")}</span>
                                <span>{Array.isArray(item.source_refs) ? item.source_refs.length : 0} source references</span>
                              </div>
                              {Array.isArray(item.source_refs) && item.source_refs.length ? (
                                <details className="studySourceRefs">
                                  <summary>View source provenance</summary>
                                  <ul>{item.source_refs.map((source, index) => <li key={`${id}-source-${index}`}>{text(source)}</li>)}</ul>
                                </details>
                              ) : null}
                              <div className="reviewActions">
                                <button className="primary" onClick={() => onSelectMaterial(item)}>{isSelected ? "Selected for Desk" : "Move to Study Desk"}</button>
                              </div>
                            </div>
                          ) : null}
                        </article>
                      );
                    })}
                  </div>
                ) : null}
              </section>
            );
          })}
          {!filteredShelves.length ? <p className="emptyState">No approved materials match that search.</p> : null}
        </div>
      </section>
    </div>
  );
}
