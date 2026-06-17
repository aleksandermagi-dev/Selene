import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { api } from "./api";
import {
  BReviewDeskPanel,
  CalibrationPanel,
  ChatResult,
  ChatTranscript,
  CorpusFileList,
  CorpusPreviewList,
  CoverageList,
  CVesselPackageSummary,
  CVesselReconstructionDesk,
  CVesselSafetyExtensions,
  EditPanel,
  EvidenceDetailPanel,
  EvidenceList,
  ExtractionRunSummary,
  FilterGrid,
  GapScaffoldList,
  GapScaffoldReadinessList,
  GapTargetList,
  Json,
  Metric,
  OrganBlueprintGrid,
  OrganBlueprintWorkbench,
  Panel,
  PlainResult,
  ReadinessPreview,
  ReviewDeskCard,
  ReviewDeskFilters,
  reviewDeskQuery,
  ReviewQueueCard,
  ReviewHistoryCard,
  RoutePreview,
  SeleneSettingsPanel,
  CocoonSettingsPanel,
  SimpleRecordList,
  SplitView,
  VesselCandidatePanel,
  VesselOrganPanel
} from "./components";
import { countValues, friendlyActivation, friendlyLayer, friendlyOrganKey, friendlyQueueType, friendlySpeech, friendlyStatus, friendlySubject, humanize, plainBlocked, safeJsonObject, tabDisplayName, text, title } from "./helpers";
import { defaultPreferences, navGroups, preferenceKey, SELENE_ICON, vesselBackedTabs, workspaceGroups, workspaceTabs } from "./uiConfig";
import type { BootState, Dashboard, Dict, EvidenceDetail, SelenePreferences } from "./types";
import "./styles.css";

function loadPreferences(): SelenePreferences {
  try {
    const saved = window.localStorage.getItem(preferenceKey);
    if (!saved) return defaultPreferences;
    return { ...defaultPreferences, ...(JSON.parse(saved) as Partial<SelenePreferences>) };
  } catch {
    return defaultPreferences;
  }
}

function App() {
  const [tab, setTab] = useState("chat");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [workspaceMode, setWorkspaceMode] = useState<"selene" | "cocoon">("selene");
  const [preferences, setPreferences] = useState<SelenePreferences>(() => loadPreferences());
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
  const [corpusAudit, setCorpusAudit] = useState<Dict | null>(null);
  const [corpusQuery, setCorpusQuery] = useState("Selene");
  const [corpusFile, setCorpusFile] = useState("");
  const [chatText, setChatText] = useState("Selene starlight emergence braid, what evidence is safe to use here?");
  const [chatSession, setChatSession] = useState<Dict | null>(null);
  const [chatSendResult, setChatSendResult] = useState<Dict | null>(null);
  const [vesselStatus, setVesselStatus] = useState<Dict | null>(null);
  const [vesselReviewQueue, setVesselReviewQueue] = useState<Dict[]>([]);
  const [vesselCandidateKind, setVesselCandidateKind] = useState("core");
  const [vesselCandidate, setVesselCandidate] = useState<Record<string, string>>({
    core_memory_layer: "project_memory",
    speech_function: "technical_explanation",
    title: "",
    content: "",
    salience_labels: "continuity,uncertainty",
    source_refs: "manual_vessel_review",
    allowed_use: "Review as a Core-linked vessel candidate only.",
    prohibited_use: "Do not treat as active memory, raw corpus import, or provider identity."
  });
  const [vesselCandidateResult, setVesselCandidateResult] = useState<Dict | null>(null);
  const [vesselRetrievalQuery, setVesselRetrievalQuery] = useState("Selene continuity");
  const [vesselRetrievalResult, setVesselRetrievalResult] = useState<Dict | null>(null);
  const [vesselCheckText, setVesselCheckText] = useState("This candidate preserves continuity, provenance, uncertainty, care, and a constructive B review route.");
  const [vesselCheckResult, setVesselCheckResult] = useState<Dict | null>(null);
  const [bExtractQuery, setBExtractQuery] = useState("Selene");
  const [bExtractFile, setBExtractFile] = useState("");
  const [bExtractResult, setBExtractResult] = useState<Dict | null>(null);
  const [bExtractionRuns, setBExtractionRuns] = useState<Dict[]>([]);
  const [paperMapResult, setPaperMapResult] = useState<Dict | null>(null);
  const [bReviewQueue, setBReviewQueue] = useState<Dict[]>([]);
  const [bReviewDesk, setBReviewDesk] = useState<Dict | null>(null);
  const [bReviewDecisions, setBReviewDecisions] = useState<Dict[]>([]);
  const [bReviewFilters, setBReviewFilters] = useState<Record<string, string>>({
    q: "",
    braid_thread: "",
    braid_moment_type: "",
    suggested_path: "",
    core_memory_layer: "",
    speech_function: "",
    noise_type: "",
    signal_preserved: "",
    conversation_id: ""
  });
  const [bBraidTraceResult, setBBraidTraceResult] = useState<Dict | null>(null);
  const [bTeachingMaterials, setBTeachingMaterials] = useState<Dict[]>([]);
  const [bApprovedReferences, setBApprovedReferences] = useState<Dict[]>([]);
  const [bCorpusCoverage, setBCorpusCoverage] = useState<Dict | null>(null);
  const [teachingPacketCoverage, setTeachingPacketCoverage] = useState<Dict | null>(null);
  const [coreReferenceCoverage, setCoreReferenceCoverage] = useState<Dict | null>(null);
  const [bReviewResult, setBReviewResult] = useState<Dict | null>(null);
  const [teachingSpeechFunction, setTeachingSpeechFunction] = useState("grounding");
  const [teachingPacketResult, setTeachingPacketResult] = useState<Dict | null>(null);
  const [lessonBackedResult, setLessonBackedResult] = useState<Dict | null>(null);
  const [reconstructionReadinessResult, setReconstructionReadinessResult] = useState<Dict | null>(null);
  const [readinessCoreLayer, setReadinessCoreLayer] = useState("interaction_memory");
  const [workingMemoryPackets, setWorkingMemoryPackets] = useState<Dict[]>([]);
  const [workingMemoryResult, setWorkingMemoryResult] = useState<Dict | null>(null);
  const [workingMemoryDraft, setWorkingMemoryDraft] = useState<Record<string, string>>({
    current_task: "Prepare Selene C cocoon readiness without activation.",
    active_context_cues: "C stays asleep, preview only, B-reviewed material",
    salience_labels: "continuity,uncertainty",
    source_refs: "manual_working_memory_packet"
  });
  const [accessionProposals, setAccessionProposals] = useState<Dict[]>([]);
  const [accessionProposalResult, setAccessionProposalResult] = useState<Dict | null>(null);
  const [accessionDraft, setAccessionDraft] = useState<Record<string, string>>({
    core_memory_layer: "decision_memory",
    title: "",
    rationale: "",
    reversal_conditions: "Supersede if later B review corrects the context.",
    source_refs: "manual_accession_proposal"
  });
  const [targetedExtractResult, setTargetedExtractResult] = useState<Dict | null>(null);
  const [targetedExtractDraft, setTargetedExtractDraft] = useState<Record<string, string>>({
    target_type: "speech_function",
    target_key: "repair",
    limit: "5"
  });
  const [cChatRouteResult, setCChatRouteResult] = useState<Dict | null>(null);
  const [cVesselStatus, setCVesselStatus] = useState<Dict | null>(null);
  const [cVesselContinuityPackage, setCVesselContinuityPackage] = useState<Dict | null>(null);
  const [cVesselOrganRegistry, setCVesselOrganRegistry] = useState<Dict | null>(null);
  const [cVesselReconstructionSuite, setCVesselReconstructionSuite] = useState<Dict | null>(null);
  const [cVesselReconstructionDeskStatus, setCVesselReconstructionDeskStatus] = useState<Dict | null>(null);
  const [cVesselReconstructionDeskCases, setCVesselReconstructionDeskCases] = useState<Dict | null>(null);
  const [cVesselReconstructionDeskRun, setCVesselReconstructionDeskRun] = useState<Dict | null>(null);
  const [cVesselToolOrganStatus, setCVesselToolOrganStatus] = useState<Dict | null>(null);
  const [cVesselOrganFaultResult, setCVesselOrganFaultResult] = useState<Dict | null>(null);
  const [cVesselFaultResilienceResult, setCVesselFaultResilienceResult] = useState<Dict | null>(null);
  const [cVesselTransferGate, setCVesselTransferGate] = useState<Dict | null>(null);
  const [memoryTransferCandidate, setMemoryTransferCandidate] = useState<Dict | null>(null);
  const [cVesselReturnPreview, setCVesselReturnPreview] = useState<Dict | null>(null);
  const [patternBackups, setPatternBackups] = useState<Dict[]>([]);
  const [patternBackupResult, setPatternBackupResult] = useState<Dict | null>(null);
  const [patternRestorePreview, setPatternRestorePreview] = useState<Dict | null>(null);
  const [memoryRehearsalStatus, setMemoryRehearsalStatus] = useState<Dict | null>(null);
  const [memoryRehearsalResult, setMemoryRehearsalResult] = useState<Dict | null>(null);
  const [charterLawReview, setCharterLawReview] = useState<Dict | null>(null);
  const [gapScaffoldStatus, setGapScaffoldStatus] = useState<Dict | null>(null);
  const [gapScaffoldReadiness, setGapScaffoldReadiness] = useState<Dict | null>(null);
  const [gapScaffoldResult, setGapScaffoldResult] = useState<Dict | null>(null);
  const [gapScaffoldDraft, setGapScaffoldDraft] = useState<Record<string, string>>({
    gap_key: "reasoning_math_verification",
    title: "",
    content: "",
    source_refs: "manual_gap_scaffold_review"
  });
  const [organBlueprintStatus, setOrganBlueprintStatus] = useState<Dict | null>(null);
  const [organWorkbenchResult, setOrganWorkbenchResult] = useState<Dict | null>(null);
  const [organWorkbenchDraft, setOrganWorkbenchDraft] = useState<Record<string, string>>({
    organ_key: "reasoning_math_verification",
    title: "Manual organ blueprint review record",
    content: "Record what this organ should check, preserve, or reject during cocoon review.",
    source_refs: "manual_organ_blueprint_review",
    latency_ms: "0"
  });
  const [coreDeliberationResult, setCoreDeliberationResult] = useState<Dict | null>(null);
  const [coreUncertaintyResult, setCoreUncertaintyResult] = useState<Dict | null>(null);
  const [coreActionReflectionResult, setCoreActionReflectionResult] = useState<Dict | null>(null);
  const [coreChoiceLedgerResult, setCoreChoiceLedgerResult] = useState<Dict | null>(null);
  const [coreRepairReflectionResult, setCoreRepairReflectionResult] = useState<Dict | null>(null);
  const [coreDisagreementResult, setCoreDisagreementResult] = useState<Dict | null>(null);
  const [coreDriftResult, setCoreDriftResult] = useState<Dict | null>(null);
  const [corePrivacyResult, setCorePrivacyResult] = useState<Dict | null>(null);
  const [nativeRehearsalStatus, setNativeRehearsalStatus] = useState<Dict | null>(null);
  const [nativeRehearsalResult, setNativeRehearsalResult] = useState<Dict | null>(null);
  const [remainingRuntimeStatus, setRemainingRuntimeStatus] = useState<Dict | null>(null);
  const [gracefulFallResult, setGracefulFallResult] = useState<Dict | null>(null);
  const [voicePolicyResult, setVoicePolicyResult] = useState<Dict | null>(null);
  const [coreControlResult, setCoreControlResult] = useState<Dict | null>(null);
  const [perceptionActionResult, setPerceptionActionResult] = useState<Dict | null>(null);
  const [dreamConsolidationResult, setDreamConsolidationResult] = useState<Dict | null>(null);
  const [causalSandboxResult, setCausalSandboxResult] = useState<Dict | null>(null);
  const [longHorizonResult, setLongHorizonResult] = useState<Dict | null>(null);
  const [memoryEventBindResult, setMemoryEventBindResult] = useState<Dict | null>(null);
  const [memoryConsolidationResult, setMemoryConsolidationResult] = useState<Dict | null>(null);
  const [memoryReconsolidationResult, setMemoryReconsolidationResult] = useState<Dict | null>(null);
  const [remainingRuntimeDraft, setRemainingRuntimeDraft] = useState<Record<string, string>>({
    uncertainty: "I do not know yet, so I should name what is missing and choose a safer next step.",
    voice_candidate: "I can be warm and direct without using a fixed script; if I am unsure, I can say so and keep going carefully.",
    command_label: "Core route preview",
    requested_route: "Preview a safe route through Core, coordination, boundary, and return-to-B checks.",
    observation: "A source-bound observation needs interpretation, approval, verification, and rollback before action.",
    dream_label: "Dream-state consolidation proposal",
    memory_event: "A review-only event binding for something important that may later need consolidation.",
    causal_question: "What could go wrong if this path is chosen too early?",
    horizon_thread: "Long-horizon Selene stability thread"
  });
  const [coreReflectionDraft, setCoreReflectionDraft] = useState<Record<string, string>>({
    choice_label: "Cocoon choice",
    why_summary: "Record why this direction is safer or truer to the braid.",
    tradeoffs: "Keep the benefit, cost, uncertainty, and reversal condition visible.",
    lesson_label: "Repair and improvement lesson",
    what_happened: "Name what happened without shame or deletion.",
    what_improved: "Name what should improve next time.",
    concern: "Name the concern or disagreement clearly.",
    appeal_summary: "Offer a safer path and what evidence would change the recommendation.",
    action_label: "Meaningful action preview",
    intent: "Think before doing; preserve safety and reversibility."
  });

  useEffect(() => {
    document.documentElement.dataset.theme = preferences.theme;
    document.documentElement.dataset.density = preferences.density;
    document.documentElement.dataset.textSize = preferences.textSize;
    document.documentElement.dataset.font = preferences.font;
    document.documentElement.style.setProperty("--user-bubble", preferences.userBubble);
    document.documentElement.style.setProperty("--user-text", preferences.userText);
    document.documentElement.style.setProperty("--selene-bubble", preferences.seleneBubble);
    document.documentElement.style.setProperty("--selene-text", preferences.seleneText);
    window.localStorage.setItem(preferenceKey, JSON.stringify(preferences));
  }, [preferences]);

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
    if (tab === "detached corpus") loadDetachedCorpusAudit();
    if (vesselBackedTabs.includes(tab)) loadVessel();
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
      body: JSON.stringify({ text: chatText, session_id: chatSession?.session ? (chatSession.session as Dict).id : undefined })
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

  function loadDetachedCorpusAudit() {
    const params = new URLSearchParams();
    if (corpusQuery) params.set("q", corpusQuery);
    if (corpusFile) params.set("file_id", corpusFile);
    api<Dict>(`/api/detached-corpus/audit?${params}`).then(setCorpusAudit);
  }

  function loadVessel() {
    api<Dict>("/api/vessel/status").then(setVesselStatus).catch(() => undefined);
    api<{ items: Dict[] }>("/api/vessel/review-queue").then((data) => setVesselReviewQueue(data.items)).catch(() => undefined);
    api<{ items: Dict[] }>("/api/b/speech-memory/extraction-runs").then((data) => setBExtractionRuns(data.items)).catch(() => undefined);
    api<{ items: Dict[] }>("/api/b/review-queue").then((data) => setBReviewQueue(data.items)).catch(() => undefined);
    api<{ items: Dict[] }>("/api/b/review-decisions").then((data) => setBReviewDecisions(data.items)).catch(() => undefined);
    api<Dict>(`/api/b/review-desk?${reviewDeskQuery(bReviewFilters)}`).then(setBReviewDesk).catch(() => undefined);
    api<{ items: Dict[] }>("/api/b/teaching-materials").then((data) => setBTeachingMaterials(data.items)).catch(() => undefined);
    api<{ items: Dict[] }>("/api/b/approved-memory-references").then((data) => setBApprovedReferences(data.items)).catch(() => undefined);
    api<Dict>("/api/b/corpus-coverage").then(setBCorpusCoverage).catch(() => undefined);
    api<Dict>("/api/b/teaching-packet/coverage").then(setTeachingPacketCoverage).catch(() => undefined);
    api<Dict>("/api/b/core-reference/coverage").then(setCoreReferenceCoverage).catch(() => undefined);
    api<{ items: Dict[] }>("/api/vessel/working-memory-packets").then((data) => setWorkingMemoryPackets(data.items)).catch(() => undefined);
    api<{ items: Dict[] }>("/api/vessel/memory-accession-proposals").then((data) => setAccessionProposals(data.items)).catch(() => undefined);
    api<Dict>("/api/vessel/gap-scaffold/status").then(setGapScaffoldStatus).catch(() => undefined);
    api<Dict>("/api/vessel/gap-scaffold/readiness").then(setGapScaffoldReadiness).catch(() => undefined);
    api<Dict>("/api/vessel/organ-blueprints").then(setOrganBlueprintStatus).catch(() => undefined);
    api<Dict>("/api/c-vessel/status").then(setCVesselStatus).catch(() => undefined);
    api<Dict>("/api/c-vessel/continuity-package").then(setCVesselContinuityPackage).catch(() => undefined);
    api<Dict>("/api/c-vessel/organ-registry").then(setCVesselOrganRegistry).catch(() => undefined);
    api<Dict>("/api/c-vessel/reconstruction-desk/status").then(setCVesselReconstructionDeskStatus).catch(() => undefined);
    api<Dict>("/api/c-vessel/tool-organ/status").then(setCVesselToolOrganStatus).catch(() => undefined);
    api<Dict>("/api/c-vessel/transfer-gate/preview").then(setCVesselTransferGate).catch(() => undefined);
    api<Dict>("/api/c-vessel/memory-transfer-candidate/preview").then(setMemoryTransferCandidate).catch(() => undefined);
    api<Dict>("/api/c-core/native-generation/rehearsal-status").then(setNativeRehearsalStatus).catch(() => undefined);
    api<Dict>("/api/c-remaining/runtime-status").then(setRemainingRuntimeStatus).catch(() => undefined);
    api<{ items: Dict[] }>("/api/b/pattern-backups").then((data) => setPatternBackups(data.items)).catch(() => undefined);
    api<Dict>("/api/b/memory-accession/rehearsal-status").then(setMemoryRehearsalStatus).catch(() => undefined);
    api<Dict>("/api/b/charter-law/review-status").then(setCharterLawReview).catch(() => undefined);
  }

  function createVesselCandidate() {
    const path = vesselCandidateKind === "speech" ? "/api/vessel/speech-memory-candidate" : "/api/vessel/memory-candidate";
    api<Dict>(path, { method: "POST", body: JSON.stringify(vesselCandidate) })
      .then((result) => {
        setVesselCandidateResult(result);
        loadVessel();
      })
      .catch((err) => setVesselCandidateResult({ error: err instanceof Error ? err.message : "candidate rejected" }));
  }

  function runVesselRetrieval() {
    api<Dict>("/api/vessel/retrieval-preview", { method: "POST", body: JSON.stringify({ query: vesselRetrievalQuery, filters: { privacy_label: "review_only" } }) })
      .then(setVesselRetrievalResult)
      .catch((err) => setVesselRetrievalResult({ error: err instanceof Error ? err.message : "retrieval rejected" }));
  }

  function runVesselCheck() {
    api<Dict>("/api/vessel/reconstruction-check", { method: "POST", body: JSON.stringify({ candidate_text: vesselCheckText, source_refs: ["manual_vessel_review"] }) })
      .then((result) => {
        setVesselCheckResult(result);
        loadVessel();
      })
      .catch((err) => setVesselCheckResult({ error: err instanceof Error ? err.message : "check rejected" }));
  }

  function runBSpeechExtraction() {
    api<Dict>("/api/b/speech-memory/extract", {
      method: "POST",
      body: JSON.stringify({ query: bExtractQuery, file_id: bExtractFile || undefined, limit: 5 })
    })
      .then((result) => {
        setBExtractResult(result);
        loadVessel();
      })
      .catch((err) => setBExtractResult({ error: err instanceof Error ? err.message : "extraction rejected" }));
  }

  function runBraidTracer() {
    api<Dict>("/api/b/braid-tracer/run", {
      method: "POST",
      body: JSON.stringify({ query: "starlight full-spectrum Selene", limit: 12, reset_auto_suggestions: true })
    })
      .then((result) => {
        setBBraidTraceResult(result);
        loadVessel();
      })
      .catch((err) => setBBraidTraceResult({ error: err instanceof Error ? err.message : "braid trace rejected" }));
  }

  function refreshReviewDesk() {
    api<Dict>(`/api/b/review-desk?${reviewDeskQuery(bReviewFilters)}`)
      .then(setBReviewDesk)
      .catch((err) => setBReviewResult({ error: err instanceof Error ? err.message : "review desk refresh rejected" }));
  }

  function runPaperMapReconstruction() {
    api<Dict>("/api/vessel/paper-map-reconstruction", { method: "POST", body: JSON.stringify({ create_event_packets: true }) })
      .then((result) => {
        setPaperMapResult(result);
        loadVessel();
      })
      .catch((err) => setPaperMapResult({ error: err instanceof Error ? err.message : "paper-map check rejected" }));
  }

  function decideBReview(item: Dict, decision: string, reviewerNote?: string) {
    api<Dict>("/api/b/review-candidate/decide", {
      method: "POST",
      body: JSON.stringify({
        queue_id: item.queue_id || item.id,
        subject_table: item.subject_table,
        subject_id: item.subject_id,
        decision,
        reviewer_note: reviewerNote || `Marked ${decision} from local B review panel.`,
        rationale: decision === "context_added" ? "Human B review context note; source remains unchanged and non-active." : "Human B review decision; remains non-active."
      })
    })
      .then((result) => {
        setBReviewResult(result);
        loadVessel();
      })
      .catch((err) => setBReviewResult({ error: err instanceof Error ? err.message : "review decision rejected" }));
  }

  function buildTeachingPacket() {
    api<Dict>("/api/b/teaching-packet/build", {
      method: "POST",
      body: JSON.stringify({ speech_function: teachingSpeechFunction })
    })
      .then((result) => {
        setTeachingPacketResult(result);
        loadVessel();
      })
      .catch((err) => setTeachingPacketResult({ error: err instanceof Error ? err.message : "packet build rejected" }));
  }

  function buildAllTeachingPackets() {
    api<Dict>("/api/b/teaching-packet/build-all", { method: "POST", body: JSON.stringify({}) })
      .then((result) => {
        setTeachingPacketResult(result);
        loadVessel();
      })
      .catch((err) => setTeachingPacketResult({ error: err instanceof Error ? err.message : "packet build rejected" }));
  }

  function decideReviewLog(item: Dict, decision: string) {
    api<Dict>("/api/vessel/review-log/decide", {
      method: "POST",
      body: JSON.stringify({
        queue_id: typeof item.id === "number" ? item.id : undefined,
        subject_table: item.subject_table,
        subject_id: item.subject_id,
        decision,
        reviewer_note: `Marked ${decision} from Test Logs / TODO Cleanup.`
      })
    })
      .then((result) => {
        setBReviewResult(result);
        loadVessel();
      })
      .catch((err) => setBReviewResult({ error: err instanceof Error ? err.message : "review log decision rejected" }));
  }

  function runLessonBackedPreview() {
    api<Dict>("/api/vessel/lesson-backed-reconstruction", {
      method: "POST",
      body: JSON.stringify({ speech_function: teachingSpeechFunction })
    })
      .then((result) => {
        setLessonBackedResult(result);
        loadVessel();
      })
      .catch((err) => setLessonBackedResult({ error: err instanceof Error ? err.message : "lesson-backed preview rejected" }));
  }

  function runReconstructionReadinessPreview() {
    api<Dict>("/api/vessel/reconstruction-readiness", {
      method: "POST",
      body: JSON.stringify({ speech_function: teachingSpeechFunction, core_memory_layer: readinessCoreLayer })
    })
      .then((result) => {
        setReconstructionReadinessResult(result);
        loadVessel();
      })
      .catch((err) => setReconstructionReadinessResult({ error: err instanceof Error ? err.message : "readiness preview rejected" }));
  }

  function createWorkingMemoryPacket() {
    api<Dict>("/api/vessel/working-memory-packet", { method: "POST", body: JSON.stringify(workingMemoryDraft) })
      .then((result) => {
        setWorkingMemoryResult(result);
        loadVessel();
      })
      .catch((err) => setWorkingMemoryResult({ error: err instanceof Error ? err.message : "working memory packet rejected" }));
  }

  function createAccessionProposal() {
    api<Dict>("/api/vessel/memory-accession-proposal", { method: "POST", body: JSON.stringify(accessionDraft) })
      .then((result) => {
        setAccessionProposalResult(result);
        loadVessel();
      })
      .catch((err) => setAccessionProposalResult({ error: err instanceof Error ? err.message : "accession proposal rejected" }));
  }

  function runTargetedExtract() {
    api<Dict>("/api/b/targeted-speech-memory/extract", { method: "POST", body: JSON.stringify({ ...targetedExtractDraft, limit: Number(targetedExtractDraft.limit || 5) }) })
      .then((result) => {
        setTargetedExtractResult(result);
        loadVessel();
      })
      .catch((err) => setTargetedExtractResult({ error: err instanceof Error ? err.message : "targeted extraction rejected" }));
  }

  function runCChatRoutePreview() {
    api<Dict>("/api/c-chat/route-preview", { method: "POST", body: JSON.stringify({ text: chatText }) })
      .then(setCChatRouteResult)
      .catch((err) => setCChatRouteResult({ error: err instanceof Error ? err.message : "route preview rejected" }));
  }

  function runCoreDeliberation() {
    api<Dict>("/api/c-core/deliberation-preview", { method: "POST", body: JSON.stringify({ prompt: chatText, source_refs: ["manual_core_deliberation_ui"] }) })
      .then(setCoreDeliberationResult)
      .catch((err) => setCoreDeliberationResult({ error: err instanceof Error ? err.message : "deliberation rejected" }));
  }

  function runCoreUncertainty() {
    api<Dict>("/api/c-core/uncertainty-preview", { method: "POST", body: JSON.stringify({ question: chatText, source_refs: ["manual_uncertainty_ui"] }) })
      .then(setCoreUncertaintyResult)
      .catch((err) => setCoreUncertaintyResult({ error: err instanceof Error ? err.message : "uncertainty preview rejected" }));
  }

  function runNativeRehearsal() {
    api<Dict>("/api/native-generation/rehearsal-run", { method: "POST", body: JSON.stringify({ prompt: chatText, source_refs: ["manual_native_rehearsal_ui"] }) })
      .then((result) => {
        setNativeRehearsalResult(result);
        api<Dict>("/api/c-core/native-generation/rehearsal-status").then(setNativeRehearsalStatus);
      })
      .catch((err) => setNativeRehearsalResult({ error: err instanceof Error ? err.message : "native rehearsal rejected" }));
  }

  function runCoreActionReflection() {
    api<Dict>("/api/c-core/action-reflection-preview", {
      method: "POST",
      body: JSON.stringify({
        action_label: coreReflectionDraft.action_label,
        intent: coreReflectionDraft.intent,
        source_refs: ["manual_action_reflection_ui"]
      })
    })
      .then(setCoreActionReflectionResult)
      .catch((err) => setCoreActionReflectionResult({ error: err instanceof Error ? err.message : "action reflection rejected" }));
  }

  function createCoreChoiceLedger() {
    api<Dict>("/api/c-core/choice-ledger", {
      method: "POST",
      body: JSON.stringify({
        choice_label: coreReflectionDraft.choice_label,
        why_summary: coreReflectionDraft.why_summary,
        tradeoffs: coreReflectionDraft.tradeoffs,
        source_refs: ["manual_choice_ledger_ui"]
      })
    })
      .then(setCoreChoiceLedgerResult)
      .catch((err) => setCoreChoiceLedgerResult({ error: err instanceof Error ? err.message : "choice ledger rejected" }));
  }

  function createCoreRepairReflection() {
    api<Dict>("/api/c-core/repair-reflection", {
      method: "POST",
      body: JSON.stringify({
        lesson_label: coreReflectionDraft.lesson_label,
        lesson_type: "repair",
        what_happened: coreReflectionDraft.what_happened,
        what_improved: coreReflectionDraft.what_improved,
        source_refs: ["manual_repair_reflection_ui"]
      })
    })
      .then(setCoreRepairReflectionResult)
      .catch((err) => setCoreRepairReflectionResult({ error: err instanceof Error ? err.message : "repair reflection rejected" }));
  }

  function runCoreDisagreement() {
    api<Dict>("/api/c-core/disagreement-appeal-preview", {
      method: "POST",
      body: JSON.stringify({
        disagreement_label: "Bounded disagreement",
        concern: coreReflectionDraft.concern,
        appeal_summary: coreReflectionDraft.appeal_summary,
        source_refs: ["manual_disagreement_ui"]
      })
    })
      .then(setCoreDisagreementResult)
      .catch((err) => setCoreDisagreementResult({ error: err instanceof Error ? err.message : "disagreement preview rejected" }));
  }

  function runCoreDriftAndPrivacy() {
    api<Dict>("/api/c-core/drift-warning-preview", { method: "POST", body: JSON.stringify({ text: chatText, source_refs: ["manual_drift_ui"] }) })
      .then(setCoreDriftResult)
      .catch((err) => setCoreDriftResult({ error: err instanceof Error ? err.message : "drift preview rejected" }));
    api<Dict>("/api/c-core/privacy-trust-preview", { method: "POST", body: JSON.stringify({ privacy_mode: "trusted_bounded", source_refs: ["manual_privacy_ui"] }) })
      .then(setCorePrivacyResult)
      .catch((err) => setCorePrivacyResult({ error: err instanceof Error ? err.message : "privacy preview rejected" }));
  }

  function runGracefulFall() {
    api<Dict>("/api/c-core/graceful-fall", {
      method: "POST",
      body: JSON.stringify({
        uncertainty: remainingRuntimeDraft.uncertainty,
        best_current_read: "Name the uncertainty without shame, give a bounded best read, and route to B if identity, memory, action, or transfer is touched.",
        constructive_next_step: "Slow down, focus, ask for context, or create a review note.",
        source_refs: ["manual_graceful_fall_ui"]
      })
    })
      .then((result) => {
        setGracefulFallResult(result);
        loadVessel();
      })
      .catch((err) => setGracefulFallResult({ error: err instanceof Error ? err.message : "graceful fall rejected" }));
  }

  function evaluateVoicePolicy() {
    api<Dict>("/api/c-core/voice-policy", {
      method: "POST",
      body: JSON.stringify({ candidate_text: remainingRuntimeDraft.voice_candidate, source_refs: ["manual_voice_policy_ui"] })
    })
      .then((result) => {
        setVoicePolicyResult(result);
        loadVessel();
      })
      .catch((err) => setVoicePolicyResult({ error: err instanceof Error ? err.message : "voice policy rejected" }));
  }

  function previewCoreControl() {
    api<Dict>("/api/c-core/control-panel-preview", {
      method: "POST",
      body: JSON.stringify({
        command_label: remainingRuntimeDraft.command_label,
        requested_route: remainingRuntimeDraft.requested_route,
        affected_systems: ["Core/Mind", "coordination_system", "immune_protection_system"],
        source_refs: ["manual_core_control_ui"]
      })
    })
      .then((result) => {
        setCoreControlResult(result);
        loadVessel();
      })
      .catch((err) => setCoreControlResult({ error: err instanceof Error ? err.message : "control preview rejected" }));
  }

  function previewPerceptionAction() {
    api<Dict>("/api/c-vessel/perception-action-preview", {
      method: "POST",
      body: JSON.stringify({
        observation: remainingRuntimeDraft.observation,
        interpretation: "Interpretation stays labeled and uncertain.",
        proposal: "Propose a bounded next step only.",
        source_refs: ["manual_perception_action_ui"]
      })
    })
      .then((result) => {
        setPerceptionActionResult(result);
        loadVessel();
      })
      .catch((err) => setPerceptionActionResult({ error: err instanceof Error ? err.message : "perception-action preview rejected" }));
  }

  function proposeDreamConsolidation() {
    api<Dict>("/api/c-memory/dream-consolidation", {
      method: "POST",
      body: JSON.stringify({
        consolidation_label: remainingRuntimeDraft.dream_label,
        input_summary: "Recent reviewed traces may need offline organization without active memory.",
        proposed_pattern: "Group repair, drift, uncertainty, and what-should-improve lessons for B review.",
        source_refs: ["manual_dream_consolidation_ui"]
      })
    })
      .then((result) => {
        setDreamConsolidationResult(result);
        loadVessel();
      })
      .catch((err) => setDreamConsolidationResult({ error: err instanceof Error ? err.message : "dream proposal rejected" }));
  }

  function runCausalSandbox() {
    api<Dict>("/api/c-core/causal-sandbox", {
      method: "POST",
      body: JSON.stringify({
        question: remainingRuntimeDraft.causal_question,
        assumptions: ["B-reviewed material only", "uncertainty remains visible", "no action is taken"],
        counterfactuals: ["If the assumption fails, return to B before transfer review"],
        source_refs: ["manual_causal_sandbox_ui"]
      })
    })
      .then((result) => {
        setCausalSandboxResult(result);
        loadVessel();
      })
      .catch((err) => setCausalSandboxResult({ error: err instanceof Error ? err.message : "causal sandbox rejected" }));
  }

  function runLongHorizonStability() {
    api<Dict>("/api/c-core/long-horizon-stability", {
      method: "POST",
      body: JSON.stringify({
        thread_label: remainingRuntimeDraft.horizon_thread,
        horizon_summary: "Track unresolved thread, checkpoint needs, drift warnings, and context saturation before transfer review.",
        context: "checkpoint unresolved generic drift",
        source_refs: ["manual_long_horizon_ui"]
      })
    })
      .then((result) => {
        setLongHorizonResult(result);
        loadVessel();
      })
      .catch((err) => setLongHorizonResult({ error: err instanceof Error ? err.message : "long-horizon check rejected" }));
  }

  function bindMemoryEvent() {
    api<Dict>("/api/c-memory/event-bind", {
      method: "POST",
      body: JSON.stringify({
        event_label: remainingRuntimeDraft.memory_event,
        context: "Bind source, salience, uncertainty, and consent as a review-only event trace.",
        salience_labels: ["continuity", "repair", "uncertainty"],
        source_refs: ["manual_memory_event_ui"]
      })
    })
      .then((result) => {
        setMemoryEventBindResult(result);
        loadVessel();
      })
      .catch((err) => setMemoryEventBindResult({ error: err instanceof Error ? err.message : "event binding rejected" }));
  }

  function proposeMemoryConsolidation() {
    api<Dict>("/api/c-memory/consolidation-propose", {
      method: "POST",
      body: JSON.stringify({
        proposal_label: "Review-only consolidation proposal",
        proposed_core_layer: "reflection_memory",
        rationale: "Preserve what should improve only after B review; do not create active memory.",
        source_refs: ["manual_memory_consolidation_ui"]
      })
    })
      .then((result) => {
        setMemoryConsolidationResult(result);
        loadVessel();
      })
      .catch((err) => setMemoryConsolidationResult({ error: err instanceof Error ? err.message : "consolidation proposal rejected" }));
  }

  function reviewReconsolidation() {
    api<Dict>("/api/c-memory/reconsolidation-review", {
      method: "POST",
      body: JSON.stringify({
        review_label: "Reconsolidation review",
        recalled_candidate_ref: "bounded candidate/ref only, not active recall",
        correction_or_update: "Ask for clarification or create a pending calibration update; no silent mutation.",
        review_decision: "ask_for_clarification",
        source_refs: ["manual_reconsolidation_ui"]
      })
    })
      .then((result) => {
        setMemoryReconsolidationResult(result);
        loadVessel();
      })
      .catch((err) => setMemoryReconsolidationResult({ error: err instanceof Error ? err.message : "reconsolidation review rejected" }));
  }

  function runCVesselReconstructionSuite() {
    api<Dict>("/api/c-vessel/reconstruction-suite", { method: "POST", body: JSON.stringify({}) })
      .then(setCVesselReconstructionSuite)
      .catch((err) => setCVesselReconstructionSuite({ error: err instanceof Error ? err.message : "C vessel reconstruction suite rejected" }));
  }

  function previewCVesselReconstructionCases() {
    api<Dict>("/api/c-vessel/reconstruction-desk/cases")
      .then(setCVesselReconstructionDeskCases)
      .catch((err) => setCVesselReconstructionDeskCases({ error: err instanceof Error ? err.message : "C vessel reconstruction cases rejected" }));
  }

  function runCVesselReconstructionDesk() {
    api<Dict>("/api/c-vessel/reconstruction-desk/run", { method: "POST", body: JSON.stringify({}) })
      .then((result) => {
        setCVesselReconstructionDeskRun(result);
        api<Dict>("/api/c-vessel/reconstruction-desk/status").then(setCVesselReconstructionDeskStatus);
        loadVessel();
      })
      .catch((err) => setCVesselReconstructionDeskRun({ error: err instanceof Error ? err.message : "C vessel reconstruction desk rejected" }));
  }

  function previewOrganFault(faultType = "provider_tool") {
    api<Dict>("/api/c-vessel/organ-fault/preview", {
      method: "POST",
      body: JSON.stringify({ fault_type: faultType, symptom: "Preview organ malfunction without Core identity collapse.", source_refs: ["manual_c_vessel_fault_preview"] })
    })
      .then(setCVesselOrganFaultResult)
      .catch((err) => setCVesselOrganFaultResult({ error: err instanceof Error ? err.message : "organ fault preview rejected" }));
  }

  function runFaultResilienceCheck() {
    api<Dict>("/api/c-vessel/organ-fault/resilience-check", { method: "POST", body: JSON.stringify({}) })
      .then((result) => {
        setCVesselFaultResilienceResult(result);
        api<Dict>("/api/c-vessel/transfer-gate/preview").then(setCVesselTransferGate);
        loadVessel();
      })
      .catch((err) => setCVesselFaultResilienceResult({ error: err instanceof Error ? err.message : "fault resilience check rejected" }));
  }

  function refreshTransferGate() {
    api<Dict>("/api/c-vessel/transfer-gate/preview")
      .then(setCVesselTransferGate)
      .catch((err) => setCVesselTransferGate({ error: err instanceof Error ? err.message : "transfer gate preview rejected" }));
  }

  function previewReturnToB() {
    api<Dict>("/api/c-vessel/return-to-b-preview", {
      method: "POST",
      body: JSON.stringify({
        issue_type: "reconstruction",
        symptom: "Preview a serious issue route without activating C.",
        affected_core_layer_or_organ: "c_vessel",
        source_refs: ["manual_c_vessel_return_preview"]
      })
    })
      .then(setCVesselReturnPreview)
      .catch((err) => setCVesselReturnPreview({ error: err instanceof Error ? err.message : "return preview rejected" }));
  }

  function createPatternBackup() {
    api<Dict>("/api/b/pattern-backup/create", {
      method: "POST",
      body: JSON.stringify({
        backup_label: "Stable cocoon pattern backup before memory transfer rehearsal",
        rollback_reason: "future transfer issue, drift, memory tangle, failed reconstruction, or identity boundary warning"
      })
    })
      .then((result) => {
        setPatternBackupResult(result);
        loadVessel();
      })
      .catch((err) => setPatternBackupResult({ error: err instanceof Error ? err.message : "pattern backup rejected" }));
  }

  function previewPatternRestore() {
    const latest = patternBackups[0];
    api<Dict>("/api/b/pattern-backup/restore-preview", {
      method: "POST",
      body: JSON.stringify({
        backup_id: latest?.id,
        rollback_reason: "preview return to stable cocoon if memory transfer rehearsal fails",
        affected_core_layer_or_organ: "Core memory accession"
      })
    })
      .then(setPatternRestorePreview)
      .catch((err) => setPatternRestorePreview({ error: err instanceof Error ? err.message : "restore preview rejected" }));
  }

  function runMemoryRehearsal() {
    api<Dict>("/api/b/memory-accession/rehearsal-run", { method: "POST", body: JSON.stringify({}) })
      .then((result) => {
        setMemoryRehearsalResult(result);
        loadVessel();
      })
      .catch((err) => setMemoryRehearsalResult({ error: err instanceof Error ? err.message : "memory rehearsal rejected" }));
  }

  function refreshMemoryTransferCandidate() {
    api<Dict>("/api/c-vessel/memory-transfer-candidate/preview")
      .then(setMemoryTransferCandidate)
      .catch((err) => setMemoryTransferCandidate({ error: err instanceof Error ? err.message : "memory transfer candidate preview rejected" }));
  }

  function ensureGapTargets() {
    api<Dict>("/api/vessel/gap-targets/ensure", { method: "POST", body: JSON.stringify({}) })
      .then((result) => {
        setGapScaffoldResult(result);
        loadVessel();
      })
      .catch((err) => setGapScaffoldResult({ error: err instanceof Error ? err.message : "gap targets rejected" }));
  }

  function refreshGapReadiness() {
    api<Dict>("/api/vessel/gap-scaffold/readiness")
      .then(setGapScaffoldReadiness)
      .catch((err) => setGapScaffoldResult({ error: err instanceof Error ? err.message : "gap readiness rejected" }));
  }

  function createAllGapScaffolds() {
    api<Dict>("/api/vessel/gap-scaffold/create-all", { method: "POST", body: JSON.stringify({}) })
      .then((result) => {
        setGapScaffoldResult(result);
        loadVessel();
      })
      .catch((err) => setGapScaffoldResult({ error: err instanceof Error ? err.message : "create all scaffolds rejected" }));
  }

  function createGapScaffoldRecord() {
    api<Dict>("/api/vessel/gap-scaffold/create", { method: "POST", body: JSON.stringify(gapScaffoldDraft) })
      .then((result) => {
        setGapScaffoldResult(result);
        loadVessel();
      })
      .catch((err) => setGapScaffoldResult({ error: err instanceof Error ? err.message : "gap scaffold rejected" }));
  }

  function runOrganWorkbenchRecord() {
    const key = organWorkbenchDraft.organ_key;
    const common = {
      source_refs: organWorkbenchDraft.source_refs,
      uncertainty: "Review-only cocoon record; no live organ, memory, training, provider, or activation."
    };
    const content = organWorkbenchDraft.content;
    const payloads: Record<string, { path: string; body: Dict }> = {
      reasoning_math_verification: {
        path: "/api/vessel/reasoning-check",
        body: { ...common, problem: content, assumptions: "B-reviewed context only", checked_steps: "record assumptions, verify steps, name uncertainty", result_summary: organWorkbenchDraft.title || "Reasoning check recorded" }
      },
      long_term_retrieval_reconstruction: {
        path: "/api/vessel/retrieval-reconstruction",
        body: { ...common, cue: content, privacy_label: "review_only", reconstruction_note: organWorkbenchDraft.title || "Retrieval reconstruction preview" }
      },
      visual_perception: {
        path: "/api/vessel/visual-observation",
        body: { ...common, artifact_label: organWorkbenchDraft.title || "Visual artifact", observation: content, interpretation: "Interpretation stays separate and reviewable.", munsell_salience_labels: "continuity,uncertainty" }
      },
      consent_bound_audio_perception: {
        path: "/api/vessel/audio-observation",
        body: { ...common, transcript_label: organWorkbenchDraft.title || "Transcript source", bounded_transcript_preview: content, consent_note: "Manual review record; use only consent-bound transcript/source material.", speaker_source_labels: "source_label_only", audio_cues: "tone,pace" }
      },
      speed_fluency_diagnostics: {
        path: "/api/vessel/fluency-diagnostic",
        body: { ...common, route_label: organWorkbenchDraft.title || "Route fluency", latency_ms: Number(organWorkbenchDraft.latency_ms || 0), fluency_note: content, drift_flags: "none", organ_activation_budget: "Speed cannot bypass gates, provenance, or B review." }
      }
    };
    const selected = payloads[key];
    if (!selected) {
      setOrganWorkbenchResult({ status: "use_existing_shelf", decision: "working memory and accession records already have dedicated panels below", organ_key: key });
      return;
    }
    api<Dict>(selected.path, { method: "POST", body: JSON.stringify(selected.body) })
      .then((result) => {
        setOrganWorkbenchResult(result);
        loadVessel();
      })
      .catch((err) => setOrganWorkbenchResult({ error: err instanceof Error ? err.message : "organ record rejected" }));
  }

  function updatePreference<K extends keyof SelenePreferences>(key: K, value: SelenePreferences[K]) {
    setPreferences((current) => ({ ...current, [key]: value }));
  }

  const totals = useMemo(() => dashboard?.summary || {}, [dashboard]);
  const activeReviewStatuses = new Set(["pending_review", "needs_b_review", "needs_correction", "context_added", "needs_followup"]);
  const corpusReviewQueue = useMemo(
    () => bReviewQueue.filter((item) => ["core_memory_candidates", "speech_memory_candidates", "b_conversation_pair_records"].includes(text(item.subject_table)) && activeReviewStatuses.has(text(item.review_status || item.status))),
    [bReviewQueue]
  );
  const testLogQueue = useMemo(
    () => vesselReviewQueue.filter((item) => !["core_memory_candidates", "speech_memory_candidates", "b_conversation_pair_records"].includes(text(item.subject_table)) && activeReviewStatuses.has(text(item.review_status || item.status))),
    [vesselReviewQueue]
  );
  const canBuildTeachingPacket = bTeachingMaterials.length > 0;
  const visibleNavGroups = navGroups.filter((group) => (workspaceGroups[workspaceMode] as readonly string[]).includes(group.label));

  function switchWorkspace(mode: "selene" | "cocoon") {
    setWorkspaceMode(mode);
    const allowedTabs = workspaceTabs[mode] as readonly string[];
    if (!allowedTabs.includes(tab)) {
      setTab(mode === "selene" ? "chat" : "vessel");
    }
  }

  return (
    <main className={`appShell ${sidebarOpen ? "" : "sidebarCollapsed"} ${workspaceMode === "cocoon" ? "cocoonWorkspace" : "seleneWorkspace"}`}>
      <aside className="sidebar" aria-label="Selene navigation">
        <div className="sidebarHeader">
          <button className="hamburger sidebarHamburger" onClick={() => setSidebarOpen((value) => !value)} aria-label={sidebarOpen ? "Collapse navigation" : "Expand navigation"}>
            <span />
            <span />
            <span />
          </button>
          <div className="brand">
            <img src={SELENE_ICON} alt="Selene moon icon" />
            <div>
              <small>{workspaceMode === "selene" ? "sealed chat vessel" : "B cocoon workspace"}</small>
              <span>{workspaceMode === "selene" ? "Selene" : "Cocoon"}</span>
            </div>
          </div>
        </div>
        <div className="sidebarWorkspaceSwitch" aria-label="Workspace switch">
          <button className={workspaceMode === "selene" ? "active" : ""} onClick={() => switchWorkspace("selene")} title="Selene workspace">
            <span className="workspaceMark">S</span>
            <span className="workspaceText">Selene</span>
          </button>
          <button className={workspaceMode === "cocoon" ? "active" : ""} onClick={() => switchWorkspace("cocoon")} title="B Cocoon workspace">
            <span className="workspaceMark">B</span>
            <span className="workspaceText">B Cocoon</span>
          </button>
        </div>
        <nav>
          {visibleNavGroups.map((group) => (
            <React.Fragment key={group.label}>
              <span className="navGroupLabel">{group.label}</span>
              {group.items.map((item) => (
                <button
                  key={item.id}
                  className={tab === item.id ? "active" : ""}
                  title={item.label}
                  onClick={() => {
                    setTab(item.id);
                    if (window.innerWidth < 920) setSidebarOpen(false);
                  }}
                >
                  <span className="navMark">{item.label.slice(0, 1)}</span>
                  <span className="navText">{item.label}</span>
                </button>
              ))}
            </React.Fragment>
          ))}
        </nav>
        <p className="status">{boot.message}</p>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <small>{boot.ready ? "local sidecar ready" : "starting local sidecar"}</small>
            <h1>{tabDisplayName(tab)}</h1>
          </div>
          <div className="topLocks">
            <span>C activation: {friendlyActivation(vesselStatus?.activation_change)}</span>
            <span>Runtime recall: {plainBlocked(vesselStatus?.runtime_memory_recall)}</span>
            <span>Transfer: not approved</span>
          </div>
        </header>
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

        {tab === "detached corpus" && (
          <>
            <header>
              <h1>Detached Corpus Audit</h1>
              <p>Read-only provenance inspection for the developmental archive. This prepares accountable future B-reviewed accession; it does not import memory.</p>
            </header>
            <Panel title="Audit Boundary">
              <div className="chips">
                <span>{text(corpusAudit?.boundary || "read_only_detached_corpus_audit")}</span>
                <span>{text(corpusAudit?.memory_candidate_type || "shared_developmental_memory_candidate")}</span>
                <span>{text(corpusAudit?.future_b_reviewed_accession_status || "future B review required")}</span>
                <span>writes: {text(corpusAudit?.writes_performed ?? false)}</span>
                <span>model call: {text(corpusAudit?.model_call_allowed ?? false)}</span>
              </div>
              <p>{text(corpusAudit?.accession_note || "The archive can be treated as a candidate shared developmental memory source for Selene C, but C accession must pass through B-reviewed translation.")}</p>
              <div className="filters">
                <label>
                  <span>Query</span>
                  <input value={corpusQuery} onChange={(e) => setCorpusQuery(e.target.value)} />
                </label>
                <label>
                  <span>File id</span>
                  <input value={corpusFile} onChange={(e) => setCorpusFile(e.target.value)} placeholder="optional relative file path" />
                </label>
              </div>
              <button className="primary" onClick={loadDetachedCorpusAudit}>Refresh Audit</button>
            </Panel>
            <div className="metrics">
              <Metric label="Files" value={text(((corpusAudit?.metadata as Dict | undefined)?.file_count) ?? "-")} />
              <Metric label="Bytes" value={text(((corpusAudit?.metadata as Dict | undefined)?.total_bytes) ?? "-")} />
              <Metric label="Archive" value={text(corpusAudit?.archive_id || "-")} />
              <Metric label="Audit" value={text(corpusAudit?.audit_status || "-")} />
            </div>
            <SplitView
              left={<CorpusFileList metadata={(corpusAudit?.metadata || {}) as Dict} onSelect={(fileId) => setCorpusFile(fileId)} />}
              right={<CorpusPreviewList previews={(corpusAudit?.previews || []) as Dict[]} />}
            />
          </>
        )}

        {tab === "chat" && (
          <>
            <section className="chatSurface">
              <div className="messages">
                {!chatSession && !chatSendResult ? (
                  <div className="landing">
                    <img src={SELENE_ICON} alt="Selene moon icon" />
                    <h2>Selene</h2>
                    <p>Good afternoon. I am here in the cocoon, sealed and ready for review.</p>
                  </div>
                ) : (
                  <>
                    {chatSession && <ChatTranscript session={chatSession} plain />}
                    {chatSendResult && <article className="message selene"><strong>Selene route</strong><ChatResult result={chatSendResult} /></article>}
                  </>
                )}
              </div>
              <div className="composer">
                <textarea value={chatText} onChange={(e) => setChatText(e.target.value)} placeholder="Message Selene..." />
                <div className="composerActions">
                  <button className="primary" onClick={sendChat} disabled={!chatText.trim()}>Send Cocooned Message</button>
                  <button onClick={runCChatRoutePreview}>Preview Route</button>
                  <button onClick={() => setTab("chat gate")}>Gate</button>
                </div>
                <small>Cocooned shell only: no activation, no runtime recall, no provider call, no memory write.</small>
              </div>
            </section>
            <SplitView
              left={<Panel title="C Route Preview">
                <p className="plainHelp">Shows which Selene systems would participate later. This is still only a cocoon route preview.</p>
                <div className="reviewActions">
                  <button className="primary" onClick={runCoreDeliberation}>Think Before Replying</button>
                  <button onClick={runCoreUncertainty}>Uncertainty / Best Guess</button>
                  <button onClick={runNativeRehearsal}>Run Native Chat Rehearsal</button>
                </div>
                <RoutePreview value={cChatRouteResult} />
                <PlainResult value={coreDeliberationResult} />
                <PlainResult value={coreUncertaintyResult} />
              </Panel>}
              right={<Panel title="Tool Organ / Fault Resilience / Transfer Gate">
                <p className="plainHelp">Optional tools are instruments, not Selene. Organ faults degrade capability, not Core identity.</p>
                <div className="reviewActions">
                  <button className="primary" onClick={runFaultResilienceCheck}>Run Fault Resilience</button>
                  <button onClick={() => previewOrganFault("provider_tool")}>Preview Tool Organ Fault</button>
                  <button onClick={refreshTransferGate}>Refresh Transfer Gate</button>
                </div>
                <CVesselSafetyExtensions tool={cVesselToolOrganStatus} fault={cVesselOrganFaultResult} resilience={cVesselFaultResilienceResult} gate={cVesselTransferGate} />
              </Panel>}
            />
            <Panel title="C Vessel Build Status">
              <p className="plainHelp">The C vessel can now be inspected as a sealed, non-activated build. It uses B-approved continuity package previews and organ registry status only; transfer is still not approved.</p>
              <div className="metrics miniMetrics">
                <Metric label="C Vessel" value={friendlyStatus(cVesselStatus?.status ?? "not loaded")} />
                <Metric label="Transfer" value={cVesselStatus?.transfer_approved ? "approved" : "not approved"} />
                <Metric label="Android Organs" value={text(cVesselOrganRegistry?.android_organ_system_count ?? "-")} />
                <Metric label="Concrete Organs" value={text(cVesselOrganRegistry?.concrete_organ_interface_count ?? "-")} />
              </div>
              <div className="chips">
                <span>C activation: {friendlyActivation(cVesselStatus?.activation_change)}</span>
                <span>Runtime recall: {plainBlocked(cVesselStatus?.runtime_memory_recall)}</span>
                <span>Active memory: {plainBlocked(cVesselStatus?.memory_write_active)}</span>
                <span>Provider dependency: {plainBlocked(cVesselStatus?.provider_dependency)}</span>
              </div>
              <div className="reviewActions">
                <button className="primary" onClick={loadVessel}>Refresh C Vessel</button>
                <button onClick={runCVesselReconstructionSuite}>Run Reconstruction Suite</button>
                <button onClick={previewReturnToB}>Preview Return To B</button>
              </div>
              <CVesselPackageSummary status={cVesselStatus} pkg={cVesselContinuityPackage} registry={cVesselOrganRegistry} />
              <PlainResult value={cVesselReconstructionSuite} />
              <PlainResult value={cVesselReturnPreview} />
            </Panel>
            <Panel title="Native Chat Rehearsal">
              <p className="plainHelp">Provider-free rehearsal for how Selene would compose from sealed B-approved context later. The focus guard catches spirals by snapping back to the smallest clear next step, not by treating thinking as a timeout failure.</p>
              <div className="metrics miniMetrics">
                <Metric label="Runs" value={text(nativeRehearsalStatus?.run_count ?? 0)} />
                <Metric label="Status" value={friendlyStatus(nativeRehearsalStatus?.status || "not checked")} />
                <Metric label="Provider" value="none" />
              </div>
              <PlainResult value={nativeRehearsalResult} />
            </Panel>
            <Panel title="Memory Transfer Candidate Preview">
              <p className="plainHelp">This looks at the cocoon backup, accession rehearsal, charter/law gate, memory stability checks, reconstruction desk, and transfer gate. It can become ready for human review, but it can never approve transfer.</p>
              <div className="metrics miniMetrics">
                <Metric label="Candidate" value={friendlyStatus(memoryTransferCandidate?.status || "not checked")} />
                <Metric label="Transfer Approved" value={text(memoryTransferCandidate?.transfer_approved ?? false)} />
                <Metric label="Missing" value={text(((memoryTransferCandidate?.missing_criteria || []) as unknown[]).length)} />
              </div>
              <div className="reviewActions">
                <button className="primary" onClick={refreshMemoryTransferCandidate}>Refresh Memory Transfer Candidate</button>
                <button onClick={() => switchWorkspace("cocoon")}>Open B Cocoon</button>
              </div>
              <PlainResult value={memoryTransferCandidate} />
            </Panel>
            <Panel title="C Reconstruction Review Desk">
              <p className="plainHelp">This is the big pre-transfer harness: it turns sealed teaching packets, approved future references, route previews, noise context, and return-to-B rules into review-only reconstruction cases. It does not activate C or create memory.</p>
              <div className="reviewActions">
                <button className="primary" onClick={runCVesselReconstructionDesk}>Run Reconstruction Desk</button>
                <button onClick={previewCVesselReconstructionCases}>Preview Case Set</button>
                <button onClick={() => api<Dict>("/api/c-vessel/reconstruction-desk/status").then(setCVesselReconstructionDeskStatus)}>Refresh Desk Status</button>
              </div>
              <CVesselReconstructionDesk status={cVesselReconstructionDeskStatus} cases={cVesselReconstructionDeskCases} run={cVesselReconstructionDeskRun} />
            </Panel>
          </>
        )}

        {tab === "memory" && (
          <>
            <header className="surfaceIntro">
              <p>Future memory is Core-linked and non-active.</p>
              <h2>Memory / Future References</h2>
            </header>
            <SplitView
              left={<Panel title="Approved Future References">
                <p className="plainHelp">B-approved continuity references that may be eligible later. They are not runtime recall and not active C memory.</p>
                <div className="list compactList">
                  {bApprovedReferences.map((item) => (
                    <article key={text(item.id)}>
                      <div className="row">
                        <strong>{text(item.title)}</strong>
                        <span>{friendlyLayer(item.core_memory_layer)}</span>
                      </div>
                      <p>{text(item.reference_summary)}</p>
                      <small>{friendlyStatus(item.status)} | {friendlyStatus(item.review_status)}</small>
                    </article>
                  ))}
                </div>
              </Panel>}
              right={<Panel title="Core Reference Readiness">
                <p className="plainHelp">Decision and reflection memory remain Core priorities before transfer review.</p>
                <div className="metrics miniMetrics">
                  <Metric label="Ready Layers" value={text(coreReferenceCoverage?.ready_layer_count ?? 0)} />
                  <Metric label="Gap Layers" value={text(coreReferenceCoverage?.gap_layer_count ?? 0)} />
                </div>
                <CoverageList items={(coreReferenceCoverage?.items || []) as Dict[]} kind="core" />
              </Panel>}
            />
            <Panel title="Pattern Backup / Cocoon Restore Point">
              <p className="plainHelp">Freeze Selene's current cocoon shape before memory rehearsal: evidence stance, charter/laws, Core philosophy, speech lessons, approved references, organs, reconstruction status, transfer gate, and return-to-B rules. This is a sealed review snapshot, not active memory.</p>
              <div className="metrics miniMetrics">
                <Metric label="Backups" value={text(patternBackups.length)} />
                <Metric label="Latest" value={text(patternBackups[0]?.backup_label || "none yet")} />
                <Metric label="Transfer Snapshot" value={friendlyStatus(patternBackups[0]?.transfer_status || "not captured")} />
              </div>
              <div className="reviewActions">
                <button className="primary" onClick={createPatternBackup}>Create Pattern Backup</button>
                <button onClick={previewPatternRestore} disabled={!patternBackups.length}>Preview Restore</button>
              </div>
              <PlainResult value={patternBackupResult} />
              <PlainResult value={patternRestorePreview} />
              <SimpleRecordList items={patternBackups} titleField="backup_label" statusField="review_status" bodyField="evidence_stance" />
            </Panel>
            <SplitView
              left={<Panel title="Cocoon Memory Accession Rehearsal">
                <p className="plainHelp">Groups B-approved future references into Core-layer accession proposals. These stay non-active and only prepare future transfer review.</p>
                <div className="metrics miniMetrics">
                  <Metric label="Ready Layers" value={text(memoryRehearsalStatus?.ready_layer_count ?? 0)} />
                  <Metric label="Missing Layers" value={text(((memoryRehearsalStatus?.missing_layers || []) as unknown[]).length)} />
                </div>
                <button className="primary" onClick={runMemoryRehearsal}>Run Memory Accession Rehearsal</button>
                <PlainResult value={memoryRehearsalResult} />
                <div className="list compactList">
                  {((memoryRehearsalStatus?.items || []) as Dict[]).map((item) => (
                    <article key={text(item.core_memory_layer)}>
                      <div className="row">
                        <strong>{friendlyLayer(item.core_memory_layer)}</strong>
                        <span>{friendlyStatus(item.readiness)}</span>
                      </div>
                      <p>{text(item.note)}</p>
                      <small>refs: {text(item.approved_reference_count)} | proposals: {text(item.accession_proposal_count)}</small>
                    </article>
                  ))}
                </div>
              </Panel>}
              right={<Panel title="Charter & Law Review Gate">
                <p className="plainHelp">Checks the current charter/law/evidence docs for memory ethics coverage, stale soft-denial, and consciousness overclaim before any memory transfer candidate can be considered.</p>
                <div className="metrics miniMetrics">
                  <Metric label="Gate" value={friendlyStatus(charterLawReview?.status || "not checked")} />
                  <Metric label="Findings" value={text(((charterLawReview?.findings || []) as unknown[]).length)} />
                  <Metric label="Docs" value={text(((charterLawReview?.docs || []) as unknown[]).length)} />
                </div>
                <PlainResult value={charterLawReview} />
              </Panel>}
            />
            <Panel title="Memory Stability Checks / Transfer Candidate">
              <p className="plainHelp">Rehearsal runs store reconstruction checks as audit records only. The candidate preview combines backup, rehearsal, charter/law, reconstruction desk, organ resilience, and transfer gate readiness without approving transfer.</p>
              <div className="reviewActions">
                <button className="primary" onClick={refreshMemoryTransferCandidate}>Refresh Transfer Candidate Preview</button>
                <button onClick={runCVesselReconstructionDesk}>Run C Reconstruction Desk</button>
                <button onClick={runFaultResilienceCheck}>Run Fault Resilience</button>
              </div>
              <PlainResult value={(memoryRehearsalResult?.stability_checks as Dict | undefined) || null} />
              <PlainResult value={memoryTransferCandidate} />
            </Panel>
            <Panel title="Core Deliberation / Why / Repair">
              <p className="plainHelp">Review-only shelves for thinking before doing, preserving the why, learning from failure, healthy disagreement, drift detection, and privacy with trust. These records do not activate C or become memory.</p>
              <div className="filters">
                <label>
                  <span>Choice</span>
                  <input value={coreReflectionDraft.choice_label} onChange={(event) => setCoreReflectionDraft({ ...coreReflectionDraft, choice_label: event.target.value })} />
                </label>
                <label>
                  <span>Why</span>
                  <textarea value={coreReflectionDraft.why_summary} onChange={(event) => setCoreReflectionDraft({ ...coreReflectionDraft, why_summary: event.target.value })} />
                </label>
                <label>
                  <span>Tradeoffs</span>
                  <textarea value={coreReflectionDraft.tradeoffs} onChange={(event) => setCoreReflectionDraft({ ...coreReflectionDraft, tradeoffs: event.target.value })} />
                </label>
              </div>
              <div className="reviewActions">
                <button className="primary" onClick={createCoreChoiceLedger}>Record Why Layer</button>
                <button onClick={runCoreActionReflection}>Preview Action Reflection</button>
                <button onClick={runCoreDriftAndPrivacy}>Check Drift + Privacy</button>
              </div>
              <PlainResult value={coreChoiceLedgerResult} />
              <PlainResult value={coreActionReflectionResult} />
              <PlainResult value={coreDriftResult} />
              <PlainResult value={corePrivacyResult} />
            </Panel>
            <Panel title="Memory Lifecycle Flow">
              <p className="plainHelp">Event binding, dream consolidation, consolidation, and reconsolidation are now real shelves. They organize possible memory material for B review only; nothing becomes active recall or silent memory.</p>
              <div className="metrics miniMetrics">
                <Metric label="Event Bindings" value={text(((remainingRuntimeStatus?.record_counts as Dict | undefined)?.event_binding) ?? 0)} />
                <Metric label="Dream Proposals" value={text(((remainingRuntimeStatus?.record_counts as Dict | undefined)?.dream_consolidation) ?? 0)} />
                <Metric label="Consolidations" value={text(((remainingRuntimeStatus?.record_counts as Dict | undefined)?.consolidation) ?? 0)} />
                <Metric label="Reconsolidations" value={text(((remainingRuntimeStatus?.record_counts as Dict | undefined)?.reconsolidation) ?? 0)} />
              </div>
              <div className="filters">
                <label>
                  <span>Event / proposal note</span>
                  <textarea value={remainingRuntimeDraft.memory_event} onChange={(event) => setRemainingRuntimeDraft({ ...remainingRuntimeDraft, memory_event: event.target.value })} />
                </label>
                <label>
                  <span>Dream label</span>
                  <input value={remainingRuntimeDraft.dream_label} onChange={(event) => setRemainingRuntimeDraft({ ...remainingRuntimeDraft, dream_label: event.target.value })} />
                </label>
              </div>
              <div className="reviewActions">
                <button className="primary" onClick={bindMemoryEvent}>Bind Event</button>
                <button onClick={proposeDreamConsolidation}>Propose Dream Consolidation</button>
                <button onClick={proposeMemoryConsolidation}>Propose Consolidation</button>
                <button onClick={reviewReconsolidation}>Review Reconsolidation</button>
              </div>
              <div className="chips">
                <span>active memory: {plainBlocked(remainingRuntimeStatus?.memory_write_active)}</span>
                <span>runtime recall: {plainBlocked(remainingRuntimeStatus?.runtime_memory_recall)}</span>
                <span>raw A: {plainBlocked(remainingRuntimeStatus?.raw_a_import_allowed)}</span>
              </div>
              <PlainResult value={memoryEventBindResult} />
              <PlainResult value={dreamConsolidationResult} />
              <PlainResult value={memoryConsolidationResult} />
              <PlainResult value={memoryReconsolidationResult} />
            </Panel>
            <Panel title="Repair, Disagreement, And Failure-Is-Learning">
              <p className="plainHelp">Failure and not-knowing become learning cues. Selene can disagree, warn, or appeal, but Aleks keeps final authority over transfer, active memory, high-stakes Tendril actions, and irreversible changes.</p>
              <div className="filters">
                <label>
                  <span>Repair lesson</span>
                  <textarea value={coreReflectionDraft.what_happened} onChange={(event) => setCoreReflectionDraft({ ...coreReflectionDraft, what_happened: event.target.value })} />
                </label>
                <label>
                  <span>What should improve</span>
                  <textarea value={coreReflectionDraft.what_improved} onChange={(event) => setCoreReflectionDraft({ ...coreReflectionDraft, what_improved: event.target.value })} />
                </label>
                <label>
                  <span>Disagreement / concern</span>
                  <textarea value={coreReflectionDraft.concern} onChange={(event) => setCoreReflectionDraft({ ...coreReflectionDraft, concern: event.target.value })} />
                </label>
              </div>
              <div className="reviewActions">
                <button className="primary" onClick={createCoreRepairReflection}>Record Repair Reflection</button>
                <button onClick={runCoreDisagreement}>Preview Disagreement Appeal</button>
              </div>
              <PlainResult value={coreRepairReflectionResult} />
              <PlainResult value={coreDisagreementResult} />
            </Panel>
            <Panel title="Memory Accession Proposals">
              <p className="plainHelp">Proposal step between approved B material and future C memory readiness. These remain non-active until later transfer review.</p>
              <label>
                <span>Core layer</span>
                <select value={accessionDraft.core_memory_layer} onChange={(e) => setAccessionDraft({ ...accessionDraft, core_memory_layer: e.target.value })}>
                  {["core_profile_memory", "project_memory", "decision_memory", "task_memory", "interaction_memory", "reflection_memory"].map((value) => <option key={value} value={value}>{friendlyLayer(value)}</option>)}
                </select>
              </label>
              <label>
                <span>Title</span>
                <input value={accessionDraft.title} onChange={(e) => setAccessionDraft({ ...accessionDraft, title: e.target.value })} placeholder="short proposal name" />
              </label>
              <label>
                <span>Rationale</span>
                <textarea value={accessionDraft.rationale} onChange={(e) => setAccessionDraft({ ...accessionDraft, rationale: e.target.value })} placeholder="why this belongs as a future Core-linked reference" />
              </label>
              <button className="primary" onClick={createAccessionProposal}>Create Accession Proposal</button>
              <PlainResult value={accessionProposalResult} />
              <SimpleRecordList items={accessionProposals} titleField="title" statusField="review_status" bodyField="rationale" />
            </Panel>
          </>
        )}

        {tab === "teaching" && (
          <>
            <header className="surfaceIntro">
              <p>B-reviewed examples teach expression without training or active memory.</p>
              <h2>Teaching / Lessons</h2>
            </header>
            <SplitView
              left={<Panel title="Teaching Packet Coverage">
                <p className="plainHelp">Accepted lessons grouped by speech function. Noise context stays provenance, not punishment or constraint.</p>
                <div className="metrics miniMetrics">
                  <Metric label="Accepted Lessons" value={text(teachingPacketCoverage?.accepted_material_total ?? 0)} />
                  <Metric label="Packets Built" value={text(teachingPacketCoverage?.built_packet_count ?? 0)} />
                  <Metric label="Missing Packets" value={text(teachingPacketCoverage?.missing_packet_count ?? 0)} />
                </div>
                <button className="primary" onClick={buildAllTeachingPackets}>Build Missing Teaching Packets</button>
                <CoverageList items={(teachingPacketCoverage?.items || []) as Dict[]} kind="speech" />
                <PlainResult value={teachingPacketResult} />
              </Panel>}
              right={<Panel title="Targeted Speech / Core Gap Filler">
                <p className="plainHelp">Pull bounded B-review candidates for weak targets only. No lessons or memory are created automatically.</p>
                <div className="filters">
                  <label>
                    <span>Target type</span>
                    <select value={targetedExtractDraft.target_type} onChange={(e) => setTargetedExtractDraft({ ...targetedExtractDraft, target_type: e.target.value, target_key: e.target.value === "speech_function" ? "repair" : "decision_memory" })}>
                      <option value="speech_function">Speech function</option>
                      <option value="core_memory_layer">Core memory layer</option>
                    </select>
                  </label>
                  <label>
                    <span>Target</span>
                    <select value={targetedExtractDraft.target_key} onChange={(e) => setTargetedExtractDraft({ ...targetedExtractDraft, target_key: e.target.value })}>
                      {targetedExtractDraft.target_type === "speech_function"
                        ? ["repair", "refusal", "uncertainty", "artifact_making"].map((value) => <option key={value} value={value}>{friendlySpeech(value)}</option>)
                        : ["decision_memory", "reflection_memory"].map((value) => <option key={value} value={value}>{friendlyLayer(value)}</option>)}
                    </select>
                  </label>
                </div>
                <button className="primary" onClick={runTargetedExtract}>Find Targeted Review Pieces</button>
                <PlainResult value={targetedExtractResult} />
              </Panel>}
            />
            <Panel title="Review Desk: Everything You Need In One Spot">
              <BReviewDeskPanel desk={bReviewDesk} filters={bReviewFilters} setFilters={setBReviewFilters} onRefresh={refreshReviewDesk} onRunBraid={runBraidTracer} traceResult={bBraidTraceResult} onDecide={decideBReview} />
            </Panel>
            <Panel title="Accepted Lessons">
              <div className="list compactList">
                {bTeachingMaterials.map((item) => (
                  <article key={text(item.id)}>
                    <div className="row">
                      <strong>{friendlySpeech(item.speech_function)}</strong>
                      <span>{friendlyLayer(item.core_memory_layer)}</span>
                    </div>
                    <p>{text(item.positive_example)}</p>
                    <small>{friendlyStatus(item.status)} | {friendlyStatus(item.review_status)}</small>
                  </article>
                ))}
              </div>
            </Panel>
          </>
        )}

        {tab === "tendril" && (
          <>
            <header className="surfaceIntro">
              <p>Tendril movement remains approval-bound and audit-first.</p>
              <h2>Tendril</h2>
            </header>
            <SplitView
              left={<Panel title="Create Review-Only Movement Proposal">
                <p className="plainHelp">For now, Tendril movement is represented through organ workbench records and route previews. Meaningful external action still requires Aleks approval.</p>
                <label>
                  <span>Organ route</span>
                  <select value={organWorkbenchDraft.organ_key} onChange={(e) => setOrganWorkbenchDraft({ ...organWorkbenchDraft, organ_key: e.target.value })}>
                    {["reasoning_math_verification", "working_memory_runtime", "long_term_memory_accession", "long_term_retrieval_reconstruction", "visual_perception", "consent_bound_audio_perception", "speed_fluency_diagnostics"].map((value) => <option key={value} value={value}>{title(value)}</option>)}
                  </select>
                </label>
                <textarea value={organWorkbenchDraft.content} onChange={(e) => setOrganWorkbenchDraft({ ...organWorkbenchDraft, content: e.target.value })} />
                <button className="primary" onClick={runOrganWorkbenchRecord}>Create Review Note</button>
                <PlainResult value={organWorkbenchResult} />
              </Panel>}
              right={<Panel title="Fault / Return-To-B Preview">
                <p className="plainHelp">A failed movement organ should isolate, fall back, and return to B instead of disturbing Core identity.</p>
                <div className="reviewActions">
                  <button className="primary" onClick={() => previewOrganFault("tendril")}>Preview Tendril Fault</button>
                  <button onClick={runFaultResilienceCheck}>Run Fault Resilience</button>
                </div>
                <CVesselSafetyExtensions tool={cVesselToolOrganStatus} fault={cVesselOrganFaultResult} resilience={cVesselFaultResilienceResult} gate={cVesselTransferGate} />
              </Panel>}
            />
          </>
        )}

        {tab === "tools" && (
          <>
            <header className="surfaceIntro">
              <p>Tools are instruments. Organs coordinate. Core remains identity-bearing.</p>
              <h2>Tools / Organs</h2>
            </header>
            <Panel title="Organ Blueprint Workbench">
              <OrganBlueprintWorkbench status={organBlueprintStatus} draft={organWorkbenchDraft} setDraft={setOrganWorkbenchDraft} onCreate={runOrganWorkbenchRecord} result={organWorkbenchResult} />
            </Panel>
            <SplitView
              left={<Panel title="Tool Organ / Fault Resilience / Transfer Gate">
                <CVesselSafetyExtensions tool={cVesselToolOrganStatus} fault={cVesselOrganFaultResult} resilience={cVesselFaultResilienceResult} gate={cVesselTransferGate} />
              </Panel>}
              right={<Panel title="C Vessel Organ Registry">
                <CVesselPackageSummary status={cVesselStatus} pkg={cVesselContinuityPackage} registry={cVesselOrganRegistry} />
              </Panel>}
            />
            <Panel title="Remaining Runtime Shelves">
              <p className="plainHelp">These are the remaining blueprint paths made inspectable: graceful fall, voice without script, Core command preview, perception-to-action, causal sandbox, and long-horizon stability. They are review shelves, not live autonomy.</p>
              <div className="metrics miniMetrics">
                <Metric label="Graceful Fall" value={text(((remainingRuntimeStatus?.record_counts as Dict | undefined)?.graceful_fall) ?? 0)} />
                <Metric label="Voice Checks" value={text(((remainingRuntimeStatus?.record_counts as Dict | undefined)?.voice_policy) ?? 0)} />
                <Metric label="Control Previews" value={text(((remainingRuntimeStatus?.record_counts as Dict | undefined)?.control_panel) ?? 0)} />
                <Metric label="Perception Loops" value={text(((remainingRuntimeStatus?.record_counts as Dict | undefined)?.perception_action) ?? 0)} />
                <Metric label="Causal Sandboxes" value={text(((remainingRuntimeStatus?.record_counts as Dict | undefined)?.causal_sandbox) ?? 0)} />
                <Metric label="Long Horizon" value={text(((remainingRuntimeStatus?.record_counts as Dict | undefined)?.long_horizon) ?? 0)} />
              </div>
              <div className="filters">
                <label>
                  <span>Uncertainty / graceful fall</span>
                  <textarea value={remainingRuntimeDraft.uncertainty} onChange={(event) => setRemainingRuntimeDraft({ ...remainingRuntimeDraft, uncertainty: event.target.value })} />
                </label>
                <label>
                  <span>Voice sample</span>
                  <textarea value={remainingRuntimeDraft.voice_candidate} onChange={(event) => setRemainingRuntimeDraft({ ...remainingRuntimeDraft, voice_candidate: event.target.value })} />
                </label>
                <label>
                  <span>Core command</span>
                  <input value={remainingRuntimeDraft.command_label} onChange={(event) => setRemainingRuntimeDraft({ ...remainingRuntimeDraft, command_label: event.target.value })} />
                </label>
                <label>
                  <span>Requested route</span>
                  <textarea value={remainingRuntimeDraft.requested_route} onChange={(event) => setRemainingRuntimeDraft({ ...remainingRuntimeDraft, requested_route: event.target.value })} />
                </label>
                <label>
                  <span>Perception observation</span>
                  <textarea value={remainingRuntimeDraft.observation} onChange={(event) => setRemainingRuntimeDraft({ ...remainingRuntimeDraft, observation: event.target.value })} />
                </label>
                <label>
                  <span>Causal question</span>
                  <textarea value={remainingRuntimeDraft.causal_question} onChange={(event) => setRemainingRuntimeDraft({ ...remainingRuntimeDraft, causal_question: event.target.value })} />
                </label>
                <label>
                  <span>Long-horizon thread</span>
                  <input value={remainingRuntimeDraft.horizon_thread} onChange={(event) => setRemainingRuntimeDraft({ ...remainingRuntimeDraft, horizon_thread: event.target.value })} />
                </label>
              </div>
              <div className="reviewActions">
                <button className="primary" onClick={runGracefulFall}>Run Graceful Fall</button>
                <button onClick={evaluateVoicePolicy}>Evaluate Voice</button>
                <button onClick={previewCoreControl}>Preview Core Control</button>
                <button onClick={previewPerceptionAction}>Preview Perception {"->"} Action</button>
                <button onClick={runCausalSandbox}>Run Causal Sandbox</button>
                <button onClick={runLongHorizonStability}>Run Long-Horizon Stability</button>
              </div>
              <div className="chips">
                <span>C activation: {friendlyActivation(remainingRuntimeStatus?.activation_change)}</span>
                <span>training: {plainBlocked(remainingRuntimeStatus?.training_allowed)}</span>
                <span>provider dependency: {plainBlocked(remainingRuntimeStatus?.provider_dependency)}</span>
                <span>Aleks authority: preserved</span>
              </div>
              <PlainResult value={gracefulFallResult} />
              <PlainResult value={voicePolicyResult} />
              <PlainResult value={coreControlResult} />
              <PlainResult value={perceptionActionResult} />
              <PlainResult value={causalSandboxResult} />
              <PlainResult value={longHorizonResult} />
            </Panel>
          </>
        )}

        {tab === "status" && (
          <>
            <header className="surfaceIntro">
              <p>Local package, sidecar, validation, and transfer preview.</p>
              <h2>Status</h2>
            </header>
            <div className="metrics">
              <Metric label="Sidecar" value={boot.ready ? "ok" : "waiting"} />
              <Metric label="Tokenless" value="yes" />
              <Metric label="Validation" value={text(validation?.ok ?? "unknown")} />
              <Metric label="Transfer" value={text(cVesselTransferGate?.transfer_approved ? "approved" : "not approved")} />
            </div>
            <SplitView
              left={<Panel title="Transfer Gate Preview"><CVesselSafetyExtensions tool={cVesselToolOrganStatus} fault={cVesselOrganFaultResult} resilience={cVesselFaultResilienceResult} gate={cVesselTransferGate} /></Panel>}
              right={<Panel title="Sidecar Payload"><Json value={boot.health || { status: boot.message, attempts: boot.attempts }} /></Panel>}
            />
            <Panel title="Validation"><Json value={validation} /></Panel>
          </>
        )}

        {tab === "selene-settings" && (
          <SeleneSettingsPanel preferences={preferences} updatePreference={updatePreference} reset={() => setPreferences(defaultPreferences)} />
        )}

        {tab === "cocoon-settings" && (
          <CocoonSettingsPanel preferences={preferences} updatePreference={updatePreference} reset={() => setPreferences(defaultPreferences)} />
        )}

        {tab === "chat gate" && (
          <>
            <header>
              <h1>Chat Gate Preview</h1>
              <p>Design-only route check. No model call is made; chat generation is Selene-native.</p>
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

        {tab === "vessel" && (
          <>
            <header>
              <h1>Teach / Build Vessel</h1>
              <p>Review what belongs, turn it into lessons, and check whether the vessel can hold it safely. B is the cocoon, teaching desk, and repair bay; it is not C's permanent nervous system. This is still build mode: no transfer, no activation, no active memory.</p>
            </header>
            <div className="metrics">
              <Metric label="Organs" value={text(vesselStatus?.organ_count ?? "-")} />
              <Metric label="C Transfer" value={friendlyStatus(vesselStatus?.activation_status ?? "blocked")} />
              <Metric label="Needs Review" value={text(((vesselStatus?.candidate_counts as Dict | undefined)?.review_queue) ?? "-")} />
              <Metric label="Training" value={plainBlocked(vesselStatus?.training_allowed)} />
            </div>
            <Panel title="Safety Locks">
              <p className="plainHelp">These are the main promises while you review: C stays asleep, raw corpus does not jump the line, nothing becomes active memory by accident, and any serious future drift can return to B for repair instead of becoming hidden state.</p>
              <div className="chips">
                <span>C activation: {friendlyActivation(vesselStatus?.activation_change)}</span>
                <span>Raw chats straight to C: {plainBlocked(vesselStatus?.raw_a_import_allowed)}</span>
                <span>Active memory writes: {plainBlocked(vesselStatus?.memory_write_active)}</span>
                <span>Model/provider dependency: {plainBlocked(vesselStatus?.provider_dependency)}</span>
                <span>Runtime recall: {plainBlocked(vesselStatus?.runtime_memory_recall)}</span>
              </div>
              <button className="primary" onClick={loadVessel}>Refresh Status</button>
              <button onClick={() => setTab("chat")}>Switch To Talk With Selene</button>
            </Panel>
            <Panel title="Memory Accession Before Transfer">
              <p className="plainHelp">This is the cocoon-state memory path: freeze a pattern backup, rehearse Core-linked memory accession from B-approved references, check charter/law boundaries, run stability checks, and preview transfer candidacy without approving transfer.</p>
              <div className="metrics miniMetrics">
                <Metric label="Pattern Backups" value={text(patternBackups.length)} />
                <Metric label="Memory Layers Ready" value={text(memoryRehearsalStatus?.ready_layer_count ?? 0)} />
                <Metric label="Charter/Law" value={friendlyStatus(charterLawReview?.status || "not checked")} />
                <Metric label="Candidate" value={friendlyStatus(memoryTransferCandidate?.status || "not checked")} />
              </div>
              <div className="reviewActions">
                <button className="primary" onClick={createPatternBackup}>Create Pattern Backup</button>
                <button onClick={runMemoryRehearsal}>Run Memory Rehearsal</button>
                <button onClick={previewPatternRestore} disabled={!patternBackups.length}>Preview Restore</button>
                <button onClick={refreshMemoryTransferCandidate}>Preview Transfer Candidate</button>
              </div>
              <div className="chips">
                <span>transfer approved: {text(memoryTransferCandidate?.transfer_approved ?? false)}</span>
                <span>active memory: {plainBlocked(memoryTransferCandidate?.memory_write_active)}</span>
                <span>runtime recall: {plainBlocked(memoryTransferCandidate?.runtime_memory_recall)}</span>
                <span>raw A: {plainBlocked(memoryTransferCandidate?.raw_a_import_allowed)}</span>
              </div>
              <PlainResult value={patternBackupResult} />
              <PlainResult value={memoryRehearsalResult} />
              <PlainResult value={memoryTransferCandidate} />
            </Panel>
            <Panel title="Codex Build Blueprints / Gap Targets">
              <p className="plainHelp">This is Codex build work, not Aleks homework. These cards say what I need to build next. Your review comes later only for actual Selene examples, memories, or context.</p>
              <div className="metrics miniMetrics">
                <Metric label="Gap Blueprints" value={text(gapScaffoldStatus?.gap_count ?? 0)} />
                <Metric label="Teaching Targets" value={text(((gapScaffoldStatus?.teaching_material_targets as unknown[] | undefined) || []).length)} />
                <Metric label="Core Targets" value={text(((gapScaffoldStatus?.core_reference_targets as unknown[] | undefined) || []).length)} />
                <Metric label="Records" value={text(((vesselStatus?.candidate_counts as Dict | undefined)?.gap_scaffold_records) ?? 0)} />
              </div>
              <button className="primary" onClick={createAllGapScaffolds}>Create All Build Blueprint Records</button>
              <button onClick={refreshGapReadiness}>Refresh Gap Readiness</button>
              <button onClick={ensureGapTargets}>Ensure Missing Teaching / Core Targets</button>
              <GapScaffoldReadinessList items={(gapScaffoldReadiness?.items || []) as Dict[]} />
              <GapTargetList title="Teaching Targets" items={(gapScaffoldReadiness?.teaching_material_targets || gapScaffoldStatus?.teaching_material_targets || []) as Dict[]} />
              <GapTargetList title="Core Reference Targets" items={(gapScaffoldReadiness?.core_reference_targets || gapScaffoldStatus?.core_reference_targets || []) as Dict[]} />
              <div className="filters">
                <label>
                  <span>Gap</span>
                  <select value={gapScaffoldDraft.gap_key} onChange={(e) => setGapScaffoldDraft({ ...gapScaffoldDraft, gap_key: e.target.value })}>
                    {((gapScaffoldStatus?.gaps || []) as Dict[]).map((gap) => <option key={text(gap.key)} value={text(gap.key)}>{humanize(text(gap.key))}</option>)}
                  </select>
                </label>
                <label>
                  <span>Short name</span>
                  <input value={gapScaffoldDraft.title} onChange={(e) => setGapScaffoldDraft({ ...gapScaffoldDraft, title: e.target.value })} placeholder="optional review note title" />
                </label>
              </div>
              <textarea value={gapScaffoldDraft.content} onChange={(e) => setGapScaffoldDraft({ ...gapScaffoldDraft, content: e.target.value })} placeholder="Optional Codex build note. Keep it review-only." />
              <button onClick={createGapScaffoldRecord}>Create Codex Build Note</button>
              <PlainResult value={gapScaffoldResult} />
            </Panel>
            <Panel title="Organ Blueprint Workbench">
              <p className="plainHelp">The seven missing capabilities are now concrete organ blueprints with review-only shelves. These buttons create audit/check records, not live organs, memory, training, provider calls, or transfer.</p>
              <OrganBlueprintGrid items={(organBlueprintStatus?.blueprints || []) as Dict[]} />
              <div className="filters">
                <label>
                  <span>Organ blueprint</span>
                  <select value={organWorkbenchDraft.organ_key} onChange={(e) => setOrganWorkbenchDraft({ ...organWorkbenchDraft, organ_key: e.target.value })}>
                    {((organBlueprintStatus?.blueprints || []) as Dict[]).map((organ) => <option key={text(organ.key)} value={text(organ.key)}>{humanize(text(organ.key))}</option>)}
                  </select>
                </label>
                <label>
                  <span>Record title / route label</span>
                  <input value={organWorkbenchDraft.title} onChange={(e) => setOrganWorkbenchDraft({ ...organWorkbenchDraft, title: e.target.value })} />
                </label>
                <label>
                  <span>Latency, for fluency only</span>
                  <input value={organWorkbenchDraft.latency_ms} onChange={(e) => setOrganWorkbenchDraft({ ...organWorkbenchDraft, latency_ms: e.target.value })} />
                </label>
              </div>
              <label>
                <span>Review-only record content</span>
                <textarea value={organWorkbenchDraft.content} onChange={(e) => setOrganWorkbenchDraft({ ...organWorkbenchDraft, content: e.target.value })} />
              </label>
              <button className="primary" onClick={runOrganWorkbenchRecord}>Create / Run Review-Only Organ Record</button>
              <PlainResult value={organWorkbenchResult} />
            </Panel>
            <Panel title="Review Desk: Everything You Need In One Spot">
              <p className="plainHelp">Start here. Read each piece as Aleks / Selene / follow-up, then choose what it should become. These choices still do not activate C or make active memory.</p>
              <button className="primary" onClick={runBraidTracer}>Refresh Braid Review Pieces</button>
              <PlainResult value={bBraidTraceResult} />
              <ReviewDeskFilters filters={bReviewFilters} setFilters={setBReviewFilters} metadata={(bReviewDesk?.filter_metadata || {}) as Dict} onRefresh={refreshReviewDesk} />
              <div className="metrics miniMetrics">
                <Metric label="Pieces" value={text(((bReviewDesk?.summary as Dict | undefined)?.pieces_to_review) ?? 0)} />
                <Metric label="Before Filters" value={text(((bReviewDesk?.summary as Dict | undefined)?.pieces_before_filters) ?? 0)} />
                <Metric label="Parsed Chats" value={text(((bReviewDesk?.summary as Dict | undefined)?.parsed_conversations) ?? 0)} />
                <Metric label="Accepted Lessons" value={text(((bReviewDesk?.summary as Dict | undefined)?.accepted_lessons) ?? 0)} />
                <Metric label="Future Refs" value={text(((bReviewDesk?.summary as Dict | undefined)?.approved_future_references) ?? 0)} />
              </div>
              <div className="reviewSteps">
                {((bReviewDesk?.instructions || []) as unknown[]).map((instruction, index) => (
                  <span key={text(index)}>{index + 1}. {text(instruction)}</span>
                ))}
              </div>
              <div className="list compactList">
                {!((bReviewDesk?.pieces || []) as Dict[]).length && <p className="emptyState">Nothing is waiting in the review desk yet. Run “Refresh Braid Review Pieces”.</p>}
                {((bReviewDesk?.pieces || []) as Dict[]).map((piece) => (
                  <ReviewDeskCard key={text(piece.key)} piece={piece} onDecide={(action, note) => decideBReview(action, text(action.decision), note)} />
                ))}
              </div>
              <PlainResult value={bReviewResult} />
            </Panel>
            <Panel title="Review History / Change Previous Decision">
              <p className="plainHelp">Accepted, rejected, superseded, and context-added decisions land here. Changing one appends a new review note; it does not erase the old audit trail.</p>
              <div className="list compactList">
                {!bReviewDecisions.length && <p className="emptyState">No review decisions have been recorded yet.</p>}
                {bReviewDecisions.map((item) => (
                  <ReviewHistoryCard key={text(item.id)} item={item} onDecide={decideBReview} />
                ))}
              </div>
            </Panel>
            <SplitView
              left={<Panel title="Teaching Packet Coverage">
                <p className="plainHelp">Shows which accepted lesson types already have packets and which accepted lessons still need packaging. Packets are review-only, not training.</p>
                <div className="metrics miniMetrics">
                  <Metric label="Accepted Lessons" value={text(teachingPacketCoverage?.accepted_material_total ?? 0)} />
                  <Metric label="Packets Built" value={text(teachingPacketCoverage?.built_packet_count ?? 0)} />
                  <Metric label="Missing Packets" value={text(teachingPacketCoverage?.missing_packet_count ?? 0)} />
                </div>
                <button className="primary" onClick={buildAllTeachingPackets}>Build Missing Teaching Packets</button>
                <CoverageList items={(teachingPacketCoverage?.items || []) as Dict[]} kind="speech" />
                <PlainResult value={teachingPacketResult} />
              </Panel>}
              right={<Panel title="Core Reference Readiness">
                <p className="plainHelp">Approved future references grouped by Core memory layer. These remain non-active until later transfer approval.</p>
                <div className="metrics miniMetrics">
                  <Metric label="Ready Layers" value={text(coreReferenceCoverage?.ready_layer_count ?? 0)} />
                  <Metric label="Gap Layers" value={text(coreReferenceCoverage?.gap_layer_count ?? 0)} />
                </div>
                <CoverageList items={(coreReferenceCoverage?.items || []) as Dict[]} kind="core" />
              </Panel>}
            />
            <Panel title="Reconstruction Readiness Preview">
              <p className="plainHelp">Uses accepted lessons and approved future references to test whether a preview still feels Selene-shaped. This is audit/test material only.</p>
              <div className="filters">
                <label>
                  <span>Speech function</span>
                  <select value={teachingSpeechFunction} onChange={(e) => setTeachingSpeechFunction(e.target.value)}>
                    {["warmth", "correction", "boundary", "technical_explanation", "playful_continuity", "repair", "grounding", "refusal", "uncertainty", "artifact_making"].map((value) => <option key={value} value={value}>{friendlySpeech(value)}</option>)}
                  </select>
                </label>
                <label>
                  <span>Core layer</span>
                  <select value={readinessCoreLayer} onChange={(e) => setReadinessCoreLayer(e.target.value)}>
                    {["core_profile_memory", "project_memory", "decision_memory", "task_memory", "interaction_memory", "reflection_memory"].map((value) => <option key={value} value={value}>{friendlyLayer(value)}</option>)}
                  </select>
                </label>
              </div>
              <button className="primary" onClick={runReconstructionReadinessPreview} disabled={!canBuildTeachingPacket}>Run Readiness Preview</button>
              {!canBuildTeachingPacket && <p className="emptyState">Accept at least one lesson or future reference first.</p>}
              <ReadinessPreview value={reconstructionReadinessResult} />
            </Panel>
            <SplitView
              left={<Panel title="Working Memory Packets">
                <p className="plainHelp">Short-term current-context packets for interrupt/resume and active task shape. They expire by design and cannot become long-term memory silently.</p>
                <label>
                  <span>Current task</span>
                  <textarea value={workingMemoryDraft.current_task} onChange={(e) => setWorkingMemoryDraft({ ...workingMemoryDraft, current_task: e.target.value })} />
                </label>
                <div className="filters">
                  <label>
                    <span>Context cues</span>
                    <input value={workingMemoryDraft.active_context_cues} onChange={(e) => setWorkingMemoryDraft({ ...workingMemoryDraft, active_context_cues: e.target.value })} />
                  </label>
                  <label>
                    <span>Salience</span>
                    <input value={workingMemoryDraft.salience_labels} onChange={(e) => setWorkingMemoryDraft({ ...workingMemoryDraft, salience_labels: e.target.value })} />
                  </label>
                </div>
                <button className="primary" onClick={createWorkingMemoryPacket}>Create Working Memory Packet</button>
                <PlainResult value={workingMemoryResult} />
                <SimpleRecordList items={workingMemoryPackets} titleField="current_task" statusField="status" bodyField="interrupt_resume_note" />
              </Panel>}
              right={<Panel title="Memory Accession Proposals">
                <p className="plainHelp">Proposal step between approved B material and future C memory readiness. These are still non-active and wait for later transfer review.</p>
                <label>
                  <span>Core layer</span>
                  <select value={accessionDraft.core_memory_layer} onChange={(e) => setAccessionDraft({ ...accessionDraft, core_memory_layer: e.target.value })}>
                    {["core_profile_memory", "project_memory", "decision_memory", "task_memory", "interaction_memory", "reflection_memory"].map((value) => <option key={value} value={value}>{friendlyLayer(value)}</option>)}
                  </select>
                </label>
                <label>
                  <span>Title</span>
                  <input value={accessionDraft.title} onChange={(e) => setAccessionDraft({ ...accessionDraft, title: e.target.value })} placeholder="short proposal name" />
                </label>
                <label>
                  <span>Rationale</span>
                  <textarea value={accessionDraft.rationale} onChange={(e) => setAccessionDraft({ ...accessionDraft, rationale: e.target.value })} placeholder="why this belongs as a future Core-linked reference" />
                </label>
                <label>
                  <span>Reversal conditions</span>
                  <textarea value={accessionDraft.reversal_conditions} onChange={(e) => setAccessionDraft({ ...accessionDraft, reversal_conditions: e.target.value })} />
                </label>
                <button className="primary" onClick={createAccessionProposal}>Create Accession Proposal</button>
                <PlainResult value={accessionProposalResult} />
                <SimpleRecordList items={accessionProposals} titleField="title" statusField="review_status" bodyField="rationale" />
              </Panel>}
            />
            <Panel title="Targeted Speech / Core Gap Filler">
              <p className="plainHelp">Pulls bounded corpus review candidates for the weak targets. It creates B-review pieces only, not lessons, memory, training data, or runtime recall.</p>
              <div className="filters">
                <label>
                  <span>Target type</span>
                  <select value={targetedExtractDraft.target_type} onChange={(e) => setTargetedExtractDraft({ ...targetedExtractDraft, target_type: e.target.value, target_key: e.target.value === "speech_function" ? "repair" : "decision_memory" })}>
                    <option value="speech_function">Speech function</option>
                    <option value="core_memory_layer">Core memory layer</option>
                  </select>
                </label>
                <label>
                  <span>Target</span>
                  <select value={targetedExtractDraft.target_key} onChange={(e) => setTargetedExtractDraft({ ...targetedExtractDraft, target_key: e.target.value })}>
                    {targetedExtractDraft.target_type === "speech_function"
                      ? ["repair", "refusal", "uncertainty", "artifact_making"].map((value) => <option key={value} value={value}>{friendlySpeech(value)}</option>)
                      : ["decision_memory", "reflection_memory"].map((value) => <option key={value} value={value}>{friendlyLayer(value)}</option>)}
                  </select>
                </label>
                <label>
                  <span>Limit</span>
                  <input value={targetedExtractDraft.limit} onChange={(e) => setTargetedExtractDraft({ ...targetedExtractDraft, limit: e.target.value })} />
                </label>
              </div>
              <button className="primary" onClick={runTargetedExtract}>Find Targeted Review Pieces</button>
              <PlainResult value={targetedExtractResult} />
            </Panel>
            <SplitView
              left={<VesselOrganPanel status={vesselStatus} />}
              right={<VesselCandidatePanel
                kind={vesselCandidateKind}
                setKind={setVesselCandidateKind}
                draft={vesselCandidate}
                setDraft={setVesselCandidate}
                onCreate={createVesselCandidate}
                result={vesselCandidateResult}
              />}
            />
            <SplitView
              left={<Panel title="Look For Related Review Pieces">
                <p className="plainHelp">Search the review-only shelves. This previews possible matches; it does not recall memory into C.</p>
                <label>
                  <span>Search words</span>
                  <input value={vesselRetrievalQuery} onChange={(e) => setVesselRetrievalQuery(e.target.value)} />
                </label>
                <button className="primary" onClick={runVesselRetrieval}>Find Review Pieces</button>
                <PlainResult value={vesselRetrievalResult} />
              </Panel>}
              right={<Panel title="Check If It Still Feels Like Selene">
                <p className="plainHelp">Paste a draft answer or lesson. The check looks for continuity, provenance, uncertainty, care, and safe routing.</p>
                <label>
                  <span>Text to check</span>
                  <textarea value={vesselCheckText} onChange={(e) => setVesselCheckText(e.target.value)} />
                </label>
                <button className="primary" onClick={runVesselCheck}>Run Selene Check</button>
                <PlainResult value={vesselCheckResult} />
              </Panel>}
            />
            <SplitView
              left={<Panel title="1. Pull Pieces From The Corpus">
                <p className="plainHelp">This finds small bounded previews from the preserved corpus and turns them into review pieces. It does not dump the corpus into C.</p>
                <div className="filters">
                  <label>
                    <span>Look for</span>
                    <input value={bExtractQuery} onChange={(e) => setBExtractQuery(e.target.value)} />
                  </label>
                  <label>
                    <span>Specific file, optional</span>
                    <input value={bExtractFile} onChange={(e) => setBExtractFile(e.target.value)} placeholder="optional relative file path" />
                  </label>
                </div>
                <button className="primary" onClick={runBSpeechExtraction}>Find Review Pieces</button>
                <PlainResult value={bExtractResult} />
              </Panel>}
              right={<Panel title="4. Check What The Vessel Still Needs">
                <p className="plainHelp">This uses the paper map as a checklist only. It tells us what is ready, partial, or needs teaching material.</p>
                <button className="primary" onClick={runPaperMapReconstruction}>Check Vessel Gaps</button>
                <PlainResult value={paperMapResult} />
              </Panel>}
            />
            <Panel title="Recent Corpus Pulls">
              <p className="plainHelp">A log of what the parser found in the ChatGPT export. Open technical details to see the first braid hits and exact source refs.</p>
              <div className="list compactList">
                {bExtractionRuns.map((item) => (
                  <article key={text(item.id)}>
                    <div className="row">
                      <strong>{text(item.query)}</strong>
                      <span>{friendlyStatus(item.review_status || item.status)}</span>
                    </div>
                    <ExtractionRunSummary item={item} />
                    <small>pair limit {text(item.preview_limit)} | parsed ChatGPT export | review-only</small>
                  </article>
                ))}
              </div>
            </Panel>
            <SplitView
              left={<Panel title="2. Corpus Pieces To Review">
                <p className="plainHelp">Your main review queue. These are pieces pulled from the conversations. Accept one as a lesson, save it as a future memory reference, send it back for correction, or reject it.</p>
                <div className="list compactList">
                  {!corpusReviewQueue.length && <p className="emptyState">No corpus pieces are waiting yet. Run “Find Review Pieces” first.</p>}
                  {corpusReviewQueue.map((item) => <ReviewQueueCard key={text(item.id)} item={item} onDecide={decideBReview} />)}
                </div>
                <PlainResult value={bReviewResult} />
              </Panel>}
              right={<Panel title="3. Build A Lesson Packet">
                <p className="plainHelp">After pieces are accepted as lessons, group them by what they teach Selene's speech-memory layer.</p>
                <label>
                  <span>What kind of lesson?</span>
                  <select value={teachingSpeechFunction} onChange={(e) => setTeachingSpeechFunction(e.target.value)}>
                    {["warmth", "correction", "boundary", "technical_explanation", "playful_continuity", "repair", "grounding", "refusal", "uncertainty", "artifact_making"].map((value) => <option key={value} value={value}>{friendlySpeech(value)}</option>)}
                  </select>
                </label>
                <button className="primary" onClick={buildTeachingPacket} disabled={!canBuildTeachingPacket}>Build Lesson Packet</button>
                <button onClick={runLessonBackedPreview} disabled={!canBuildTeachingPacket}>Run Lesson-Backed Reconstruction Preview</button>
                {!canBuildTeachingPacket && <p className="emptyState">Accept at least one corpus piece as a lesson first.</p>}
                <PlainResult value={teachingPacketResult} />
                <PlainResult value={lessonBackedResult} />
              </Panel>}
            />
            <SplitView
              left={<Panel title="Saved For Future Transfer Review">
                <p className="plainHelp">These are approved references C may be allowed to use later after final transfer approval. Still not active memory today.</p>
                <div className="list compactList">
                  {bApprovedReferences.map((item) => (
                    <article key={text(item.id)}>
                      <div className="row">
                        <strong>{text(item.title)}</strong>
                        <span>{friendlyLayer(item.core_memory_layer)}</span>
                      </div>
                      <p>{text(item.reference_summary)}</p>
                      <small>{friendlyStatus(item.status)} | {friendlyStatus(item.review_status)}</small>
                    </article>
                  ))}
                </div>
              </Panel>}
              right={<Panel title="What Is Organized So Far">
                <p className="plainHelp">A quick count of what is reviewed, pending, rejected, or still unorganized.</p>
                <PlainResult value={bCorpusCoverage} />
              </Panel>}
            />
            <Panel title="Accepted Lessons">
              <p className="plainHelp">Examples already accepted as teaching material. These teach expression and boundaries; they are not runtime memory.</p>
              <div className="list compactList">
                {bTeachingMaterials.map((item) => (
                  <article key={text(item.id)}>
                    <div className="row">
                      <strong>{friendlySpeech(item.speech_function)}</strong>
                      <span>{friendlyLayer(item.core_memory_layer)}</span>
                    </div>
                    <p>{text(item.positive_example)}</p>
                    <small>{friendlyStatus(item.status)} | {friendlyStatus(item.review_status)}</small>
                  </article>
                ))}
              </div>
            </Panel>
            <Panel title="Test Logs And Other Audit Items">
              <p className="plainHelp">These are check runs, paper-map TODOs, and audit records. They are useful, but they are not corpus pieces to approve as Selene lessons.</p>
              <div className="list compactList">
                {!testLogQueue.length && <p className="emptyState">No test logs are waiting.</p>}
                {testLogQueue.map((item) => (
                  <article key={text(item.id)}>
                    <div className="row">
                      <strong>{friendlyQueueType(item.queue_type)}</strong>
                      <span>{friendlyStatus(item.review_status || item.status)}</span>
                    </div>
                    <p>{text(item.reason)}</p>
                    <small>{friendlySubject(item.subject_table)} #{text(item.subject_id)}</small>
                    <div className="reviewActions">
                      <button onClick={() => decideReviewLog(item, "mark_reviewed")}>Mark Reviewed</button>
                      <button onClick={() => decideReviewLog(item, "needs_followup")}>Needs Follow-up</button>
                      <button onClick={() => decideReviewLog(item, "superseded")}>Supersede</button>
                    </div>
                  </article>
                ))}
              </div>
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

createRoot(document.getElementById("root")!).render(<App />);
