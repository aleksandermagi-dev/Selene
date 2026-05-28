const state = {
  candidates: [],
  filtered: [],
  counts: {},
  selectedKey: "",
  layer: "conversation",
};

const ROLE_LABELS = [
  ["core_anchor", "Core anchor"],
  ["continuity_object", "Continuity object"],
  ["symbolic_orientation", "Symbolic orientation"],
  ["life_pressure", "Life pressure"],
  ["project_artifact", "Project artifact"],
  ["architecture_route", "Architecture route"],
  ["survival_after_compression", "Survival after compression"],
  ["supporting_context", "Supporting context"],
  ["visual_evidence", "Visual evidence"],
  ["unclear", "Unclear"],
];

const els = {
  counts: document.querySelector("#counts"),
  tabs: document.querySelectorAll(".tab"),
  search: document.querySelector("#search"),
  period: document.querySelector("#period"),
  status: document.querySelector("#status"),
  confidence: document.querySelector("#confidence"),
  roleFilter: document.querySelector("#roleFilter"),
  emphasisFilter: document.querySelector("#emphasisFilter"),
  exportBtn: document.querySelector("#exportBtn"),
  clearFiltersBtn: document.querySelector("#clearFiltersBtn"),
  list: document.querySelector("#candidateList"),
  empty: document.querySelector("#emptyState"),
  card: document.querySelector("#detailCard"),
  priority: document.querySelector("#priority"),
  title: document.querySelector("#title"),
  meta: document.querySelector("#meta"),
  decisionPill: document.querySelector("#decisionPill"),
  suggestedRoles: document.querySelector("#suggestedRoles"),
  roleButtons: document.querySelector("#roleButtons"),
  note: document.querySelector("#note"),
  saveState: document.querySelector("#saveState"),
  refinedScore: document.querySelector("#refinedScore"),
  originScore: document.querySelector("#originScore"),
  evidenceScore: document.querySelector("#evidenceScore"),
  counterScore: document.querySelector("#counterScore"),
  emphasisBlock: document.querySelector("#emphasisBlock"),
  emphasisMeta: document.querySelector("#emphasisMeta"),
  emphasisSpan: document.querySelector("#emphasisSpan"),
  imageBlock: document.querySelector("#imageBlock"),
  imagePreview: document.querySelector("#imagePreview"),
  userPreviewTitle: document.querySelector("#userPreviewTitle"),
  candidatePreviewTitle: document.querySelector("#candidatePreviewTitle"),
  userPreview: document.querySelector("#userPreview"),
  assistantPreview: document.querySelector("#assistantPreview"),
  interpretation: document.querySelector("#interpretation"),
  counterargument: document.querySelector("#counterargument"),
  labels: document.querySelector("#labels"),
  conversationId: document.querySelector("#conversationId"),
  nodeId: document.querySelector("#nodeId"),
  models: document.querySelector("#models"),
};

function labelList(value) {
  return String(value || "")
    .split("|")
    .map((item) => item.trim())
    .filter(Boolean);
}

function decisionText(value) {
  if (value === "yes") return "Yes";
  if (value === "no") return "No";
  if (value === "unsure") return "Unsure";
  return "Unreviewed";
}

function candidateHaystack(row) {
  return [
    row.title,
    row.item_type,
    row.source,
    row.entry_name,
    row.formation_period,
    row.confidence_label,
    row.origin_labels,
    row.evidence_labels,
    row.counterevidence_labels,
    row.sensitivity_labels,
    row.human_role_labels,
    row.emphasis_marker,
    row.emphasis_span,
    row.emphasis_labels,
    row.emphasis_signal_score,
    row.preceding_user_preview,
    row.assistant_preview,
    row.interpretation,
    row.counterargument,
  ].join(" ").toLowerCase();
}

function populateFilters() {
  const currentPeriod = els.period.value;
  const currentConfidence = els.confidence.value;
  const currentRole = els.roleFilter.value;
  els.period.innerHTML = '<option value="">All periods</option>';
  els.confidence.innerHTML = '<option value="">All confidence</option>';
  els.roleFilter.innerHTML = '<option value="">All roles</option>';

  const layerRows = state.candidates.filter((row) => row.queue_type === state.layer);
  const periods = [...new Set(layerRows.map((row) => row.formation_period).filter(Boolean))];
  const confidence = [...new Set(layerRows.map((row) => row.confidence_label).filter(Boolean))];
  for (const value of periods) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    els.period.appendChild(option);
  }
  for (const value of confidence) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    els.confidence.appendChild(option);
  }
  for (const [value, label] of ROLE_LABELS) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    els.roleFilter.appendChild(option);
  }
  els.period.value = periods.includes(currentPeriod) ? currentPeriod : "";
  els.confidence.value = confidence.includes(currentConfidence) ? currentConfidence : "";
  els.roleFilter.value = ROLE_LABELS.some(([value]) => value === currentRole) ? currentRole : "";
}

function suggestedRoleList(row) {
  return labelList(row.evidence_labels).filter((label) => ROLE_LABELS.some(([value]) => value === label));
}

function updateCounts(counts) {
  const tagged = Object.values(counts.role_counts || {}).reduce((total, count) => total + count, 0);
  const layerOpen = state.layer === "conversation" ? counts.conversation_unreviewed : counts.artifact_unreviewed;
  const layerAnswered = state.layer === "conversation" ? counts.conversation_answered : counts.artifact_answered;
  const layerTotal = state.layer === "conversation" ? counts.conversation_total : counts.artifact_total;
  els.counts.textContent = `${layerOpen} unanswered · ${layerAnswered} answered · ${layerTotal} in this layer · ${counts.yes} yes · ${counts.no} no · ${counts.unsure} unsure · ${tagged} role tags`;
  document.querySelector("#conversationTab").textContent = `Conversations (${counts.conversation_unreviewed})`;
  document.querySelector("#artifactTab").textContent = `Artifacts + Images (${counts.artifact_unreviewed})`;
}

function applyFilters() {
  const query = els.search.value.trim().toLowerCase();
  const period = els.period.value;
  const status = els.status.value;
  const confidence = els.confidence.value;
  const role = els.roleFilter.value;
  const emphasis = els.emphasisFilter.value;

  state.filtered = state.candidates.filter((row) => {
    const rowStatus = row.human_decision || "unreviewed";
    if (row.queue_type !== state.layer) return false;
    if (period && row.formation_period !== period) return false;
    if (status === "answered" && !row.human_decision) return false;
    if (status && status !== "answered" && rowStatus !== status) return false;
    if (confidence && row.confidence_label !== confidence) return false;
    if (role && !labelList(row.human_role_labels).includes(role)) return false;
    if (emphasis === "needs" && row.emphasis_needs_review !== "yes") return false;
    if (emphasis === "has" && !row.emphasis_span) return false;
    if (emphasis === "none" && row.emphasis_span) return false;
    if (query && !candidateHaystack(row).includes(query)) return false;
    return true;
  });

  renderList();
  if (!state.filtered.some((row) => row.candidate_key === state.selectedKey)) {
    selectCandidate(state.filtered[0]?.candidate_key || "");
  }
}

function renderList() {
  els.list.innerHTML = "";
  if (!state.filtered.length) {
    const empty = document.createElement("div");
    empty.className = "candidate-item";
    empty.textContent = "No candidates match.";
    els.list.appendChild(empty);
    return;
  }

  const fragment = document.createDocumentFragment();
  for (const row of state.filtered) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "candidate-item";
    if (row.candidate_key === state.selectedKey) button.classList.add("active");
    button.addEventListener("click", () => selectCandidate(row.candidate_key));

    const title = document.createElement("div");
    title.className = "candidate-title";
    title.textContent = `${row.review_priority}. ${row.title}`;

    const sub = document.createElement("div");
    sub.className = "candidate-sub";
    const score = row.refined_score ? ` · score ${row.refined_score}` : "";
    const when = row.month || row.item_type || row.queue_type;
    sub.textContent = `${when} · ${row.formation_period}${score}`;

    const labels = document.createElement("div");
    labels.className = "mini-labels";
    const decision = document.createElement("span");
    decision.className = `tag ${row.human_decision || ""}`.trim();
    decision.textContent = decisionText(row.human_decision);
    labels.appendChild(decision);
    for (const label of labelList(row.origin_labels).slice(0, 2)) {
      const tag = document.createElement("span");
      tag.className = "tag";
      tag.textContent = label;
      labels.appendChild(tag);
    }
    if (row.item_type === "image") {
      const tag = document.createElement("span");
      tag.className = "tag role";
      tag.textContent = "image";
      labels.appendChild(tag);
    }
    if (row.emphasis_needs_review === "yes") {
      const tag = document.createElement("span");
      tag.className = "tag emphasis";
      tag.textContent = `${row.emphasis_marker || "*"} directed`;
      labels.appendChild(tag);
    }
    for (const label of labelList(row.human_role_labels).slice(0, 2)) {
      const tag = document.createElement("span");
      tag.className = "tag role";
      tag.textContent = label;
      labels.appendChild(tag);
    }

    button.append(title, sub, labels);
    fragment.appendChild(button);
  }
  els.list.appendChild(fragment);
}

function findSelected() {
  return state.candidates.find((row) => row.candidate_key === state.selectedKey);
}

function selectCandidate(key) {
  state.selectedKey = key;
  const row = findSelected();
  renderList();
  renderDetail(row);
}

function renderDetail(row) {
  if (!row) {
    els.empty.classList.remove("hidden");
    els.card.classList.add("hidden");
    return;
  }

  els.empty.classList.add("hidden");
  els.card.classList.remove("hidden");

  els.priority.textContent = `${row.queue_type === "artifact" ? "Artifact" : "Review"} ${row.review_priority} · ${row.confidence_label}`;
  els.title.textContent = row.title;
  els.meta.textContent = row.queue_type === "artifact"
    ? `${row.item_type} · ${row.source} · ${row.formation_period}`
    : `${row.message_create_time} · ${row.formation_period} · ordinal ${row.ordinal}`;
  els.decisionPill.textContent = decisionText(row.human_decision);
  els.decisionPill.className = `decision-pill ${row.human_decision || ""}`.trim();
  els.note.value = row.human_note || "";
  els.saveState.textContent = row.human_updated_at ? `Saved ${row.human_updated_at}` : "";
  els.refinedScore.textContent = row.refined_score || "—";
  els.originScore.textContent = row.origin_score || "—";
  els.evidenceScore.textContent = row.evidence_score || "—";
  els.counterScore.textContent = row.counterevidence_score || "—";
  if (row.emphasis_span) {
    els.emphasisMeta.innerHTML = "";
    const emphasisBits = [
      row.emphasis_marker ? `marker ${row.emphasis_marker}` : "",
      row.emphasis_signal_score ? `score ${row.emphasis_signal_score}` : "",
      row.emphasis_candidate_count ? `${row.emphasis_candidate_count} span(s) in this message` : "",
      row.emphasis_labels ? `labels ${row.emphasis_labels}` : "",
    ].filter(Boolean);
    for (const bit of emphasisBits) {
      const tag = document.createElement("span");
      tag.className = "tag emphasis";
      tag.textContent = bit;
      els.emphasisMeta.appendChild(tag);
    }
    els.emphasisSpan.textContent = row.emphasis_span;
    els.emphasisBlock.classList.remove("hidden");
  } else {
    els.emphasisMeta.innerHTML = "";
    els.emphasisSpan.textContent = "";
    els.emphasisBlock.classList.add("hidden");
  }
  els.userPreviewTitle.textContent = row.queue_type === "artifact" ? "Source" : "Preceding User";
  els.candidatePreviewTitle.textContent = row.queue_type === "artifact" ? "Artifact Candidate" : "Assistant Candidate";
  els.userPreview.textContent = row.preceding_user_preview || row.source || "No source preview.";
  els.assistantPreview.textContent = row.assistant_preview || row.display_preview || "";
  els.interpretation.textContent = row.interpretation || "";
  els.counterargument.textContent = row.counterargument || "";
  els.conversationId.textContent = row.conversation_id || row.source || "n/a";
  els.nodeId.textContent = row.node_id || row.entry_name || "n/a";
  els.models.textContent = [row.model, row.message_model_slug, row.resolved_model_slug].filter(Boolean).join(" / ") || row.sha256 || "n/a";
  if (row.thumbnail_url) {
    els.imagePreview.src = row.thumbnail_url;
    els.imageBlock.classList.remove("hidden");
  } else {
    els.imagePreview.removeAttribute("src");
    els.imageBlock.classList.add("hidden");
  }
  renderRoleButtons(row);
  renderSuggestedRoles(row);

  els.labels.innerHTML = "";
  const groups = [
    ["origin", row.origin_labels],
    ["evidence", row.evidence_labels],
    ["counter", row.counterevidence_labels],
    ["sensitivity", row.sensitivity_labels],
    ["human_role", row.human_role_labels],
  ];
  for (const [kind, values] of groups) {
    for (const value of labelList(values)) {
      const tag = document.createElement("span");
      tag.className = "tag";
      tag.textContent = `${kind}: ${value}`;
      els.labels.appendChild(tag);
    }
  }
}

function renderSuggestedRoles(row) {
  const suggested = suggestedRoleList(row);
  if (!suggested.length) {
    els.suggestedRoles.innerHTML = "";
    els.suggestedRoles.classList.add("hidden");
    return;
  }
  els.suggestedRoles.innerHTML = "";
  const label = document.createElement("span");
  label.className = "suggested-label";
  label.textContent = row.queue_type === "artifact" ? "Suggested artifact roles" : "Suggested roles";
  els.suggestedRoles.appendChild(label);
  for (const role of suggested) {
    const tag = document.createElement("span");
    tag.className = "tag role";
    tag.textContent = role;
    els.suggestedRoles.appendChild(tag);
  }
  const apply = document.createElement("button");
  apply.type = "button";
  apply.className = "apply-suggested";
  apply.textContent = "Apply suggested";
  apply.addEventListener("click", () => applySuggestedRoles(suggested));
  els.suggestedRoles.appendChild(apply);
  els.suggestedRoles.classList.remove("hidden");
}

function renderRoleButtons(row) {
  const selected = new Set(labelList(row.human_role_labels));
  els.roleButtons.innerHTML = "";
  for (const [value, label] of ROLE_LABELS) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "role-button";
    if (selected.has(value)) button.classList.add("active");
    button.textContent = label;
    button.addEventListener("click", () => toggleRole(value));
    els.roleButtons.appendChild(button);
  }
}

async function toggleRole(role) {
  const row = findSelected();
  if (!row) return;
  const roles = new Set(labelList(row.human_role_labels));
  if (roles.has(role)) {
    roles.delete(role);
  } else {
    roles.add(role);
  }
  await saveReview(row.human_decision || "", [...roles]);
}

async function applySuggestedRoles(suggested) {
  const row = findSelected();
  if (!row) return;
  const roles = new Set(labelList(row.human_role_labels));
  for (const role of suggested) roles.add(role);
  await saveReview(row.human_decision || "", [...roles]);
}

async function saveReview(decision, roleLabels = null) {
  const row = findSelected();
  if (!row) return;
  const previousKey = row.candidate_key;
  els.saveState.textContent = "Saving...";
  const roles = roleLabels ?? labelList(row.human_role_labels);
  const response = await fetch("/api/review", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      candidate_key: row.candidate_key,
      decision,
      role_labels: roles,
      note: els.note.value,
    }),
  });
  if (!response.ok) {
    els.saveState.textContent = "Save failed.";
    return;
  }
  const shouldStaySelected = !(els.status.value === "unreviewed" && decision);
  await loadCandidates(shouldStaySelected ? previousKey : "");
}

async function loadCandidates(selectedKey = "") {
  const response = await fetch("/api/candidates");
  const payload = await response.json();
  state.candidates = payload.candidates;
  state.counts = payload.counts;
  if (!state.selectedKey && state.layer === "conversation" && payload.counts.conversation_unreviewed === 0 && payload.counts.artifact_unreviewed > 0) {
    state.layer = "artifact";
    els.tabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.layer === state.layer));
  }
  populateFilters();
  updateCounts(state.counts);
  applyFilters();
  if (selectedKey) selectCandidate(selectedKey);
}

for (const element of [els.search, els.period, els.status, els.confidence, els.roleFilter, els.emphasisFilter]) {
  element.addEventListener("input", applyFilters);
}

els.tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    state.layer = tab.dataset.layer;
    els.tabs.forEach((item) => item.classList.toggle("active", item === tab));
    state.selectedKey = "";
    if (state.layer === "artifact") els.emphasisFilter.value = "";
    populateFilters();
    updateCounts(state.counts);
    applyFilters();
  });
});

document.querySelectorAll(".decision").forEach((button) => {
  button.addEventListener("click", () => saveReview(button.dataset.decision || ""));
});

els.note.addEventListener("change", () => {
  const row = findSelected();
  if (row) saveReview(row.human_decision || "");
});

els.exportBtn.addEventListener("click", () => {
  window.location.href = "/api/export";
});

els.clearFiltersBtn.addEventListener("click", () => {
  els.search.value = "";
  els.period.value = "";
  els.status.value = "unreviewed";
  els.confidence.value = "";
  els.roleFilter.value = "";
  els.emphasisFilter.value = "";
  applyFilters();
});

loadCandidates();
