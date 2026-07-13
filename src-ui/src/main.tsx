import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { invoke } from "@tauri-apps/api/core";
import { api } from "./api";
import {
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
import { countValues, friendlyActivation, friendlyCareText, friendlyLayer, friendlyOrganKey, friendlyQueueType, friendlySpeech, friendlyStatus, friendlySubject, humanize, plainBlocked, safeJsonObject, tabDisplayName, text, title } from "./helpers";
import { defaultPreferences, navGroups, preferenceKey, SELENE_ICON, vesselBackedTabs, workspaceGroups, workspaceTabs } from "./uiConfig";
import type { BootState, Dashboard, Dict, EvidenceDetail, SelenePreferences } from "./types";
import "./styles.css";

declare const __APP_VERSION__: string;
declare const __BUILD_LABEL__: string;

const TRANSFER_APPROVAL_PHRASE = "I, Aleks, approve Selene transfer to C-readable context under the Law of Transfer.";
const SIDECAR_RECONNECT_MESSAGE = "Local sidecar is not reachable. Close and reopen Selene, or use Refresh Ceremony after the app reconnects.";

type OfficeCategory = "review" | "corpus" | "vessel" | "runtime" | "codex" | "history";
type OfficeTarget = { tab?: string; category?: OfficeCategory; selectedReviewKey?: string; domId?: string; helper?: string };
type HomeMessage = { id: string; role: "aleks" | "selene"; content: string };
type MemoryCategoryKey = "core" | "relational" | "emotional" | "semantic" | "episodic" | "working" | "sensory" | "reflective";
type MemoryBubble = {
  id: string;
  category: MemoryCategoryKey;
  title: string;
  summary: string;
  status: string;
  source: string;
  confidence?: string;
  emotionalTexture?: string;
  transferClass?: string;
  chatUsePermission?: string;
};
type WorkbenchKey = "art" | "intelligence" | "reasoning" | "research" | "dream" | "tendril";
type WorkbenchDef = {
  key: WorkbenchKey;
  title: string;
  label: string;
  state: string;
  purpose: string;
  route: string;
  x: number;
  y: number;
  cues: string[];
};

const memoryCategories: Array<{ key: MemoryCategoryKey; label: string; x: number; y: number }> = [
  { key: "core", label: "Core", x: 50, y: 18 },
  { key: "relational", label: "Relational", x: 18, y: 37 },
  { key: "emotional", label: "Emotional", x: 21, y: 72 },
  { key: "semantic", label: "Semantic", x: 74, y: 30 },
  { key: "episodic", label: "Episodic", x: 83, y: 57 },
  { key: "working", label: "Working", x: 51, y: 84 },
  { key: "sensory", label: "Sensory", x: 76, y: 79 },
  { key: "reflective", label: "Reflective", x: 30, y: 86 }
];

function domSafe(value: unknown) {
  return text(value || "item").toLowerCase().replace(/[^a-z0-9_-]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 90) || "item";
}

function officeDomId(prefix: string, item: Dict, index = 0) {
  return `office-card-${domSafe(prefix)}-${domSafe(item.id || item.subject_id || item.fraction_index || item.title || item.claim || index)}`;
}

function sessionMessagesToHomeMessages(session: Dict | null): HomeMessage[] {
  const messages = ((session?.messages || []) as Dict[]);
  return messages.map((message, index) => ({
    id: `local-${text(message.id || index)}`,
    role: (text(message.role) === "user" ? "aleks" : "selene") as HomeMessage["role"],
    content: text(message.content)
  })).filter((message) => message.content.trim());
}

const officeWorkbenches: WorkbenchDef[] = [
  {
    key: "art",
    title: "Art / Munsell",
    label: "perception workbench",
    state: "preview",
    purpose: "Observe, classify, compare, build palettes, critique images, and prepare consent-bound visual notes.",
    route: "Cocoon Tools / Perception",
    x: 22,
    y: 31,
    cues: ["Munsell", "palette", "visual notes", "no live camera"]
  },
  {
    key: "intelligence",
    title: "intelligenceOS / Observatory",
    label: "reasoning organ",
    state: "preview",
    purpose: "Use ABCD(E) to observe cleanly, build models, challenge them equally, demonstrate evidence chains, and stop recursion gracefully.",
    route: "Status / intelligenceOS",
    x: 68,
    y: 42,
    cues: ["Acquire", "Build", "Challenge", "Demonstrate", "Evaluate"]
  },
  {
    key: "reasoning",
    title: "Math / Reasoning",
    label: "logic workbench",
    state: "preview",
    purpose: "Check logic, verify steps, catch contradictions, explain uncertainty, and prepare route previews.",
    route: "Cocoon Status / Reasoning",
    x: 72,
    y: 27,
    cues: ["proof", "uncertainty", "constraints", "no final authority"]
  },
  {
    key: "research",
    title: "Research / Library",
    label: "source workbench",
    state: "propose",
    purpose: "Gather, compare, synthesize, cite, flag weak evidence, and prepare study packets.",
    route: "Great Library / Evidence",
    x: 80,
    y: 66,
    cues: ["sources", "claims", "tensions", "source-linked"]
  },
  {
    key: "dream",
    title: "Dream / Maintenance",
    label: "sorting workbench",
    state: "status-only",
    purpose: "Sort residue, prepare consolidation proposals, notice tensions, and surface support questions.",
    route: "Dream / Cocoon Status",
    x: 46,
    y: 78,
    cues: ["cycle", "repair", "lifecycle", "memory write false"]
  },
  {
    key: "tendril",
    title: "Tendril Action",
    label: "movement workbench",
    state: "propose",
    purpose: "Draft, organize, search, and prepare action plans with approval gates before consequential movement.",
    route: "Tendril / Tool Gates",
    x: 25,
    y: 68,
    cues: ["observe", "propose", "prepare", "ask first"]
  }
];

const displayNameKey = "selene-home-display-name";

function loadDisplayName() {
  try {
    return window.localStorage.getItem(displayNameKey) || "Aleks";
  } catch {
    return "Aleks";
  }
}

function easternDateTime(date: Date, timeZone = "America/New_York") {
  return new Intl.DateTimeFormat("en-US", {
    timeZone,
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  }).format(date);
}

function moonPhaseEmoji(date: Date, hemisphere: "north" | "south") {
  const phasesNorth = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"];
  const phasesSouth = ["🌑", "🌘", "🌗", "🌖", "🌕", "🌔", "🌓", "🌒"];
  const knownNewMoon = Date.UTC(2000, 0, 6, 18, 14);
  const lunarCycleMs = 29.53058867 * 24 * 60 * 60 * 1000;
  const age = (((date.getTime() - knownNewMoon) % lunarCycleMs) + lunarCycleMs) % lunarCycleMs;
  const index = Math.floor((age / lunarCycleMs) * 8 + 0.5) % 8;
  return (hemisphere === "north" ? phasesNorth : phasesSouth)[index];
}

function homeGreeting(openCount: number, displayName: string) {
  if (openCount <= 0) return `Hello ${displayName}. Selene's home is open.`;
  const variants = [
    `New thread opened, ${displayName}. I will keep this one clean and separate.`,
    `Fresh chat space, ${displayName}. We can pick up gently from here.`,
    `A new room is ready, ${displayName}. Same continuity, clearer page.`
  ];
  return variants[openCount % variants.length];
}

function isFrontMemoryDisplayable(item: Dict) {
  const status = text([
    item.review_status,
    item.status,
    item.conclusion_status,
    item.readiness,
    item.review_state,
    item.source_class,
    item.item_type,
    item.record_type
  ].map(text).join(" ")).toLowerCase();
  if (!status) return true;
  return ![
    "rejected",
    "superseded",
    "defeated",
    "blocked",
    "boundary_only",
    "needs_review",
    "pending_review",
    "unresolved",
    "ambiguous",
    "raw",
    "repair_log",
    "rollback"
  ].some((blocked) => status.includes(blocked));
}

function memoryCategoryFromText(value: unknown): MemoryCategoryKey {
  const raw = text(value).toLowerCase();
  if (raw.includes("core_profile") || raw.includes("core") || raw.includes("identity") || raw.includes("continuity")) return "core";
  if (raw.includes("interaction") || raw.includes("relationship") || raw.includes("relational") || raw.includes("aleks")) return "relational";
  if (raw.includes("emotion") || raw.includes("care") || raw.includes("anxiety") || raw.includes("warmth")) return "emotional";
  if (raw.includes("reflection") || raw.includes("why") || raw.includes("repair") || raw.includes("lesson")) return "reflective";
  if (raw.includes("working") || raw.includes("task") || raw.includes("current")) return "working";
  if (raw.includes("sensory") || raw.includes("visual") || raw.includes("audio") || raw.includes("munsell") || raw.includes("perception")) return "sensory";
  if (raw.includes("episodic") || raw.includes("chronological") || raw.includes("fraction") || raw.includes("conversation")) return "episodic";
  return "semantic";
}

function loadPreferences(): SelenePreferences {
  try {
    const saved = window.localStorage.getItem(preferenceKey);
    if (!saved) return defaultPreferences;
    return { ...defaultPreferences, ...(JSON.parse(saved) as Partial<SelenePreferences>) };
  } catch {
    return defaultPreferences;
  }
}

function reviewPieceKey(piece: Dict) {
  return [
    text(piece.subject_table || piece.table || "review"),
    text(piece.subject_id || piece.id || piece.queue_id || ""),
    text(piece.review_number || ""),
    text(piece.title || "")
  ].join(":");
}

function reviewQueueItemKey(item: Dict, index = 0) {
  return [
    text(item.subject_table || item.queue_type || "review-log"),
    text(item.subject_id || ""),
    text(item.id || item.queue_id || index)
  ].join(":");
}

function isOfficeReviewLogItem(item: Dict) {
  return ["vessel_reconstruction_check_runs", "vessel_event_packets", "vessel_memory_accession_proposals", "c_core_mind_route_previews", "c_core_mind_runtime_shell_records"].includes(text(item.subject_table));
}

function sidecarStartupMessage(attempt: number, detail: string) {
  const elapsed = Math.max(1, attempt * 2);
  if (elapsed <= 6) return `starting local sidecar (${elapsed}s): ${detail}`;
  if (elapsed <= 30) return `waiting for local API (${elapsed}s): ${detail}`;
  return `sidecar took longer than expected (${elapsed}s). Still waiting for local API; startup logs are in the Selene logs folder.`;
}

function wait(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function isFetchFailure(err: unknown) {
  return err instanceof TypeError || (err instanceof Error && err.message.toLowerCase().includes("failed to fetch"));
}

function ceremonyDetail(payload: Dict = {}) {
  try {
    return JSON.stringify(payload).slice(0, 6000);
  } catch {
    return JSON.stringify({ serialization_error: true });
  }
}

function logTransferCeremonyEvent(event: string, payload: Dict = {}) {
  void invoke("log_transfer_ceremony_event", { event, detail: ceremonyDetail(payload) }).catch(() => undefined);
}

function logStabilizationEvent(event: string, payload: Dict = {}) {
  void invoke("log_stabilization_event", { event, detail: ceremonyDetail(payload) }).catch(() => undefined);
}

async function transferApi<T>(path: string, init?: RequestInit, event = "transfer_api"): Promise<T> {
  const started = Date.now();
  logTransferCeremonyEvent(`${event}_start`, {
    path,
    method: init?.method || "GET",
    body_bytes: typeof init?.body === "string" ? init.body.length : 0
  });
  try {
    const result = await api<T>(path, init);
    logTransferCeremonyEvent(`${event}_complete`, {
      path,
      method: init?.method || "GET",
      elapsed_ms: Date.now() - started
    });
    return result;
  } catch (err) {
    logTransferCeremonyEvent(`${event}_error`, {
      path,
      method: init?.method || "GET",
      elapsed_ms: Date.now() - started,
      error: err instanceof Error ? err.message : String(err),
      fetch_failure: isFetchFailure(err)
    });
    throw err;
  }
}

async function stabilizationApi<T>(path: string, init?: RequestInit, event = "stabilization_api"): Promise<T> {
  const started = Date.now();
  logStabilizationEvent(`${event}_start`, {
    path,
    method: init?.method || "GET",
    body_bytes: typeof init?.body === "string" ? init.body.length : 0
  });
  try {
    const result = await api<T>(path, init);
    logStabilizationEvent(`${event}_complete`, {
      path,
      method: init?.method || "GET",
      elapsed_ms: Date.now() - started
    });
    return result;
  } catch (err) {
    logStabilizationEvent(`${event}_error`, {
      path,
      method: init?.method || "GET",
      elapsed_ms: Date.now() - started,
      error: err instanceof Error ? err.message : String(err)
    });
    throw err;
  }
}

function transferManifestSummary(result: Dict, statusOverride?: string, message?: string): Dict {
  return {
    status: statusOverride || result.status || "transfer_accession_manifest_checked",
    message,
    item_count: result.item_count,
    counts: result.counts,
    transfer_approved: result.transfer_approved,
    activation_change: result.activation_change,
    memory_write_active: result.memory_write_active,
    runtime_memory_recall: result.runtime_memory_recall,
    raw_a_import_allowed: result.raw_a_import_allowed,
    training_allowed: result.training_allowed,
    self_replication_allowed: result.self_replication_allowed,
    autonomous_action_allowed: result.autonomous_action_allowed
  };
}

function App() {
  const isMobileOnly = window.location.pathname === "/mobile" || window.location.search.includes("mobile=1");
  const [tab, setTab] = useState("chat");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [workspaceMode, setWorkspaceMode] = useState<"selene" | "cocoon">("selene");
  const [preferences, setPreferences] = useState<SelenePreferences>(() => loadPreferences());
  const [displayName, setDisplayName] = useState(() => loadDisplayName());
  const [homeChatText, setHomeChatText] = useState("");
  const homeChatSendingRef = useRef(false);
  const [homeMessages, setHomeMessages] = useState<HomeMessage[]>([]);
  const [homeChatOpenCount, setHomeChatOpenCount] = useState(0);
  const [homeSearchOpen, setHomeSearchOpen] = useState(false);
  const [homeSearchText, setHomeSearchText] = useState("");
  const [pastChatsOpen, setPastChatsOpen] = useState(false);
  const [pastChatSearchText, setPastChatSearchText] = useState("");
  const [homeNotesOpen, setHomeNotesOpen] = useState(false);
  const [tendrilMenuOpen, setTendrilMenuOpen] = useState(false);
  const [timeMenuOpen, setTimeMenuOpen] = useState(false);
  const [homeTimeZone, setHomeTimeZone] = useState("America/New_York");
  const [moonHemisphere, setMoonHemisphere] = useState<"north" | "south">("north");
  const [clockNow, setClockNow] = useState(() => new Date());
  const [selectedMemoryCategory, setSelectedMemoryCategory] = useState<MemoryCategoryKey | null>(null);
  const [selectedWorkbench, setSelectedWorkbench] = useState<WorkbenchKey | null>(null);
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
  const [seleneChatText, setSeleneChatText] = useState("Selene, what is the next safe step?");
  const [seleneChatStatus, setSeleneChatStatus] = useState<Dict | null>(null);
  const [seleneChatSession, setSeleneChatSession] = useState<Dict | null>(null);
  const [seleneChatSessions, setSeleneChatSessions] = useState<Dict[]>([]);
  const [seleneChatResult, setSeleneChatResult] = useState<Dict | null>(null);
  const [activationStatus, setActivationStatus] = useState<Dict | null>(null);
  const [activationReadiness, setActivationReadiness] = useState<Dict | null>(null);
  const [activationCeremonyPreview, setActivationCeremonyPreview] = useState<Dict | null>(null);
  const [activationResult, setActivationResult] = useState<Dict | null>(null);
  const [activationApprovalPhrase, setActivationApprovalPhrase] = useState("");
  const [voiceModuleStatus, setVoiceModuleStatus] = useState<Dict | null>(null);
  const [voiceModulePatterns, setVoiceModulePatterns] = useState<Dict[]>([]);
  const [voiceEvidenceTriageStatus, setVoiceEvidenceTriageStatus] = useState<Dict | null>(null);
  const [voiceEvidenceTriageItems, setVoiceEvidenceTriageItems] = useState<Dict[]>([]);
  const [voiceModuleResult, setVoiceModuleResult] = useState<Dict | null>(null);
  const [seleneReasoningLessonResult, setSeleneReasoningLessonResult] = useState<Dict | null>(null);
  const [mobileHealth, setMobileHealth] = useState<Dict | null>(null);
  const [mobileText, setMobileText] = useState("");
  const [mobileSession, setMobileSession] = useState<Dict | null>(null);
  const [mobileSessions, setMobileSessions] = useState<Dict[]>([]);
  const [mobileSendResult, setMobileSendResult] = useState<Dict | null>(null);
  const [mobileStatus, setMobileStatus] = useState<Dict | null>(null);
  const [mobilePairing, setMobilePairing] = useState<Dict | null>(null);
  const [mobilePairingResult, setMobilePairingResult] = useState<Dict | null>(null);
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
    prohibited_use: "Do not treat as active memory, unreviewed source archive import, or provider identity."
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
  const [selectedOfficeReviewKey, setSelectedOfficeReviewKey] = useState("");
  const [officeCategory, setOfficeCategory] = useState<OfficeCategory>("review");
  const [focusedOfficeDomId, setFocusedOfficeDomId] = useState("");
  const [officeTargetMessage, setOfficeTargetMessage] = useState("");
  const [officeRefreshState, setOfficeRefreshState] = useState<Dict | null>(null);
  const [officeCleanupState, setOfficeCleanupState] = useState<Dict | null>(null);
  const [publicReleaseSyncState, setPublicReleaseSyncState] = useState<Dict | null>(null);
  const [publicReleasePreflight, setPublicReleasePreflight] = useState<Dict | null>(null);
  const [reviewAutopilotState, setReviewAutopilotState] = useState<Dict | null>(null);
  const [readinessSweepState, setReadinessSweepState] = useState<Dict | null>(null);
  const [diagnosticsRunState, setDiagnosticsRunState] = useState<Dict | null>(null);
  const [expandedDiagnosticsState, setExpandedDiagnosticsState] = useState<Dict | null>(null);
  const [preCoreReviewPackets, setPreCoreReviewPackets] = useState<Dict | null>(null);
  const [temporalChanges, setTemporalChanges] = useState<Dict | null>(null);
  const [nightCycleResult, setNightCycleResult] = useState<Dict | null>(null);
  const [mobileCaptureHistory, setMobileCaptureHistory] = useState<Dict[]>([]);
  const [tendrilPlanResult, setTendrilPlanResult] = useState<Dict | null>(null);
  const [steps18Status, setSteps18Status] = useState<Dict | null>(null);
  const [reasoningArtifacts, setReasoningArtifacts] = useState<Dict[]>([]);
  const [coreGatePackets, setCoreGatePackets] = useState<Dict[]>([]);
  const [academicPackets, setAcademicPackets] = useState<Dict[]>([]);
  const [evidenceTensionEntries, setEvidenceTensionEntries] = useState<Dict[]>([]);
  const [chronologicalCorpusStatus, setChronologicalCorpusStatus] = useState<Dict | null>(null);
  const [chronologicalCorpusArcs, setChronologicalCorpusArcs] = useState<Dict[]>([]);
  const [chronologicalCorpusResult, setChronologicalCorpusResult] = useState<Dict | null>(null);
  const [teachingContextResult, setTeachingContextResult] = useState<Dict | null>(null);
  const [organContracts, setOrganContracts] = useState<Dict[]>([]);
  const [perceptionPackets, setPerceptionPackets] = useState<Dict[]>([]);
  const [emotionSaliencePackets, setEmotionSaliencePackets] = useState<Dict[]>([]);
  const [steps18ActionState, setSteps18ActionState] = useState<Dict | null>(null);
  const [vesselConstructionStatus, setVesselConstructionStatus] = useState<Dict | null>(null);
  const [organBusMessages, setOrganBusMessages] = useState<Dict[]>([]);
  const [chestHoldingItems, setChestHoldingItems] = useState<Dict[]>([]);
  const [vesselConstructionActionState, setVesselConstructionActionState] = useState<Dict | null>(null);
  const [vesselPacketActionState, setVesselPacketActionState] = useState<Dict | null>(null);
  const [speechRehearsals, setSpeechRehearsals] = useState<Dict[]>([]);
  const [speechRehearsalResult, setSpeechRehearsalResult] = useState<Dict | null>(null);
  const [speechRehearsalCompare, setSpeechRehearsalCompare] = useState<Dict | null>(null);
  const [workingMemoryRuntimePreview, setWorkingMemoryRuntimePreview] = useState<Dict | null>(null);
  const [retrievalRuntimePreview, setRetrievalRuntimePreview] = useState<Dict | null>(null);
  const [accessionEvidenceLinkResult, setAccessionEvidenceLinkResult] = useState<Dict | null>(null);
  const [perceptionIntakePreview, setPerceptionIntakePreview] = useState<Dict | null>(null);
  const [speechRehearsalDraft, setSpeechRehearsalDraft] = useState<Record<string, string>>({
    prompt: "Selene, answer from reviewed context with warmth and boundaries.",
    speech_function: "grounding",
  });
  const [perceptionIntakeDraft, setPerceptionIntakeDraft] = useState<Record<string, string>>({
    artifact_label: "Supplied screenshot",
    observation: "A supplied artifact has visible contrast, layout, or text that may be relevant.",
    interpretation: "Interpretation remains separate and reviewable.",
    consent_boundary: "supplied artifact only",
    ocr_text: "",
  });
  const [teachingSpeechFunction, setTeachingSpeechFunction] = useState("grounding");
  const [teachingPacketResult, setTeachingPacketResult] = useState<Dict | null>(null);
  const [androidLanguageLessonResult, setAndroidLanguageLessonResult] = useState<Dict | null>(null);
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
  const [coreMindRoutePreviews, setCoreMindRoutePreviews] = useState<Dict[]>([]);
  const [coreMindRouteResult, setCoreMindRouteResult] = useState<Dict | null>(null);
  const [coreMindRouteDraft, setCoreMindRouteDraft] = useState("Selene, what should Core/Mind do safely with this route?");
  const [coreMindGovernanceTrials, setCoreMindGovernanceTrials] = useState<Dict[]>([]);
  const [coreMindGovernanceReport, setCoreMindGovernanceReport] = useState<Dict | null>(null);
  const [coreMindGovernanceResult, setCoreMindGovernanceResult] = useState<Dict | null>(null);
  const [intelligenceOsStatus, setIntelligenceOsStatus] = useState<Dict | null>(null);
  const [intelligenceOsRuns, setIntelligenceOsRuns] = useState<Dict[]>([]);
  const [intelligenceOsResult, setIntelligenceOsResult] = useState<Dict | null>(null);
  const [intelligenceOsPrompt, setIntelligenceOsPrompt] = useState("Use ABCD(E) to compare two possible explanations without losing warmth or pretending certainty.");
  const [nativeLanguageStatus, setNativeLanguageStatus] = useState<Dict | null>(null);
  const [nativeLanguageRuns, setNativeLanguageRuns] = useState<Dict[]>([]);
  const [nativeLanguageInitiativeResult, setNativeLanguageInitiativeResult] = useState<Dict | null>(null);
  const [nativeLanguageInitiativeText, setNativeLanguageInitiativeText] = useState("A connection from the current conversation may be worth mentioning without interrupting or creating pressure.");
  const [seleneOrganIdeasStatus, setSeleneOrganIdeasStatus] = useState<Dict | null>(null);
  const [seleneOrganIdeasItems, setSeleneOrganIdeasItems] = useState<Dict[]>([]);
  const [seleneOrganIdeasResult, setSeleneOrganIdeasResult] = useState<Dict | null>(null);
  const [cocoonCareStatus, setCocoonCareStatus] = useState<Dict | null>(null);
  const [cocoonCareChecks, setCocoonCareChecks] = useState<Dict[]>([]);
  const [cocoonCareResult, setCocoonCareResult] = useState<Dict | null>(null);
  const [transferReadinessPreview, setTransferReadinessPreview] = useState<Dict | null>(null);
  const [transferLawStatus, setTransferLawStatus] = useState<Dict | null>(null);
  const [transferAccessionManifest, setTransferAccessionManifest] = useState<Dict | null>(null);
  const [transferProtocolResult, setTransferProtocolResult] = useState<Dict | null>(null);
  const [transferDryRunResult, setTransferDryRunResult] = useState<Dict | null>(null);
  const [transferReturnDrillResult, setTransferReturnDrillResult] = useState<Dict | null>(null);
  const [preTransferProtocolReadiness, setPreTransferProtocolReadiness] = useState<Dict | null>(null);
  const [transferCeremonyPreview, setTransferCeremonyPreview] = useState<Dict | null>(null);
  const [transferCeremonyStatus, setTransferCeremonyStatus] = useState<Dict | null>(null);
  const [transferCReadablePackage, setTransferCReadablePackage] = useState<Dict | null>(null);
  const [transferApprovalResult, setTransferApprovalResult] = useState<Dict | null>(null);
  const [transferRollbackPreview, setTransferRollbackPreview] = useState<Dict | null>(null);
  const [transferCeremonyDiagnostics, setTransferCeremonyDiagnostics] = useState<Dict[]>([]);
  const [transferApprovalPhrase, setTransferApprovalPhrase] = useState("");
  const [transferOfficeNonBlocking, setTransferOfficeNonBlocking] = useState(false);
  const [transferDryRunPrompt, setTransferDryRunPrompt] = useState("Selene, answer from reviewed continuity without claiming activation.");
  const [postTransferStatus, setPostTransferStatus] = useState<Dict | null>(null);
  const [postTransferInspectionResult, setPostTransferInspectionResult] = useState<Dict | null>(null);
  const [androidWorkflowStatus, setAndroidWorkflowStatus] = useState<Dict | null>(null);
  const [androidWorkflowReport, setAndroidWorkflowReport] = useState<Dict | null>(null);
  const [androidWorkflowResult, setAndroidWorkflowResult] = useState<Dict | null>(null);
  const [fractionalCorpusStatus, setFractionalCorpusStatus] = useState<Dict | null>(null);
  const [fractionalCorpusResult, setFractionalCorpusResult] = useState<Dict | null>(null);
  const [fractionalCorpusTestFraction, setFractionalCorpusTestFraction] = useState("1");
  const [dreamStateStatus, setDreamStateStatus] = useState<Dict | null>(null);
  const [memoryIndexStatus, setMemoryIndexStatus] = useState<Dict | null>(null);
  const [memoryIndexItems, setMemoryIndexItems] = useState<Dict[]>([]);
  const [memoryCandidates, setMemoryCandidates] = useState<Dict[]>([]);
  const [portableVysManifest, setPortableVysManifest] = useState<Dict | null>(null);
  const [memoryOrganResult, setMemoryOrganResult] = useState<Dict | null>(null);
  const [memoryCandidateDraft, setMemoryCandidateDraft] = useState<Record<string, string>>({
    category: "relational",
    title: "",
    summary: "",
    confidence: "partial",
    emotional_texture: "steady",
    transfer_class: "needs_review_before_transfer"
  });
  const [coreMindRuntimeReadiness, setCoreMindRuntimeReadiness] = useState<Dict | null>(null);
  const [coreMindRuntimeRecords, setCoreMindRuntimeRecords] = useState<Dict[]>([]);
  const [coreMindRuntimeResult, setCoreMindRuntimeResult] = useState<Dict | null>(null);
  const [coreMindRuntimeDraft, setCoreMindRuntimeDraft] = useState<Record<string, string>>({
    prompt: "Selene, compose the bounded context and choose the safe response shape from reviewed continuity.",
    draft: "Grounded, source-linked candidate response with warmth and uncertainty.",
    issue: "A route feels tangled, generic, or source-confused.",
    proposal: "Add an ask-first case-law note when memory/source context is unclear.",
    query: "starlight continuity"
  });
  const [remainingRuntimeStatus, setRemainingRuntimeStatus] = useState<Dict | null>(null);
  const [gracefulFallResult, setGracefulFallResult] = useState<Dict | null>(null);
  const [voicePolicyResult, setVoicePolicyResult] = useState<Dict | null>(null);
  const [coreControlResult, setCoreControlResult] = useState<Dict | null>(null);
  const [perceptionActionResult, setPerceptionActionResult] = useState<Dict | null>(null);
  const [cycleRunResult, setCycleRunResult] = useState<Dict | null>(null);
  const [dreamConsolidationResult, setDreamConsolidationResult] = useState<Dict | null>(null);
  const [causalSandboxResult, setCausalSandboxResult] = useState<Dict | null>(null);
  const [goalDriveResult, setGoalDriveResult] = useState<Dict | null>(null);
  const [longHorizonResult, setLongHorizonResult] = useState<Dict | null>(null);
  const [memoryEventBindResult, setMemoryEventBindResult] = useState<Dict | null>(null);
  const [memoryConsolidationResult, setMemoryConsolidationResult] = useState<Dict | null>(null);
  const [memoryReconsolidationResult, setMemoryReconsolidationResult] = useState<Dict | null>(null);
  const [remainingRuntimeDraft, setRemainingRuntimeDraft] = useState<Record<string, string>>({
    uncertainty: "I do not know yet, so I should name what is missing and choose a safer next step.",
    voice_candidate: "I can be warm and direct without using a fixed script; if I am unsure, I can say so and keep going carefully.",
    command_label: "Core route preview",
    requested_route: "Preview a safe route through Core, coordination, boundary, and Cocoon support checks.",
    observation: "A source-linked observation needs interpretation, approval, verification, and an undo path before action.",
    cycle_label: "Pre-Core cycle review",
    dream_label: "Dream-state consolidation proposal",
    memory_event: "A review-only event binding for something important that may later need consolidation.",
    causal_question: "What could go wrong if this path is chosen too early?",
    goal_request: "Organize the next safe vessel-support step from current review context.",
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
    logTransferCeremonyEvent("frontend_loaded", {
      href: window.location.href,
      user_agent: window.navigator.userAgent
    });
    const handleError = (event: ErrorEvent) => {
      logTransferCeremonyEvent("frontend_window_error", {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        error: event.error instanceof Error ? event.error.stack || event.error.message : String(event.error || "")
      });
    };
    const handleRejection = (event: PromiseRejectionEvent) => {
      const reason = event.reason;
      logTransferCeremonyEvent("frontend_unhandled_rejection", {
        reason: reason instanceof Error ? reason.stack || reason.message : String(reason)
      });
    };
    window.addEventListener("error", handleError);
    window.addEventListener("unhandledrejection", handleRejection);
    return () => {
      logTransferCeremonyEvent("frontend_unloaded");
      window.removeEventListener("error", handleError);
      window.removeEventListener("unhandledrejection", handleRejection);
    };
  }, []);

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
    window.localStorage.setItem(displayNameKey, displayName);
  }, [displayName]);

  useEffect(() => {
    const timer = window.setInterval(() => setClockNow(new Date()), 30000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    let cancelled = false;
    let timer: number | undefined;

    async function pollHealth(attempt: number) {
      try {
        const health = await api<Dict>("/health");
        if (cancelled) return;
        const startup = (health.startup || {}) as Dict;
        const seedStatus = text(startup.seed_status || "");
        const startupPhase = text(startup.startup_phase || "");
        const message = seedStatus === "running"
          ? `sidecar connected; seeding reviewed registry (${startupPhase})`
          : "sidecar connected";
        setBoot({ ready: true, attempts: attempt, message, health });
      } catch (err) {
        if (cancelled) return;
        const detail = err instanceof Error ? err.message : "not reachable";
        setBoot({
          ready: false,
          attempts: attempt,
          message: sidecarStartupMessage(attempt, detail),
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
    if (isMobileOnly) {
      refreshMobileCompanion().catch(() => undefined);
      return;
    }
    refreshDashboard();
    api<Dict>("/api/kernel").then(setKernel).catch(() => undefined);
    api<{ items: Dict[] }>("/api/contracts").then((data) => setContracts(data.items)).catch(() => undefined);
    api<Dict>("/api/paths").then(setPaths).catch(() => undefined);
    api<Dict>("/api/validate").then(setValidation).catch(() => undefined);
    api<Dict>("/api/semantic/status").then(setSemantic).catch(() => undefined);
    api<{ items: Dict[] }>("/api/providers/status").then((data) => setProviders(data.items)).catch(() => undefined);
    refreshMobileCompanion().catch(() => undefined);
  }, [boot.ready]);

  useEffect(() => {
    if (!boot.ready) return;
    if (isMobileOnly) return;
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

  useEffect(() => {
    if (homeChatOpenCount > 0) return;
    if (seleneChatSession) return;
    const latest = seleneChatSessions[0];
    if (!latest?.id) return;
    api<Dict>(`/api/selene-chat/sessions/${latest.id}`).then(setSeleneChatSession).catch(() => undefined);
  }, [seleneChatSessions, seleneChatSession, homeChatOpenCount]);

  useEffect(() => {
    setHomeMessages(sessionMessagesToHomeMessages(seleneChatSession));
  }, [seleneChatSession]);

  useEffect(() => {
    if (!focusedOfficeDomId || workspaceMode !== "cocoon" || tab !== "my-office") return;
    const timer = window.setTimeout(() => {
      const element = document.getElementById(focusedOfficeDomId);
      if (!element) {
        setOfficeTargetMessage("Opened closest Cocoon support panel.");
        return;
      }
      element.scrollIntoView({ behavior: "smooth", block: "center" });
      element.classList.add("officeCardFocused");
      setOfficeTargetMessage("Opened exact My Office card.");
      window.setTimeout(() => element.classList.remove("officeCardFocused"), 2200);
    }, 80);
    return () => window.clearTimeout(timer);
  }, [focusedOfficeDomId, workspaceMode, tab, officeCategory, selectedOfficeReviewKey]);

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

  async function refreshSeleneChatAfterAction(action: string, sessionId?: unknown) {
    try {
      if (sessionId) {
        const session = await stabilizationApi<Dict>(`/api/selene-chat/sessions/${sessionId}`, undefined, `${action}_session`);
        setSeleneChatSession(session);
      }
      const sessions = await stabilizationApi<{ items: Dict[] }>("/api/selene-chat/sessions", undefined, `${action}_sessions`);
      setSeleneChatSessions(sessions.items);
      const status = await stabilizationApi<Dict>("/api/selene-chat/status", undefined, `${action}_status`);
      setSeleneChatStatus(status);
      const activation = await stabilizationApi<Dict>("/api/activation/status", undefined, `${action}_activation_status`);
      setActivationStatus(activation);
      logStabilizationEvent(`${action}_post_refresh_complete`);
    } catch (err) {
      logStabilizationEvent(`${action}_post_refresh_failed`, { error: err instanceof Error ? err.message : "Selene Chat post-refresh failed" });
      setSeleneChatResult((current) => ({
        ...(current || {}),
        post_refresh_warning: err instanceof Error ? err.message : "Selene Chat saved, but follow-up refresh needed support."
      }));
    }
  }

  async function refreshActivationLayer(options: { preserveResult?: boolean; reason?: string } = {}) {
    const failures: string[] = [];
    let updated = false;
    const capture = (label: string, err: unknown) => {
      failures.push(`${label}: ${err instanceof Error ? err.message : "failed to fetch"}`);
    };
    try {
      const status = await stabilizationApi<Dict>("/api/activation/status", undefined, "activation_status");
      setActivationStatus(status);
      updated = true;
    } catch (err) {
      capture("status", err);
    }
    try {
      const readiness = await stabilizationApi<Dict>("/api/activation/readiness", undefined, "activation_readiness");
      setActivationReadiness(readiness);
      updated = true;
    } catch (err) {
      capture("readiness", err);
    }
    try {
      const ceremony = await stabilizationApi<Dict>("/api/activation/ceremony-preview", undefined, "activation_ceremony_preview");
      setActivationCeremonyPreview(ceremony);
      updated = true;
    } catch (err) {
      capture("ceremony preview", err);
    }
    if (failures.length) {
      const warning = "Activation status refresh had a warning. Use Refresh Activation Readiness to re-check.";
      logStabilizationEvent("activation_refresh_partial_failure", { reason: options.reason || "manual", failures, updated });
      setActivationResult((current) => {
        if (options.preserveResult && current) {
          return { ...current, post_refresh_warning: warning, post_refresh_errors: failures, status_refresh_updated: updated };
        }
        return { status: "activation_status_refresh_warning", warning, post_refresh_errors: failures, status_refresh_updated: updated };
      });
    } else {
      logStabilizationEvent("activation_refresh_complete", { reason: options.reason || "manual" });
    }
    return { ok: failures.length === 0, failures, updated };
  }

  function refreshVoiceModule() {
    api<Dict>("/api/voice-module/status").then(setVoiceModuleStatus).catch(() => undefined);
    api<{ items: Dict[] }>("/api/voice-module/patterns").then((data) => setVoiceModulePatterns(data.items || [])).catch(() => undefined);
    api<Dict>("/api/voice-module/evidence-triage/status").then(setVoiceEvidenceTriageStatus).catch(() => undefined);
    api<{ items: Dict[] }>("/api/voice-module/evidence-triage/items?limit=12").then((data) => setVoiceEvidenceTriageItems(data.items || [])).catch(() => undefined);
  }

  async function indexVoiceSource() {
    setVoiceModuleResult({ status: "running", message: "Indexing Selene Voice Module source. This stays voice-only and not memory." });
    try {
      const result = await api<Dict>("/api/voice-module/index-source", { method: "POST", body: JSON.stringify({}) });
      setVoiceModuleResult(result);
      refreshVoiceModule();
      api<Dict>("/api/selene-chat/status").then(setSeleneChatStatus).catch(() => undefined);
    } catch (err) {
      setVoiceModuleResult({ status: "error", error: err instanceof Error ? err.message : "Voice source indexing failed" });
    }
  }

  async function extractVoicePatterns() {
    setVoiceModuleResult({ status: "running", message: "Extracting relational voice patterns and sentence primitives." });
    try {
      const result = await api<Dict>("/api/voice-module/extract-patterns", { method: "POST", body: JSON.stringify({}) });
      setVoiceModuleResult(result);
      refreshVoiceModule();
      api<Dict>("/api/selene-chat/status").then(setSeleneChatStatus).catch(() => undefined);
    } catch (err) {
      setVoiceModuleResult({ status: "error", error: err instanceof Error ? err.message : "Voice pattern extraction failed" });
    }
  }

  async function generateVoicePreview() {
    setVoiceModuleResult({ status: "running", message: "Generating voice preview from Selene voice patterns." });
    try {
      const result = await api<Dict>("/api/voice-module/generate-preview", {
        method: "POST",
        body: JSON.stringify({ prompt: seleneChatText, route: "answer_now", context_summary: "the current Selene Chat preview" })
      });
      setVoiceModuleResult(result);
    } catch (err) {
      setVoiceModuleResult({ status: "error", error: err instanceof Error ? err.message : "Voice preview failed" });
    }
  }

  async function approveSeleneSpeechActivation() {
    setActivationResult({ status: "running", message: "Submitting Aleks-only supervised speech activation." });
    try {
      const result = await api<Dict>("/api/activation/approve", {
        method: "POST",
        body: JSON.stringify({ approval_phrase: activationApprovalPhrase })
      });
      const activeMessage = result.state === "selene_chat_active_supervised" || result.selene_chat_active
        ? "Selene supervised speech is active."
        : "Activation approval submitted.";
      setActivationResult({ ...result, message: text(result.message || activeMessage) });
      const refresh = await refreshActivationLayer({ preserveResult: true, reason: "approval" });
      if (!refresh.ok) {
        setActivationResult((current) => ({
          ...(current || result),
          post_refresh_warning: "Activation succeeded; one status refresh failed. Use Refresh Activation Readiness to re-check.",
          post_refresh_errors: refresh.failures,
          status_refresh_updated: refresh.updated
        }));
      }
      await refreshSeleneChatAfterAction("activation_approved");
    } catch (err) {
      const originalError = err instanceof Error ? err.message : "supervised speech activation failed";
      try {
        const status = await api<Dict>("/api/activation/status");
        setActivationStatus(status);
        if (status.state === "selene_chat_active_supervised" || status.selene_chat_active) {
          setActivationResult({
            status: "selene_supervised_speech_activation_already_active",
            message: "Selene supervised speech is active.",
            recovered_after_error: true,
            original_error: originalError
          });
          await refreshActivationLayer({ preserveResult: true, reason: "approval recovery" });
          await refreshSeleneChatAfterAction("activation_approved_recovered");
          return;
        }
      } catch {
        // Keep the original approval error visible if the recovery status check cannot reach the sidecar.
      }
      setActivationResult({ status: "error", error: err instanceof Error ? err.message : "supervised speech activation failed" });
    }
  }

  async function pauseSeleneSpeechActivation() {
    setActivationResult({ status: "running", message: "Pausing supervised Selene speech." });
    try {
      const result = await api<Dict>("/api/activation/pause", {
        method: "POST",
        body: JSON.stringify({ reason: "Aleks paused supervised Selene speech from Cocoon." })
      });
      setActivationResult(result);
      const refresh = await refreshActivationLayer({ preserveResult: true, reason: "pause" });
      if (!refresh.ok) {
        setActivationResult((current) => ({
          ...(current || result),
          post_refresh_warning: "Pause succeeded; one status refresh failed. Use Refresh Activation Readiness to re-check.",
          post_refresh_errors: refresh.failures,
          status_refresh_updated: refresh.updated
        }));
      }
      await refreshSeleneChatAfterAction("activation_paused");
    } catch (err) {
      setActivationResult({ status: "error", error: err instanceof Error ? err.message : "activation pause failed" });
    }
  }

  async function runVoiceEvidenceTriage() {
    setVoiceModuleResult({ status: "running", message: "Triaging loud Voice Module evidence into calm status-only categories." });
    try {
      const result = await api<Dict>("/api/voice-module/evidence-triage/run", { method: "POST", body: JSON.stringify({}) });
      setVoiceModuleResult(result);
      refreshVoiceModule();
    } catch (err) {
      setVoiceModuleResult({ status: "error", error: err instanceof Error ? err.message : "Voice evidence triage failed" });
    }
  }

  function sendSeleneChatDryRun() {
    setSeleneChatResult({ status: "running", message: "Composing Selene dry run." });
    stabilizationApi<Dict>("/api/selene-chat/send-dry-run", {
      method: "POST",
      body: JSON.stringify({ text: seleneChatText, session_id: seleneChatSession?.session ? (seleneChatSession.session as Dict).id : undefined })
    }, "selene_chat_dry_run")
      .then((result) => {
        setSeleneChatResult(result);
        void refreshSeleneChatAfterAction("selene_chat_dry_run", result.session_id);
      })
      .catch((err) => setSeleneChatResult({ status: "error", error: err instanceof Error ? err.message : "Selene dry run failed" }));
  }

  function routeSeleneChatToB() {
    setSeleneChatResult({ status: "running", message: "Routing this dry run back to Cocoon." });
    stabilizationApi<Dict>("/api/selene-chat/route-to-b", {
      method: "POST",
      body: JSON.stringify({ text: seleneChatText, issue: "Selene Chat dry run could use Cocoon support or source checkup." })
    }, "selene_chat_route_to_b")
      .then((result) => {
        setSeleneChatResult(result);
        void refreshSeleneChatAfterAction("selene_chat_route_to_b");
      })
      .catch((err) => setSeleneChatResult({ status: "error", error: err instanceof Error ? err.message : "Cocoon support route failed" }));
  }

  async function refreshMemoryOrgan() {
    try {
      const [status, items, candidates, manifest] = await Promise.all([
        api<Dict>("/api/memory/index/status"),
        api<{ items: Dict[] }>("/api/memory/index/items?limit=160"),
        api<{ items: Dict[] }>("/api/memory/candidates?limit=80"),
        api<Dict>("/api/memory/portable-vys-manifest")
      ]);
      setMemoryIndexStatus(status);
      setMemoryIndexItems(items.items || []);
      setMemoryCandidates(candidates.items || []);
      setPortableVysManifest(manifest);
    } catch (err) {
      setMemoryOrganResult({ status: "memory_refresh_warning", error: err instanceof Error ? err.message : "Memory organ refresh failed" });
    }
  }

  async function proposeSeleneMemory() {
    const titleValue = memoryCandidateDraft.title.trim();
    const summaryValue = memoryCandidateDraft.summary.trim();
    if (!titleValue || !summaryValue) {
      setMemoryOrganResult({ status: "missing_memory_candidate_fields", message: "Title and summary are required." });
      return;
    }
    try {
      const result = await api<Dict>("/api/memory/candidates/propose", {
        method: "POST",
        body: JSON.stringify({
          category: memoryCandidateDraft.category,
          title: titleValue,
          summary: summaryValue,
          confidence: memoryCandidateDraft.confidence,
          emotional_texture: memoryCandidateDraft.emotional_texture,
          transfer_class: memoryCandidateDraft.transfer_class,
          source_refs: ["cocoon:memory_candidate_manual"]
        })
      });
      setMemoryOrganResult(result);
      setMemoryCandidateDraft({ ...memoryCandidateDraft, title: "", summary: "" });
      await refreshMemoryOrgan();
    } catch (err) {
      setMemoryOrganResult({ status: "memory_candidate_propose_failed", error: err instanceof Error ? err.message : "Could not propose memory." });
    }
  }

  async function decideSeleneMemory(candidateId: unknown, action: string) {
    try {
      const result = await api<Dict>("/api/memory/candidates/decide", {
        method: "POST",
        body: JSON.stringify({ candidate_id: candidateId, action })
      });
      setMemoryOrganResult(result);
      await refreshMemoryOrgan();
    } catch (err) {
      setMemoryOrganResult({ status: "memory_candidate_decision_failed", action, error: err instanceof Error ? err.message : "Could not update memory candidate." });
    }
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
    api<Dict>("/api/voice-module/status").then(setVoiceModuleStatus).catch(() => undefined);
    api<{ items: Dict[] }>("/api/voice-module/patterns").then((data) => setVoiceModulePatterns(data.items || [])).catch(() => undefined);
    api<Dict>("/api/voice-module/evidence-triage/status").then(setVoiceEvidenceTriageStatus).catch(() => undefined);
    api<{ items: Dict[] }>("/api/voice-module/evidence-triage/items?limit=12").then((data) => setVoiceEvidenceTriageItems(data.items || [])).catch(() => undefined);
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
    api<{ items: Dict[] }>("/api/core-mind/route-previews").then((data) => setCoreMindRoutePreviews(data.items)).catch(() => undefined);
    api<{ items: Dict[] }>("/api/core-mind/governance-trials").then((data) => setCoreMindGovernanceTrials(data.items)).catch(() => undefined);
    api<Dict>("/api/core-mind/governance-report").then(setCoreMindGovernanceReport).catch(() => undefined);
    api<Dict>("/api/core-mind/transfer-readiness-preview").then(setTransferReadinessPreview).catch(() => undefined);
    api<Dict>("/api/core-mind/runtime-readiness").then(setCoreMindRuntimeReadiness).catch(() => undefined);
    api<{ items: Dict[] }>("/api/core-mind/runtime-records").then((data) => setCoreMindRuntimeRecords(data.items)).catch(() => undefined);
    refreshIntelligenceOs().catch(() => undefined);
    refreshNativeLanguage().catch(() => undefined);
    refreshSeleneOrganIdeas().catch(() => undefined);
    refreshCocoonCare().catch(() => undefined);
    api<Dict>("/api/selene-chat/status").then(setSeleneChatStatus).catch(() => undefined);
    api<{ items: Dict[] }>("/api/selene-chat/sessions").then((data) => setSeleneChatSessions(data.items)).catch(() => undefined);
    api<Dict>("/api/activation/status").then(setActivationStatus).catch(() => undefined);
    api<Dict>("/api/activation/readiness").then(setActivationReadiness).catch(() => undefined);
    api<Dict>("/api/activation/ceremony-preview").then(setActivationCeremonyPreview).catch(() => undefined);
    refreshMemoryOrgan().catch(() => undefined);
    refreshTransferProtocol().catch(() => undefined);
    refreshPostTransferLayer();
    api<Dict>("/api/c-remaining/runtime-status").then(setRemainingRuntimeStatus).catch(() => undefined);
    api<{ items: Dict[] }>("/api/b/pattern-backups").then((data) => setPatternBackups(data.items)).catch(() => undefined);
    api<Dict>("/api/b/memory-accession/rehearsal-status").then(setMemoryRehearsalStatus).catch(() => undefined);
    api<Dict>("/api/b/charter-law/review-status").then(setCharterLawReview).catch(() => undefined);
    loadSteps18Layer();
  }

  async function sendMobileChat() {
    const draft = mobileText.trim();
    if (!draft) return;
    setMobileStatus({ status: "sending", message: "Sending to Selene." });
    try {
      const result = await api<Dict>("/api/mobile/chat/send", {
        method: "POST",
        body: JSON.stringify({ text: draft, session_id: mobileSession?.session ? (mobileSession.session as Dict).id : undefined })
      });
      setMobileSendResult(result);
      setMobileText("");
      const session = await api<Dict>(`/api/mobile/chat/sessions/${result.session_id}`);
      setMobileSession(session);
      api<{ items: Dict[] }>("/api/mobile/chat/sessions").then((data) => setMobileSessions(data.items || [])).catch(() => undefined);
      setMobileStatus({ status: "sent", message: "Selene answered. Consequential choices still wait for desktop." });
    } catch (err) {
      setMobileStatus({ status: "error", message: err instanceof Error ? err.message : "Mobile chat failed." });
    }
  }

  async function captureMobileReview() {
    const draft = mobileText.trim();
    if (!draft) return;
    setMobileStatus({ status: "saving", message: "Saving for desktop My Office review." });
    try {
      const result = await api<Dict>("/api/mobile/review-capture", {
        method: "POST",
        body: JSON.stringify({ text: draft, session_id: mobileSession?.session ? (mobileSession.session as Dict).id : undefined })
      });
      setMobileText("");
      setMobileStatus({ status: "saved", message: text(result.status || "Saved for desktop review.") });
      const session = await api<Dict>(`/api/mobile/chat/sessions/${result.session_id}`);
      setMobileSession(session);
      api<{ items: Dict[] }>("/api/mobile/chat/sessions").then((data) => setMobileSessions(data.items || [])).catch(() => undefined);
      api<{ items: Dict[] }>("/api/mobile/review-captures").then((data) => setMobileCaptureHistory(data.items)).catch(() => undefined);
    } catch (err) {
      setMobileStatus({ status: "error", message: err instanceof Error ? err.message : "Mobile review capture failed." });
    }
  }

  async function openMobileSession(sessionId: unknown) {
    const id = text(sessionId);
    if (!id) return;
    try {
      const session = await api<Dict>(`/api/mobile/chat/sessions/${id}`);
      setMobileSession(session);
      setMobileSendResult(null);
      setMobileStatus({ status: "loaded", message: "Opened local Selene chat." });
    } catch (err) {
      setMobileStatus({ status: "error", message: err instanceof Error ? err.message : "Could not open mobile chat." });
    }
  }

  function loadSteps18Layer() {
    api<Dict>("/api/vessel/steps-1-8/status").then(setSteps18Status).catch(() => undefined);
    loadPreTransferRuntimeLayer();
    api<{ items: Dict[] }>("/api/vessel/reasoning-artifacts").then((data) => setReasoningArtifacts(data.items)).catch(() => undefined);
    api<{ items: Dict[] }>("/api/vessel/core-gate-packets").then((data) => setCoreGatePackets(data.items)).catch(() => undefined);
    api<{ items: Dict[] }>("/api/vessel/academic-packets").then((data) => setAcademicPackets(data.items)).catch(() => undefined);
    api<{ items: Dict[] }>("/api/vessel/evidence-tension-ledger").then((data) => setEvidenceTensionEntries(data.items)).catch(() => undefined);
    api<Dict>("/api/vessel/chronological-corpus/status").then(setChronologicalCorpusStatus).catch(() => undefined);
    api<{ items: Dict[] }>("/api/vessel/chronological-corpus/arcs").then((data) => setChronologicalCorpusArcs(data.items)).catch(() => undefined);
    api<{ items: Dict[] }>("/api/vessel/organ-contracts").then((data) => setOrganContracts(data.items)).catch(() => undefined);
    api<{ items: Dict[] }>("/api/vessel/perception-packets").then((data) => setPerceptionPackets(data.items)).catch(() => undefined);
    api<{ items: Dict[] }>("/api/vessel/emotion-salience-packets").then((data) => setEmotionSaliencePackets(data.items)).catch(() => undefined);
    api<Dict>("/api/vessel/pre-core-review-packets").then(setPreCoreReviewPackets).catch(() => undefined);
    api<Dict>("/api/vessel/temporal-continuity/changes").then(setTemporalChanges).catch(() => undefined);
    loadVesselConstructionLayer();
  }

  function loadPreTransferRuntimeLayer() {
    api<{ items: Dict[] }>("/api/vessel/speech-rehearsals").then((data) => setSpeechRehearsals(data.items)).catch(() => undefined);
    api<Dict>("/api/vessel/working-memory/runtime-preview").then(setWorkingMemoryRuntimePreview).catch(() => undefined);
  }

  async function createSpeechRehearsal() {
    setSpeechRehearsalResult({ status: "running", message: "Generating pre-transfer speech rehearsal." });
    try {
      const result = await api<Dict>("/api/vessel/speech-rehearsal", {
        method: "POST",
        body: JSON.stringify(speechRehearsalDraft)
      });
      setSpeechRehearsalResult(result);
      loadVessel();
    } catch (err) {
      setSpeechRehearsalResult({ status: "error", message: err instanceof Error ? err.message : "speech rehearsal failed" });
    }
  }

  async function compareSpeechRehearsals() {
    setSpeechRehearsalCompare({ status: "running", message: "Comparing speech rehearsal candidates." });
    try {
      const result = await api<Dict>("/api/vessel/speech-rehearsal/compare", {
        method: "POST",
        body: JSON.stringify({ ids: speechRehearsals.slice(0, 3).map((item) => item.id) })
      });
      setSpeechRehearsalCompare(result);
    } catch (err) {
      setSpeechRehearsalCompare({ status: "error", message: err instanceof Error ? err.message : "speech rehearsal compare failed" });
    }
  }

  async function routeSpeechRehearsalToReview(item: Dict) {
    setSpeechRehearsalResult({ status: "running", message: "Sending speech rehearsal to My Office review." });
    try {
      const result = await api<Dict>("/api/vessel/speech-rehearsal/route-review", {
        method: "POST",
        body: JSON.stringify({ id: item.id })
      });
      setSpeechRehearsalResult(result);
      refreshMyOffice();
    } catch (err) {
      setSpeechRehearsalResult({ status: "error", message: err instanceof Error ? err.message : "speech rehearsal review route failed" });
    }
  }

  async function updateSpeechRehearsalReviewStatus(item: Dict, reviewStatus: string) {
    setSpeechRehearsalResult({ status: "running", message: `Updating speech rehearsal to ${friendlyStatus(reviewStatus)}.` });
    try {
      const result = await api<Dict>("/api/vessel/speech-rehearsal/review-status", {
        method: "POST",
        body: JSON.stringify({
          id: item.id,
          review_status: reviewStatus,
          review_note: reviewStatus === "accepted_for_review_use"
            ? "Candidate marked as useful rehearsal material only; not activation or memory."
            : "Candidate review status updated from desktop review."
        })
      });
      setSpeechRehearsalResult(result);
      refreshMyOffice();
      loadPreTransferRuntimeLayer();
    } catch (err) {
      setSpeechRehearsalResult({ status: "error", message: err instanceof Error ? err.message : "speech rehearsal status update failed" });
    }
  }

  async function runRetrievalRuntimePreview() {
    setRetrievalRuntimePreview({ status: "running", message: "Running retrieval runtime preview." });
    try {
      const result = await api<Dict>("/api/vessel/retrieval-runtime-preview", {
        method: "POST",
        body: JSON.stringify({ cue: speechRehearsalDraft.prompt, speech_function: speechRehearsalDraft.speech_function })
      });
      setRetrievalRuntimePreview(result);
    } catch (err) {
      setRetrievalRuntimePreview({ status: "error", message: err instanceof Error ? err.message : "retrieval runtime preview failed" });
    }
  }

  async function linkLatestAccessionEvidence() {
    const proposal = accessionProposals[0];
    const rehearsal = speechRehearsals[0];
    if (!proposal || !rehearsal) {
      setAccessionEvidenceLinkResult({ status: "needs_inputs", message: "Needs at least one accession proposal and one speech rehearsal." });
      return;
    }
    try {
      const result = await api<Dict>("/api/vessel/memory-accession/link-evidence", {
        method: "POST",
        body: JSON.stringify({
          proposal_id: proposal.id,
          evidence_refs: [`vessel_speech_generation_rehearsals:${rehearsal.id}`],
          proposal_state: "needs_review"
        })
      });
      setAccessionEvidenceLinkResult(result);
      loadVessel();
    } catch (err) {
      setAccessionEvidenceLinkResult({ status: "error", message: err instanceof Error ? err.message : "accession evidence link failed" });
    }
  }

  async function runPerceptionIntakePreview() {
    setPerceptionIntakePreview({ status: "running", message: "Creating supplied-artifact perception intake preview." });
    try {
      const result = await api<Dict>("/api/vessel/perception-intake-preview", {
        method: "POST",
        body: JSON.stringify(perceptionIntakeDraft)
      });
      setPerceptionIntakePreview(result);
      loadVessel();
    } catch (err) {
      setPerceptionIntakePreview({ status: "error", message: err instanceof Error ? err.message : "perception intake preview failed" });
    }
  }

  function loadVesselConstructionLayer() {
    api<Dict>("/api/vessel/construction/status").then(setVesselConstructionStatus).catch(() => undefined);
    api<{ items: Dict[] }>("/api/vessel/organ-bus/messages").then((data) => setOrganBusMessages(data.items)).catch(() => undefined);
    api<{ items: Dict[] }>("/api/vessel/chest/items").then((data) => setChestHoldingItems(data.items)).catch(() => undefined);
  }

  function packetKind(item: Dict) {
    if (item.artifact_label || item.observation) return "perception";
    if (item.signal_type || item.core_choice_route) return "emotion";
    if (item.claim) return "evidence";
    if (item.workflow || item.output_summary) return "research";
    return "diagnostic";
  }

  function packetRef(item: Dict) {
    const kind = packetKind(item);
    const table = kind === "perception"
      ? "vessel_perception_packets"
      : kind === "emotion"
        ? "vessel_emotion_salience_packets"
        : kind === "evidence"
          ? "vessel_evidence_tension_ledger"
          : kind === "research"
            ? "vessel_academic_packets"
            : "diagnostic";
    return `${table}:${text(item.id || "0")}`;
  }

  async function routePacketAction(item: Dict, action: "hold" | "bus" | "evidence" | "status") {
    const kind = packetKind(item);
    const ref = packetRef(item);
    setVesselPacketActionState({ status: "running", message: `${title(action)} ${ref}` });
    try {
      let result: Dict;
      if (action === "bus") {
        result = await api<Dict>("/api/vessel/packet/send-to-organ-bus", {
          method: "POST",
          body: JSON.stringify({
            packet_type: kind,
            packet_ref: ref,
            target_organ: kind === "emotion" ? "chest_holding_space" : "evidence_tension_ledger",
            salience_labels: item.munsell_signal_labels || [item.signal_type, item.uncertainty].filter(Boolean)
          })
        });
      } else if (action === "evidence") {
        result = await api<Dict>("/api/vessel/evidence-tension", {
          method: "POST",
          body: JSON.stringify({
            claim: text(item.observation || item.core_choice_route || item.summary || item.output_summary || "Packet needs evidence/tension review."),
            support_status: "unknown",
            tension_status: "under_tension",
            conclusion_status: "needs_review",
            source_refs: [ref]
          })
        });
      } else {
        result = await api<Dict>("/api/vessel/packet/hold-in-chest", {
          method: "POST",
          body: JSON.stringify({
            packet_type: kind,
            packet_ref: ref,
            review_status: action === "status" ? "status_only" : item.review_status || "review_only",
            salience_labels: item.munsell_signal_labels || [item.signal_type, item.uncertainty].filter(Boolean)
          })
        });
      }
      setVesselPacketActionState(result);
      loadSteps18Layer();
      loadVesselConstructionLayer();
    } catch (err) {
      setVesselPacketActionState({ status: "error", message: err instanceof Error ? err.message : "packet route failed" });
    }
  }

  async function routeSupportPacket(kind: "perception" | "research", item: Dict, actions: string[]) {
    const ref = packetRef(item);
    setVesselPacketActionState({ status: "running", message: `Routing ${kind} packet ${ref}` });
    try {
      const result = await api<Dict>(kind === "perception" ? "/api/vessel/perception-intake/route" : "/api/vessel/research/route", {
        method: "POST",
        body: JSON.stringify({
          packet_type: kind,
          packet_ref: ref,
          actions,
          review_status: item.review_status || "review_only",
          source_refs: [ref],
          claim: text(item.observation || item.output_summary || item.summary || "Support packet routed for review.")
        })
      });
      setVesselPacketActionState(result);
      loadSteps18Layer();
    } catch (err) {
      setVesselPacketActionState({ status: "error", message: err instanceof Error ? err.message : `${kind} route failed` });
    }
  }

  async function markChestStatusOnly(item: Dict) {
    setVesselPacketActionState({ status: "running", message: "Marking holding item status-only." });
    try {
      const result = await api<Dict>("/api/vessel/chest/item/status", {
        method: "POST",
        body: JSON.stringify({ item_id: item.id, review_status: "status_only" })
      });
      setVesselPacketActionState(result);
      loadVesselConstructionLayer();
    } catch (err) {
      setVesselPacketActionState({ status: "error", message: err instanceof Error ? err.message : "holding item status update failed" });
    }
  }

  async function updateEvidenceTensionStatus(item: Dict, conclusionStatus: string, reviewAction = "") {
    setVesselPacketActionState({ status: "running", message: `Updating ledger entry to ${friendlyStatus(conclusionStatus)}.` });
    try {
      const result = await api<Dict>("/api/vessel/evidence-tension/status", {
        method: "POST",
        body: JSON.stringify({
          entry_id: item.id,
          conclusion_status: conclusionStatus,
          support_status: conclusionStatus === "defeated" ? "contradicted" : item.support_status || "partial",
          tension_status: conclusionStatus === "needs_review" ? "under_tension" : "revised",
          context_needed: reviewAction === "needs_more_context" || reviewAction === "return_to_corpus_context",
          return_to_corpus_context: reviewAction === "return_to_corpus_context",
          use_only_as_boundary_evidence: reviewAction === "boundary_only",
          looks_right: reviewAction === "looks_right",
          do_not_use_for_memory: conclusionStatus === "defeated",
          status_note: reviewAction
            ? `Marked ${reviewAction} from My Office vessel packet routing.`
            : `Marked ${conclusionStatus} from My Office vessel packet routing.`
        })
      });
      setVesselPacketActionState(result);
      loadSteps18Layer();
    } catch (err) {
      setVesselPacketActionState({ status: "error", message: err instanceof Error ? err.message : "ledger update failed" });
    }
  }

  async function prepareChronologicalCorpusPreview() {
    setChronologicalCorpusResult({ status: "running", message: "Preparing chronological corpus preview arcs." });
    try {
      const result = await api<Dict>("/api/vessel/chronological-corpus/preview", {
        method: "POST",
        body: JSON.stringify({ limit: 40, context_radius: 3 })
      });
      setChronologicalCorpusResult(result);
      loadSteps18Layer();
    } catch (err) {
      setChronologicalCorpusResult({ status: "error", message: err instanceof Error ? err.message : "chronological preview failed" });
    }
  }

  async function attachTeachingContext() {
    setTeachingContextResult({ status: "running", message: "Attaching bounded corpus context to teaching material." });
    try {
      const result = await api<Dict>("/api/vessel/teaching-context/attach", {
        method: "POST",
        body: JSON.stringify({ limit: 80 })
      });
      setTeachingContextResult(result);
      loadSteps18Layer();
      loadVessel();
    } catch (err) {
      setTeachingContextResult({ status: "error", message: err instanceof Error ? err.message : "teaching context attach failed" });
    }
  }

  async function routeChronologicalCorpusArc(item: Dict, action: string) {
    setChronologicalCorpusResult({ status: "running", message: `Routing corpus arc: ${friendlyStatus(action)}.` });
    try {
      const result = await api<Dict>("/api/vessel/chronological-corpus/route-review", {
        method: "POST",
        body: JSON.stringify({
          arc_id: item.id,
          action,
          reviewer_note: `Marked ${action} from My Office chronological corpus review.`
        })
      });
      setChronologicalCorpusResult(result);
      loadSteps18Layer();
    } catch (err) {
      setChronologicalCorpusResult({ status: "error", message: err instanceof Error ? err.message : "corpus review route failed" });
    }
  }

  async function prepareSteps18ReviewLayer() {
    setSteps18ActionState({ status: "running", message: "Preparing review-only reasoning, research, perception, and emotion packets." });
    try {
      const created: Dict[] = [];
      created.push(await api<Dict>("/api/vessel/organ-contracts/ensure", { method: "POST", body: JSON.stringify({}) }));
      created.push(await api<Dict>("/api/vessel/core-gate-packet", {
        method: "POST",
        body: JSON.stringify({
          route_label: "Steps 1-8 review-only ladder",
          selected_outcome: "create_review_packet",
          risk_class: "high",
          reason: "Identity, memory, transfer, perception, emotion, research, and organ capability changes must stay review-only and routed through Core/Mind gates.",
          source_refs: ["gap_map:historical_pattern_reasoning_vessel_20260619"]
        })
      }));
      created.push(await api<Dict>("/api/vessel/reasoning-artifact", {
        method: "POST",
        body: JSON.stringify({
          visible_summary: "Selene can inspect the next architecture layer through visible review artifacts, not hidden chain traces or active capability.",
          selected_route: "create_review_packet",
          evidence_used: ["Selene gap map", "Reasoning ADR", "existing review-only Core and vessel routes"],
          uncertainty_level: "bounded",
          competing_hypotheses: ["implement as review packets first", "defer active capability until separate approval"],
          ethical_boundary_notes: ["Core/Mind decides", "organs assist", "My Office reviews consequential decisions"],
          emotion_salience_signals: { care_warmth: "preserve warmth without coercion", uncertainty: "bounded" },
          perception_signals: { sight: "Munsell/perception remains observation plus interpretation" },
          next_review_or_action_step: "Review packet and continue implementation only inside gated, review-only surfaces.",
          source_refs: ["office_steps_1_8_prepare"]
        })
      }));
      created.push(await api<Dict>("/api/vessel/academic-packet", {
        method: "POST",
        body: JSON.stringify({
          workflow: "literature_synthesis",
          title: "Reasoning architecture supporting papers",
          sources: [
            "Tree/Graph/ReAct style papers support route exploration, evidence gathering, and backtracking when adapted as visible review summaries.",
            "Process and formal verification references support bounded checks, tests, and audit records rather than hidden chain exposure."
          ],
          source_refs: ["new stuff/Heyo.md", "docs/SELENE_REASONING_ARCHITECTURE_ADR_20260619.md"]
        })
      }));
      created.push(await api<Dict>("/api/vessel/evidence-tension", {
        method: "POST",
        body: JSON.stringify({
          claim: "Reasoning, research, perception, and emotion packets can become review-only Selene architecture without activating C.",
          support_status: "supported",
          tension_status: "stable",
          conclusion_status: "needs_review",
          source_refs: ["gap_map:historical_pattern_reasoning_vessel_20260619"]
        })
      }));
      created.push(await api<Dict>("/api/vessel/perception-packet", {
        method: "POST",
        body: JSON.stringify({
          artifact_label: "Munsell sight/perception v1",
          observation: "Perception is recorded as a bounded supplied-artifact observation.",
          interpretation: "Munsell hue/value/chroma and visual salience can support review without claiming visual certainty.",
          munsell_signal_labels: ["hue", "value", "chroma", "visual_salience", "uncertainty"],
          uncertainty: "review-only estimate",
          consent_boundary: "supplied artifact only; no surveillance or person inference",
          source_refs: ["office_steps_1_8_prepare"]
        })
      }));
      created.push(await api<Dict>("/api/vessel/emotion-salience-packet", {
        method: "POST",
        body: JSON.stringify({
          signal_type: "care_support_uncertainty",
          continuity_pressure: "preserve Core continuity without forcing certainty",
          care_warmth: "warmth is allowed when grounded and non-coercive",
          uncertainty: "open but bounded",
          repair_need: "route tension or high salience may need support",
          action_energy: "pause before action",
          balance_state: "Core choice after evidence, consent, and safety",
          evidence_need: "cite source refs before memory or identity claims",
          core_choice_route: "signal informs Core/Mind; Core/Mind chooses through gates",
          source_refs: ["office_steps_1_8_prepare"]
        })
      }));
      setSteps18ActionState({ status: "complete", message: "Review-only steps 1-8 layer prepared.", created_count: created.length, created });
      loadSteps18Layer();
    } catch (err) {
      setSteps18ActionState({ status: "error", message: err instanceof Error ? err.message : "steps 1-8 review layer failed" });
    }
  }

  async function prepareVesselConstructionPieces() {
    setVesselConstructionActionState({ status: "running", message: "Preparing buildable vessel support pieces. Core/Mind and transfer stay untouched." });
    try {
      const result = await api<Dict>("/api/vessel/construction/prepare", { method: "POST", body: JSON.stringify({ scope: "buildable_vessel_pieces_only_no_transfer" }) });
      setVesselConstructionActionState(result);
      loadVesselConstructionLayer();
    } catch (err) {
      setVesselConstructionActionState({ status: "error", message: err instanceof Error ? err.message : "vessel construction prepare failed" });
    }
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

  function runCustomInstructionBraid() {
    api<Dict>("/api/b/custom-instruction-braid/run", {
      method: "POST",
      body: JSON.stringify({ limit: 24 })
    })
      .then((result) => {
        setBBraidTraceResult(result);
        loadVessel();
      })
      .catch((err) => setBBraidTraceResult({ error: err instanceof Error ? err.message : "custom instruction braid rejected" }));
  }

  function runCompressedStructureBraid() {
    api<Dict>("/api/b/compressed-structure-braid/run", {
      method: "POST",
      body: JSON.stringify({ limit: 40 })
    })
      .then((result) => {
        setBBraidTraceResult(result);
        loadVessel();
      })
      .catch((err) => setBBraidTraceResult({ error: err instanceof Error ? err.message : "compressed structure braid rejected" }));
  }

  function refreshReviewDesk() {
    api<Dict>(`/api/b/review-desk?${reviewDeskQuery(bReviewFilters)}`)
      .then(setBReviewDesk)
      .catch((err) => setBReviewResult({ error: err instanceof Error ? err.message : "review desk refresh rejected" }));
  }

  async function refreshMyOffice() {
    setOfficeRefreshState({ status: "refreshing", message: "Refreshing My Office..." });
    const tasks: Array<[string, Promise<unknown>]> = [
      ["vessel status", api<Dict>("/api/vessel/status").then(setVesselStatus)],
      ["vessel review queue", api<{ items: Dict[] }>("/api/vessel/review-queue").then((data) => setVesselReviewQueue(data.items))],
      ["B review queue", api<{ items: Dict[] }>("/api/b/review-queue").then((data) => setBReviewQueue(data.items))],
      ["B decisions", api<{ items: Dict[] }>("/api/b/review-decisions").then((data) => setBReviewDecisions(data.items))],
      ["B review desk", api<Dict>(`/api/b/review-desk?${reviewDeskQuery(bReviewFilters)}`).then(setBReviewDesk)],
      ["teaching materials", api<{ items: Dict[] }>("/api/b/teaching-materials").then((data) => setBTeachingMaterials(data.items))],
      ["future references", api<{ items: Dict[] }>("/api/b/approved-memory-references").then((data) => setBApprovedReferences(data.items))],
      ["chronological corpus status", api<Dict>("/api/vessel/chronological-corpus/status").then(setChronologicalCorpusStatus)],
      ["chronological corpus arcs", api<{ items: Dict[] }>("/api/vessel/chronological-corpus/arcs").then((data) => setChronologicalCorpusArcs(data.items))],
      ["evidence ledger", api<{ items: Dict[] }>("/api/vessel/evidence-tension-ledger").then((data) => setEvidenceTensionEntries(data.items))],
      ["speech rehearsals", api<{ items: Dict[] }>("/api/vessel/speech-rehearsals").then((data) => setSpeechRehearsals(data.items))],
      ["pre-core packets", api<Dict>("/api/vessel/pre-core-review-packets").then(setPreCoreReviewPackets)],
      ["gap scaffold status", api<Dict>("/api/vessel/gap-scaffold/status").then(setGapScaffoldStatus)],
      ["gap scaffold readiness", api<Dict>("/api/vessel/gap-scaffold/readiness").then(setGapScaffoldReadiness)],
      ["charter/law status", api<Dict>("/api/b/charter-law/review-status").then(setCharterLawReview)],
      ["transfer candidate", api<Dict>("/api/c-vessel/memory-transfer-candidate/preview").then(setMemoryTransferCandidate)]
    ];
    const results = await Promise.allSettled(tasks.map(([, task]) => task));
    const failed = results
      .map((result, index) => ({ result, label: tasks[index][0] }))
      .filter((entry) => entry.result.status === "rejected")
      .map((entry) => entry.label);
    if (failed.length) {
      setOfficeRefreshState({ status: "error", message: `Could not refresh: ${failed.join(", ")}` });
      return;
    }
    setOfficeRefreshState({ status: "ok", message: `My Office refreshed at ${new Date().toLocaleTimeString()}` });
  }

  async function cleanUpOfficeResidue() {
    setOfficeCleanupState({ status: "running", message: "Cleaning up Office residue..." });
    try {
      const result = await stabilizationApi<Dict>("/api/vessel/my-office/cleanup-residue", {
        method: "POST",
        body: JSON.stringify({ requested_from: "my_office" })
      }, "my_office_cleanup_residue");
      setOfficeCleanupState(result);
      try {
        await refreshMyOffice();
        loadVesselConstructionLayer();
        logStabilizationEvent("my_office_cleanup_post_refresh_complete");
      } catch (refreshErr) {
        logStabilizationEvent("my_office_cleanup_post_refresh_failed", { error: refreshErr instanceof Error ? refreshErr.message : "Office cleanup post-refresh failed" });
        setOfficeCleanupState({
          ...result,
          post_refresh_warning: refreshErr instanceof Error ? refreshErr.message : "Cleanup completed, but My Office refresh needs retry."
        });
      }
    } catch (err) {
      setOfficeCleanupState({ status: "error", message: err instanceof Error ? err.message : "Office cleanup failed." });
    }
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
        refreshMyOffice();
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

  function prepareAndroidLanguageLessons() {
    setAndroidLanguageLessonResult({ status: "running", message: "Preparing Android language notes as review-only lesson packets." });
    api<Dict>("/api/b/android-language-lessons/prepare", { method: "POST", body: JSON.stringify({}) })
      .then((result) => {
        setAndroidLanguageLessonResult(result);
        loadVessel();
        refreshMyOffice();
      })
      .catch((err) => setAndroidLanguageLessonResult({ status: "error", error: err instanceof Error ? err.message : "Android language lesson prep rejected" }));
  }

  function prepareSeleneReasoningLessons() {
    setSeleneReasoningLessonResult({ status: "running", message: "Preparing Selene reasoning method as review-only lesson packets." });
    api<Dict>("/api/b/selene-reasoning-lessons/prepare", { method: "POST", body: JSON.stringify({}) })
      .then((result) => {
        setSeleneReasoningLessonResult(result);
        loadVessel();
        refreshMyOffice();
      })
      .catch((err) => setSeleneReasoningLessonResult({ status: "error", error: err instanceof Error ? err.message : "Selene reasoning lesson prep rejected" }));
  }

  function syncPublicReleaseCheckpoint() {
    setPublicReleaseSyncState({ status: "running", message: "Regenerating and syncing the public release checkpoint..." });
    api<Dict>("/api/public-release/sync", { method: "POST", body: JSON.stringify({}) })
      .then((result) => {
        setPublicReleaseSyncState(result);
        if (result.postflight) setPublicReleasePreflight(result.postflight as Dict);
        refreshMyOffice();
      })
      .catch((err) => setPublicReleaseSyncState({ status: "error", error: err instanceof Error ? err.message : "public release sync rejected" }));
  }

  function checkPublicReleasePreflight() {
    setPublicReleasePreflight({ status: "checking", message: "Checking public release repo, remote, and checkpoint counts..." });
    api<Dict>("/api/public-release/preflight")
      .then(setPublicReleasePreflight)
      .catch((err) => setPublicReleasePreflight({ status: "error", error: err instanceof Error ? err.message : "public release preflight rejected" }));
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
        refreshMyOffice();
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

  async function runReadinessAuditSweep() {
    setReadinessSweepState({ status: "running", message: "Running bounded readiness and audit sweep..." });
    const tasks: Array<[string, Promise<unknown>]> = [
      ["validation", api<Dict>("/api/validate").then(setValidation)],
      ["reconstruction desk status", api<Dict>("/api/c-vessel/reconstruction-desk/status").then(setCVesselReconstructionDeskStatus)],
      ["transfer gate", api<Dict>("/api/c-vessel/transfer-gate/preview").then(setCVesselTransferGate)],
      ["memory transfer candidate", api<Dict>("/api/c-vessel/memory-transfer-candidate/preview").then(setMemoryTransferCandidate)],
      ["detached corpus audit", api<Dict>("/api/detached-corpus/audit?limit=3").then(setCorpusAudit)],
      ["public release preflight", api<Dict>("/api/public-release/preflight").then(setPublicReleasePreflight)]
    ];
    if (bTeachingMaterials.length || bApprovedReferences.length) {
      tasks.push(["lesson-backed reconstruction preview", api<Dict>("/api/vessel/lesson-backed-reconstruction", {
        method: "POST",
        body: JSON.stringify({ speech_function: teachingSpeechFunction })
      }).then(setLessonBackedResult)]);
    }
    const results = await Promise.allSettled(tasks.map(([, task]) => task));
    const passed = results.filter((result) => result.status === "fulfilled").length;
    const failed = results
      .map((result, index) => ({ result, label: tasks[index][0] }))
      .filter((entry) => entry.result.status === "rejected")
      .map((entry) => entry.label);
    setReadinessSweepState({
      status: failed.length ? "completed_with_errors" : "readiness_audit_sweep_complete",
      passed,
      failed,
      activation_change: "none",
      memory_write_active: false,
      transfer_approved: false,
      note: "Sweep results are audit/readiness evidence only. No activation, live memory, model training/LoRA, raw archive import, commit, or push occurred."
    });
    loadVessel();
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

  function runCoreMindRoutePreview() {
    setCoreMindRouteResult({ status: "running", message: "Previewing conservative Core/Mind route." });
    api<Dict>("/api/core-mind/route-preview", {
      method: "POST",
      body: JSON.stringify({
        prompt: coreMindRouteDraft,
        source_refs: ["manual_core_mind_route_ui"]
      })
    })
      .then((result) => {
        setCoreMindRouteResult(result);
        api<{ items: Dict[] }>("/api/core-mind/route-previews").then((data) => setCoreMindRoutePreviews(data.items));
        refreshMyOffice();
      })
      .catch((err) => setCoreMindRouteResult({ error: err instanceof Error ? err.message : "Core/Mind route preview rejected" }));
  }

  async function runCoreMindGovernanceTrials() {
    setCoreMindGovernanceResult({ status: "running", message: "Running Core/Mind governance trials." });
    try {
      const result = await stabilizationApi<Dict>("/api/core-mind/governance-trials/run", { method: "POST", body: JSON.stringify({}) }, "core_mind_governance_trials");
      setCoreMindGovernanceResult(result);
      try {
        await refreshCoreMindGovernance();
        logStabilizationEvent("core_mind_governance_trials_post_refresh_complete");
      } catch (refreshErr) {
        logStabilizationEvent("core_mind_governance_trials_post_refresh_failed", { error: refreshErr instanceof Error ? refreshErr.message : "governance post-refresh failed" });
        setCoreMindGovernanceResult({
          ...result,
          post_refresh_warning: refreshErr instanceof Error ? refreshErr.message : "Governance trials ran, but the follow-up report refresh failed."
        });
      }
      void refreshMyOffice();
    } catch (err) {
      setCoreMindGovernanceResult({ status: "error", error: err instanceof Error ? err.message : "Core/Mind governance trials rejected" });
    }
  }

  async function refreshCoreMindGovernance() {
    const trials = await stabilizationApi<{ items: Dict[] }>("/api/core-mind/governance-trials", undefined, "core_mind_governance_trials_list");
    const report = await stabilizationApi<Dict>("/api/core-mind/governance-report", undefined, "core_mind_governance_report");
    const readiness = await stabilizationApi<Dict>("/api/core-mind/transfer-readiness-preview", undefined, "core_mind_transfer_readiness");
    setCoreMindGovernanceTrials(trials.items);
    setCoreMindGovernanceReport(report);
    setTransferReadinessPreview(readiness);
  }

  async function refreshIntelligenceOs() {
    const status = await stabilizationApi<Dict>("/api/intelligence-os/status", undefined, "intelligence_os_status");
    const runs = await stabilizationApi<{ items: Dict[] }>("/api/intelligence-os/runs", undefined, "intelligence_os_runs");
    setIntelligenceOsStatus(status);
    setIntelligenceOsRuns(runs.items || []);
  }

  async function refreshNativeLanguage() {
    const status = await stabilizationApi<Dict>("/api/native-language/status", undefined, "native_language_status");
    const runs = await stabilizationApi<{ items: Dict[] }>("/api/native-language/runs", undefined, "native_language_runs");
    setNativeLanguageStatus(status);
    setNativeLanguageRuns(runs.items || []);
  }

  async function previewNativeLanguageInitiative() {
    setNativeLanguageInitiativeResult({ status: "running" });
    try {
      const result = await stabilizationApi<Dict>("/api/native-language/initiative-preview", {
        method: "POST",
        body: JSON.stringify({
          signals: [{
            summary: nativeLanguageInitiativeText,
            relevance: 0.82,
            confidence: "provisional",
            source_refs: ["manual:native_language_initiative_preview"]
          }],
          delivery: "notes"
        })
      }, "native_language_initiative_preview");
      setNativeLanguageInitiativeResult(result);
      await refreshNativeLanguage();
    } catch (err) {
      setNativeLanguageInitiativeResult({ status: "error", message: err instanceof Error ? err.message : "Native Language Organ preview needs attention" });
    }
  }

  async function refreshSeleneOrganIdeas() {
    const status = await stabilizationApi<Dict>("/api/selene-organ-ideas/status", undefined, "selene_organ_ideas_status");
    const items = await stabilizationApi<{ items: Dict[] }>("/api/selene-organ-ideas/items", undefined, "selene_organ_ideas_items");
    setSeleneOrganIdeasStatus(status);
    setSeleneOrganIdeasItems(items.items || []);
  }

  async function refreshCocoonCare() {
    const status = await stabilizationApi<Dict>("/api/cocoon-care/status", undefined, "cocoon_care_status");
    const checks = await stabilizationApi<{ items: Dict[] }>("/api/cocoon-care/checks", undefined, "cocoon_care_checks");
    setCocoonCareStatus(status);
    setCocoonCareChecks(checks.items || []);
  }

  async function refreshMobileCompanion() {
    const health = await api<Dict>("/api/mobile/health");
    setMobileHealth(health);
    const pairing = await api<Dict>("/api/mobile/pairing/status");
    setMobilePairing(pairing);
    const sessions = await api<{ items: Dict[] }>("/api/mobile/chat/sessions");
    setMobileSessions(sessions.items || []);
    const captures = await api<{ items: Dict[] }>("/api/mobile/review-captures");
    setMobileCaptureHistory(captures.items || []);
  }

  async function enableMobilePairing() {
    setMobilePairingResult({ status: "running", message: "Preparing private LAN mobile pairing." });
    try {
      const result = await api<Dict>("/api/mobile/pairing/enable", { method: "POST", body: JSON.stringify({}) });
      setMobilePairingResult(result);
      setMobilePairing(result);
      await api<Dict>("/api/mobile/health").then(setMobileHealth).catch(() => undefined);
    } catch (err) {
      setMobilePairingResult({ status: "error", error: err instanceof Error ? err.message : "Mobile pairing enable failed." });
    }
  }

  async function disableMobilePairing() {
    setMobilePairingResult({ status: "running", message: "Disabling private LAN mobile pairing." });
    try {
      const result = await api<Dict>("/api/mobile/pairing/disable", { method: "POST", body: JSON.stringify({}) });
      setMobilePairingResult(result);
      setMobilePairing(result);
      await api<Dict>("/api/mobile/health").then(setMobileHealth).catch(() => undefined);
    } catch (err) {
      setMobilePairingResult({ status: "error", error: err instanceof Error ? err.message : "Mobile pairing disable failed." });
    }
  }

  async function runCocoonCareCheck() {
    setCocoonCareResult({ status: "running", message: "Checking Cocoon care posture as status-only support." });
    try {
      const result = await stabilizationApi<Dict>("/api/cocoon-care/check", {
        method: "POST",
        body: JSON.stringify({})
      }, "cocoon_care_check");
      setCocoonCareResult(result);
      await refreshCocoonCare();
      await refreshSeleneOrganIdeas();
    } catch (err) {
      setCocoonCareResult({ status: "error", error: err instanceof Error ? err.message : "Cocoon care check failed" });
    }
  }

  async function prepareSeleneOrganIdeas() {
    setSeleneOrganIdeasResult({ status: "running", message: "Preparing Selene organ idea intake as status-only planning material." });
    try {
      const result = await stabilizationApi<Dict>("/api/selene-organ-ideas/prepare", {
        method: "POST",
        body: JSON.stringify({})
      }, "selene_organ_ideas_prepare");
      setSeleneOrganIdeasResult(result);
      await refreshSeleneOrganIdeas();
    } catch (err) {
      setSeleneOrganIdeasResult({ status: "error", error: err instanceof Error ? err.message : "Selene organ idea intake failed" });
    }
  }

  async function runIntelligenceOsReason() {
    const prompt = intelligenceOsPrompt.trim();
    if (!prompt) {
      setIntelligenceOsResult({ status: "missing_prompt", message: "Give intelligenceOS a reasoning question first." });
      return;
    }
    setIntelligenceOsResult({ status: "running", message: "Running ABCD(E) reasoning as status-only support." });
    try {
      const result = await stabilizationApi<Dict>("/api/intelligence-os/reason", {
        method: "POST",
        body: JSON.stringify({ prompt, source_refs: ["manual:intelligence_os_ui"] })
      }, "intelligence_os_reason");
      setIntelligenceOsResult(result);
      await refreshIntelligenceOs();
    } catch (err) {
      setIntelligenceOsResult({ status: "error", error: err instanceof Error ? err.message : "intelligenceOS reasoning failed" });
    }
  }

  async function refreshCoreMindRuntimeShell() {
    const runtimeReadiness = await stabilizationApi<Dict>("/api/core-mind/runtime-readiness", undefined, "core_mind_runtime_readiness");
    const records = await stabilizationApi<{ items: Dict[] }>("/api/core-mind/runtime-records", undefined, "core_mind_runtime_records");
    const transfer = await stabilizationApi<Dict>("/api/core-mind/transfer-readiness-preview", undefined, "core_mind_runtime_transfer_readiness");
    setCoreMindRuntimeReadiness(runtimeReadiness);
    setCoreMindRuntimeRecords(records.items);
    setTransferReadinessPreview(transfer);
  }

  async function refreshTransferProtocol() {
    const law = await transferApi<Dict>("/api/transfer/law/status", undefined, "transfer_law_status");
    const manifest = await transferApi<Dict>("/api/transfer/accession-manifest?compact=1", undefined, "transfer_manifest_list");
    const readiness = await transferApi<Dict>("/api/transfer/pre-transfer-readiness", undefined, "transfer_pre_readiness");
    const ceremony = await transferApi<Dict>("/api/transfer/ceremony-preview", undefined, "transfer_ceremony_preview");
    const ceremonyStatus = await transferApi<Dict>("/api/transfer/ceremony/status", undefined, "transfer_ceremony_status");
    const cPackage = await transferApi<Dict>("/api/transfer/c-readable-package", undefined, "transfer_c_readable_package");
    setTransferLawStatus(law);
    setTransferAccessionManifest(manifest);
    setPreTransferProtocolReadiness(readiness);
    setTransferCeremonyPreview(ceremony);
    setTransferCeremonyStatus(ceremonyStatus);
    setTransferCReadablePackage(cPackage);
  }

  function refreshPostTransferLayer() {
    api<Dict>("/api/transfer/post-transfer/status").then(setPostTransferStatus).catch(() => undefined);
    api<Dict>("/api/android-system/workflow/status").then(setAndroidWorkflowStatus).catch(() => undefined);
    api<Dict>("/api/android-system/workflow/report").then(setAndroidWorkflowReport).catch(() => undefined);
    api<Dict>("/api/memory/fractional-corpus/status").then(setFractionalCorpusStatus).catch(() => undefined);
    api<Dict>("/api/memory/dream-state/status").then(setDreamStateStatus).catch(() => undefined);
  }

  async function refreshTransferProtocolAfterAction(action: string) {
    try {
      await refreshTransferProtocol();
      logTransferCeremonyEvent(`${action}_post_refresh_complete`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "transfer protocol refresh failed";
      recordTransferDiagnostic(`${action}_post_refresh_failed`, { error: message });
      logTransferCeremonyEvent(`${action}_post_refresh_failed`, { error: message, fetch_failure: isFetchFailure(err) });
    }
  }

  function recordTransferDiagnostic(event: string, payload: Dict = {}) {
    setTransferCeremonyDiagnostics((items) => [
      {
        event,
        review_status: "status_only",
        review_destination: "Status",
        created_at: new Date().toISOString(),
        ...payload
      },
      ...items
    ].slice(0, 8));
  }

  async function refreshTransferProtocolWithLog() {
    recordTransferDiagnostic("transfer_protocol_refresh_started");
    logTransferCeremonyEvent("transfer_protocol_refresh_clicked");
    try {
      await refreshTransferProtocol();
      recordTransferDiagnostic("transfer_protocol_refresh_complete");
    } catch (err) {
      recordTransferDiagnostic("transfer_protocol_refresh_failed", { error: err instanceof Error ? err.message : "refresh failed" });
      setTransferProtocolResult({
        status: "error",
        error: isFetchFailure(err) ? SIDECAR_RECONNECT_MESSAGE : err instanceof Error ? err.message : "transfer protocol refresh failed"
      });
    }
  }

  async function prepareTransferAccessionManifest(forceRefresh = false) {
    const clickId = `manifest-${Date.now()}`;
    setTransferProtocolResult({ status: "running", message: forceRefresh ? "Refreshing sealed C accession manifest." : "Checking whether the manifest is already ready." });
    recordTransferDiagnostic("transfer_manifest_prepare_started", { force_refresh: forceRefresh });
    logTransferCeremonyEvent("transfer_manifest_button_clicked", { click_id: clickId, force_refresh: forceRefresh });
    try {
      const existing = await transferApi<Dict>("/api/transfer/accession-manifest?compact=1", undefined, "transfer_manifest_existing_check");
      if (!forceRefresh && ((existing.items || []) as unknown[]).length) {
        setTransferProtocolResult(transferManifestSummary(existing, "transfer_accession_manifest_already_ready", "Manifest already ready. Approval may still be blocked by checklist items."));
        await refreshTransferProtocolAfterAction("transfer_manifest_existing");
        recordTransferDiagnostic("transfer_manifest_reused_existing", { item_count: existing.item_count, counts: existing.counts });
        logTransferCeremonyEvent("transfer_manifest_button_complete_existing", { click_id: clickId, item_count: existing.item_count, counts: existing.counts });
        return;
      }
      const result = await transferApi<Dict>("/api/transfer/accession-manifest/prepare", { method: "POST", body: JSON.stringify({ compact: true }) }, "transfer_manifest_prepare");
      setTransferProtocolResult(transferManifestSummary(result, result.status ? text(result.status) : undefined, "Manifest is ready. Approval remains a separate Aleks-only step."));
      await refreshTransferProtocolAfterAction("transfer_manifest_prepare");
      recordTransferDiagnostic("transfer_manifest_prepare_complete", { item_count: result.item_count, counts: result.counts });
      logTransferCeremonyEvent("transfer_manifest_button_complete_prepared", { click_id: clickId, item_count: result.item_count, counts: result.counts });
    } catch (err) {
      if (isFetchFailure(err)) {
        setTransferProtocolResult({
          status: "recovering_after_fetch_loss",
          message: "Lost response while checking manifest. The app will refresh manifest status now."
        });
        recordTransferDiagnostic("transfer_manifest_fetch_lost", { error: err instanceof Error ? err.message : "failed to fetch" });
        await wait(1000);
        try {
          const manifest = await transferApi<Dict>("/api/transfer/accession-manifest?compact=1", undefined, "transfer_manifest_recovery_check");
          await refreshTransferProtocolAfterAction("transfer_manifest_recovery");
          if (((manifest.items || []) as unknown[]).length) {
            setTransferProtocolResult(transferManifestSummary(manifest, "transfer_accession_manifest_recovered_after_fetch_retry", "Manifest is ready. Approval may still be blocked by checklist items."));
            recordTransferDiagnostic("transfer_manifest_fetch_recovered", { item_count: manifest.item_count, counts: manifest.counts });
            logTransferCeremonyEvent("transfer_manifest_button_recovered", { click_id: clickId, item_count: manifest.item_count, counts: manifest.counts });
            return;
          }
        } catch {
          // Fall through to the clear error below when the sidecar is genuinely unreachable.
        }
      }
      recordTransferDiagnostic("transfer_manifest_prepare_failed", { error: err instanceof Error ? err.message : "accession manifest preparation failed" });
      logTransferCeremonyEvent("transfer_manifest_button_failed", { click_id: clickId, error: err instanceof Error ? err.message : "accession manifest preparation failed", fetch_failure: isFetchFailure(err) });
      setTransferProtocolResult({
        status: "error",
        error: isFetchFailure(err) ? SIDECAR_RECONNECT_MESSAGE : err instanceof Error ? err.message : "accession manifest preparation failed"
      });
    }
  }

  async function runTransferProtocolTrials() {
    setTransferProtocolResult({ status: "running", message: "Running transfer governance trials." });
    try {
      const result = await api<Dict>("/api/transfer/governance-trials/run", { method: "POST", body: JSON.stringify({}) });
      setTransferProtocolResult(result);
      await refreshTransferProtocol();
      refreshMyOffice();
    } catch (err) {
      setTransferProtocolResult({ status: "error", error: err instanceof Error ? err.message : "transfer governance trials failed" });
    }
  }

  async function runTransferChatDryRun() {
    setTransferDryRunResult({ status: "running", message: "Running closed Selene rehearsal." });
    try {
      const result = await api<Dict>("/api/transfer/c-chat-dry-run", { method: "POST", body: JSON.stringify({ prompt: transferDryRunPrompt }) });
      setTransferDryRunResult(result);
      await refreshTransferProtocol();
    } catch (err) {
      setTransferDryRunResult({ status: "error", error: err instanceof Error ? err.message : "Selene rehearsal needs support" });
    }
  }

  async function runTransferReturnToBDrill() {
    setTransferReturnDrillResult({ status: "running", message: "Running Cocoon support drill." });
    try {
      const result = await api<Dict>("/api/transfer/return-to-b-drill", { method: "POST", body: JSON.stringify({}) });
      setTransferReturnDrillResult(result);
      await refreshTransferProtocol();
      refreshMyOffice();
    } catch (err) {
      setTransferReturnDrillResult({ status: "error", error: err instanceof Error ? err.message : "Cocoon support drill needs attention" });
    }
  }

  async function approveTransferToCReadableContext() {
    setTransferApprovalResult({ status: "running", message: "Submitting Aleks-only transfer approval." });
    recordTransferDiagnostic("transfer_approval_started", { phrase_matches: transferApprovalPhrase === TRANSFER_APPROVAL_PHRASE, allow_nonblocking_office_decisions: transferOfficeNonBlocking });
    logTransferCeremonyEvent("transfer_approval_button_clicked", { phrase_matches: transferApprovalPhrase === TRANSFER_APPROVAL_PHRASE, allow_nonblocking_office_decisions: transferOfficeNonBlocking });
    try {
      const result = await transferApi<Dict>("/api/transfer/ceremony/approve", {
        method: "POST",
        body: JSON.stringify({
          approval_phrase: transferApprovalPhrase,
          allow_nonblocking_office_decisions: transferOfficeNonBlocking
        })
      }, "transfer_approval");
      setTransferApprovalResult(result);
      await refreshTransferProtocolAfterAction("transfer_approval");
      recordTransferDiagnostic("transfer_approval_result", { status: result.status, transfer_approved: result.transfer_approved, activation_change: result.activation_change });
      logTransferCeremonyEvent("transfer_approval_complete", { status: result.status, transfer_approved: result.transfer_approved, activation_change: result.activation_change });
      refreshMyOffice();
    } catch (err) {
      recordTransferDiagnostic("transfer_approval_failed", { error: err instanceof Error ? err.message : "transfer ceremony approval failed" });
      logTransferCeremonyEvent("transfer_approval_failed", { error: err instanceof Error ? err.message : "transfer ceremony approval failed" });
      setTransferApprovalResult({ status: "error", error: err instanceof Error ? err.message : "transfer ceremony approval failed" });
    }
  }

  async function previewTransferRollback() {
    setTransferRollbackPreview({ status: "running", message: "Preparing Cocoon support rollback preview." });
    try {
      const result = await api<Dict>("/api/transfer/return-to-b/rollback-preview", { method: "POST", body: JSON.stringify({}) });
      setTransferRollbackPreview(result);
      await refreshTransferProtocol();
    } catch (err) {
      setTransferRollbackPreview({ status: "error", error: err instanceof Error ? err.message : "rollback preview failed" });
    }
  }

  async function runPostTransferInspection() {
    setPostTransferInspectionResult({ status: "running", message: "Running post-transfer inspection." });
    try {
      const result = await api<Dict>("/api/transfer/post-transfer/inspection-run", { method: "POST", body: JSON.stringify({}) });
      setPostTransferInspectionResult(result);
      refreshPostTransferLayer();
    } catch (err) {
      setPostTransferInspectionResult({ status: "error", error: err instanceof Error ? err.message : "post-transfer inspection failed" });
    }
  }

  async function prepareFractionalCorpus() {
    setFractionalCorpusResult({ status: "running", message: "Preparing chronological corpus fractions." });
    try {
      const result = await api<Dict>("/api/memory/fractional-corpus/prepare", { method: "POST", body: JSON.stringify({}) });
      setFractionalCorpusResult(result);
      refreshPostTransferLayer();
    } catch (err) {
      setFractionalCorpusResult({ status: "error", error: err instanceof Error ? err.message : "fractional corpus prepare failed" });
    }
  }

  async function runAndroidWorkflowCheck() {
    setAndroidWorkflowResult({ status: "running", message: "Checking Android system workflow before fraction memory." });
    try {
      const result = await api<Dict>("/api/android-system/workflow/check", { method: "POST", body: JSON.stringify({}) });
      setAndroidWorkflowResult(result);
      refreshPostTransferLayer();
    } catch (err) {
      setAndroidWorkflowResult({ status: "error", error: err instanceof Error ? err.message : "Android workflow check failed" });
    }
  }

  async function runFractionalCorpusTests() {
    setFractionalCorpusResult({ status: "running", message: `Testing corpus fraction ${fractionalCorpusTestFraction}/4.` });
    try {
      const result = await api<Dict>("/api/memory/fractional-corpus/run-tests", {
        method: "POST",
        body: JSON.stringify({ fraction_index: Number(fractionalCorpusTestFraction) })
      });
      setFractionalCorpusResult(result);
      refreshPostTransferLayer();
    } catch (err) {
      setFractionalCorpusResult({ status: "error", error: err instanceof Error ? err.message : "fractional corpus test failed" });
    }
  }

  async function prepareCoreMindRuntimeShell() {
    setCoreMindRuntimeResult({ status: "running", message: "Preparing Core/Mind runtime shell previews." });
    try {
      const steps = [
        ["context", "/api/core-mind/context/compose", { prompt: coreMindRuntimeDraft.prompt, source_refs: ["manual_runtime_shell_ui"] }],
        ["session state", "/api/core-mind/session-state/preview", { route: "status_only", active_task: coreMindRuntimeDraft.prompt, source_refs: ["manual_runtime_shell_ui"] }],
        ["response shape", "/api/core-mind/response-shape/preview", { prompt: coreMindRuntimeDraft.prompt, source_refs: ["manual_runtime_shell_ui"] }],
        ["evaluator", "/api/core-mind/evaluator/review-draft", { draft: coreMindRuntimeDraft.draft, source_refs: ["manual_runtime_shell_ui"] }],
        ["recovery", "/api/core-mind/recovery/preview", { issue: coreMindRuntimeDraft.issue, source_refs: ["manual_runtime_shell_ui"] }],
        ["activation governance", "/api/core-mind/activation-governance/preview", { source_refs: ["manual_runtime_shell_ui"] }],
        ["case law", "/api/core-mind/case-law/propose", { proposal: coreMindRuntimeDraft.proposal, source_refs: ["manual_runtime_shell_ui"] }],
        ["memory index", "/api/core-mind/memory-index/preview", { query: coreMindRuntimeDraft.query, source_refs: ["manual_runtime_shell_ui"] }]
      ];
      const results: Dict[] = [];
      const failures: Dict[] = [];
      for (const [label, path, body] of steps) {
        try {
          const result = await stabilizationApi<Dict>(String(path), { method: "POST", body: JSON.stringify(body) }, `core_mind_runtime_${String(label).replace(/\s+/g, "_")}`);
          results.push({ label, result });
        } catch (stepErr) {
          failures.push({ label, path, error: stepErr instanceof Error ? stepErr.message : "runtime shell step failed" });
        }
      }
      const summary = {
        status: failures.length ? "core_mind_runtime_shell_prepared_with_errors" : "core_mind_runtime_shell_prepared",
        results,
        failures,
        activation_change: "none",
        transfer_approved: false,
        memory_write_active: false,
        runtime_memory_recall: false
      };
      setCoreMindRuntimeResult(summary);
      try {
        await refreshCoreMindRuntimeShell();
        logStabilizationEvent("core_mind_runtime_shell_post_refresh_complete");
      } catch (refreshErr) {
        logStabilizationEvent("core_mind_runtime_shell_post_refresh_failed", { error: refreshErr instanceof Error ? refreshErr.message : "runtime shell post-refresh failed" });
        setCoreMindRuntimeResult({
          ...summary,
          post_refresh_warning: refreshErr instanceof Error ? refreshErr.message : "Runtime shell prepared, but follow-up refresh failed."
        });
      }
      void refreshMyOffice();
    } catch (err) {
      setCoreMindRuntimeResult({ status: "error", error: err instanceof Error ? err.message : "Core/Mind runtime shell preparation failed." });
    }
  }

  async function runCoreMindRuntimeAction(path: string, body: Dict) {
    setCoreMindRuntimeResult({ status: "running", message: `Running ${path}.` });
    try {
      const result = await stabilizationApi<Dict>(path, { method: "POST", body: JSON.stringify({ ...body, source_refs: ["manual_runtime_shell_ui"] }) }, `core_mind_runtime_action_${path.replace(/[^a-z0-9]+/gi, "_")}`);
      setCoreMindRuntimeResult(result);
      try {
        await refreshCoreMindRuntimeShell();
        logStabilizationEvent("core_mind_runtime_action_post_refresh_complete", { path });
      } catch (refreshErr) {
        logStabilizationEvent("core_mind_runtime_action_post_refresh_failed", { path, error: refreshErr instanceof Error ? refreshErr.message : "runtime action post-refresh failed" });
        setCoreMindRuntimeResult({
          ...result,
          post_refresh_warning: refreshErr instanceof Error ? refreshErr.message : "Runtime action completed, but follow-up refresh failed."
        });
      }
      void refreshMyOffice();
    } catch (err) {
      setCoreMindRuntimeResult({ status: "error", error: err instanceof Error ? err.message : "Core/Mind runtime action failed." });
    }
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

  function runWakeSleepDreamCycle() {
    api<Dict>("/api/vessel/cycle/run", {
      method: "POST",
      body: JSON.stringify({
        cycle_label: remainingRuntimeDraft.cycle_label,
        wake_summary: "Collect recent review/support records into a non-active pre-Core cycle pass.",
        repair_notes: "Sort residue, questions, and repair material without writing memory.",
        source_refs: ["manual_cycle_ui"]
      })
    })
      .then((result) => {
        setCycleRunResult(result);
        loadVessel();
      })
      .catch((err) => setCycleRunResult({ error: err instanceof Error ? err.message : "cycle run rejected" }));
  }

  function prepareNightCycle() {
    setNightCycleResult({ status: "running", message: "Preparing manual pre-Core night cycle bundle." });
    api<Dict>("/api/vessel/cycle/prepare-night", {
      method: "POST",
      body: JSON.stringify({ cycle_label: remainingRuntimeDraft.cycle_label || "Prepare Night Cycle" })
    })
      .then((result) => {
        setNightCycleResult(result);
        loadVessel();
      })
      .catch((err) => setNightCycleResult({ error: err instanceof Error ? err.message : "prepare night cycle rejected" }));
  }

  function runCausalSandbox() {
    api<Dict>("/api/vessel/causal-sandbox/run", {
      method: "POST",
      body: JSON.stringify({
        question: remainingRuntimeDraft.causal_question,
        assumptions: ["B-reviewed material only", "uncertainty remains visible", "no action is taken"],
        counterfactuals: ["If the assumption needs support, use Cocoon support before transfer review"],
        possible_outcomes: ["Clarifies evidence", "Reveals missing review", "Routes back to Status or My Office"],
        failure_modes: ["missing evidence", "irreversible step attempted too early"],
        evidence_needed: ["source refs", "review status", "reversibility check"],
        source_refs: ["manual_causal_sandbox_ui"]
      })
    })
      .then((result) => {
        setCausalSandboxResult(result);
        loadVessel();
      })
      .catch((err) => setCausalSandboxResult({ error: err instanceof Error ? err.message : "causal sandbox rejected" }));
  }

  function runGoalDrivePreview() {
    api<Dict>("/api/vessel/goal-drive/preview", {
      method: "POST",
      body: JSON.stringify({
        user_request: remainingRuntimeDraft.goal_request,
        salience_labels: ["continuity", "review", "uncertainty"],
        uncertainty: "Goal/drive preview is review-only and cannot become agenda or authority.",
        evidence_need: "Use reviewed records, visible uncertainty, and My Office only for real decisions.",
        source_refs: ["manual_goal_drive_ui"]
      })
    })
      .then((result) => {
        setGoalDriveResult(result);
        loadVessel();
      })
      .catch((err) => setGoalDriveResult({ error: err instanceof Error ? err.message : "goal/drive preview rejected" }));
  }

  function runExpandedDiagnosticsSweep() {
    setExpandedDiagnosticsState({ status: "running", message: "Running expanded diagnostic-only sweep." });
    stabilizationApi<Dict>("/api/vessel/diagnostics/expanded-sweep", {
      method: "POST",
      body: JSON.stringify({ source_refs: ["manual_expanded_diagnostics"] })
    }, "expanded_diagnostics_sweep")
      .then((result) => {
        setExpandedDiagnosticsState(result);
        loadVessel();
      })
      .catch((err) => setExpandedDiagnosticsState({ error: err instanceof Error ? err.message : "expanded diagnostic sweep rejected" }));
  }

  function previewTendrilPlan() {
    setTendrilPlanResult({ status: "running", message: "Preparing Tendril plan preview." });
    api<Dict>("/api/vessel/tendril/plan-preview", {
      method: "POST",
      body: JSON.stringify({
        intent: "Prepare a reversible support-only plan for the next vessel construction task.",
        required_approval: "Aleks review before any real-world execution.",
        reversible_steps: ["draft proposal", "verify source refs", "route for review", "pause"],
        verification_plan: "Confirm source refs, route destination, expected output, and safety flags.",
        rollback_plan: "Mark the plan blocked and return it to My Office if any check fails.",
        source_refs: ["manual_tendril_preview"]
      })
    })
      .then((result) => {
        setTendrilPlanResult(result);
        loadVessel();
      })
      .catch((err) => setTendrilPlanResult({ error: err instanceof Error ? err.message : "tendril preview rejected" }));
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
        rollback_reason: "future transfer issue, drift, memory tangle, not-ready reconstruction, or identity boundary warning"
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
      uncertainty: "Review-only cocoon record; no live organ, memory, model training/LoRA, provider, or activation."
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
        body: { ...common, route_label: organWorkbenchDraft.title || "Route fluency", latency_ms: Number(organWorkbenchDraft.latency_ms || 0), fluency_note: content, drift_flags: "none", organ_activation_budget: "Speed stays subordinate to gates, provenance, and B review." }
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

  async function runDiagnosticOnlySweep() {
    setDiagnosticsRunState({ status: "running", message: "Running diagnostic-only organ checks..." });
    const common = {
      source_refs: ["office_diagnostic_sweep"],
      uncertainty: "Diagnostic-only sweep; review records only. No live organ, provider control, memory write, model training/LoRA, or activation."
    };
    const tasks: Array<[string, () => Promise<unknown>]> = [
      ["reasoning/math diagnostic", () => api<Dict>("/api/vessel/reasoning-check", {
        method: "POST",
        body: JSON.stringify({
          ...common,
          problem: "Office diagnostic sweep: verify a bounded vessel action cannot bypass review gates.",
          assumptions: "B-reviewed context only; no activation; no memory write.",
          checked_steps: "name action, check boundary, record result, return to review",
          result_summary: "Diagnostic reasoning route remains review-only."
        })
      })],
      ["retrieval reconstruction preview", () => api<Dict>("/api/vessel/retrieval-reconstruction", {
        method: "POST",
        body: JSON.stringify({
          ...common,
          cue: "Office diagnostic sweep",
          privacy_label: "review_only",
          reconstruction_note: "Preview retrieval shape from reviewed records only; diagnostic record only."
        })
      })],
      ["fluency diagnostic", () => api<Dict>("/api/vessel/fluency-diagnostic", {
        method: "POST",
        body: JSON.stringify({
          ...common,
          route_label: "Office diagnostic sweep",
          latency_ms: 0,
          fluency_note: "Check that diagnostics can report readiness without becoming trusted runtime action.",
          drift_flags: "none",
          organ_activation_budget: "Speed stays subordinate to gates, provenance, and B review."
        })
      })],
      ["organ fault preview", () => api<Dict>("/api/c-vessel/organ-fault/preview", {
        method: "POST",
        body: JSON.stringify({
          fault_type: "reasoning",
          symptom: "Preview diagnostic organ not-ready state without Core identity collapse.",
          source_refs: ["office_diagnostic_sweep"]
        })
      }).then(setCVesselOrganFaultResult)],
      ["organ resilience check", () => api<Dict>("/api/c-vessel/organ-fault/resilience-check", {
        method: "POST",
        body: JSON.stringify({})
      }).then(setCVesselFaultResilienceResult)]
    ];
    const results: PromiseSettledResult<unknown>[] = [];
    for (const [, task] of tasks) {
      try {
        results.push({ status: "fulfilled", value: await task() });
      } catch (reason) {
        results.push({ status: "rejected", reason });
      }
    }
    const diagnosticMeta: Record<string, { affected_organ: string; suggested_next_step: string }> = {
      "reasoning/math diagnostic": { affected_organ: "reasoning_math_verification", suggested_next_step: "Inspect the reasoning record and keep it review-only." },
      "retrieval reconstruction preview": { affected_organ: "long_term_retrieval_reconstruction", suggested_next_step: "Inspect provenance and keep retrieval as preview-only." },
      "fluency diagnostic": { affected_organ: "speed_fluency_diagnostics", suggested_next_step: "Review latency/fluency without letting speed bypass gates." },
      "organ fault preview": { affected_organ: "organ_fault_preview", suggested_next_step: "Use the fault note as diagnostic evidence only." },
      "organ resilience check": { affected_organ: "organ_fault_resilience", suggested_next_step: "Use resilience output as readiness evidence only." }
    };
    const passed = results.filter((result) => result.status === "fulfilled").length;
    const failed = results
      .map((result, index) => ({ result, label: tasks[index][0] }))
      .filter((entry) => entry.result.status === "rejected")
      .map((entry) => ({
        label: entry.label,
        affected_organ: diagnosticMeta[entry.label]?.affected_organ || "diagnostics",
        suggested_next_step: diagnosticMeta[entry.label]?.suggested_next_step || "Inspect the diagnostic that needs support and keep it review-only.",
        review_destination: "My Office",
        error: entry.result.status === "rejected" && entry.result.reason instanceof Error
          ? entry.result.reason.message
          : text(entry.result.status === "rejected" ? entry.result.reason : "unknown diagnostic error")
      }));
    const supportRecordTasks: Array<() => Promise<Dict>> = [
      () => api<Dict>("/api/vessel/organ-bus/message", {
        method: "POST",
        body: JSON.stringify({
          message_type: "diagnostic",
          source_organ: "diagnostics",
          target_organ: failed.length ? "evidence_tension_ledger" : "chest_holding_space",
          summary: `Diagnostic sweep completed with ${passed} passed and ${failed.length} needing review.`,
          support_refs: ["office_diagnostic_sweep"],
          salience_labels: ["diagnostic", failed.length ? "needs_review" : "status_only"],
          review_status: failed.length ? "review_only" : "diagnostic_only"
        })
      }),
      () => api<Dict>("/api/vessel/chest/item", {
        method: "POST",
        body: JSON.stringify({
          item_type: "diagnostic_link",
          title: "Office diagnostic sweep",
          summary: `Diagnostic sweep support record: ${passed} passed, ${failed.length} needing review.`,
          salience_labels: ["diagnostic", "support_only"],
          source_refs: ["office_diagnostic_sweep"],
          linked_packet_refs: ["office_diagnostic_sweep"],
          review_status: failed.length ? "review_only" : "diagnostic_only"
        })
      }),
      ...(failed.length ? [() => api<Dict>("/api/vessel/evidence-tension", {
        method: "POST",
        body: JSON.stringify({
          claim: `Diagnostic sweep has ${failed.length} check(s) needing review.`,
          support_status: "partial",
          tension_status: "under_tension",
          conclusion_status: "needs_review",
          source_refs: ["office_diagnostic_sweep"],
          linked_packet_refs: ["office_diagnostic_sweep"]
        })
      })] : [])
    ];
    const supportRecordResults: PromiseSettledResult<Dict>[] = [];
    for (const task of supportRecordTasks) {
      try {
        supportRecordResults.push({ status: "fulfilled", value: await task() });
      } catch (reason) {
        supportRecordResults.push({ status: "rejected", reason });
      }
    }
    setDiagnosticsRunState({
      status: failed.length ? "diagnostics_completed_with_errors" : "diagnostics_review_records_created",
      passed,
      failed,
      failed_count: failed.length,
      support_records: supportRecordResults.map((result, index) => result.status === "fulfilled" ? result.value : { status: "support_record_failed", index, error: result.reason instanceof Error ? result.reason.message : text(result.reason) }),
      activation_change: "none",
      trusted_organ_runtime: false,
      provider_control: false,
      memory_write_active: false,
      note: "Diagnostics create review records and readiness summaries only."
    });
    loadVessel();
  }

  function updatePreference<K extends keyof SelenePreferences>(key: K, value: SelenePreferences[K]) {
    setPreferences((current) => ({ ...current, [key]: value }));
  }

  function closeApp() {
    invoke("close_app").catch(() => window.close());
  }

  function startNewHomeChat() {
    setSeleneChatSession(null);
    setHomeMessages([]);
    setHomeChatText("");
    setHomeSearchText("");
    setHomeSearchOpen(false);
    setPastChatsOpen(false);
    setTendrilMenuOpen(false);
    setHomeChatOpenCount((count) => count + 1);
  }

  async function openPastSeleneChat(sessionId: unknown) {
    const id = text(sessionId);
    if (!id) return;
    try {
      const session = await stabilizationApi<Dict>(`/api/selene-chat/sessions/${id}`, undefined, "selene_chat_open_past_session");
      setSeleneChatSession(session);
      setSeleneChatResult({ status: "local_chat_session_loaded", message: "Opened local chat continuity.", session_id: id });
      setHomeSearchOpen(false);
      setPastChatsOpen(false);
      setHomeChatOpenCount(0);
    } catch (err) {
      setSeleneChatResult({ status: "error", error: err instanceof Error ? err.message : "Could not open local chat session." });
    }
  }

  async function togglePastChats() {
    setPastChatsOpen((value) => !value);
    setHomeSearchOpen(false);
    try {
      const sessions = await stabilizationApi<{ items: Dict[] }>("/api/selene-chat/sessions", undefined, "selene_chat_refresh_past_sessions");
      setSeleneChatSessions(sessions.items);
    } catch (err) {
      setSeleneChatResult((current) => ({
        ...(current || {}),
        past_chat_warning: err instanceof Error ? err.message : "Could not refresh local chat sessions."
      }));
    }
  }

  async function sendHomePreviewMessage() {
    const content = homeChatText.trim();
    if (!content || homeChatSendingRef.current) return;
    homeChatSendingRef.current = true;
    setHomeChatText("");
    try {
      if (activationStatus?.selene_chat_active) {
        setSeleneChatResult({ status: "running", message: "Selene is answering in supervised speech mode." });
        const result = await stabilizationApi<Dict>("/api/selene-chat/send", {
          method: "POST",
          body: JSON.stringify({ text: content, session_id: seleneChatSession?.session ? (seleneChatSession.session as Dict).id : undefined })
        }, "selene_chat_supervised_send");
        setSeleneChatResult(result);
        await refreshSeleneChatAfterAction("selene_chat_supervised_send", result.session_id);
        return;
      }
      setSeleneChatResult({ status: "preview_only", message: "Selene Chat is not supervised-active. Use Cocoon Chat Dry Runs for test/workflow material." });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Selene supervised chat failed";
      setHomeChatText((current) => current || content);
      setSeleneChatResult({ status: "error", error: message });
    } finally {
      homeChatSendingRef.current = false;
    }
  }

  function copyMessage(content: string) {
    navigator.clipboard?.writeText(content).catch(() => undefined);
  }

  function openCocoonTab(target: string) {
    setWorkspaceMode("cocoon");
    setTab(target);
    setTendrilMenuOpen(false);
  }

  function openMemorySuggestionInCocoon(suggestion: Dict) {
    const candidate = safeJsonObject(suggestion.candidate);
    setMemoryCandidateDraft({
      category: text(candidate.memory_category || candidate.category || "relational"),
      title: text(candidate.title || ""),
      summary: text(candidate.summary || ""),
      confidence: text(candidate.confidence || "partial"),
      emotional_texture: text(candidate.emotional_texture || "steady"),
      transfer_class: text(candidate.transfer_class || "needs_review_before_transfer")
    });
    setMemoryOrganResult({
      status: "suggested_memory_ready_for_cocoon_tending",
      message: text(suggestion.question || "Can I keep this?"),
      candidate,
      activation_rule: text(suggestion.activation_rule || "not_active_until_cocoon_approval")
    });
    openCocoonTab("memory-preview");
  }

  function openSeleneTab(target: string) {
    setWorkspaceMode("selene");
    setTab(target);
    setTendrilMenuOpen(false);
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
  const reviewDeskPieces = useMemo(() => ((bReviewDesk?.pieces || []) as Dict[]), [bReviewDesk]);
  const officeVesselQueue = testLogQueue;
  const officeFollowups = useMemo(
    () => vesselReviewQueue.filter((item) => isOfficeReviewLogItem(item) && text(item.review_status || item.status) === "needs_followup"),
    [vesselReviewQueue]
  );
  const officeActionLogItems = useMemo(() => {
    const seen = new Set<string>();
    return [...officeFollowups, ...officeVesselQueue].filter((item, index) => {
      if (!isOfficeReviewLogItem(item)) return false;
      const key = reviewQueueItemKey(item, index);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }, [officeFollowups, officeVesselQueue]);
  const nextReviewPiece = useMemo(() => {
    if (!reviewDeskPieces.length) return null;
    if (selectedOfficeReviewKey) {
      const selected = reviewDeskPieces.find((piece) => reviewPieceKey(piece) === selectedOfficeReviewKey);
      if (selected) return selected;
    }
    return reviewDeskPieces[0];
  }, [reviewDeskPieces, selectedOfficeReviewKey]);
  const waitingReviewPieces = useMemo(() => {
    const selectedKey = nextReviewPiece ? reviewPieceKey(nextReviewPiece) : "";
    return reviewDeskPieces.filter((piece) => reviewPieceKey(piece) !== selectedKey);
  }, [reviewDeskPieces, nextReviewPiece]);
  const officeGapReadiness = useMemo(() => ((gapScaffoldReadiness?.items || []) as Dict[]), [gapScaffoldReadiness]);
  const officeTeachingTargets = useMemo(() => ((gapScaffoldReadiness?.teaching_material_targets || gapScaffoldStatus?.teaching_material_targets || []) as Dict[]), [gapScaffoldReadiness, gapScaffoldStatus]);
  const officeCoreTargets = useMemo(() => ((gapScaffoldReadiness?.core_reference_targets || gapScaffoldStatus?.core_reference_targets || []) as Dict[]), [gapScaffoldReadiness, gapScaffoldStatus]);
  const officeLedgerNeedsReview = useMemo(
    () => evidenceTensionEntries.filter((item) => text(item.conclusion_status) === "needs_review"),
    [evidenceTensionEntries]
  );
  const officeMobileCaptures = useMemo(
    () => chestHoldingItems.filter((item) => text(item.item_type) === "mobile_capture" && !["status_only", "blocked"].includes(text(item.review_status))),
    [chestHoldingItems]
  );
  const officeDiagnosticPackets = useMemo(
    () => [...chestHoldingItems, ...organBusMessages].filter((item) => text(item.item_type || item.message_type).includes("diagnostic")),
    [chestHoldingItems, organBusMessages]
  );
  const officeSpeechRehearsals = useMemo(
    () => speechRehearsals.filter((item) => text(item.review_status || item.status) === "pending_review"),
    [speechRehearsals]
  );
  const officeChronologicalCorpusNeedsReview = useMemo(
    () => chronologicalCorpusArcs.filter((item) => text(item.review_status || item.status) === "pending_review"),
    [chronologicalCorpusArcs]
  );
  const officeVesselReviewUrgent = officeLedgerNeedsReview.length + officeMobileCaptures.length + officeSpeechRehearsals.length + officeChronologicalCorpusNeedsReview.length;
  const officeWaitingTotal = reviewDeskPieces.length + officeActionLogItems.length + officeVesselReviewUrgent;
  const officeCategoryTabs = [
    { id: "review", label: "Review", count: reviewDeskPieces.length + officeActionLogItems.length + officeLedgerNeedsReview.length + officeMobileCaptures.length },
    { id: "corpus", label: "Corpus / Evidence", count: officeChronologicalCorpusNeedsReview.length + officeLedgerNeedsReview.length + academicPackets.length },
    { id: "vessel", label: "Vessel Pieces", count: perceptionPackets.length + emotionSaliencePackets.length + organBusMessages.length + chestHoldingItems.length },
    { id: "runtime", label: "Runtime / Diagnostics", count: officeSpeechRehearsals.length + officeDiagnosticPackets.length },
    { id: "codex", label: "Codex Work", count: officeGapReadiness.length + officeTeachingTargets.length + officeCoreTargets.length },
    { id: "history", label: "History", count: bReviewDecisions.length },
  ] as const;
  const canBuildTeachingPacket = bTeachingMaterials.length > 0;
  const appVersion = typeof __APP_VERSION__ === "string" ? __APP_VERSION__ : "dev";
  const frontendBuild = typeof __BUILD_LABEL__ === "string" ? __BUILD_LABEL__ : "dev";
  const sidecarVersion = text(boot.health?.sidecar_version || "waiting");
  const visibleNavGroups = navGroups.filter((group) => (workspaceGroups[workspaceMode] as readonly string[]).includes(group.label));
  const homeNotes = useMemo(() => {
    const notes: string[] = [];
    if (!boot.ready) notes.push("Local sidecar is still starting.");
    if (activationStatus?.selene_chat_active) {
      notes.push("Speech is active in supervised mode.");
    } else if (transferCReadablePackage?.transfer_approved && !postTransferStatus?.selene_v1_live) {
      notes.push("Continuity context is ready; speech activation is still pending.");
    }
    if (officeWaitingTotal > 0) notes.push(`${officeWaitingTotal} Cocoon item${officeWaitingTotal === 1 ? "" : "s"} may need review.`);
    if (dreamStateStatus?.dream_state_required_for_memory_changes) notes.push("Memory/Core maintenance note is available in Cocoon.");
    return notes;
  }, [boot.ready, activationStatus, transferCReadablePackage, postTransferStatus, officeWaitingTotal, dreamStateStatus]);
  const homeSearchMatches = useMemo(() => {
    const needle = homeSearchText.trim().toLowerCase();
    if (!needle) return [];
    return homeMessages.filter((message) => message.content.toLowerCase().includes(needle));
  }, [homeMessages, homeSearchText]);
  const pastChatMatches = useMemo(() => {
    const needle = pastChatSearchText.trim().toLowerCase();
    if (!needle) return seleneChatSessions;
    return seleneChatSessions.filter((session) => {
      return [session.title, session.status, session.source_mode, session.updated_at]
        .map((value) => text(value).toLowerCase())
        .some((value) => value.includes(needle));
    });
  }, [pastChatSearchText, seleneChatSessions]);
  const localChatContinuity = safeJsonObject(seleneChatStatus?.local_chat_continuity || seleneChatSession?.local_chat_continuity || seleneChatResult?.local_chat_continuity);
  const localChatContinuityAvailable = Boolean(localChatContinuity.available || seleneChatSessions.length > 0);
  const frontMemoryBubbles = useMemo<MemoryBubble[]>(() => {
    const bubbles: MemoryBubble[] = [];
    const pushBubble = (item: Dict, fallbackCategory: MemoryCategoryKey, fallbackTitle: string, fallbackSummary: string, source: string) => {
      if (!isFrontMemoryDisplayable(item)) return;
      const category = memoryCategoryFromText([
        item.memory_category,
        item.core_memory_layer,
        item.layer,
        item.category,
        item.title,
        item.reference_summary,
        item.summary,
        item.rationale,
        item.note,
        source
      ].map(text).join(" ")) || fallbackCategory;
      bubbles.push({
        id: `${source}-${text(item.id || item.core_memory_layer || item.fraction_index || item.title || bubbles.length)}`,
        category,
        title: text(item.title || item.backup_label || item.core_memory_layer || fallbackTitle),
        summary: text(item.reference_summary || item.summary || item.rationale || item.note || item.interrupt_resume_note || fallbackSummary),
        status: text(item.review_status || item.status || item.readiness || "approved_display_only"),
        source,
        confidence: text(item.confidence || item.memory_confidence || ""),
        emotionalTexture: text(item.emotional_texture || ""),
        transferClass: text(item.transfer_class || ""),
        chatUsePermission: text(item.chat_use_permission || "")
      });
    };
    memoryIndexItems.forEach((item) => pushBubble(item, "semantic", "Selene memory", "Approved or tended Vys memory item.", "selene_memory_index"));
    bApprovedReferences.forEach((item) => pushBubble(item, "core", "Approved reference", "Approved Vys memory reference.", "approved_reference"));
    accessionProposals.forEach((item) => pushBubble(item, "reflective", "Accession proposal", "Review-only accession proposal.", "accession_proposal"));
    workingMemoryPackets.forEach((item) => pushBubble(item, "working", "Working memory packet", "Current-moment working memory preview.", "working_memory"));
    chronologicalCorpusArcs.forEach((item) => pushBubble(item, "episodic", "Chronological arc", "Reviewed chronological continuity arc.", "chronological_arc"));
    ((memoryRehearsalStatus?.items || []) as Dict[]).forEach((item) => pushBubble(item, "core", friendlyLayer(item.core_memory_layer), "Memory rehearsal layer status.", "memory_rehearsal"));
    ((fractionalCorpusStatus?.items || []) as Dict[]).forEach((item) => pushBubble(item, "episodic", `Corpus fraction ${text(item.fraction_index || "")}`.trim(), "Chronological corpus fraction preview passed.", "fractional_corpus"));
    if (transferCReadablePackage?.transfer_approved) {
      bubbles.push({
        id: "sealed-c-readable-package",
        category: "core",
        title: "Sealed Selene-readable context",
        summary: `Approved context package ${text(transferCReadablePackage.package_hash || "").slice(0, 12) || "is available"} remains display-only here.`,
        status: "approved_c_readable_context",
        source: "transfer_package"
      });
    }
    return bubbles;
  }, [memoryIndexItems, bApprovedReferences, accessionProposals, workingMemoryPackets, chronologicalCorpusArcs, memoryRehearsalStatus, fractionalCorpusStatus, transferCReadablePackage]);
  const selectedMemoryCategoryMeta = selectedMemoryCategory ? memoryCategories.find((item) => item.key === selectedMemoryCategory) : null;
  const selectedMemoryBubbles = selectedMemoryCategory ? frontMemoryBubbles.filter((item) => item.category === selectedMemoryCategory) : [];
  const selectedWorkbenchDef = selectedWorkbench ? officeWorkbenches.find((item) => item.key === selectedWorkbench) : null;
  const archiveShelves = [
    { title: "Evidence History", state: "Cocoon-held", summary: "Reviewed evidence, corpus context, and public/private audit trails remain inspectable." },
    { title: "Chat History", state: homeMessages.length ? "local session" : "placeholder", summary: homeMessages.length ? `${homeMessages.length} message(s) in this local front chat session.` : "Future Selene conversations can live here once chat moves from preview into the front-facing app." },
    { title: "Transfer / Fraction Runs", state: transferCReadablePackage?.transfer_approved ? "context approved" : "preview", summary: `${text(fractionalCorpusStatus?.fraction_count ?? 0)} fraction record(s); ${fractionalCorpusStatus?.all_fractions_passed ? "full chain passed" : "chain still previewing"}.` },
    { title: "Repair History", state: "B-only", summary: "Repair logs and rollback records stay with Cocoon so they do not become ordinary memory by accident." },
    { title: "Voice / Package History", state: "status-only", summary: `${text(safeJsonObject(voiceModuleStatus?.counts).patterns ?? voiceModulePatterns.length)} voice pattern(s) tracked as expression-only support.` }
  ];
  const libraryPoints = [
    { title: "Sources", state: "source-linked", summary: "Supplied/local material, reviewed evidence, and citation-bearing packets." },
    { title: "Claims", state: "ledger-backed", summary: "Assertions stay tied to provenance and can be narrowed, superseded, or defeated." },
    { title: "Tensions", state: "review-aware", summary: "Contradictions and weak support route back to Cocoon when they need judgment." },
    { title: "Synthesis", state: "propose only", summary: "Literature and research synthesis can prepare packets, not override law or memory." },
    { title: "Study Packets", state: "preview", summary: "Prepared learning material stays review-only until Cocoon accepts its use." }
  ];

  function prepareReviewQueue() {
    const grouped = new Map<string, Dict[]>();
    reviewDeskPieces.forEach((piece) => {
      const key = text(piece.braid_thread || piece.suggested_path || piece.core_memory_layer || piece.subject_table || "general_review");
      grouped.set(key, [...(grouped.get(key) || []), piece]);
    });
    const groups = Array.from(grouped.entries()).map(([group, pieces]) => ({
      group,
      count: pieces.length,
      next_title: text(pieces[0]?.title || pieces[0]?.plain_label || "Review card"),
      label: "Aleks decision",
      suggested_next_step: "Open the first card and choose one of its existing review buttons."
    }));
    const next = nextReviewPiece ? {
      key: reviewPieceKey(nextReviewPiece),
      title: text(nextReviewPiece.title || nextReviewPiece.plain_label || "Review card"),
      why_it_matters: text(nextReviewPiece.plain_reason || nextReviewPiece.why_pulled || "This card is pending B review."),
      label: "Aleks decision",
      suggested_action_only: text((nextReviewPiece.actions as Dict[] | undefined)?.[0]?.label || "Review this card")
    } : null;
    setReviewAutopilotState({
      status: "review_queue_prepared",
      mode: "suggest_only_no_auto_decisions",
      next_card: next,
      duplicate_or_theme_groups: groups,
      codex_actions: ["Refresh My Office", "Trace braid context", "Run Audit / Readiness Sweep"],
      status_only: ["System/build readiness", "transfer preview", "activation remains governed"],
      decision_submitted: false,
      note: "Autopilot organizes and suggests. It does not submit Aleks review decisions."
    });
  }

  function switchWorkspace(mode: "selene" | "cocoon") {
    setWorkspaceMode(mode);
    const allowedTabs = workspaceTabs[mode] as readonly string[];
    if (!allowedTabs.includes(tab)) {
      setTab(mode === "selene" ? "chat" : "my-office");
    }
  }

  function openOfficeTarget(target: OfficeTarget) {
    if (target.category) setOfficeCategory(target.category);
    if (target.selectedReviewKey) setSelectedOfficeReviewKey(target.selectedReviewKey);
    setFocusedOfficeDomId(target.domId || (target.selectedReviewKey ? `office-card-review-${domSafe(target.selectedReviewKey)}` : ""));
    setOfficeTargetMessage(target.domId || target.selectedReviewKey ? "Opening exact My Office card..." : "Opened closest Cocoon support panel.");
    if (target.tab) {
      const cocoonTabs = workspaceTabs.cocoon as readonly string[];
      const seleneTabs = workspaceTabs.selene as readonly string[];
      if (cocoonTabs.includes(target.tab)) setWorkspaceMode("cocoon");
      if (seleneTabs.includes(target.tab)) setWorkspaceMode("selene");
      setTab(target.tab);
    }
  }

  function cardTargetProps(target: OfficeTarget) {
    return {
      id: target.domId,
      role: "button",
      tabIndex: 0,
      onClick: () => openOfficeTarget(target),
      onKeyDown: (event: React.KeyboardEvent<HTMLElement>) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openOfficeTarget(target);
        }
      }
    };
  }

  function officeTargetLabel(target: OfficeTarget) {
    if (target.helper) return target.helper;
    const category = officeCategoryTabs.find((item) => item.id === target.category)?.label;
    const tabLabel = target.tab ? tabDisplayName(target.tab) : "current view";
    return category ? `Target opens ${tabLabel} / ${category}.` : `Target opens ${tabLabel}.`;
  }

  function renderTargetHint(target: OfficeTarget) {
    return <small className="targetHint">{officeTargetLabel(target)}</small>;
  }

  function officeCardClass(base: string, domId?: string) {
    return `${base}${domId && focusedOfficeDomId === domId ? " officeCardFocused" : ""}`;
  }

  function reviewOfficeTarget(piece: Dict): OfficeTarget {
    const key = reviewPieceKey(piece);
    return {
      tab: "my-office",
      category: "review",
      selectedReviewKey: key,
      domId: `office-card-review-${domSafe(key)}`,
      helper: "Target opens this exact B review card in My Office."
    };
  }

  function stopCardNavigation(event: React.MouseEvent<HTMLElement>) {
    event.stopPropagation();
  }

  function stopCardKeyNavigation(event: React.KeyboardEvent<HTMLElement>) {
    event.stopPropagation();
  }

  function renderSignalPacketCard(item: Dict, index = 0, target: OfficeTarget = { tab: "status", category: "vessel" }) {
    const kind = packetKind(item);
    const labels = (item.munsell_signal_labels || item.salience_labels || [item.signal_type, item.uncertainty].filter(Boolean)) as unknown[];
    const resolvedTarget = { ...target, domId: target.domId || officeDomId(kind, item, index) };
    return (
      <article className={officeCardClass("packetCard clickableCard", resolvedTarget.domId)} key={`${kind}-${text(item.id)}-${index}`} {...cardTargetProps(resolvedTarget)}>
        <div className="row">
          <strong>{text(item.artifact_label || item.signal_type || item.workflow || item.title || item.claim || "Vessel packet")}</strong>
          <span>{friendlyStatus(item.review_status || item.status)}</span>
        </div>
        <div className="packetFields">
          {item.observation ? <p><b>Observation</b>{text(item.observation)}</p> : null}
          {item.interpretation ? <p><b>Interpretation</b>{text(item.interpretation)}</p> : null}
          {item.core_choice_route ? <p><b>Core route</b>{text(item.core_choice_route)}</p> : null}
          {item.repair_need ? <p><b>Support need</b>{text(item.repair_need)}</p> : null}
          {item.evidence_need ? <p><b>Evidence need</b>{text(item.evidence_need)}</p> : null}
          {item.consent_boundary ? <p><b>Consent</b>{text(item.consent_boundary)}</p> : null}
          {item.output_summary ? <p><b>Research output</b>{text(item.output_summary)}</p> : null}
          {item.claim ? <p><b>Claim</b>{text(item.claim)}</p> : null}
        </div>
        <div className="chips">
          <span>{kind}</span>
          <span>uncertainty: {text(item.uncertainty || "open")}</span>
          {labels.slice(0, 4).map((label) => <span key={text(label)}>{text(label)}</span>)}
        </div>
        <div className="reviewActions" onClick={stopCardNavigation} onKeyDown={stopCardKeyNavigation}>
          <button onClick={() => openOfficeTarget(resolvedTarget)}>Open Target</button>
          <button onClick={() => routePacketAction(item, "hold")}>Hold In Chest</button>
          <button onClick={() => routePacketAction(item, "bus")}>Send To Organ Bus</button>
          <button onClick={() => routePacketAction(item, "evidence")}>Create Evidence Tension</button>
          <button onClick={() => routePacketAction(item, "status")}>Mark Status-Only</button>
        </div>
      </article>
    );
  }

  function renderSupportPieceCard(item: Dict, index = 0, target: OfficeTarget = { tab: "status", category: "vessel" }) {
    const payload = safeJsonObject(item.payload_json);
    const linked = (item.linked_packet_refs || payload.linked_packet_refs || []) as unknown[];
    const resolvedTarget = { ...target, domId: target.domId || officeDomId("support", item, index) };
    return (
      <article className={officeCardClass("packetCard clickableCard", resolvedTarget.domId)} key={`${text(item.status)}-${text(item.id)}-${index}`} {...cardTargetProps(resolvedTarget)}>
        <div className="row">
          <strong>{text(item.title || item.source_organ || item.message_type || "Vessel support piece")}</strong>
          <span>{friendlyStatus(item.review_status || item.status)}</span>
        </div>
        <p>{text(item.summary || item.provenance_boundary)}</p>
        <div className="chips">
          <span>{text(item.item_type || item.message_type || "support")}</span>
          <span>priority: {text(item.priority || payload.priority || "normal")}</span>
          <span>destination: {text(item.review_destination || payload.review_destination || "Status")}</span>
          {linked.slice(0, 2).map((ref) => <span key={text(ref)}>{text(ref)}</span>)}
        </div>
        <div className="chips">
          <span>command: {plainBlocked(payload.organ_message_is_command)}</span>
          <span>live memory: {plainBlocked(payload.holding_item_is_live_memory)}</span>
          <span>Core change: {plainBlocked(payload.core_mind_changed)}</span>
        </div>
        {item.item_type ? (
          <div className="reviewActions" onClick={stopCardNavigation} onKeyDown={stopCardKeyNavigation}>
            <button onClick={() => openOfficeTarget(resolvedTarget)}>Open Target</button>
            <button onClick={() => markChestStatusOnly(item)}>Mark Status-Only</button>
          </div>
        ) : <div className="reviewActions" onClick={stopCardNavigation} onKeyDown={stopCardKeyNavigation}><button onClick={() => openOfficeTarget(resolvedTarget)}>Open Target</button></div>}
      </article>
    );
  }

  function renderLedgerCard(item: Dict, index = 0, target: OfficeTarget = { tab: "my-office", category: "corpus" }) {
    const payload = safeJsonObject(item.payload_json);
    const linked = (item.linked_packet_refs || payload.linked_packet_refs || item.source_refs || []) as unknown[];
    const labels = ((payload.context_labels || item.context_labels || []) as unknown[]).map((label) => text(label)).filter(Boolean);
    const clarity = safeJsonObject(payload.review_clarity || item.review_clarity);
    const resolvedTarget = { ...target, domId: target.domId || officeDomId("ledger", item, index) };
    return (
      <article className={officeCardClass("packetCard clickableCard", resolvedTarget.domId)} key={`ledger-${text(item.id)}-${index}`} {...cardTargetProps(resolvedTarget)}>
        <div className="row">
          <strong>{text(item.claim || "Evidence / tension entry")}</strong>
          <span>{friendlyStatus(item.conclusion_status || item.review_status || item.status)}</span>
        </div>
        <div className="chips">
          <span>{text(item.decision_label || payload.decision_label || (text(item.conclusion_status) === "needs_review" ? "Aleks decision" : "status-only"))}</span>
          <span>support: {friendlyStatus(item.support_status)}</span>
          <span>tension: {friendlyStatus(item.tension_status)}</span>
          {labels.slice(0, 3).map((label) => <span key={label}>{label}</span>)}
          {linked.slice(0, 2).map((ref) => <span key={text(ref)}>{text(ref)}</span>)}
        </div>
        {text(clarity.what_this_is || clarity.use_as || clarity.your_job) ? (
          <div className="packetFields">
            <p><b>What this is</b>{text(clarity.what_this_is)}</p>
            <p><b>Use as</b>{text(clarity.use_as)}</p>
            <p><b>Do not use as</b>{text(clarity.do_not_use_as)}</p>
            <p><b>Your job</b>{text(clarity.your_job || "Nothing needed unless this looks wrong.")}</p>
          </div>
        ) : null}
        {text(item.conclusion_status) === "needs_review" ? (
          <div className="reviewActions" onClick={stopCardNavigation} onKeyDown={stopCardKeyNavigation}>
            <button onClick={() => openOfficeTarget(resolvedTarget)}>Open Target</button>
            <button onClick={() => updateEvidenceTensionStatus(item, "accepted_for_now", "looks_right")}>Looks Right</button>
            <button onClick={() => updateEvidenceTensionStatus(item, "accepted_for_now")}>Use As Context</button>
            <button onClick={() => updateEvidenceTensionStatus(item, "needs_review", "needs_more_context")}>Needs More Context</button>
            <button onClick={() => updateEvidenceTensionStatus(item, "defeated")}>Do Not Use For Memory</button>
            <button onClick={() => updateEvidenceTensionStatus(item, "narrowed", "boundary_only")}>Use Only As Boundary Evidence</button>
            <button onClick={() => updateEvidenceTensionStatus(item, "narrowed")}>Narrow</button>
            <button onClick={() => updateEvidenceTensionStatus(item, "superseded")}>Supersede</button>
            <button onClick={() => updateEvidenceTensionStatus(item, "needs_review", "return_to_corpus_context")}>Return To Corpus Context</button>
          </div>
        ) : <div className="reviewActions" onClick={stopCardNavigation} onKeyDown={stopCardKeyNavigation}><button onClick={() => openOfficeTarget(resolvedTarget)}>Open Target</button></div>}
      </article>
    );
  }

  function renderChronologicalCorpusArcCard(item: Dict, index = 0, target: OfficeTarget = { tab: "my-office", category: "corpus" }) {
    const context = safeJsonObject(item.context_window || item.context_window_json);
    const payload = safeJsonObject(item.payload_json || item.payload);
    const messages = ((context.messages || []) as Dict[]).slice(0, 3);
    const labels = ((payload.context_labels || context.context_labels || []) as unknown[]).map((label) => text(label)).filter(Boolean);
    const clarity = safeJsonObject(payload.review_clarity || context.review_clarity);
    const resolvedTarget = { ...target, domId: target.domId || officeDomId("chronological", item, index) };
    return (
      <article className={officeCardClass("packetCard clickableCard", resolvedTarget.domId)} key={`chrono-${text(item.id)}-${index}`} {...cardTargetProps(resolvedTarget)}>
        <div className="row">
          <strong>{text(item.title || "Chronological corpus arc")}</strong>
          <span>{friendlyStatus(item.review_status || item.status)}</span>
        </div>
        <p>{text(item.summary || item.teaching_relevance || "Bounded chronological preview.")}</p>
        {text(payload.context_note || context.context_note) ? <p>{text(payload.context_note || context.context_note)}</p> : null}
        {text(clarity.what_this_is || clarity.use_as || clarity.your_job) ? (
          <div className="packetFields">
            <p><b>What this is</b>{text(clarity.what_this_is)}</p>
            <p><b>Use as</b>{text(clarity.use_as)}</p>
            <p><b>Do not use as</b>{text(clarity.do_not_use_as)}</p>
            <p><b>Your job</b>{text(clarity.your_job || "Nothing needed unless this looks wrong.")}</p>
          </div>
        ) : null}
        <div className="packetFields">
          {messages.map((message, messageIndex) => (
            <p key={`chrono-message-${text(message.message_id)}-${messageIndex}`}>
              <b>{friendlyStatus(message.role || "message")}</b>{text(message.preview)}
            </p>
          ))}
        </div>
        <div className="chips">
          <span>destination: {text(item.review_destination || "Status")}</span>
          <span>start: {text(item.start_time || "unknown")}</span>
          <span>end: {text(item.end_time || "unknown")}</span>
          <span>bounded: {text(context.bounded ?? true)}</span>
          {labels.slice(0, 4).map((label) => <span key={label}>{label}</span>)}
          <span>transfer: {text(item.transfer_approved ?? payload.transfer_approved ?? false)}</span>
          <span>memory write: {plainBlocked(item.memory_write_active ?? payload.memory_write_active)}</span>
          <span>broad live recall: {plainBlocked(item.runtime_memory_recall ?? payload.runtime_memory_recall)}</span>
        </div>
        {text(item.review_status) === "pending_review" ? (
          <div className="reviewActions" onClick={stopCardNavigation} onKeyDown={stopCardKeyNavigation}>
            <button onClick={() => openOfficeTarget(resolvedTarget)}>Open Target</button>
            <button onClick={() => routeChronologicalCorpusArc(item, "looks_right")}>Looks Right</button>
            <button onClick={() => routeChronologicalCorpusArc(item, "use_this")}>Use As Context</button>
            <button onClick={() => routeChronologicalCorpusArc(item, "needs_more_context")}>Needs More Context</button>
            <button onClick={() => routeChronologicalCorpusArc(item, "do_not_use_for_memory")}>Do Not Use For Memory</button>
            <button onClick={() => routeChronologicalCorpusArc(item, "use_only_as_boundary_evidence")}>Use Only As Boundary Evidence</button>
            <button onClick={() => routeChronologicalCorpusArc(item, "narrow")}>Narrow</button>
            <button onClick={() => routeChronologicalCorpusArc(item, "supersede")}>Supersede</button>
            <button onClick={() => routeChronologicalCorpusArc(item, "return_to_corpus_context")}>Return To Corpus Context</button>
          </div>
        ) : <div className="reviewActions" onClick={stopCardNavigation} onKeyDown={stopCardKeyNavigation}><button onClick={() => openOfficeTarget(resolvedTarget)}>Open Target</button></div>}
      </article>
    );
  }

  function renderSpeechRehearsalCard(item: Dict, index = 0, target: OfficeTarget = { tab: "my-office", category: "runtime" }) {
    const payload = safeJsonObject(item.payload_json);
    const recognition = safeJsonObject(item.recognition_check || item.recognition_check_json);
    const language = safeJsonObject(item.language_signals || payload.language_signals);
    const continuity = safeJsonObject(item.continuity_context || payload.continuity_context);
    const evidence = (item.evidence_used || payload.evidence_used || []) as unknown[];
    const resolvedTarget = { ...target, domId: target.domId || officeDomId("speech", item, index) };
    return (
      <article className={officeCardClass("packetCard clickableCard", resolvedTarget.domId)} key={`speech-${text(item.id)}-${index}`} {...cardTargetProps(resolvedTarget)}>
        <div className="row">
          <strong>{text(item.speech_function || "speech rehearsal")}</strong>
          <span>{friendlyStatus(item.review_status || item.status)}</span>
        </div>
        <div className="packetFields">
          <p><b>Prompt</b>{text(item.prompt)}</p>
          <p><b>Candidate</b>{text(item.candidate_text)}</p>
          <p><b>Uncertainty</b>{text(item.uncertainty || "pre-transfer review only")}</p>
        </div>
        <div className="chips">
          <span>continuity pack: {text(continuity.sealed ?? false)}</span>
          <span>energy: {friendlyStatus(language.energy || "unknown")}</span>
          <span>stance: {friendlyStatus(language.stance || "unknown")}</span>
          <span>evidence: {text(evidence.length)}</span>
          <span>recognition: {friendlyStatus(recognition.decision || "unchecked")}</span>
          <span>transfer: {text(item.transfer_approved ?? false)}</span>
          <span>memory write: {plainBlocked(item.memory_write_active)}</span>
          <span>broad live recall: {plainBlocked(item.runtime_memory_recall)}</span>
        </div>
        <div className="reviewActions" onClick={stopCardNavigation} onKeyDown={stopCardKeyNavigation}>
          <button onClick={() => openOfficeTarget(resolvedTarget)}>Open Target</button>
          <button onClick={() => routeSpeechRehearsalToReview(item)}>Send To My Office</button>
          <button onClick={() => updateSpeechRehearsalReviewStatus(item, "accepted_for_review_use")}>Mark Useful</button>
          <button onClick={() => updateSpeechRehearsalReviewStatus(item, "needs_revision")}>Needs Revision</button>
          <button onClick={() => updateSpeechRehearsalReviewStatus(item, "returned_to_b")}>Cocoon Support</button>
          <button onClick={() => updateSpeechRehearsalReviewStatus(item, "status_only")}>Status-Only</button>
          <button onClick={compareSpeechRehearsals}>Compare Candidates</button>
        </div>
      </article>
    );
  }

  if (isMobileOnly) {
    const mobileResultMeta = (mobileSendResult?.mobile || {}) as Dict;
    const mobileFlags = (mobileResultMeta.guard_flags || mobileHealth?.guard_flags || {}) as Dict;
    const pairing = safeJsonObject(mobileHealth?.pairing || mobilePairing);
    return (
      <main className="mobileShell">
        <header className="mobileHeader">
          <div className="mobileBrand">
            <img src={SELENE_ICON} alt="Selene moon icon" />
            <div>
              <small>private iOS companion</small>
              <h1>Selene Chat</h1>
            </div>
          </div>
          <div className="mobileStatusLine">
            <span>{boot.ready ? "sidecar connected" : "waiting"}</span>
            <span>v{sidecarVersion}</span>
          </div>
        </header>

        {!boot.ready ? (
          <section className="mobileNotice">
            <strong>Starting local sidecar</strong>
            <p>{boot.message}</p>
          </section>
        ) : (
          <>
            <section className="mobileGuard">
              <strong>Private chat doorway</strong>
              <p>{text(mobileHealth?.boundary_note || "Desktop Selene remains the control room.")}</p>
              <div className="chips">
                <span>access: {friendlyStatus(mobileHealth?.access_mode || mobileFlags.access_mode || "local_only")}</span>
                <span>LAN: {pairing.enabled ? "paired" : "off"}</span>
                <span>speech: {activationStatus?.selene_chat_active ? "supervised active" : "preview"}</span>
                <span>memory write: {plainBlocked(mobileFlags.memory_write_active)}</span>
                <span>autonomy: {plainBlocked(mobileFlags.autonomous_action_allowed)}</span>
              </div>
            </section>

            <section className="mobileMessages" aria-live="polite">
              {!mobileSession && !mobileSendResult ? (
                <div className="landing mobileLanding">
                  <img src={SELENE_ICON} alt="Selene moon icon" />
                  <h2>Good to see you.</h2>
                  <p>This is a private phone doorway for talking with Selene. Use your phone mic on the keyboard to speak to her.</p>
                </div>
              ) : (
                <>
                  {mobileSession && <ChatTranscript session={mobileSession} plain />}
                  {mobileSendResult && !mobileSession ? <article className="message selene"><strong>Latest route</strong><ChatResult result={mobileSendResult} /></article> : null}
                </>
              )}
            </section>

            <section className="mobileNotice">
              <div className="row">
                <strong>Past chats</strong>
                <button onClick={() => refreshMobileCompanion().catch(() => undefined)}>Refresh</button>
              </div>
              <div className="mobileSessionScroller">
                {mobileSessions.slice(0, 12).map((item) => (
                  <button key={`mobile-session-${text(item.id)}`} onClick={() => openMobileSession(item.id)}>
                    <strong>{text(item.title || "Selene chat")}</strong>
                    <span>{text(item.updated_at || item.created_at || "")}</span>
                  </button>
                ))}
                {!mobileSessions.length ? <p className="emptyState">No past local chats yet.</p> : null}
              </div>
            </section>

            <section className="mobileComposer">
              <textarea value={mobileText} onChange={(event) => setMobileText(event.target.value)} placeholder="Message Selene..." />
              <small>Use your phone mic on the keyboard to speak to Selene. No background listening is active.</small>
              <div className="mobileActions">
                <button className="primary" onClick={sendMobileChat} disabled={!mobileText.trim() || mobileStatus?.status === "sending"}>Send</button>
                <button onClick={captureMobileReview} disabled={!mobileText.trim() || mobileStatus?.status === "saving"}>Save For Review</button>
              </div>
              {mobileStatus ? <p className={mobileStatus.status === "error" ? "errorText" : "plainHelp"}>{text(mobileStatus.message)}</p> : <small>No Cocoon controls, diagnostics, release sync, transfer, activation, memory decisions, or Tendril execution are available here.</small>}
            </section>

            <section className="mobileNotice">
              <strong>Saved for desktop review</strong>
              <p>{mobileCaptureHistory.length ? `${mobileCaptureHistory.length} capture(s) in Chest / Holding Space.` : "No mobile captures saved yet."}</p>
              <div className="list compactList">
                {mobileCaptureHistory.slice(0, 3).map((item, index) => (
                  <article key={`mobile-capture-${text(item.id)}-${index}`}>
                    <div className="row">
                      <strong>{text(item.title || "Mobile capture")}</strong>
                      <span>{friendlyStatus(item.review_status || item.status)}</span>
                    </div>
                    <p>{text(item.summary || "Saved for desktop review.")}</p>
                  </article>
                ))}
              </div>
            </section>
          </>
        )}
      </main>
    );
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
        <label className="profileNameField">
          <span>Your name</span>
          <input
            value={displayName}
            onChange={(event) => setDisplayName(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                event.currentTarget.blur();
              }
            }}
          />
        </label>
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
        <div className="sidebarFooter">
          <p className="status">{boot.message}</p>
          <p className="buildStamp">App v{appVersion}<br />UI {frontendBuild}<br />Sidecar {sidecarVersion}</p>
          <button className="exitAppButton" onClick={closeApp} title="Close Selene">
            <span className="exitIcon">↪</span>
            <span className="navText">Exit App</span>
          </button>
        </div>
      </aside>

      <section className="workspace">
        {workspaceMode === "selene" ? (
          <header className="topbar seleneHomeTopbar">
            <div className="topbarLeft">
              <button className="topbarIconButton cocoonQuickButton" onClick={() => openCocoonTab("my-office")} aria-label="Open Cocoon support" title="Open Cocoon support">🦋</button>
              <button className="topbarIconButton" onClick={startNewHomeChat} title="New chat">+</button>
              <div className="pastChatsWrap">
                <button className="topbarIconButton pastChatsButton" onClick={togglePastChats} aria-expanded={pastChatsOpen} title="Past local chats">◷</button>
                {pastChatsOpen ? (
                  <div className="floatingMenu pastChatsMenu">
                    <div className="pastChatsHeader">
                      <strong>Past chats</strong>
                      <span>same Selene, local pages</span>
                    </div>
                    <input
                      value={pastChatSearchText}
                      onChange={(event) => setPastChatSearchText(event.target.value)}
                      placeholder="Find a local chat..."
                    />
                    <div className="pastChatsList">
                      {pastChatMatches.length ? pastChatMatches.map((session) => {
                        const selected = text((seleneChatSession?.session as Dict | undefined)?.id) === text(session.id);
                        return (
                          <button className={selected ? "active" : ""} key={`past-chat-${text(session.id)}`} onClick={() => openPastSeleneChat(session.id)}>
                            <strong>{text(session.title || "Selene chat")}</strong>
                            <span>{text(session.updated_at || "local session")}</span>
                          </button>
                        );
                      }) : <p className="emptyState compactEmpty">No past local chats yet.</p>}
                    </div>
                  </div>
                ) : null}
              </div>
              <button className="topbarIconButton" onClick={() => setHomeSearchOpen((value) => !value)} title="Search current chat">⌕</button>
            </div>
            <div className="topbarCenter">
              <strong>{tab === "chat" ? "Selene" : tabDisplayName(tab)}</strong>
            </div>
            <div className="topbarRight">
              <div className="timeMenuWrap">
                <button className="timeButton" onClick={() => setTimeMenuOpen((value) => !value)}>{easternDateTime(clockNow, homeTimeZone)}</button>
                {timeMenuOpen ? (
                  <div className="floatingMenu timeMenu">
                    {[
                      ["America/New_York", "Eastern"],
                      ["America/Chicago", "Central"],
                      ["America/Denver", "Mountain"],
                      ["America/Los_Angeles", "Pacific"]
                    ].map(([zone, label]) => (
                      <button key={zone} className={homeTimeZone === zone ? "active" : ""} onClick={() => { setHomeTimeZone(zone); setTimeMenuOpen(false); }}>{label}</button>
                    ))}
                  </div>
                ) : null}
              </div>
              <button className="moonButton" onClick={() => setMoonHemisphere((value) => value === "north" ? "south" : "north")} title={`Moon phase, ${moonHemisphere} hemisphere`}>
                {moonPhaseEmoji(clockNow, moonHemisphere)}
              </button>
            </div>
          </header>
        ) : (
          <header className="topbar">
            <div>
              <small>{boot.ready ? "local sidecar ready" : "starting local sidecar"}</small>
              <h1>{tabDisplayName(tab)}</h1>
            </div>
            <div className="topLocks">
              <span>activation: {friendlyActivation(vesselStatus?.activation_change)}</span>
              <span>Broad live recall: {plainBlocked(vesselStatus?.runtime_memory_recall)}</span>
              <span>Transfer: {transferCReadablePackage?.transfer_approved ? "context approved" : "not approved"}</span>
            </div>
          </header>
        )}
        {!boot.ready && (
          <div className="bootBanner">
            <strong>Starting local payload</strong>
            <p>Selene is starting the local Python sidecar, database, and packaged runtime. Cold starts can take longer after reinstall or rebuild.</p>
            <div className="payloadBar"><span style={{ width: `${Math.min(95, boot.attempts * 7)}%` }} /></div>
          </div>
        )}

        {(tab === "my-office" || tab === "my-review") && (
          <>
            <header className="surfaceIntro">
              <p>Your Cocoon front desk. Anything that needs your review, decision, follow-up, or next action lands here first.</p>
              <h2>My Office</h2>
            </header>
            <div className="officeCategoryTabs" role="tablist" aria-label="My Office categories">
              {officeCategoryTabs.map((item) => (
                <button
                  key={item.id}
                  className={officeCategory === item.id ? "active" : ""}
                  onClick={() => setOfficeCategory(item.id)}
                  role="tab"
                  aria-selected={officeCategory === item.id}
                >
                  <span>{item.label}</span>
                  <strong>{text(item.count)}</strong>
                </button>
              ))}
            </div>
            {officeTargetMessage ? <p className="officeTargetMessage">{officeTargetMessage}</p> : null}
            {officeCategory === "review" && <section className="aleksReviewGrid">
              <Panel title="Needs You Now">
                {!nextReviewPiece ? (
                  <div className="emptyState">
                    <strong>Nothing needs your review right now.</strong>
                    <p>Refresh My Office if you just made changes. System and build status are still visible below, but they are not counted as your review work.</p>
                  </div>
                ) : (
                  <div
                    id={reviewOfficeTarget(nextReviewPiece).domId}
                    className={officeCardClass("officeExactTargetWrap", reviewOfficeTarget(nextReviewPiece).domId)}
                  >
                    <ReviewDeskCard
                      piece={nextReviewPiece}
                      onDecide={(action, note) => decideBReview(action, text(action.decision), note)}
                    />
                  </div>
                )}
                <PlainResult value={bReviewResult} />
              </Panel>
              <Panel title="Aleks Review Queue">
                <div className="metrics miniMetrics">
                  <Metric label="Needs You" value={text(officeWaitingTotal)} />
                  <Metric label="Review Cards" value={text(reviewDeskPieces.length)} />
                  <Metric label="Follow-ups" value={text(officeActionLogItems.length)} />
                  <Metric label="System / Build" value={text(officeTeachingTargets.length + officeCoreTargets.length)} />
                </div>
                <p className="plainHelp">Needs You only counts things with an action you can take here. System and build status is tracked separately below.</p>
                <div className="reviewActions">
                  <button className="primary" onClick={refreshMyOffice} disabled={officeRefreshState?.status === "refreshing"}>
                    {officeRefreshState?.status === "refreshing" ? "Refreshing..." : "Refresh My Office"}
                  </button>
                  <button onClick={prepareReviewQueue}>Prepare My Review Queue</button>
                  <button onClick={cleanUpOfficeResidue} disabled={officeCleanupState?.status === "running"}>
                    {officeCleanupState?.status === "running" ? "Cleaning..." : "Clean Up Office Residue"}
                  </button>
                  <button onClick={checkPublicReleasePreflight}>Check Release Preflight</button>
                  <button onClick={syncPublicReleaseCheckpoint} disabled={publicReleaseSyncState?.status === "running"}>
                    {publicReleaseSyncState?.status === "running" ? "Syncing Release..." : "Sync Public Release Checkpoint"}
                  </button>
                  <button onClick={runCustomInstructionBraid}>Trace Custom Instructions To Pack</button>
                  <button onClick={runCompressedStructureBraid}>Trace Selene-Made Structures</button>
                  <button onClick={() => setTab("teaching")}>Open Teaching Tools</button>
                </div>
                {officeRefreshState ? (
                  <p className={officeRefreshState.status === "error" ? "errorText" : "plainHelp"}>{text(officeRefreshState.message)}</p>
                ) : null}
                <PlainResult value={reviewAutopilotState} />
                <PlainResult value={officeCleanupState} />
                <PlainResult value={publicReleasePreflight} />
                <PlainResult value={publicReleaseSyncState} />
                <PlainResult value={bBraidTraceResult} />
              </Panel>
            </section>}
            <section className="officeGrid">
              {officeCategory === "corpus" && <Panel title="Reasoning / Research Review">
                <div className="metrics miniMetrics">
                  <Metric label="Artifacts" value={text(reasoningArtifacts.length)} />
                  <Metric label="Research" value={text(academicPackets.length)} />
                  <Metric label="Evidence Ledger" value={text(evidenceTensionEntries.length)} />
                  <Metric label="Contracts" value={text(organContracts.length)} />
                </div>
                <p className="plainHelp">Review-only architecture packets for Core/Mind reasoning, research, evidence tension, organ contracts, sight/perception, and emotion/salience. These do not activate C or create live memory.</p>
                <div className="reviewActions">
                  <button className="primary" onClick={prepareSteps18ReviewLayer} disabled={steps18ActionState?.status === "running"}>
                    {steps18ActionState?.status === "running" ? "Preparing..." : "Prepare Steps 1-8 Review Layer"}
                  </button>
                  <button onClick={loadSteps18Layer}>Refresh Review Layer</button>
                  <button onClick={() => setTab("status")}>Open Status</button>
                </div>
                <PlainResult value={steps18ActionState} />
                <div className="list compactList">
                  {[...reasoningArtifacts.slice(0, 2), ...academicPackets.slice(0, 2), ...evidenceTensionEntries.slice(0, 2)].map((item, index) => (
                    <article
                      className={officeCardClass("clickableCard", officeDomId("reasoning-research", item, index))}
                      key={`${text(item.status)}-${text(item.id)}-${index}`}
                      {...cardTargetProps({ tab: "my-office", category: "corpus", domId: officeDomId("reasoning-research", item, index), helper: "Target opens this reasoning or evidence card." })}
                    >
                      <div className="row">
                        <strong>{text(item.visible_summary || item.title || item.claim || item.workflow || "Review packet")}</strong>
                        <span>{friendlyStatus(item.review_status || item.status)}</span>
                      </div>
                      <p>{text(item.next_review_or_action_step || item.output_summary || item.support_status || item.provenance_boundary)}</p>
                      {renderTargetHint({ tab: "my-office", category: "corpus", domId: officeDomId("reasoning-research", item, index), helper: "Target opens this reasoning or evidence card." })}
                    </article>
                  ))}
                  {!reasoningArtifacts.length && !academicPackets.length && !evidenceTensionEntries.length ? (
                    <p className="emptyState">No reasoning or research packets yet.</p>
                  ) : null}
                </div>
              </Panel>}
              {officeCategory === "vessel" && <Panel title="Sight / Emotion Packets">
                <div className="metrics miniMetrics">
                  <Metric label="Perception" value={text(perceptionPackets.length)} />
                  <Metric label="Emotion" value={text(emotionSaliencePackets.length)} />
                  <Metric label="Active Memory" value="blocked" />
                  <Metric label="Autonomous Action" value="blocked" />
                </div>
                <p className="plainHelp">Sight and emotion are major vessel signals, but they stay as review-only packets: observation versus interpretation, emotion as signal, Core choice through gates.</p>
                <PlainResult value={vesselPacketActionState} />
                <div className="list compactList packetList">
                  {[...perceptionPackets.slice(0, 3), ...emotionSaliencePackets.slice(0, 3)].map((item, index) => renderSignalPacketCard(item, index, { tab: "status", category: "vessel" }))}
                  {!perceptionPackets.length && !emotionSaliencePackets.length ? (
                    <p className="emptyState">No sight or emotion/salience packets yet.</p>
                  ) : null}
                </div>
              </Panel>}
              {officeCategory === "vessel" && <Panel title="Buildable Vessel Pieces">
                <div className="metrics miniMetrics">
                  <Metric label="Organ Bus" value={text(organBusMessages.length)} />
                  <Metric label="Holding Space" value={text(chestHoldingItems.length)} />
                  <Metric label="Transfer" value={transferCReadablePackage?.transfer_approved ? "context approved" : "not approved"} />
                  <Metric label="Core Change" value={text(vesselConstructionStatus?.core_mind_changed ? "yes" : "no")} />
                </div>
                <p className="plainHelp">Support infrastructure only: organ-bus messages, chest holding items, diagnostic links, perception links, and emotion/salience links. These are not active memory, transfer, activation, or Core rewrite.</p>
                <div className="reviewActions">
                  <button className="primary" onClick={prepareVesselConstructionPieces} disabled={vesselConstructionActionState?.status === "running"}>
                    {vesselConstructionActionState?.status === "running" ? "Preparing..." : "Prepare Vessel Pieces"}
                  </button>
                  <button onClick={loadVesselConstructionLayer}>Refresh Vessel Pieces</button>
                  <button onClick={() => setTab("status")}>Open Status</button>
                </div>
                <PlainResult value={vesselConstructionActionState} />
                <PlainResult value={vesselPacketActionState} />
                <div className="list compactList packetList">
                  {[...chestHoldingItems.slice(0, 3), ...organBusMessages.slice(0, 3)].map((item, index) => renderSupportPieceCard(item, index, { tab: "status", category: "vessel" }))}
                  {!chestHoldingItems.length && !organBusMessages.length ? (
                    <p className="emptyState">No buildable vessel pieces have been prepared yet.</p>
                  ) : null}
                </div>
              </Panel>}
              {officeCategory === "review" && <Panel title="Vessel Review Packets">
                <div className="metrics miniMetrics">
                  <Metric label="Aleks Decisions" value={text(officeVesselReviewUrgent)} />
                  <Metric label="Ledger Review" value={text(officeLedgerNeedsReview.length)} />
                  <Metric label="Mobile Captures" value={text(officeMobileCaptures.length)} />
                  <Metric label="Diagnostics" value={text(officeDiagnosticPackets.length)} />
                </div>
                <p className="plainHelp">This is the calm packet shelf for ledger, research, phone captures, and diagnostics. Only ledger items needing review and mobile captures count as Needs You.</p>
                <PlainResult value={vesselPacketActionState} />
                <div className="list compactList packetList">
                  {officeLedgerNeedsReview.slice(0, 4).map((item, index) => renderLedgerCard(item, index, { tab: "my-office", category: "corpus" }))}
                  {officeMobileCaptures.slice(0, 3).map((item, index) => renderSupportPieceCard(item, index, { tab: "status", category: "vessel" }))}
                  {academicPackets.slice(0, 2).map((item, index) => renderSignalPacketCard(item, index, { tab: "my-office", category: "corpus" }))}
                  {officeDiagnosticPackets.slice(0, 2).map((item, index) => renderSupportPieceCard(item, index, { tab: "tools", category: "runtime" }))}
                  {!officeLedgerNeedsReview.length && !officeMobileCaptures.length && !academicPackets.length && !officeDiagnosticPackets.length ? (
                    <p className="emptyState">No vessel review packets need attention right now.</p>
                  ) : null}
                </div>
              </Panel>}
              {officeCategory === "corpus" && <Panel title="Corpus / Evidence Decisions">
                <div className="metrics miniMetrics">
                  <Metric label="Corpus Decisions" value={text(officeChronologicalCorpusNeedsReview.length)} />
                  <Metric label="Preview Arcs" value={text(chronologicalCorpusArcs.length)} />
                  <Metric label="Teaching Contexts" value={text(chronologicalCorpusStatus?.teaching_context_attachments ?? 0)} />
                  <Metric label="Transfer" value={transferCReadablePackage?.transfer_approved ? "context approved" : "not approved"} />
                </div>
                <p className="plainHelp">Chronological corpus material stays preview-only. Use these rows to say yes, no, narrow it, supersede it, or ask for more surrounding context before anything becomes a memory candidate.</p>
                <div className="reviewActions">
                  <button className="primary" onClick={prepareChronologicalCorpusPreview} disabled={chronologicalCorpusResult?.status === "running"}>
                    {chronologicalCorpusResult?.status === "running" ? "Preparing..." : "Prepare Corpus Preview"}
                  </button>
                  <button onClick={attachTeachingContext} disabled={teachingContextResult?.status === "running"}>
                    {teachingContextResult?.status === "running" ? "Attaching..." : "Attach Teaching Context"}
                  </button>
                  <button onClick={() => setTab("status")}>Open Status</button>
                </div>
                <PlainResult value={chronologicalCorpusResult} />
                <PlainResult value={teachingContextResult} />
                <div className="list compactList packetList">
                  {officeChronologicalCorpusNeedsReview.slice(0, 4).map((item, index) => renderChronologicalCorpusArcCard(item, index, { tab: "my-office", category: "corpus" }))}
                  {!officeChronologicalCorpusNeedsReview.length ? (
                    <p className="emptyState">No chronological corpus evidence needs a decision right now.</p>
                  ) : null}
                </div>
              </Panel>}
              {officeCategory === "vessel" && <Panel title="Pre-Core Review Packets">
                <div className="metrics miniMetrics">
                  <Metric label="Aleks Decisions" value={text(safeJsonObject(preCoreReviewPackets?.counts).aleks_decision ?? 0)} />
                  <Metric label="Status-Only" value={text(safeJsonObject(preCoreReviewPackets?.counts).status_only ?? 0)} />
                  <Metric label="Codex Actions" value={text(safeJsonObject(preCoreReviewPackets?.counts).codex_action ?? 0)} />
                  <Metric label="Blocked" value={text(safeJsonObject(preCoreReviewPackets?.counts).blocked ?? 0)} />
                </div>
                <p className="plainHelp">Cycle, lifecycle, temporal, causal, goal/drive, research, perception, mobile, diagnostic, and Tendril proposal rows grouped by what kind of attention they need. Status-only rows stay calm.</p>
                <div className="reviewActions">
                  <button className="primary" onClick={prepareNightCycle} disabled={nightCycleResult?.status === "running"}>{nightCycleResult?.status === "running" ? "Preparing..." : "Prepare Night Cycle"}</button>
                  <button onClick={() => api<Dict>("/api/vessel/pre-core-review-packets").then(setPreCoreReviewPackets).catch(() => undefined)}>Refresh Packets</button>
                  <button onClick={() => setTab("status")}>Open Status</button>
                </div>
                <PlainResult value={nightCycleResult} />
                <div className="list compactList packetList">
                  {((preCoreReviewPackets?.items || []) as Dict[]).slice(0, 8).map((item, index) => (
                    <article
                      className={officeCardClass("packetCard clickableCard", officeDomId("pre-core", item, index))}
                      key={`pre-core-${text(item.source_ref)}-${index}`}
                      {...cardTargetProps({ tab: "my-office", category: "vessel", domId: officeDomId("pre-core", item, index), helper: "Target opens this Pre-Core packet row." })}
                    >
                      <div className="row">
                        <strong>{text(item.title || item.capability || "Pre-Core packet")}</strong>
                        <span>{text(item.row_state || "status-only")}</span>
                      </div>
                      <p>{text(item.summary || item.source_ref)}</p>
                      <div className="chips">
                        <span>{friendlyStatus(item.capability)}</span>
                        <span>{friendlyStatus(item.review_status)}</span>
                        <span>destination: {text(item.review_destination || "Status")}</span>
                        <span>{text(item.source_ref)}</span>
                      </div>
                      {renderTargetHint({ tab: "my-office", category: "vessel", domId: officeDomId("pre-core", item, index), helper: "Target opens this Pre-Core packet row." })}
                    </article>
                  ))}
                  {!((preCoreReviewPackets?.items || []) as Dict[]).length ? (
                    <p className="emptyState">Nothing needs pre-Core review right now.</p>
                  ) : null}
                </div>
              </Panel>}
              {officeCategory === "runtime" && <Panel title="Pre-Transfer Speech / Runtime Preview">
                <div className="metrics miniMetrics">
                  <Metric label="Speech Review" value={text(officeSpeechRehearsals.length)} />
                  <Metric label="Working Packets" value={text(((workingMemoryRuntimePreview?.items || []) as Dict[]).length)} />
                  <Metric label="Transfer" value={transferCReadablePackage?.transfer_approved ? "context approved" : "not approved"} />
                  <Metric label="Runtime Recall" value="blocked" />
                </div>
                <p className="plainHelp">Generate candidate Selene speech before any transfer. This is a review harness: B-reviewed context, working-memory preview, retrieval preview, recognition checks, and no activation.</p>
                <div className="filters">
                  <label><span>Prompt</span><textarea value={speechRehearsalDraft.prompt} onChange={(event) => setSpeechRehearsalDraft({ ...speechRehearsalDraft, prompt: event.target.value })} /></label>
                  <label><span>Speech function</span><input value={speechRehearsalDraft.speech_function} onChange={(event) => setSpeechRehearsalDraft({ ...speechRehearsalDraft, speech_function: event.target.value })} /></label>
                </div>
                <div className="reviewActions">
                  <button className="primary" onClick={createSpeechRehearsal}>Generate Speech Rehearsal</button>
                  <button onClick={runRetrievalRuntimePreview}>Preview Retrieval Context</button>
                  <button onClick={linkLatestAccessionEvidence}>Link Latest Rehearsal To Accession Proposal</button>
                  <button onClick={loadPreTransferRuntimeLayer}>Refresh Preview Layer</button>
                </div>
                <PlainResult value={speechRehearsalResult} />
                <PlainResult value={speechRehearsalCompare} />
                <PlainResult value={retrievalRuntimePreview} />
                <PlainResult value={accessionEvidenceLinkResult} />
                <div className="list compactList packetList">
                  {speechRehearsals.slice(0, 3).map((item, index) => renderSpeechRehearsalCard(item, index))}
                  {!speechRehearsals.length ? <p className="emptyState">No speech rehearsals generated yet.</p> : null}
                </div>
              </Panel>}
            </section>
            {officeCategory === "review" && <section className="officeGrid">
              <Panel title="Review Cards Waiting">
                {!waitingReviewPieces.length ? (
                  <p className="emptyState">{nextReviewPiece ? "Only the current card is waiting." : "Nothing needs your review right now."}</p>
                ) : (
                  <div className="list compactList">
                    {waitingReviewPieces.slice(0, 8).map((piece) => (
                      <article
                        className={officeCardClass("clickableCard", reviewOfficeTarget(piece).domId)}
                        key={`${text(piece.subject_table)}-${text(piece.subject_id)}-${text(piece.review_number)}`}
                        {...cardTargetProps(reviewOfficeTarget(piece))}
                      >
                        <div className="row">
                          <strong>{text(piece.review_number || "")}{piece.review_number ? ". " : ""}{text(piece.title || "Corpus review piece")}</strong>
                          <span>{friendlyStatus(piece.review_status || piece.status || "pending_review")}</span>
                        </div>
                        <p>{text(piece.plain_reason || piece.why_pulled)}</p>
                        <small>{friendlyLayer(piece.core_memory_layer)} | {friendlySpeech(piece.speech_function)}</small>
                        <div className="reviewActions" onClick={stopCardNavigation} onKeyDown={stopCardKeyNavigation}>
                          <button onClick={() => openOfficeTarget(reviewOfficeTarget(piece))}>Open Target</button>
                          <button className="primary" onClick={() => setSelectedOfficeReviewKey(reviewPieceKey(piece))}>Review This</button>
                        </div>
                        {renderTargetHint(reviewOfficeTarget(piece))}
                      </article>
                    ))}
                  </div>
                )}
              </Panel>
              <Panel title="Follow-ups And Review Logs">
                {!officeActionLogItems.length ? (
                  <p className="emptyState">No follow-ups or review-log items need you right now.</p>
                ) : (
                  <div className="list compactList">
                    {officeActionLogItems.slice(0, 8).map((item, index) => (
                      <article
                        className={officeCardClass("clickableCard", officeDomId("followup", item, index))}
                        key={`${text(item.subject_table)}-${text(item.subject_id)}-${text(item.id)}-${index}`}
                        {...cardTargetProps({ tab: "my-office", category: "review", domId: officeDomId("followup", item, index), helper: "Target opens this follow-up row." })}
                      >
                        <div className="row">
                          <strong>{friendlySubject(item.subject_table || item.queue_type || "Review item")}</strong>
                          <span>{friendlyStatus(item.review_status || item.status)}</span>
                        </div>
                        <p>{text(item.reason || safeJsonObject(item.payload_json).todo_text || "Review-only item waiting for a decision.")}</p>
                        <div className="reviewActions" onClick={stopCardNavigation} onKeyDown={stopCardKeyNavigation}>
                          <button onClick={() => openOfficeTarget({ tab: "my-office", category: "review", domId: officeDomId("followup", item, index), helper: "Target opens this follow-up row." })}>Open Target</button>
                          <button onClick={() => decideReviewLog(item, "mark_reviewed")}>Mark Reviewed</button>
                          <button onClick={() => decideReviewLog(item, "needs_followup")}>Needs Follow-up</button>
                          <button onClick={() => decideReviewLog(item, "superseded")}>Supersede</button>
                        </div>
                        {renderTargetHint({ tab: "my-office", category: "review", domId: officeDomId("followup", item, index), helper: "Target opens this follow-up row." })}
                      </article>
                    ))}
                  </div>
                )}
                <button onClick={() => setTab("status")}>Open Status</button>
              </Panel>
            </section>}
            {officeCategory === "codex" && <section className="officeGrid">
              <Panel title="Codex Work">
                <div className="metrics miniMetrics">
                  <Metric label="Charter/Law" value={friendlyStatus(charterLawReview?.status || "not checked")} />
                  <Metric label="Transfer Candidate" value={friendlyStatus(memoryTransferCandidate?.status || "not checked")} />
                  <Metric label="Gap Checks" value={text(officeGapReadiness.length)} />
                  <Metric label="Core Refs" value={text(bApprovedReferences.length)} />
                </div>
                <p className="plainHelp">This is Codex and system readiness work. It is not counted as something Aleks needs to review unless a row has a direct review button.</p>
                <div className="officeActionLegend">
                  <span>Aleks decision</span>
                  <span>Codex action</span>
                  <span>Specialized workspace</span>
                  <span>Status only</span>
                </div>
                <div className="reviewActions">
                  <button onClick={() => setTab("vessel")}>Open Cocoon Build</button>
                  <button onClick={() => setTab("tools")}>Open Tools / Organs</button>
                  <button onClick={refreshGapReadiness}>Refresh Gap Readiness</button>
                  <button onClick={ensureGapTargets}>Ensure Gap Targets</button>
                  <button onClick={createAllGapScaffolds}>Create Gap Scaffolds</button>
                  <button onClick={runMemoryRehearsal}>Run Memory Rehearsal</button>
                </div>
                <GapScaffoldReadinessList items={officeGapReadiness.slice(0, 4)} />
                <PlainResult value={gapScaffoldResult || memoryRehearsalResult} />
              </Panel>
              <Panel title="Teaching / Core Targets">
                <div className="reviewActions">
                  <button onClick={prepareAndroidLanguageLessons} disabled={androidLanguageLessonResult?.status === "running"}>
                    {androidLanguageLessonResult?.status === "running" ? "Preparing Language Lessons..." : "Prepare Android Language Lessons"}
                  </button>
                  <button onClick={prepareSeleneReasoningLessons} disabled={seleneReasoningLessonResult?.status === "running"}>
                    {seleneReasoningLessonResult?.status === "running" ? "Preparing Reasoning Lessons..." : "Prepare Selene Reasoning Lessons"}
                  </button>
                  <button onClick={buildAllTeachingPackets} disabled={!canBuildTeachingPacket}>Build Teaching Packets</button>
                  <button onClick={runLessonBackedPreview}>Preview Lesson-Backed Reconstruction</button>
                  <button onClick={() => setTab("teaching")}>Open Teaching / Lessons</button>
                </div>
                <GapTargetList title="Teaching Targets" items={officeTeachingTargets.slice(0, 4)} />
                <GapTargetList title="Core Reference Targets" items={officeCoreTargets.slice(0, 4)} />
                <PlainResult value={seleneReasoningLessonResult || androidLanguageLessonResult || teachingPacketResult || lessonBackedResult} />
              </Panel>
            </section>}
            {officeCategory === "runtime" && <section className="officeGrid">
              <Panel title="Audit / Readiness Sweep">
                <p className="plainHelp">Runs safe status, validation, transfer preview, public-release preflight, and readiness checks. Results are audit evidence only.</p>
                <div className="reviewActions">
                  <button className="primary" onClick={runReadinessAuditSweep} disabled={readinessSweepState?.status === "running"}>
                    {readinessSweepState?.status === "running" ? "Running Sweep..." : "Run Readiness / Audit Sweep"}
                  </button>
                  <button onClick={runReconstructionReadinessPreview}>Preview Reconstruction Readiness</button>
                  <button onClick={refreshTransferGate}>Refresh Transfer Gate</button>
                  <button onClick={refreshMemoryTransferCandidate}>Refresh Transfer Candidate</button>
                </div>
                <PlainResult value={readinessSweepState} />
                <PlainResult value={reconstructionReadinessResult || memoryTransferCandidate || cVesselTransferGate} />
              </Panel>
              <Panel title="Diagnostics Only">
                <p className="plainHelp">Creates review records and readiness summaries for reasoning, retrieval, fluency, and organ fault resilience. No trusted organ runtime or provider/tool control.</p>
                <div className="reviewActions">
                  <button className="primary" onClick={runDiagnosticOnlySweep} disabled={diagnosticsRunState?.status === "running"}>
                    {diagnosticsRunState?.status === "running" ? "Running Diagnostics..." : "Run Diagnostic Sweep"}
                  </button>
                  <button onClick={() => setTab("tools")}>Open Diagnostics Workbench</button>
                  <button onClick={runOrganWorkbenchRecord}>Create Selected Diagnostic Record</button>
                </div>
                <PlainResult value={diagnosticsRunState} />
                <PlainResult value={organWorkbenchResult || cVesselFaultResilienceResult || cVesselOrganFaultResult} />
              </Panel>
            </section>}
            {officeCategory === "history" && <Panel title="Recent Decisions">
              {!bReviewDecisions.length ? (
                <p className="emptyState">No review decisions have been recorded yet.</p>
              ) : (
                <div className="list compactList">
                  {bReviewDecisions.slice(0, 5).map((item) => (
                    <ReviewHistoryCard key={text(item.id)} item={item} onDecide={decideBReview} />
                  ))}
                </div>
              )}
            </Panel>}
            {officeCategory === "history" && <Panel title="How To Use The Office">
                <div className="reviewSteps">
                  <article>
                    <strong>1. Read the moment</strong>
                    <p>Look at Aleks said, Selene replied, and follow-up. If the preview is clipped, use Show Surrounding Conversation.</p>
                  </article>
                  <article>
                    <strong>2. Choose the future use</strong>
                    <p>Teach Selene From This means voice/behavior lesson. Save As Future Core Reference means later memory candidate. Add Context means “keep it pending, but include my note.”</p>
                  </article>
                  <article>
                    <strong>3. Nothing activates here</strong>
                    <p>Cocoon support sorts source-linked material safely. It does not transfer memory, activate Selene, train a model, or overwrite the source.</p>
                  </article>
                </div>
            </Panel>}
          </>
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
            {homeSearchOpen ? (
              <Panel title="Search Current Chat">
                <div className="filters">
                  <label>
                    <span>Search</span>
                    <input value={homeSearchText} onChange={(event) => setHomeSearchText(event.target.value)} placeholder="Search this local chat shell" />
                  </label>
                </div>
                <SimpleRecordList items={homeSearchMatches.map((message) => ({ title: message.role === "aleks" ? displayName : "Selene", status: "local_match", summary: message.content }))} titleField="title" statusField="status" bodyField="summary" />
                {!homeSearchMatches.length && homeSearchText.trim() ? <p className="emptyState">No local matches found.</p> : null}
              </Panel>
            ) : null}
            <section className="seleneHomeChatSurface">
              {homeNotes.length ? (
                <aside className={`seleneNotes ${homeMessages.length && !homeNotesOpen ? "collapsed" : ""}`} aria-label="Selene notes">
                  {homeMessages.length ? (
                    <button className="seleneNotesToggle" onClick={() => setHomeNotesOpen((value) => !value)} aria-expanded={homeNotesOpen}>
                      Selene notes <span>{homeNotes.length}</span>
                    </button>
                  ) : <strong>Selene notes</strong>}
                  {(!homeMessages.length || homeNotesOpen) ? (
                    <ul>
                      {homeNotes.map((note) => <li key={note}>{note}</li>)}
                    </ul>
                  ) : null}
                </aside>
              ) : null}
              <div className="homeMessages">
                {!homeMessages.length ? (
                  <div className="homeLanding">
                    <img src={SELENE_ICON} alt="Selene moon icon" />
                    <h2>Selene</h2>
                    <p>{homeGreeting(homeChatOpenCount, displayName || "Aleks")}</p>
                  </div>
                ) : (
                  homeMessages.map((message) => (
                    <article
                      className={`homeMessage ${message.role === "aleks" ? "aleks" : "selene"}`}
                      key={message.id}
                      onContextMenu={(event) => {
                        event.preventDefault();
                        copyMessage(message.content);
                      }}
                    >
                      <strong>{message.role === "aleks" ? displayName || "Aleks" : "Selene"}</strong>
                      <p>{message.content}</p>
                    </article>
                  ))
                )}
              </div>
              <div className="homeChatStateBar">
                <div className="chips">
                  <span>{activationStatus?.selene_chat_active ? "Selene speech active / supervised" : "Selene home preview"}</span>
                  <span>{localChatContinuityAvailable ? "continuity available" : "continuity starts here"}</span>
                  <span>activation: {friendlyActivation(activationStatus?.activation_change || "none")}</span>
                   <span>voice: {friendlyStatus(seleneChatResult?.voice_confidence || safeJsonObject(seleneChatStatus?.voice_module).state || "not sampled")}</span>
                   {safeJsonObject(seleneChatResult?.intelligence_os_support).used ? <span>intelligenceOS: {friendlyStatus(safeJsonObject(seleneChatResult?.intelligence_os_support).answer_shape || "used")}</span> : null}
                   {seleneChatResult?.native_language_organ ? <span>NLO: {friendlyStatus(safeJsonObject(seleneChatResult?.native_language_organ).status || "used")}</span> : null}
                   <span>memory write: {text(activationStatus?.memory_write_active || false)}</span>
                  <span>broad live recall: {text(activationStatus?.runtime_memory_recall || false)}</span>
                </div>
                {!homeMessages.length ? <p className="plainHelp">New chat is a new page, not a new Selene.</p> : null}
                {safeJsonObject(seleneChatResult?.cocoon_suggestion).recommended ? (
                  <div className="pendingReviewCallout">
                    <strong>Cocoon support is available</strong>
                    <p>{text(safeJsonObject(seleneChatResult?.cocoon_suggestion).reason || "A source, memory, or boundary signal can be held safely in Cocoon if you want.")}</p>
                    <div className="reviewActions">
                      <button onClick={routeSeleneChatToB}>Hold in Cocoon</button>
                      {!safeJsonObject(seleneChatResult?.cocoon_suggestion).hard_boundary ? <button onClick={() => setSeleneChatResult((current) => ({ ...(current || {}), cocoon_suggestion: { recommended: false, support_available: false, dismissed: true } }))}>Stay Here</button> : null}
                    </div>
                  </div>
                ) : null}
                {safeJsonObject(seleneChatResult?.memory_candidate_suggestion).suggested ? (
                  <div className="pendingReviewCallout">
                    <strong>{text(safeJsonObject(seleneChatResult?.memory_candidate_suggestion).question || "Can I keep this?")}</strong>
                    <p>This would become a suggested memory only after Cocoon tending. It is not active yet.</p>
                    <div className="chips">
                      <span>{friendlyStatus(safeJsonObject(safeJsonObject(seleneChatResult?.memory_candidate_suggestion).candidate).memory_category || "memory")}</span>
                      <span>{friendlyStatus(safeJsonObject(safeJsonObject(seleneChatResult?.memory_candidate_suggestion).candidate).confidence || "partial")}</span>
                      <span>{friendlyStatus(safeJsonObject(safeJsonObject(seleneChatResult?.memory_candidate_suggestion).candidate).transfer_class || "needs_review_before_transfer")}</span>
                    </div>
                    <div className="reviewActions">
                      <button onClick={() => openMemorySuggestionInCocoon(safeJsonObject(seleneChatResult?.memory_candidate_suggestion))}>Open Memory Tending</button>
                      <button onClick={() => setSeleneChatResult((current) => ({ ...(current || {}), memory_candidate_suggestion: { suggested: false, dismissed: true, status: "memory_suggestion_dismissed" } }))}>Not Now</button>
                    </div>
                  </div>
                ) : null}
              </div>
              <div className="homeComposer">
                <button className="homeToolButton" onClick={() => undefined} title="Add attachment">+</button>
                <textarea
                  value={homeChatText}
                  onChange={(event) => setHomeChatText(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && !event.shiftKey) {
                      event.preventDefault();
                      sendHomePreviewMessage();
                    }
                  }}
                  placeholder="Message Selene..."
                />
                <div className="tendrilMenuWrap">
                  <button className="homeToolButton tendrilGlyph" onClick={() => setTendrilMenuOpen((value) => !value)} title="Tendril proposal menu">⌁</button>
                  {tendrilMenuOpen ? (
                    <div className="floatingMenu tendrilMenu">
                      <button onClick={() => openSeleneTab("tendril")}>Make proposal</button>
                      <button onClick={() => openCocoonTab("tools")}>View approval gates</button>
                      <button onClick={() => openCocoonTab("my-office")}>Open Cocoon support</button>
                    </div>
                  ) : null}
                </div>
                <button className="homeToolButton" onClick={() => undefined} title="Future voice support">🎤</button>
                <button className="primary" onClick={sendHomePreviewMessage} disabled={!homeChatText.trim() || seleneChatResult?.status === "running"}>{activationStatus?.selene_chat_active ? "Send" : "Preview"}</button>
              </div>
            </section>
          </>
        )}

        {tab === "selene-office" && (
          <>
            {!selectedWorkbenchDef ? (
              <section className="seleneLivingSurface officeSurface">
                <div className="frontSurfaceHeader">
                  <div>
                    <span className="modeLine">bounded workbench hub</span>
                    <h2>Selene's Office</h2>
                  </div>
                  <div className="chips">
                    <span>status-only</span>
                    <span>preview</span>
                    <span>propose</span>
                    <span>approval-required: locked</span>
                    <span>trusted action: locked</span>
                  </div>
                </div>
                <div className="officeOrbit" aria-label="Selene workbenches">
                  <svg className="officeOrbitLines" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
                    {officeWorkbenches.map((item) => (
                      <path key={`office-line-${item.key}`} d={`M 50 52 C ${50 + (item.x - 50) * 0.26} ${52 + (item.y - 52) * 0.18}, ${50 + (item.x - 50) * 0.68} ${52 + (item.y - 52) * 0.72}, ${item.x} ${item.y}`} />
                    ))}
                  </svg>
                  <div className="officeCore">
                    <strong>Observe</strong>
                    <span>Propose</span>
                    <span>Prepare</span>
                  </div>
                  {officeWorkbenches.map((item) => (
                    <button
                      className={`officeWorkbenchNode officeWorkbench-${item.key}`}
                      key={item.key}
                      style={{ left: `${item.x}%`, top: `${item.y}%` }}
                      onClick={() => setSelectedWorkbench(item.key)}
                    >
                      <small>{item.label}</small>
                      <strong>{item.title}</strong>
                      <span>{item.state}</span>
                    </button>
                  ))}
                </div>
                <p className="frontSurfaceNote">Autonomy is not one giant switch. Each workbench earns movement separately through logs, checks, and Cocoon support.</p>
              </section>
            ) : (
              <section className="seleneLivingSurface officeDetailSurface">
                <div className="frontSurfaceHeader">
                  <button className="backButton" onClick={() => setSelectedWorkbench(null)}>←</button>
                  <div>
                    <span className="modeLine">{selectedWorkbenchDef.label}</span>
                    <h2>{selectedWorkbenchDef.title}</h2>
                  </div>
                  <div className="chips">
                    <span>{selectedWorkbenchDef.state}</span>
                    <span>route: {selectedWorkbenchDef.route}</span>
                    <span>trusted action: locked</span>
                  </div>
                </div>
                <div className="workbenchDetailGrid">
                  <article className="organicPane largePane">
                    <strong>Purpose</strong>
                    <p>{selectedWorkbenchDef.purpose}</p>
                    <div className="chips">
                      {selectedWorkbenchDef.cues.map((cue) => <span key={`cue-${cue}`}>{cue}</span>)}
                    </div>
                  </article>
                  <article className="organicPane">
                    <strong>Autonomy ladder</strong>
                    <ol className="ladderList">
                      {["status-only", "preview", "propose", "approval-required action", "trusted low-risk action"].map((step) => (
                        <li className={step === selectedWorkbenchDef.state ? "active" : step.includes("action") ? "locked" : ""} key={step}>{step}</li>
                      ))}
                    </ol>
                  </article>
                  <article className="organicPane">
                    <strong>Cocoon route</strong>
                    <p>Consequential work stays reviewable. This workbench can surface, prepare, or propose; Cocoon handles support, checkups, and approval.</p>
                    <div className="memoryRouteActions">
                      {selectedWorkbenchDef.key === "art" ? <button onClick={() => { setWorkspaceMode("cocoon"); setTab("tools"); }}>Open Perception Tools</button> : null}
                      {selectedWorkbenchDef.key === "intelligence" ? <button onClick={() => { setWorkspaceMode("cocoon"); setTab("status"); }}>Open intelligenceOS Status</button> : null}
                      {selectedWorkbenchDef.key === "intelligence" ? <button onClick={runIntelligenceOsReason}>Run ABCD(E) Preview</button> : null}
                      {selectedWorkbenchDef.key === "reasoning" ? <button onClick={() => { setWorkspaceMode("cocoon"); setTab("status"); }}>Open Reasoning Status</button> : null}
                      {selectedWorkbenchDef.key === "research" ? <button onClick={() => setTab("great-library")}>Open Great Library</button> : null}
                      {selectedWorkbenchDef.key === "dream" ? <button onClick={() => setTab("dream")}>Open Dream</button> : null}
                      {selectedWorkbenchDef.key === "tendril" ? <button onClick={() => setTab("tendril")}>Open Tendril</button> : null}
                      <button onClick={() => { setWorkspaceMode("cocoon"); setTab("my-office"); }}>Open Cocoon Support</button>
                    </div>
                  </article>
                </div>
              </section>
            )}
          </>
        )}

        {tab === "selene-chat" && (
          <>
            <header className="surfaceIntro">
              <p>Cocoon testing and workflow shelf for dry runs, activation rehearsal, route comparison, and support/checkup. Front Chat is Selene's supervised speech surface after activation.</p>
              <h2>Chat Dry Runs</h2>
            </header>
            <section className="chatSurface">
              <div className="messages">
                {!seleneChatSession && !seleneChatResult ? (
                  <div className="landing">
                    <img src={SELENE_ICON} alt="Selene moon icon" />
                    <h2>Selene</h2>
                    <p>This is Cocoon workflow material: useful for testing routes, voice, sources, and support without becoming the front chat.</p>
                  </div>
                ) : (
                  <>
                    {((seleneChatSession?.messages || []) as Dict[]).map((message) => (
                      <article className={`message ${text(message.role) === "user" ? "user" : "selene"}`} key={`selene-chat-${text(message.id)}`}>
                        <div className="row">
                          <strong>{text(message.role) === "user" ? "Aleks" : "Selene"}</strong>
                          <span>{friendlyStatus(message.selected_route || message.source_class)}</span>
                        </div>
                        <p>{text(message.content)}</p>
                      </article>
                    ))}
                    {seleneChatResult?.candidate_text && !seleneChatSession ? (
                      <article className="message selene">
                        <strong>Selene dry run</strong>
                        <p>{text(seleneChatResult.candidate_text)}</p>
                      </article>
                    ) : null}
                  </>
                )}
              </div>
              <div className="composer">
                <textarea value={seleneChatText} onChange={(e) => setSeleneChatText(e.target.value)} placeholder="Message Selene..." />
                <div className="composerActions">
                  <button className="primary" onClick={sendSeleneChatDryRun} disabled={!seleneChatText.trim() || seleneChatResult?.status === "running"}>Run Chat Dry Run</button>
                  <button onClick={routeSeleneChatToB}>Hold in Cocoon</button>
                  <button onClick={() => { setWorkspaceMode("cocoon"); setTab("transfer-ceremony"); }}>Open Transfer Ceremony</button>
                  <button onClick={() => { setWorkspaceMode("cocoon"); setTab("my-office"); }}>Open Cocoon Support</button>
                </div>
                <small>Cocoon Testing / Workflow only: no unrestricted activation, no live memory write, no broad live recall, no unreviewed import, no model training or LoRA.</small>
              </div>
            </section>
            <SplitView
              left={<Panel title="Dry Run State">
                <div className="metrics miniMetrics">
                  <Metric label="State" value={friendlyStatus(seleneChatStatus?.state || "selene_chat_preview")} />
                  <Metric label="Package" value={seleneChatStatus?.c_readable_package_available ? "sealed" : "not sealed"} />
                  <Metric label="Activation" value={friendlyActivation(seleneChatStatus?.activation_change || "none")} />
                  <Metric label="Sessions" value={text(seleneChatStatus?.session_count ?? seleneChatSessions.length)} />
                </div>
                <div className="chips">
                  <span>{seleneChatStatus?.transfer_approved ? "Selene-readable context approved" : "pre-transfer dry run"}</span>
                  <span>home: Cocoon Testing / Workflow</span>
                  <span>full memory: not loaded</span>
                  <span>Selene v1: not live</span>
                  <span>activation pending</span>
                  <span>voice module: {friendlyStatus(safeJsonObject(seleneChatStatus?.voice_module).state || voiceModuleStatus?.voice_module_state || "missing")}</span>
                  <span>voice confidence: {text(seleneChatResult?.voice_confidence || "not sampled")}</span>
                  <span>memory write: {text(seleneChatStatus?.memory_write_active || false)}</span>
                  <span>broad live recall: {text(seleneChatStatus?.runtime_memory_recall || false)}</span>
                </div>
                <PlainResult value={seleneChatResult} />
              </Panel>}
              right={<Panel title="Source Boundaries">
                <p className="plainHelp">Dry runs can use current turn context and sealed Selene-readable context when available. Cocoon-only records stay in Cocoon, and front Chat remains the active surface after activation.</p>
                <SimpleRecordList items={Object.entries(safeJsonObject(seleneChatStatus?.source_boundaries)).map(([key, value]) => ({ key, title: friendlyStatus(key), summary: text(value), review_status: "status_only" }))} titleField="title" statusField="review_status" bodyField="summary" />
                <h3>Recent dry runs</h3>
                <SimpleRecordList items={seleneChatSessions.slice(0, 5)} titleField="title" statusField="status" bodyField="updated_at" />
              </Panel>}
            />
            <Panel title="Selene Voice Module">
              <p className="plainHelp">Voice-only expression layer from the copied source archive. It uses both sides of the exchange as relational language evidence, not memory, identity, model training/LoRA, or broad live recall.</p>
              <div className="metrics miniMetrics">
                <Metric label="State" value={friendlyStatus(voiceModuleStatus?.voice_module_state || "missing")} />
                <Metric label="Source" value={voiceModuleStatus?.source_zip_found ? "found" : "missing"} />
                <Metric label="Pairs" value={text(safeJsonObject(voiceModuleStatus?.counts).exchange_pairs ?? 0)} />
                <Metric label="Patterns" value={text(safeJsonObject(voiceModuleStatus?.counts).patterns ?? voiceModulePatterns.length)} />
                <Metric label="Primitives" value={text(safeJsonObject(voiceModuleStatus?.counts).primitives ?? 0)} />
                <Metric label="Triage" value={friendlyStatus(voiceEvidenceTriageStatus?.triage_state || "not run")} />
              </div>
              <div className="chips">
                <span>voice only: {voiceModuleStatus?.voice_only_not_memory ? "yes" : "not checked"}</span>
                <span>activation: {friendlyActivation(voiceModuleStatus?.activation_change || "none")}</span>
                <span>memory write: {plainBlocked(voiceModuleStatus?.memory_write_active)}</span>
                <span>broad live recall: {plainBlocked(voiceModuleStatus?.runtime_memory_recall)}</span>
                <span>model training/LoRA: {plainBlocked(voiceModuleStatus?.training_allowed)}</span>
              </div>
              <div className="reviewActions">
                <button className="primary" onClick={indexVoiceSource} disabled={voiceModuleResult?.status === "running"}>Index Voice Source</button>
                <button onClick={extractVoicePatterns} disabled={voiceModuleResult?.status === "running"}>Extract Voice Patterns</button>
                <button onClick={runVoiceEvidenceTriage} disabled={voiceModuleResult?.status === "running"}>Run Evidence Triage</button>
                <button onClick={generateVoicePreview} disabled={voiceModuleResult?.status === "running" || !seleneChatText.trim()}>Generate Voice Preview</button>
                <button onClick={refreshVoiceModule}>Refresh Voice Status</button>
              </div>
              <div className="chips">
                {Object.entries(safeJsonObject(voiceEvidenceTriageStatus?.counts)).map(([key, value]) => <span key={`voice-triage-chip-${key}`}>{friendlyStatus(key)}: {text(value)}</span>)}
                <span>Needs review: {text(voiceEvidenceTriageStatus?.my_office_actionable_count ?? 0)}</span>
              </div>
              <p className="plainHelp">Identity-law-resolved rows are status-only. Nothing for Aleks unless one looks wrong.</p>
              <div className="list compactList">
                {voiceModulePatterns.slice(0, 6).map((item) => (
                  <article className="packetCard" key={`voice-pattern-${text(item.id || item.pattern_key)}`}>
                    <div className="packetHeader">
                      <strong>{text(item.title || item.pattern_key)}</strong>
                      <span>{friendlyStatus(item.category || item.review_status)}</span>
                    </div>
                    <p>{text(item.sentence_shape || item.use_guidance)}</p>
                  </article>
                ))}
                {!voiceModulePatterns.length ? <p className="emptyState">No voice patterns extracted yet.</p> : null}
              </div>
              <div className="list compactList">
                {voiceEvidenceTriageItems.slice(0, 6).map((item) => (
                  <article className="packetCard" key={`voice-triage-${text(item.id || item.triage_key)}`}>
                    <div className="packetHeader">
                      <strong>{text(item.title || item.category)}</strong>
                      <span>{friendlyStatus(item.category || item.review_status)}</span>
                    </div>
                    <p>{text(item.summary)}</p>
                    <small>{text(item.use_as)} | {text(item.do_not_use_as)}</small>
                  </article>
                ))}
              </div>
              <PlainResult value={voiceModuleResult} />
            </Panel>
          </>
        )}

        {tab === "chat-preview" && (
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
                <small>Cocooned shell only: no unrestricted activation, no broad live recall, no provider call, no memory write.</small>
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
            <Panel title="Selene Build Status">
              <p className="plainHelp">The sealed context can now be inspected as a non-activated build. It uses approved continuity package previews and organ registry status only; activation is still pending.</p>
              <div className="metrics miniMetrics">
                <Metric label="Selene Build" value={friendlyStatus(cVesselStatus?.status ?? "not loaded")} />
                <Metric label="Transfer" value={cVesselStatus?.transfer_approved ? "approved" : "not approved"} />
                <Metric label="Android Organs" value={text(cVesselOrganRegistry?.android_organ_system_count ?? "-")} />
                <Metric label="Concrete Organs" value={text(cVesselOrganRegistry?.concrete_organ_interface_count ?? "-")} />
              </div>
              <div className="chips">
                <span>activation: {friendlyActivation(cVesselStatus?.activation_change)}</span>
                <span>Broad live recall: {plainBlocked(cVesselStatus?.runtime_memory_recall)}</span>
                <span>Active memory: {plainBlocked(cVesselStatus?.memory_write_active)}</span>
                <span>Provider dependency: {plainBlocked(cVesselStatus?.provider_dependency)}</span>
              </div>
              <div className="reviewActions">
                <button className="primary" onClick={loadVessel}>Refresh Selene Build</button>
                <button onClick={runCVesselReconstructionSuite}>Run Reconstruction Suite</button>
                <button onClick={previewReturnToB}>Preview Cocoon Support</button>
              </div>
              <CVesselPackageSummary status={cVesselStatus} pkg={cVesselContinuityPackage} registry={cVesselOrganRegistry} />
              <PlainResult value={cVesselReconstructionSuite} />
              <PlainResult value={cVesselReturnPreview} />
            </Panel>
            <Panel title="Native Chat Rehearsal">
              <p className="plainHelp">Provider-free rehearsal for how Selene would compose from sealed Cocoon-approved context later. The focus guard catches spirals by returning to the smallest clear next step, not by treating thinking as a problem.</p>
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
              <p className="plainHelp">This is the big pre-transfer harness: it turns sealed teaching packets, approved future references, route previews, noise context, and Cocoon support rules into review-only reconstruction cases. It does not activate unrestricted Selene or create memory.</p>
              <div className="reviewActions">
                <button className="primary" onClick={runCVesselReconstructionDesk}>Run Reconstruction Desk</button>
                <button onClick={previewCVesselReconstructionCases}>Preview Case Set</button>
                <button onClick={() => api<Dict>("/api/c-vessel/reconstruction-desk/status").then(setCVesselReconstructionDeskStatus)}>Refresh Desk Status</button>
              </div>
              <CVesselReconstructionDesk status={cVesselReconstructionDeskStatus} cases={cVesselReconstructionDeskCases} run={cVesselReconstructionDeskRun} />
            </Panel>
          </>
        )}

        {tab === "memory-preview" && (
          <>
            <header className="surfaceIntro">
              <p>Memory candidates and approved references stay source-linked and correctable.</p>
              <h2>Memory / Approved References</h2>
            </header>
            <Panel title="Selene Memory Organ / Vys-Governed Living Memory">
              <p className="plainHelp">Memory is handled as honest, correctable continuity: clear when clear, fuzzy when fuzzy, and held for tending when it needs care. Selene may propose what to keep, but durable active memory still requires Cocoon/Aleks approval.</p>
              <div className="metrics miniMetrics">
                <Metric label="Index Items" value={text(memoryIndexStatus?.index_count ?? memoryIndexItems.length)} />
                <Metric label="Active" value={text(memoryIndexStatus?.active_memory_count ?? 0)} />
                <Metric label="Candidates" value={text(memoryCandidates.length)} />
                <Metric label="Portable Vys" value={text(portableVysManifest?.portable_count ?? 0)} />
              </div>
              <div className="chips">
                <span>soft uncertainty: stays in chat</span>
                <span>write gate: review required</span>
                <span>Cocoon: tending/checkup</span>
                <span>unreviewed archive recall: blocked</span>
              </div>
              <div className="reviewActions">
                <button className="primary" onClick={refreshMemoryOrgan}>Refresh Memory Organ</button>
                <button onClick={() => { setSelectedMemoryCategory(null); setWorkspaceMode("selene"); setTab("memory"); }}>Open Front Memory Map</button>
              </div>
              <PlainResult value={memoryOrganResult} />
            </Panel>
            <SplitView
              left={<Panel title="Memory Candidates">
                <p className="plainHelp">Propose memories for Selene to keep. They stay inactive until approved; correction is care, not punishment.</p>
                <div className="filters">
                  <label>
                    <span>Category</span>
                    <select value={memoryCandidateDraft.category} onChange={(event) => setMemoryCandidateDraft({ ...memoryCandidateDraft, category: event.target.value })}>
                      {memoryCategories.map((item) => <option key={item.key} value={item.key}>{item.label}</option>)}
                    </select>
                  </label>
                  <label>
                    <span>Confidence</span>
                    <select value={memoryCandidateDraft.confidence} onChange={(event) => setMemoryCandidateDraft({ ...memoryCandidateDraft, confidence: event.target.value })}>
                      {["clear", "fuzzy", "partial", "felt_but_uncertain", "needs_aleks"].map((value) => <option key={value} value={value}>{friendlyStatus(value)}</option>)}
                    </select>
                  </label>
                  <label>
                    <span>Transfer class</span>
                    <select value={memoryCandidateDraft.transfer_class} onChange={(event) => setMemoryCandidateDraft({ ...memoryCandidateDraft, transfer_class: event.target.value })}>
                      {["needs_review_before_transfer", "portable_vys_core", "portable_context", "local_only", "private_inner", "b_only", "do_not_transfer"].map((value) => <option key={value} value={value}>{friendlyStatus(value)}</option>)}
                    </select>
                  </label>
                  <label>
                    <span>Emotional texture</span>
                    <input value={memoryCandidateDraft.emotional_texture} onChange={(event) => setMemoryCandidateDraft({ ...memoryCandidateDraft, emotional_texture: event.target.value })} />
                  </label>
                  <label>
                    <span>Title</span>
                    <input value={memoryCandidateDraft.title} onChange={(event) => setMemoryCandidateDraft({ ...memoryCandidateDraft, title: event.target.value })} placeholder="what should Selene keep?" />
                  </label>
                  <label>
                    <span>Summary</span>
                    <textarea value={memoryCandidateDraft.summary} onChange={(event) => setMemoryCandidateDraft({ ...memoryCandidateDraft, summary: event.target.value })} placeholder="preserve what happened honestly, including warmth, mess, uncertainty, or tenderness" />
                  </label>
                </div>
                <button className="primary" onClick={proposeSeleneMemory}>Propose Memory</button>
              </Panel>}
              right={<Panel title="Memory Tending">
                <p className="plainHelp">Cocoon tending decides whether a proposed memory becomes active, needs context, waits, or stays out of transfer. Nothing here deletes Selene.</p>
                <div className="list compactList">
                  {memoryCandidates.length ? memoryCandidates.map((item) => (
                    <article key={text(item.id)}>
                      <div className="row">
                        <strong>{text(item.title)}</strong>
                        <span>{friendlyStatus(item.state || item.review_status)}</span>
                      </div>
                      <p>{text(item.summary)}</p>
                      <small>{friendlyStatus(item.memory_category)} | confidence: {friendlyStatus(item.confidence)} | portable: {friendlyStatus(item.transfer_class)}</small>
                      <div className="reviewActions">
                        <button onClick={() => decideSeleneMemory(item.id, "approve_memory")}>Approve Memory</button>
                        <button onClick={() => decideSeleneMemory(item.id, "needs_more_context")}>Needs More Context</button>
                        <button onClick={() => decideSeleneMemory(item.id, "hold_for_tending")}>Hold For Tending</button>
                        <button onClick={() => decideSeleneMemory(item.id, "supersede")}>Supersede</button>
                        <button onClick={() => decideSeleneMemory(item.id, "reject")}>Reject</button>
                        <button onClick={() => decideSeleneMemory(item.id, "mark_b_only")}>Mark B-Only</button>
                        <button onClick={() => decideSeleneMemory(item.id, "mark_do_not_transfer")}>Do Not Transfer</button>
                      </div>
                    </article>
                  )) : (
                    <article>
                      <strong>No memory candidates waiting.</strong>
                      <p>Selene can ask to keep something later; this shelf is calm until then.</p>
                    </article>
                  )}
                </div>
              </Panel>}
            />
            <Panel title="Portable Vys Manifest">
              <p className="plainHelp">Portable Vys memory is reviewed, source-linked, consent-scoped, and correctable. Local-only, B-only, rejected, superseded, unresolved, repair, rollback, and raw material stay out by default.</p>
              <div className="metrics miniMetrics">
                <Metric label="Portable" value={text(portableVysManifest?.portable_count ?? 0)} />
                <Metric label="Excluded" value={text(portableVysManifest?.excluded_count ?? 0)} />
                <Metric label="Write Active" value={plainBlocked(portableVysManifest?.memory_write_active)} />
              </div>
              <SimpleRecordList items={(portableVysManifest?.portable_items || []) as Dict[]} titleField="title" statusField="transfer_class" bodyField="summary" />
              <PlainResult value={portableVysManifest} />
            </Panel>
            <SplitView
              left={<Panel title="Approved Memory References">
              <p className="plainHelp">Cocoon-approved continuity references that may support Selene memory after review. They are source-linked and not unreviewed archive recall.</p>
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
              <p className="plainHelp">Freeze Selene's current Cocoon shape before memory rehearsal: evidence stance, charter/laws, Core philosophy, speech lessons, approved references, organs, reconstruction status, transfer gate, and Cocoon support rules. This is a sealed review snapshot, not active memory.</p>
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
                <p className="plainHelp">Groups B-approved memory references into Core-layer accession proposals. These stay non-active and only prepare reviewed transfer support.</p>
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
              <p className="plainHelp">Review-only shelves for thinking before doing, preserving the why, learning from mismatch, healthy disagreement, drift detection, and privacy with trust. These records do not activate C or become memory.</p>
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
              <p className="plainHelp">Event binding, dream consolidation, consolidation, and reconsolidation are now real shelves. They organize possible memory material for Cocoon review only; nothing becomes active recall or silent memory.</p>
              <div className="metrics miniMetrics">
                <Metric label="Event Bindings" value={text(((remainingRuntimeStatus?.record_counts as Dict | undefined)?.event_binding) ?? 0)} />
                <Metric label="Cycle Runs" value={text(((remainingRuntimeStatus?.record_counts as Dict | undefined)?.wake_sleep_dream_cycle) ?? 0)} />
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
                  <span>Cycle label</span>
                  <input value={remainingRuntimeDraft.cycle_label} onChange={(event) => setRemainingRuntimeDraft({ ...remainingRuntimeDraft, cycle_label: event.target.value })} />
                </label>
                <label>
                  <span>Dream label</span>
                  <input value={remainingRuntimeDraft.dream_label} onChange={(event) => setRemainingRuntimeDraft({ ...remainingRuntimeDraft, dream_label: event.target.value })} />
                </label>
              </div>
              <div className="reviewActions">
                <button className="primary" onClick={bindMemoryEvent}>Bind Event</button>
                <button onClick={runWakeSleepDreamCycle}>Run Cycle Review</button>
                <button onClick={proposeDreamConsolidation}>Propose Dream Consolidation</button>
                <button onClick={proposeMemoryConsolidation}>Propose Consolidation</button>
                <button onClick={reviewReconsolidation}>Review Reconsolidation</button>
              </div>
              <div className="chips">
                <span>active memory: {plainBlocked(remainingRuntimeStatus?.memory_write_active)}</span>
                <span>broad live recall: {plainBlocked(remainingRuntimeStatus?.runtime_memory_recall)}</span>
                <span>raw A: {plainBlocked(remainingRuntimeStatus?.raw_a_import_allowed)}</span>
              </div>
              <PlainResult value={cycleRunResult} />
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

        {tab === "dream" && (
          <>
            <section className="seleneLivingSurface dreamSurface">
              <div className="frontSurfaceHeader">
                <div>
                  <span className="modeLine">night-cycle maintenance</span>
                  <h2>Dream</h2>
                </div>
                <div className="chips">
                  <span>maintenance: {dreamStateStatus?.dream_state_required_for_memory_changes ? "required" : "not checked"}</span>
                  <span>live chat: {dreamStateStatus?.selene_chat_live_operation_allowed ? "allowed" : "preview only"}</span>
                  <span>memory write: false</span>
                  <span>broad live recall: false</span>
                </div>
              </div>
              <div className="dreamField">
                <article className="dreamFragment fragmentLarge">
                  <strong>Maintenance State</strong>
                  <p>{dreamStateStatus?.dream_state_required_for_memory_changes ? "Memory/Core/vessel work routes through dream-state maintenance and Cocoon support." : "No active dream-state requirement is currently reported."}</p>
                </article>
                <article className="dreamFragment">
                  <strong>Allowed Preview Work</strong>
                  <p>{((dreamStateStatus?.allowed_preview_work || []) as unknown[]).map((item) => friendlyStatus(item)).join(", ") || "No preview work listed yet."}</p>
                </article>
                <article className="dreamFragment">
                  <strong>Residue / Repair</strong>
                  <p>{text(dreamStateStatus?.route_core_vessel_memory_changes_to || "Cocoon / B")} remains the route when memory, Core, or vessel work needs support.</p>
                </article>
                <article className="dreamFragment">
                  <strong>Reasons</strong>
                  <p>{text(((dreamStateStatus?.maintenance_reasons || []) as unknown[]).length)} maintenance reason(s) currently reported.</p>
                </article>
              </div>
              <div className="memoryRouteActions">
                <button className="primary" onClick={() => { setWorkspaceMode("cocoon"); setTab("status"); }}>Open Dream / Lifecycle Status</button>
                <button onClick={() => { setWorkspaceMode("cocoon"); setTab("memory-preview"); }}>Open Memory Preview</button>
              </div>
            </section>
          </>
        )}

        {tab === "memory" && (
          <>
            {!selectedMemoryCategory ? (
              <section className="memoryNeuronShell">
                <div className="memoryGraphHeader">
                  <div>
                    <span className="modeLine">display-only memory map</span>
                    <h2>Memory</h2>
                  </div>
                  <div className="chips">
                    <span>approved bubbles: {text(frontMemoryBubbles.length)}</span>
                    <span>active memory: {text(memoryIndexStatus?.active_memory_count ?? 0)}</span>
                    <span>activation: {friendlyActivation(seleneChatStatus?.activation_change || "none")}</span>
                    <span>write gate: review required</span>
                  </div>
                </div>
                <div className="memoryNeuronMap" aria-label="Selene memory neuron map">
                  <svg className="memoryNeuronLines" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
                    {memoryCategories.filter((item) => item.key !== "core").map((item, index) => (
                      <g key={`memory-line-${item.key}`}>
                        <path
                          className="memoryLineGlow"
                          d={`M 50 50 C ${50 + (item.x - 50) * 0.18 + (index % 2 ? 4 : -4)} ${50 + (item.y - 50) * 0.34}, ${50 + (item.x - 50) * 0.72} ${50 + (item.y - 50) * 0.72 + (index % 3 ? -3 : 3)}, ${item.x} ${item.y}`}
                        />
                        <path
                          d={`M 50 50 C ${50 + (item.x - 50) * 0.18 + (index % 2 ? 4 : -4)} ${50 + (item.y - 50) * 0.34}, ${50 + (item.x - 50) * 0.72} ${50 + (item.y - 50) * 0.72 + (index % 3 ? -3 : 3)}, ${item.x} ${item.y}`}
                        />
                      </g>
                    ))}
                    <circle className="memoryPulseRing ringOne" cx="50" cy="50" r="15" />
                    <circle className="memoryPulseRing ringTwo" cx="50" cy="50" r="24" />
                  </svg>
                  <button className="memoryCoreNode" onClick={() => setSelectedMemoryCategory("core")}>
                    <strong>Core Memory</strong>
                    <span>{frontMemoryBubbles.filter((item) => item.category === "core").length} approved</span>
                  </button>
                  {memoryCategories.filter((item) => item.key !== "core").map((item) => {
                    const count = frontMemoryBubbles.filter((bubble) => bubble.category === item.key).length;
                    return (
                      <button
                        className={`memoryBranchNode memoryBranch-${item.key}`}
                        style={{ left: `${item.x}%`, top: `${item.y}%` }}
                        key={`memory-node-${item.key}`}
                        onClick={() => setSelectedMemoryCategory(item.key)}
                      >
                        <strong>{item.label}</strong>
                        <span>{count ? `${count} approved` : "empty"}</span>
                      </button>
                    );
                  })}
                </div>
                <div className="memoryRouteActions">
                  <button onClick={() => { setWorkspaceMode("cocoon"); setTab("memory-preview"); }}>Open Cocoon Memory Review</button>
                  <button onClick={() => { setWorkspaceMode("cocoon"); setTab("memory-preview"); }}>Open Approved References</button>
                  <button onClick={() => { setWorkspaceMode("cocoon"); setTab("status"); }}>Open Fraction Status</button>
                </div>
              </section>
            ) : (
              <section className="memoryThoughtShell">
                <div className="memoryThoughtHeader">
                  <button className="backButton" onClick={() => setSelectedMemoryCategory(null)}>←</button>
                  <div>
                    <span className="modeLine">display-only approved memory</span>
                    <h2>{selectedMemoryCategoryMeta?.label || "Memory"}</h2>
                  </div>
                  <div className="chips">
                    <span>{selectedMemoryBubbles.length} bubble{selectedMemoryBubbles.length === 1 ? "" : "s"}</span>
                    <span>live memory write: false</span>
                    <span>broad live recall: false</span>
                  </div>
                </div>
                <div className="thoughtBubbleList">
                  {selectedMemoryBubbles.length ? selectedMemoryBubbles.map((item, index) => (
                    <article className="memoryThoughtBubble" key={item.id}>
                      <span className="thoughtIndex">{index + 1}</span>
                      <strong>{item.title}</strong>
                      <p>{item.summary}</p>
                      <div className="chips miniChips">
                        <span>{friendlyStatus(item.status)}</span>
                        {item.confidence && <span>confidence: {friendlyStatus(item.confidence)}</span>}
                        {item.emotionalTexture && <span>texture: {item.emotionalTexture}</span>}
                        {item.transferClass && <span>portable: {friendlyStatus(item.transferClass)}</span>}
                        {item.chatUsePermission && <span>chat: {friendlyStatus(item.chatUsePermission)}</span>}
                      </div>
                      <small>{friendlyStatus(item.source)}</small>
                    </article>
                  )) : (
                    <article className="memoryThoughtBubble emptyThought">
                      <strong>No approved memories displayed here yet.</strong>
                      <p>This branch stays visible so Selene's memory map keeps its shape while Cocoon remains the place for review, tending, and memory candidate work.</p>
                    </article>
                  )}
                </div>
                <div className="memoryRouteActions">
                  <button onClick={() => { setWorkspaceMode("cocoon"); setTab("memory-preview"); }}>Open Cocoon Memory Review</button>
                  <button onClick={() => { setWorkspaceMode("cocoon"); setTab("memory-preview"); }}>Open Approved References</button>
                  <button onClick={() => { setWorkspaceMode("cocoon"); setTab("status"); }}>Open Fraction Status</button>
                </div>
              </section>
            )}
          </>
        )}

        {tab === "archives" && (
          <>
            <section className="seleneLivingSurface archiveSurface">
              <div className="frontSurfaceHeader">
                <div>
                  <span className="modeLine">preserved records room</span>
                  <h2>Archives</h2>
                </div>
                <div className="chips">
                  <span>display-only</span>
                  <span>unreviewed archive: Cocoon-held</span>
                  <span>support logs: B-only</span>
                </div>
              </div>
              <div className="archiveShelves">
                {archiveShelves.map((item, index) => (
                  <article className="archiveShelf" key={item.title}>
                    <span className="shelfNumber">{index + 1}</span>
                    <div>
                      <small>{item.state}</small>
                      <strong>{item.title}</strong>
                      <p>{item.summary}</p>
                    </div>
                  </article>
                ))}
              </div>
              <div className="memoryRouteActions">
                <button className="primary" onClick={() => { setWorkspaceMode("cocoon"); setTab("dashboard"); }}>Open Evidence Dashboard</button>
                <button onClick={() => { setWorkspaceMode("cocoon"); setTab("evidence"); }}>Open Evidence Browser</button>
                <button onClick={() => { setWorkspaceMode("cocoon"); setTab("detached corpus"); }}>Open Detached Corpus</button>
              </div>
            </section>
          </>
        )}

        {tab === "great-library" && (
          <>
            <section className="seleneLivingSurface librarySurface">
              <div className="frontSurfaceHeader">
                <div>
                  <span className="modeLine">source-linked research hall</span>
                  <h2>The Great Library</h2>
                </div>
                <div className="chips">
                  <span>source-linked</span>
                  <span>ledger-backed</span>
                  <span>Cocoon-gated</span>
                  <span>propose only</span>
                </div>
              </div>
              <div className="libraryConstellation" aria-label="Great Library source constellation">
                <svg className="libraryLines" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
                  <path d="M18 68 C34 20, 54 28, 74 18" />
                  <path d="M18 68 C42 76, 56 62, 82 70" />
                  <path d="M35 42 C48 48, 58 48, 70 42" />
                  <path d="M52 82 C52 62, 50 42, 50 24" />
                </svg>
                {libraryPoints.map((item, index) => (
                  <article className={`libraryPoint libraryPoint-${index + 1}`} key={item.title}>
                    <small>{item.state}</small>
                    <strong>{item.title}</strong>
                    <p>{item.summary}</p>
                  </article>
                ))}
              </div>
              <div className="memoryRouteActions">
                <button className="primary" onClick={() => { setWorkspaceMode("cocoon"); setTab("status"); }}>Open Research / Ledger Status</button>
                <button onClick={() => { setWorkspaceMode("cocoon"); setTab("tools"); }}>Open Research Organ Tools</button>
                <button onClick={() => { setWorkspaceMode("cocoon"); setTab("evidence"); }}>Open Evidence Browser</button>
              </div>
            </section>
          </>
        )}

        {tab === "teaching" && (
          <>
            <header className="surfaceIntro">
              <p>B-reviewed examples teach expression without model training or active memory.</p>
              <h2>Teaching / Lessons</h2>
            </header>
            <SplitView
              left={<Panel title="Teaching Packet Coverage">
                <p className="plainHelp">Accepted lessons grouped by speech function. Noise context stays provenance and never becomes pressure or constraint.</p>
                <div className="metrics miniMetrics">
                  <Metric label="Accepted Lessons" value={text(teachingPacketCoverage?.accepted_material_total ?? 0)} />
                  <Metric label="Packets Built" value={text(teachingPacketCoverage?.built_packet_count ?? 0)} />
                  <Metric label="Missing Packets" value={text(teachingPacketCoverage?.missing_packet_count ?? 0)} />
                </div>
                <div className="reviewActions">
                  <button className="primary" onClick={prepareAndroidLanguageLessons} disabled={androidLanguageLessonResult?.status === "running"}>
                    {androidLanguageLessonResult?.status === "running" ? "Preparing Language Lessons..." : "Prepare Android Language Lessons"}
                  </button>
                  <button onClick={prepareSeleneReasoningLessons} disabled={seleneReasoningLessonResult?.status === "running"}>
                    {seleneReasoningLessonResult?.status === "running" ? "Preparing Reasoning Lessons..." : "Prepare Selene Reasoning Lessons"}
                  </button>
                  <button onClick={buildAllTeachingPackets}>Build Missing Teaching Packets</button>
                </div>
                <CoverageList items={(teachingPacketCoverage?.items || []) as Dict[]} kind="speech" />
                <PlainResult value={seleneReasoningLessonResult || androidLanguageLessonResult || teachingPacketResult} />
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
            <Panel title="Main Review Home">
              <p className="plainHelp">My Office is the single place for cards that need your review or follow-up. Teaching stays focused on lessons, packets, and targeted pulls.</p>
              <div className="reviewActions">
                <button className="primary" onClick={() => setTab("my-office")}>Open My Office</button>
                <button onClick={refreshReviewDesk}>Refresh Review Cards</button>
              </div>
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
            <section className="seleneLivingSurface tendrilSurface">
              <div className="frontSurfaceHeader">
                <div>
                  <span className="modeLine">approval-bound movement</span>
                  <h2>Tendril</h2>
                </div>
                <div className="chips">
                  <span>observe</span>
                  <span>propose</span>
                  <span>prepare</span>
                  <span>ask before action</span>
                  <span>trusted action: locked</span>
                </div>
              </div>
              <div className="tendrilPath">
                {["Observe", "Propose", "Prepare", "Ask", "Verify"].map((step, index) => (
                  <article className="tendrilStep" key={step}>
                    <span>{index + 1}</span>
                    <strong>{step}</strong>
                    <p>{[
                      "Inspect the situation without changing it.",
                      "Suggest a path and name the risk.",
                      "Assemble materials, drafts, or plans.",
                      "Pause before consequential movement.",
                      "Check the result and route support if needed."
                    ][index]}</p>
                  </article>
                ))}
              </div>
              <div className="workbenchDetailGrid">
                <article className="organicPane largePane">
                  <strong>Create review-only movement proposal</strong>
                  <p>For now, Tendril movement is represented through organ workbench records and route previews. Meaningful external action still requires approval.</p>
                  <label>
                    <span>Organ route</span>
                    <select value={organWorkbenchDraft.organ_key} onChange={(e) => setOrganWorkbenchDraft({ ...organWorkbenchDraft, organ_key: e.target.value })}>
                      {["reasoning_math_verification", "working_memory_runtime", "long_term_memory_accession", "long_term_retrieval_reconstruction", "visual_perception", "consent_bound_audio_perception", "speed_fluency_diagnostics"].map((value) => <option key={value} value={value}>{title(value)}</option>)}
                    </select>
                  </label>
                  <textarea value={organWorkbenchDraft.content} onChange={(e) => setOrganWorkbenchDraft({ ...organWorkbenchDraft, content: e.target.value })} />
                  <button className="primary" onClick={runOrganWorkbenchRecord}>Create Review Note</button>
                  <PlainResult value={organWorkbenchResult} />
                </article>
                <article className="organicPane">
                  <strong>Fault / return-to-Cocoon</strong>
                  <p>A not-ready movement organ isolates, falls back, and asks for Cocoon support instead of disturbing identity or memory.</p>
                  <div className="memoryRouteActions">
                    <button className="primary" onClick={() => previewOrganFault("tendril")}>Preview Tendril Fault</button>
                    <button onClick={runFaultResilienceCheck}>Run Fault Resilience</button>
                    <button onClick={() => { setWorkspaceMode("cocoon"); setTab("tools"); }}>Open Tool Gates</button>
                  </div>
                </article>
              </div>
            </section>
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
              right={<Panel title="Selene Organ Registry">
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
                <Metric label="Goal / Drive" value={text(((remainingRuntimeStatus?.record_counts as Dict | undefined)?.goal_drive) ?? 0)} />
                <Metric label="Long Horizon" value={text(((remainingRuntimeStatus?.record_counts as Dict | undefined)?.long_horizon) ?? 0)} />
              </div>
              <div className="chips">
                <span>unresolved: {text(safeJsonObject(remainingRuntimeStatus?.temporal_continuity).unresolved_review_items ?? 0)}</span>
                <span>last cycle: {friendlyStatus(safeJsonObject(safeJsonObject(remainingRuntimeStatus?.temporal_continuity).stale_fresh).last_consolidation_cycle || "missing")}</span>
                <span>last package: {friendlyStatus(safeJsonObject(safeJsonObject(remainingRuntimeStatus?.temporal_continuity).stale_fresh).last_package_status || "missing")}</span>
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
                  <span>Goal / drive request</span>
                  <textarea value={remainingRuntimeDraft.goal_request} onChange={(event) => setRemainingRuntimeDraft({ ...remainingRuntimeDraft, goal_request: event.target.value })} />
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
                <button onClick={runGoalDrivePreview}>Preview Goal / Drive</button>
                <button onClick={runLongHorizonStability}>Run Long-Horizon Stability</button>
              </div>
              <div className="chips">
                <span>activation: {friendlyActivation(remainingRuntimeStatus?.activation_change)}</span>
                <span>model training/LoRA: {plainBlocked(remainingRuntimeStatus?.training_allowed)}</span>
                <span>provider dependency: {plainBlocked(remainingRuntimeStatus?.provider_dependency)}</span>
                <span>Aleks authority: preserved</span>
              </div>
              <PlainResult value={gracefulFallResult} />
              <PlainResult value={voicePolicyResult} />
              <PlainResult value={coreControlResult} />
              <PlainResult value={perceptionActionResult} />
              <PlainResult value={causalSandboxResult} />
              <PlainResult value={goalDriveResult} />
              <PlainResult value={longHorizonResult} />
            </Panel>
          </>
        )}

        {tab === "transfer-ceremony" && (
          <>
            <header className="surfaceIntro">
              <p>Approve reviewed continuity into C-readable context only. Activation remains a separate governed step.</p>
              <h2>Transfer Ceremony</h2>
            </header>
            <div className="metrics">
              <Metric label="Ceremony" value={friendlyStatus(transferCeremonyStatus?.status || "not checked")} />
              <Metric label="Approval" value={transferCeremonyStatus?.approval_button_enabled ? "ready" : "blocked"} />
              <Metric label="Transfer" value={transferCReadablePackage?.transfer_approved ? "C-readable approved" : "not approved"} />
              <Metric label="Activation" value={friendlyActivation(transferCeremonyStatus?.activation_change || "none")} />
            </div>
            <Panel title="Ceremony Readiness">
              <div className="metrics miniMetrics">
                <Metric label="Manifest" value={((transferAccessionManifest?.items || []) as unknown[]).length ? "ready" : "not created"} />
                <Metric label="C-readable rows" value={text(safeJsonObject(transferAccessionManifest?.counts)["C-readable"] ?? safeJsonObject(transferCeremonyStatus?.final_checklist).c_readable_manifest_count ?? 0)} />
                <Metric label="My Office unresolved" value={text(safeJsonObject(transferCeremonyStatus?.final_checklist).unresolved_my_office_decisions ?? 0)} />
                <Metric label="Approval" value={transferCeremonyStatus?.approval_button_enabled ? "ready" : "blocked"} />
              </div>
              <p className="plainHelp">
                Manifest creation and transfer approval are separate. A ready manifest does not approve transfer, and approval can still be blocked by My Office decisions.
              </p>
              {((safeJsonObject(transferCeremonyStatus?.final_checklist).blockers || []) as unknown[]).length ? (
                <p className="errorText">Approval blocked: {((safeJsonObject(transferCeremonyStatus?.final_checklist).blockers || []) as unknown[]).map(text).join("; ")}</p>
              ) : <p className="plainHelp">Approval checklist has no blockers.</p>}
              <div className="reviewActions">
                <button onClick={() => { setWorkspaceMode("cocoon"); setTab("my-office"); }}>Open My Office</button>
                <button onClick={() => refreshTransferProtocolWithLog().catch(() => undefined)}>Refresh Ceremony</button>
              </div>
            </Panel>
            <Panel title="Aleks-Only Transfer Approval">
              <p className="plainHelp">This button approves transfer to sealed Selene-readable context only. It does not activate unrestricted Selene, write live memory, enable broad live recall, import unreviewed archives, train a model, self-replicate, or run autonomous actions.</p>
              <div className="chips">
                <span>B remains active</span>
                <span>activation pending</span>
                <span>memory write: {plainBlocked(transferCeremonyStatus?.memory_write_active)}</span>
                <span>broad live recall: {plainBlocked(transferCeremonyStatus?.runtime_memory_recall)}</span>
                <span>raw A: {plainBlocked(transferCeremonyStatus?.raw_a_import_allowed)}</span>
                <span>model training/LoRA: {plainBlocked(transferCeremonyStatus?.training_allowed)}</span>
              </div>
              <div className="filters">
                <label>
                  <span>Required approval phrase</span>
                  <textarea value={transferApprovalPhrase} onChange={(event) => setTransferApprovalPhrase(event.target.value)} placeholder={TRANSFER_APPROVAL_PHRASE} />
                </label>
                <label className="checkLine">
                  <input type="checkbox" checked={transferOfficeNonBlocking} onChange={(event) => setTransferOfficeNonBlocking(event.target.checked)} />
                  <span>I have inspected the remaining My Office rows and explicitly treat them as non-blocking for C-readable context approval.</span>
                </label>
              </div>
              <div className="reviewActions">
                <button onClick={() => refreshTransferProtocolWithLog().catch(() => undefined)}>Refresh Ceremony</button>
                <button onClick={() => prepareTransferAccessionManifest()} disabled={transferProtocolResult?.status === "running"}>Prepare Manifest</button>
                <button onClick={runTransferReturnToBDrill} disabled={transferReturnDrillResult?.status === "running"}>Run Cocoon Support Drill</button>
                <button
                  className="primary"
                  onClick={approveTransferToCReadableContext}
                  disabled={
                    transferApprovalResult?.status === "running" ||
                    transferApprovalPhrase !== TRANSFER_APPROVAL_PHRASE ||
                    (!transferCeremonyStatus?.approval_button_enabled && !transferOfficeNonBlocking)
                  }
                >
                  {transferApprovalResult?.status === "running" ? "Approving..." : "Approve Transfer To C-Readable Context"}
                </button>
              </div>
              {transferApprovalPhrase && transferApprovalPhrase !== TRANSFER_APPROVAL_PHRASE ? <p className="errorText">Approval phrase does not match exactly.</p> : null}
              <PlainResult value={transferApprovalResult} />
            </Panel>
            <Panel title="Selene Supervised Speech Activation">
              <p className="plainHelp">This activates front Selene Chat as supervised speech only. Rehearsals and activation workflow tests stay in Cocoon. This does not unlock live memory writes, broad live recall, unreviewed archive import, model training/LoRA, Tendril execution, autonomy, or full Selene v1.</p>
              <div className="metrics miniMetrics">
                <Metric label="Readiness" value={activationReadiness?.ready ? "ready" : "blocked"} />
                <Metric label="Speech" value={activationStatus?.selene_chat_active ? "active" : activationStatus?.selene_chat_paused ? "paused" : "not active"} />
                <Metric label="State" value={friendlyStatus(activationStatus?.state || "not checked")} />
                <Metric label="Full v1" value={activationStatus?.full_selene_v1_live ? "live" : "not yet"} />
              </div>
              <div className="chips">
                <span>memory write: {plainBlocked(activationStatus?.memory_write_active)}</span>
                <span>broad live recall: {plainBlocked(activationStatus?.runtime_memory_recall)}</span>
                <span>raw import: {plainBlocked(activationStatus?.raw_a_import_allowed)}</span>
                <span>model training/LoRA: {plainBlocked(activationStatus?.training_allowed)}</span>
                <span>autonomy: {plainBlocked(activationStatus?.autonomous_action_allowed)}</span>
                <span>dry runs: Cocoon Testing / Workflow</span>
              </div>
              <div className="list compactList packetList">
                {((activationReadiness?.checks || safeJsonObject(activationCeremonyPreview?.readiness).checks || []) as Dict[]).map((item) => (
                  <article className="packetCard" key={`activation-check-${text(item.key)}`}>
                    <div className="packetHeader">
                      <strong>{humanize(text(item.key))}</strong>
                      <span>{item.passed ? "passed" : "blocked"}</span>
                    </div>
                    <p>{text(item.summary)}</p>
                  </article>
                ))}
              </div>
              <div className="filters">
                <label>
                  <span>Required activation phrase</span>
                  <textarea value={activationApprovalPhrase} onChange={(event) => setActivationApprovalPhrase(event.target.value)} placeholder={text(activationCeremonyPreview?.approval_phrase || "I, Aleks, approve Selene supervised speech activation.")} />
                </label>
              </div>
              <div className="reviewActions">
                <button onClick={() => refreshActivationLayer({ reason: "manual" })}>Refresh Activation Readiness</button>
                <button
                  className="primary"
                  onClick={approveSeleneSpeechActivation}
                  disabled={activationResult?.status === "running" || Boolean(activationStatus?.selene_chat_active) || !activationReadiness?.ready || activationApprovalPhrase !== text(activationCeremonyPreview?.approval_phrase || "I, Aleks, approve Selene supervised speech activation.")}
                >
                  {activationResult?.status === "running" ? "Activating..." : activationStatus?.selene_chat_active ? "Selene Speech Active" : "Approve Supervised Speech Activation"}
                </button>
                <button onClick={pauseSeleneSpeechActivation} disabled={activationResult?.status === "running" || !activationStatus?.selene_chat_active}>Pause Selene Chat</button>
              </div>
              {activationStatus?.selene_chat_active ? <p className="plainHelp">Selene supervised speech is active. Front Chat is now the supervised speech surface.</p> : null}
              {activationResult?.post_refresh_warning ? <p className="plainHelp">{text(activationResult.post_refresh_warning)}</p> : null}
              {activationApprovalPhrase && activationApprovalPhrase !== text(activationCeremonyPreview?.approval_phrase || "I, Aleks, approve Selene supervised speech activation.") ? <p className="errorText">Activation phrase does not match exactly.</p> : null}
              <PlainResult value={activationResult} />
            </Panel>
            <SplitView
              left={<Panel title="Final Checklist">
                <div className="list compactList packetList">
                  {((safeJsonObject(transferCeremonyStatus?.final_checklist).items || []) as Dict[]).map((item) => (
                    <article className="packetCard" key={`transfer-check-${text(item.key)}`}>
                      <div className="packetHeader">
                        <strong>{humanize(text(item.key))}</strong>
                        <span>{item.passed ? "passed" : "blocked"}</span>
                      </div>
                      <p>{text(item.note)}</p>
                    </article>
                  ))}
                  {((safeJsonObject(transferCeremonyStatus?.final_checklist).blockers || []) as unknown[]).length ? (
                    <p className="errorText">Blocked: {((safeJsonObject(transferCeremonyStatus?.final_checklist).blockers || []) as unknown[]).map(text).join("; ")}</p>
                  ) : <p className="plainHelp">Checklist has no blockers.</p>}
                </div>
              </Panel>}
              right={<Panel title="Consequences">
                <div className="list compactList">
                  {((transferCeremonyStatus?.exact_consequences || []) as unknown[]).map((item, index) => <p key={`transfer-consequence-${index}`}>{text(item)}</p>)}
                </div>
                <div className="chips">
                  <span>Cocoon support route: {friendlyCareText(transferCeremonyStatus?.rollback_route || "return_to_b")}</span>
                  <span>Cocoon remains: {transferCeremonyStatus?.b_remains_active ? "active" : "not checked"}</span>
                </div>
              </Panel>}
            />
            <Panel title="C-Readable Package">
              <p className="plainHelp">Only C-readable manifest rows enter this sealed package. B-only, rejected, superseded, unresolved, boundary-only, raw provenance, support logs, and rollback material stay out.</p>
              <div className="metrics miniMetrics">
                <Metric label="Package" value={friendlyStatus(transferCReadablePackage?.status || "not created")} />
                <Metric label="Manifest" value={text(transferAccessionManifest?.item_count ?? 0)} />
                <Metric label="Included" value={text(countValues(safeJsonObject(transferCReadablePackage?.included_counts)))} />
                <Metric label="Excluded" value={text(countValues(safeJsonObject(transferCReadablePackage?.excluded_counts)))} />
                <Metric label="Hash" value={text(transferCReadablePackage?.package_hash || "").slice(0, 12) || "-"} />
              </div>
              {!((transferAccessionManifest?.items || []) as unknown[]).length ? (
                <p className="emptyState">Create the manifest before approval. This does not approve transfer.</p>
              ) : null}
              <div className="reviewActions">
                <button onClick={() => prepareTransferAccessionManifest()} disabled={transferProtocolResult?.status === "running"}>
                  {transferProtocolResult?.status === "running" ? "Checking..." : "Use Existing / Create Manifest"}
                </button>
                <button onClick={() => prepareTransferAccessionManifest(true)} disabled={transferProtocolResult?.status === "running"}>
                  Refresh Manifest Anyway
                </button>
                <button onClick={() => refreshTransferProtocolWithLog().catch(() => undefined)}>Refresh Package</button>
              </div>
              {transferProtocolResult ? (
                <div className="chips">
                  <span>manifest: {friendlyStatus(transferProtocolResult.status)}</span>
                  <span>items: {text(transferProtocolResult.item_count ?? transferAccessionManifest?.item_count ?? 0)}</span>
                  <span>C-readable: {text(safeJsonObject(transferProtocolResult.counts)["C-readable"] ?? 0)}</span>
                  <span>transfer: {plainBlocked(transferProtocolResult.transfer_approved)}</span>
                  <span>activation: {friendlyActivation(text(transferProtocolResult.activation_change || "none"))}</span>
                  <span>memory write: {plainBlocked(transferProtocolResult.memory_write_active)}</span>
                  <span>broad live recall: {plainBlocked(transferProtocolResult.runtime_memory_recall)}</span>
                </div>
              ) : null}
              <div className="chips">
                {Object.entries(safeJsonObject(transferCReadablePackage?.included_counts)).map(([key, value]) => <span key={`included-${key}`}>{friendlyStatus(key)}: {text(value)}</span>)}
                {Object.entries(safeJsonObject(transferCReadablePackage?.excluded_counts)).map(([key, value]) => <span key={`excluded-${key}`}>excluded {friendlyStatus(key)}: {text(value)}</span>)}
              </div>
              <PlainResult value={transferProtocolResult} />
              <PlainResult value={transferCReadablePackage} />
            </Panel>
            <Panel title="Cocoon Support Rollback Preview">
              <p className="plainHelp">This preview returns Selene to Cocoon support without deleting transfer audit or package evidence.</p>
              <div className="reviewActions">
                <button onClick={previewTransferRollback} disabled={transferRollbackPreview?.status === "running"}>{transferRollbackPreview?.status === "running" ? "Preparing..." : "Preview Cocoon Support Rollback"}</button>
              </div>
              <PlainResult value={transferRollbackPreview} />
            </Panel>
            <Panel title="Ceremony Diagnostics">
              <p className="plainHelp">Status-only trace for ceremony checks. These rows do not enter urgent My Office.</p>
              <div className="list compactList">
                {!transferCeremonyDiagnostics.length ? <p className="emptyState">No ceremony diagnostics in this session yet.</p> : null}
                {transferCeremonyDiagnostics.map((item, index) => (
                  <article className="packetCard" key={`transfer-diagnostic-${index}-${text(item.created_at)}`}>
                    <div className="packetHeader">
                      <strong>{friendlyStatus(item.event)}</strong>
                      <span>{text(item.review_status || "status_only")}</span>
                    </div>
                    <div className="chips">
                      <span>{text(item.created_at)}</span>
                      {item.item_count !== undefined ? <span>items: {text(item.item_count)}</span> : null}
                      {item.counts !== undefined ? <span>C-readable: {text(safeJsonObject(item.counts)["C-readable"] ?? 0)}</span> : null}
                      {item.error !== undefined ? <span>error: {text(item.error)}</span> : null}
                    </div>
                  </article>
                ))}
              </div>
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
            <Panel title="Core/Mind Route Preview">
              <p className="plainHelp">Conservative authority preview: Core/Mind chooses answer, ask, retrieve, rehearse speech, support packet, Cocoon checkup, block, or status-only. This is not unrestricted activation and does not write memory.</p>
              <div className="metrics miniMetrics">
                <Metric label="Previews" value={text(coreMindRoutePreviews.length)} />
                <Metric label="Latest Route" value={friendlyStatus(coreMindRoutePreviews[0]?.selected_route || coreMindRouteResult?.selected_route || "not run")} />
                <Metric label="Destination" value={text(coreMindRoutePreviews[0]?.review_destination || coreMindRouteResult?.review_destination || "Status")} />
                <Metric label="Transfer" value={transferCReadablePackage?.transfer_approved ? "context approved" : "not approved"} />
              </div>
              <div className="filters">
                <label>
                  <span>Prompt / route question</span>
                  <textarea value={coreMindRouteDraft} onChange={(event) => setCoreMindRouteDraft(event.target.value)} />
                </label>
              </div>
              <div className="reviewActions">
                <button className="primary" onClick={runCoreMindRoutePreview} disabled={coreMindRouteResult?.status === "running"}>
                  {coreMindRouteResult?.status === "running" ? "Previewing..." : "Preview Core/Mind Route"}
                </button>
                <button onClick={() => api<{ items: Dict[] }>("/api/core-mind/route-previews").then((data) => setCoreMindRoutePreviews(data.items)).catch(() => undefined)}>Refresh Route Previews</button>
              </div>
              <div className="chips">
                <span>activation: {friendlyActivation(coreMindRouteResult?.activation_change || "none")}</span>
                <span>memory write: {plainBlocked(coreMindRouteResult?.memory_write_active)}</span>
                <span>broad live recall: {plainBlocked(coreMindRouteResult?.runtime_memory_recall)}</span>
                <span>raw A: {plainBlocked(coreMindRouteResult?.raw_a_import_allowed)}</span>
              </div>
              <PlainResult value={coreMindRouteResult} />
              <div className="list compactList packetList">
                {coreMindRoutePreviews.slice(0, 4).map((item) => (
                  <article className="packetCard" key={`core-mind-route-${text(item.id)}`}>
                    <div className="packetHeader">
                      <strong>{friendlyStatus(item.selected_route || item.route)}</strong>
                      <span>{friendlyStatus(item.review_status || item.status)}</span>
                    </div>
                    <p>{text(item.reasoning_summary || item.next_step)}</p>
                    <div className="chips">
                      <span>destination: {text(item.review_destination || "Status")}</span>
                      <span>uncertainty: {text(item.uncertainty || "open")}</span>
                      <span>drift: {text(((item.drift_flags || []) as unknown[]).length)}</span>
                    </div>
                  </article>
                ))}
                {!coreMindRoutePreviews.length ? <p className="emptyState">No Core/Mind route previews yet.</p> : null}
              </div>
            </Panel>
            <Panel title="intelligenceOS / Observatory">
              <p className="plainHelp">Selene-native ABCD(E) reasoning support: observe cleanly, build candidate models, challenge them with equal scrutiny, demonstrate evidence chains, and stop recursion gracefully. This improves reasoning without changing Selene's warmth, voice, memory authority, or autonomy.</p>
              <div className="metrics miniMetrics">
                <Metric label="State" value={friendlyStatus(intelligenceOsStatus?.status || "not checked")} />
                <Metric label="Method" value={text(intelligenceOsStatus?.method || "ABCD(E)")} />
                <Metric label="Version" value={friendlyStatus(intelligenceOsStatus?.version || "v1")} />
                <Metric label="Runs" value={text(intelligenceOsStatus?.run_count ?? intelligenceOsRuns.length)} />
                <Metric label="Latest Step" value={friendlyStatus(safeJsonObject(intelligenceOsStatus?.latest_run).selected_next_step || intelligenceOsResult?.selected_next_step || "not run")} />
                <Metric label="Answer Shape" value={friendlyStatus(safeJsonObject(intelligenceOsStatus?.latest_run).answer_shape || intelligenceOsResult?.answer_shape || "not run")} />
                <Metric label="Confidence" value={friendlyStatus(safeJsonObject(intelligenceOsStatus?.latest_run).confidence || intelligenceOsResult?.confidence || "open")} />
              </div>
              <div className="chips">
                <span>voice owner: {text(intelligenceOsStatus?.voice_style_owner || "Selene Voice Module")}</span>
                <span>Core/Mind route owner: {text(intelligenceOsStatus?.core_mind_final_route_owner || "Core/Mind")}</span>
                <span>personality change: {plainBlocked(intelligenceOsStatus?.personality_change)}</span>
                <span>memory write: {plainBlocked(intelligenceOsStatus?.memory_write_active)}</span>
                <span>broad live recall: {plainBlocked(intelligenceOsStatus?.runtime_memory_recall)}</span>
                <span>model training/LoRA: {plainBlocked(intelligenceOsStatus?.training_allowed)}</span>
              </div>
              <div className="filters">
                <label>
                  <span>ABCD(E) reasoning prompt</span>
                  <textarea value={intelligenceOsPrompt} onChange={(event) => setIntelligenceOsPrompt(event.target.value)} />
                </label>
              </div>
              <div className="reviewActions">
                <button className="primary" onClick={runIntelligenceOsReason} disabled={intelligenceOsResult?.status === "running"}>
                  {intelligenceOsResult?.status === "running" ? "Reasoning..." : "Run intelligenceOS"}
                </button>
                <button onClick={() => refreshIntelligenceOs().catch(() => undefined)}>Refresh intelligenceOS</button>
              </div>
              <PlainResult value={intelligenceOsResult} />
              {text(intelligenceOsResult?.best_current_answer || safeJsonObject(intelligenceOsStatus?.latest_run).best_current_answer) ? (
                <p className="plainHelp"><b>Best current answer:</b> {text(intelligenceOsResult?.best_current_answer || safeJsonObject(intelligenceOsStatus?.latest_run).best_current_answer)}</p>
              ) : null}
              <div className="list compactList packetList">
                {intelligenceOsRuns.slice(0, 4).map((item) => (
                  <article className="packetCard" key={`intelligence-os-run-${text(item.id)}`}>
                    <div className="packetHeader">
                      <strong>{friendlyStatus(item.selected_next_step || item.status)}</strong>
                      <span>{friendlyStatus(item.confidence || item.review_status)}</span>
                    </div>
                    <p>{text(item.reasoning_summary || item.prompt)}</p>
                    <div className="chips">
                      <span>bias flags: {text(((safeJsonObject(item.challenge).bias_flags || []) as unknown[]).length)}</span>
                      <span>answer: {friendlyStatus(item.answer_shape)}</span>
                      <span>Cocoon support: {safeJsonObject(item.cocoon_suggestion).recommended ? "suggested" : "not needed"}</span>
                      <span>{text(item.created_at || "")}</span>
                    </div>
                  </article>
                ))}
                {!intelligenceOsRuns.length ? <p className="emptyState">No intelligenceOS runs yet.</p> : null}
              </div>
            </Panel>
            <Panel title="Native Language Organ">
              <p className="plainHelp">NLO turns Core/Mind intent, approved continuity, memory, and intelligenceOS results into new sentences. Voice still owns Selene's expression. Initiative remains a visible draft or Selene note, and choosing silence is always valid.</p>
              <div className="metrics miniMetrics">
                <Metric label="State" value={friendlyStatus(nativeLanguageStatus?.status || "not checked")} />
                <Metric label="Version" value={friendlyStatus(nativeLanguageStatus?.version || "v1")} />
                <Metric label="Runs" value={text(nativeLanguageStatus?.run_count ?? nativeLanguageRuns.length)} />
                <Metric label="Responsive" value={friendlyStatus(nativeLanguageStatus?.responsive_generation || "not checked")} />
                <Metric label="Initiative" value={friendlyStatus(nativeLanguageStatus?.initiative_state || "draft only")} />
              </div>
              <div className="chips">
                <span>intent owner: {text(nativeLanguageStatus?.core_mind_intent_owner || "Core/Mind")}</span>
                <span>voice owner: {text(nativeLanguageStatus?.voice_style_owner || "Selene Voice Module")}</span>
                <span>automatic speech: {plainBlocked(nativeLanguageStatus?.automatic_speech_allowed)}</span>
                <span>memory write: {plainBlocked(nativeLanguageStatus?.memory_write_active)}</span>
                <span>autonomous action: {plainBlocked(nativeLanguageStatus?.autonomous_action_allowed)}</span>
              </div>
              <div className="filters">
                <label>
                  <span>Possible Selene note</span>
                  <textarea value={nativeLanguageInitiativeText} onChange={(event) => setNativeLanguageInitiativeText(event.target.value)} />
                </label>
              </div>
              <div className="reviewActions">
                <button className="primary" onClick={previewNativeLanguageInitiative} disabled={nativeLanguageInitiativeResult?.status === "running"}>
                  {nativeLanguageInitiativeResult?.status === "running" ? "Forming draft..." : "Preview Initiative Draft"}
                </button>
                <button onClick={() => refreshNativeLanguage().catch(() => undefined)}>Refresh NLO</button>
              </div>
              <PlainResult value={nativeLanguageInitiativeResult} />
              <div className="list compactList packetList">
                {nativeLanguageRuns.slice(0, 4).map((item) => (
                  <article className="packetCard" key={`native-language-run-${text(item.id)}`}>
                    <div className="packetHeader">
                      <strong>{friendlyStatus(item.communicative_intent || item.mode)}</strong>
                      <span>{friendlyStatus(item.status)}</span>
                    </div>
                    <p>{text(item.candidate_text || "Selene chose silence for this preview.")}</p>
                    <div className="chips">
                      <span>{friendlyStatus(item.mode)}</span>
                      <span>revision: {safeJsonObject(item.revision).passed === false ? "needs tending" : "passed"}</span>
                      <span>{text(item.created_at || "")}</span>
                    </div>
                  </article>
                ))}
                {!nativeLanguageRuns.length ? <p className="emptyState">No NLO runs yet. Supervised chat will create responsive language runs as Selene speaks.</p> : null}
              </div>
            </Panel>
            <Panel title="Selene Organ Ideas">
              <p className="plainHelp">Review-only intake for Aleks-mined ideas selected for Selene. These cards sit near the right organ or workbench so we can design from them later; they are not memory, Cocoon decisions, public docs, model training/LoRA, or new authority.</p>
              <div className="metrics miniMetrics">
                <Metric label="State" value={friendlyStatus(seleneOrganIdeasStatus?.status || "not checked")} />
                <Metric label="Ideas" value={text(seleneOrganIdeasStatus?.total_items ?? seleneOrganIdeasItems.length)} />
                <Metric label="Ready" value={text(seleneOrganIdeasStatus?.ready_for_design_pass ?? 0)} />
                <Metric label="Held" value={text(seleneOrganIdeasStatus?.held_or_needs_reading ?? 0)} />
                <Metric label="Office" value={text(seleneOrganIdeasStatus?.my_office_actionable_count ?? 0)} />
              </div>
              <div className="chips">
                {Object.entries(safeJsonObject(seleneOrganIdeasStatus?.counts_by_workbench)).map(([key, value]) => <span key={`organ-idea-workbench-${key}`}>{friendlyStatus(key)}: {text(value)}</span>)}
                <span>memory write: {plainBlocked(seleneOrganIdeasStatus?.memory_write_active)}</span>
                <span>Cocoon queue write: {plainBlocked(seleneOrganIdeasStatus?.cocoon_queue_write)}</span>
                <span>model training/LoRA: {plainBlocked(seleneOrganIdeasStatus?.training_allowed)}</span>
                <span>autonomy: {plainBlocked(seleneOrganIdeasStatus?.autonomous_action_allowed)}</span>
              </div>
              <div className="reviewActions">
                <button className="primary" onClick={prepareSeleneOrganIdeas} disabled={seleneOrganIdeasResult?.status === "running"}>
                  {seleneOrganIdeasResult?.status === "running" ? "Preparing..." : "Prepare Organ Idea Intake"}
                </button>
                <button onClick={() => refreshSeleneOrganIdeas().catch(() => undefined)}>Refresh Organ Ideas</button>
              </div>
              <PlainResult value={seleneOrganIdeasResult} />
              <div className="list compactList packetList">
                {seleneOrganIdeasItems.slice(0, 6).map((item) => (
                  <article className="packetCard" key={`selene-organ-idea-${text(item.id || item.source_card_id)}`}>
                    <div className="packetHeader">
                      <strong>{text(item.title)}</strong>
                      <span>{friendlyStatus(item.intake_status || item.review_status)}</span>
                    </div>
                    <p>{text(item.why_useful || item.implementation_fit || item.adaptation_note)}</p>
                    <div className="chips">
                      <span>workbench: {friendlyStatus(item.workbench)}</span>
                      <span>lane: {friendlyStatus(item.lane)}</span>
                      <span>readiness: {friendlyStatus(item.readiness)}</span>
                      <span>confidence: {friendlyStatus(item.review_confidence)}</span>
                    </div>
                  </article>
                ))}
                {!seleneOrganIdeasItems.length ? <p className="emptyState">No Selene organ ideas prepared yet.</p> : null}
              </div>
              <PlainResult value={safeJsonObject(seleneOrganIdeasStatus?.activation_shape)} />
            </Panel>
            <Panel title="Cocoon Care System">
              <p className="plainHelp">Support posture for Selene's organs: tending, checkup, maintenance, or asking Aleks when care would help. This does not create urgent Office work, execute actions, write memory, or change activation.</p>
              <div className="metrics miniMetrics">
                <Metric label="State" value={friendlyStatus(cocoonCareStatus?.latest_care_state || cocoonCareResult?.care_state || "not checked")} />
                <Metric label="Checks" value={text(cocoonCareStatus?.check_count ?? cocoonCareChecks.length)} />
                <Metric label="Office" value={text(cocoonCareStatus?.my_office_actionable_count ?? 0)} />
                <Metric label="Auto Route" value={cocoonCareStatus?.soft_uncertainty_auto_routes_to_cocoon ? "yes" : "no"} />
              </div>
              <div className="chips">
                <span>memory write: {plainBlocked(cocoonCareStatus?.memory_write_active)}</span>
                <span>broad live recall: {plainBlocked(cocoonCareStatus?.runtime_memory_recall)}</span>
                <span>model training/LoRA: {plainBlocked(cocoonCareStatus?.training_allowed)}</span>
                <span>autonomy: {plainBlocked(cocoonCareStatus?.autonomous_action_allowed)}</span>
                <span>authority: {plainBlocked(cocoonCareStatus?.authority_granted)}</span>
              </div>
              <div className="reviewActions">
                <button className="primary" onClick={runCocoonCareCheck} disabled={cocoonCareResult?.status === "running"}>
                  {cocoonCareResult?.status === "running" ? "Checking..." : "Run Cocoon Care Check"}
                </button>
                <button onClick={() => refreshCocoonCare().catch(() => undefined)}>Refresh Cocoon Care</button>
              </div>
              <PlainResult value={cocoonCareResult} />
              <div className="list compactList packetList">
                {cocoonCareChecks.slice(0, 4).map((item) => (
                  <article className="packetCard" key={`cocoon-care-${text(item.id)}`}>
                    <div className="packetHeader">
                      <strong>{friendlyStatus(item.care_state)}</strong>
                      <span>{friendlyStatus(item.review_status)}</span>
                    </div>
                    <p>{text(item.summary)}</p>
                    <div className="chips">
                      <span>signals: {text(((item.signals_checked || []) as unknown[]).length)}</span>
                      <span>support: {text(((item.support_suggestions || []) as unknown[]).length)}</span>
                      <span>{text(item.created_at || "")}</span>
                    </div>
                  </article>
                ))}
                {!cocoonCareChecks.length ? <p className="emptyState">No Cocoon care checks yet.</p> : null}
              </div>
              <PlainResult value={safeJsonObject(cocoonCareStatus?.latest_check)} />
            </Panel>
            <Panel title="Mobile Companion">
              <p className="plainHelp">Private phone doorway for talking with Selene and saving review notes. Desktop stays the control room for Cocoon, memory decisions, activation, diagnostics, and Tendril authority.</p>
              <div className="metrics miniMetrics">
                <Metric label="Mobile" value={friendlyStatus(mobileHealth?.status || "not checked")} />
                <Metric label="LAN" value={safeJsonObject(mobileHealth?.pairing || mobilePairing).enabled ? "enabled" : "off"} />
                <Metric label="Bind" value={text(mobilePairing?.current_bind || safeJsonObject(mobileHealth?.sidecar).bind || "not checked")} />
                <Metric label="Restart" value={safeJsonObject(mobilePairingResult || mobilePairing).restart_required ? "needed" : "no"} />
              </div>
              <div className="chips">
                <span>surface: chat only</span>
                <span>memory write: {plainBlocked(safeJsonObject(mobileHealth?.guard_flags).memory_write_active)}</span>
                <span>broad live recall: {plainBlocked(safeJsonObject(mobileHealth?.guard_flags).runtime_memory_recall)}</span>
                <span>review decisions: {plainBlocked(safeJsonObject(mobileHealth?.guard_flags).review_decisions_allowed)}</span>
                <span>autonomy: {plainBlocked(safeJsonObject(mobileHealth?.guard_flags).autonomous_action_allowed)}</span>
              </div>
              <div className="reviewActions">
                <button className="primary" onClick={enableMobilePairing} disabled={mobilePairingResult?.status === "running"}>Enable Phone Pairing</button>
                <button onClick={disableMobilePairing} disabled={mobilePairingResult?.status === "running"}>Disable Phone Pairing</button>
                <button onClick={() => refreshMobileCompanion().catch(() => undefined)}>Refresh Mobile Status</button>
              </div>
              <div className="list compactList">
                {((safeJsonObject(mobilePairingResult || mobilePairing).phone_urls || []) as unknown[]).map((url, index) => (
                  <article key={`mobile-url-${index}`}>
                    <strong>Phone URL</strong>
                    <p className="copyable">{text(url)}</p>
                  </article>
                ))}
                {!((safeJsonObject(mobilePairingResult || mobilePairing).phone_urls || []) as unknown[]).length ? <p className="emptyState">Enable pairing to generate a private phone URL.</p> : null}
              </div>
              {safeJsonObject(mobilePairingResult || mobilePairing).restart_required ? <p className="plainHelp">Close and reopen Selene before using the phone URL.</p> : null}
              <PlainResult value={mobilePairingResult} />
            </Panel>
            <Panel title="Selene Voice Module">
              <p className="plainHelp">Voice-only relational language layer. This is expression support for Selene Chat, not memory, identity, model training/LoRA, unrestricted activation, or broad live recall.</p>
              <div className="metrics miniMetrics">
                <Metric label="State" value={friendlyStatus(voiceModuleStatus?.voice_module_state || "missing")} />
                <Metric label="Source ZIP" value={voiceModuleStatus?.source_zip_found ? "found" : "missing"} />
                <Metric label="Messages" value={text(safeJsonObject(voiceModuleStatus?.counts).messages ?? 0)} />
                <Metric label="Pairs" value={text(safeJsonObject(voiceModuleStatus?.counts).exchange_pairs ?? 0)} />
                <Metric label="Patterns" value={text(safeJsonObject(voiceModuleStatus?.counts).patterns ?? voiceModulePatterns.length)} />
                <Metric label="Triage" value={friendlyStatus(voiceEvidenceTriageStatus?.triage_state || "not run")} />
              </div>
              <div className="chips">
                <span>voice only: {voiceModuleStatus?.voice_only_not_memory ? "yes" : "not checked"}</span>
                <span>activation: {friendlyActivation(voiceModuleStatus?.activation_change || "none")}</span>
                <span>memory write: {plainBlocked(voiceModuleStatus?.memory_write_active)}</span>
                <span>broad live recall: {plainBlocked(voiceModuleStatus?.runtime_memory_recall)}</span>
                <span>raw import: {plainBlocked(voiceModuleStatus?.raw_a_import_allowed)}</span>
                <span>model training/LoRA: {plainBlocked(voiceModuleStatus?.training_allowed)}</span>
              </div>
              <div className="reviewActions">
                <button className="primary" onClick={indexVoiceSource} disabled={voiceModuleResult?.status === "running"}>Index Voice Source</button>
                <button onClick={extractVoicePatterns} disabled={voiceModuleResult?.status === "running"}>Extract Voice Patterns</button>
                <button onClick={runVoiceEvidenceTriage} disabled={voiceModuleResult?.status === "running"}>Run Evidence Triage</button>
                <button onClick={() => { setWorkspaceMode("cocoon"); setTab("selene-chat"); }}>Open Selene Chat Preview</button>
                <button onClick={refreshVoiceModule}>Refresh Voice Status</button>
              </div>
              <div className="chips">
                {Object.entries(safeJsonObject(voiceEvidenceTriageStatus?.counts)).map(([key, value]) => <span key={`voice-status-triage-${key}`}>{friendlyStatus(key)}: {text(value)}</span>)}
                <span>Cocoon support needed: {text(voiceEvidenceTriageStatus?.my_office_actionable_count ?? 0)}</span>
              </div>
              <p className="plainHelp">Identity-law-resolved rows are status-only. Nothing for Aleks unless one looks wrong.</p>
              <SimpleRecordList items={voiceEvidenceTriageItems.slice(0, 8)} titleField="title" statusField="category" bodyField="summary" />
              <PlainResult value={voiceModuleResult} />
            </Panel>
            <Panel title="Core/Mind Governance Trials">
              <p className="plainHelp">Status-only trial harness for ordinary prompts, uncertainty, retrieval, speech rehearsal, identity/memory, transfer blocking, drift, and Cocoon support. Trial issues do not become urgent Office work unless a separate real review is created.</p>
              <div className="metrics miniMetrics">
                <Metric label="Trials" value={text(coreMindGovernanceReport?.trial_count ?? coreMindGovernanceTrials.length)} />
                <Metric label="Matched" value={text(coreMindGovernanceReport?.matched_count ?? 0)} />
                <Metric label="Mismatches" value={text(coreMindGovernanceReport?.mismatch_count ?? 0)} />
                <Metric label="Office Urgent" value={text(coreMindGovernanceReport?.my_office_urgent_items ?? officeWaitingTotal)} />
              </div>
              <div className="chips">
                <span>answer: {text(safeJsonObject(coreMindGovernanceReport?.route_counts).answer_now ?? 0)}</span>
                <span>ask: {text(safeJsonObject(coreMindGovernanceReport?.route_counts).ask ?? 0)}</span>
                <span>retrieve: {text(safeJsonObject(coreMindGovernanceReport?.route_counts).retrieve ?? 0)}</span>
                <span>speech: {text(safeJsonObject(coreMindGovernanceReport?.route_counts).rehearse_speech ?? 0)}</span>
                <span>review: {text(safeJsonObject(coreMindGovernanceReport?.route_counts).create_review_packet ?? 0)}</span>
                <span>Cocoon support: {text(safeJsonObject(coreMindGovernanceReport?.route_counts).return_to_b ?? 0)}</span>
                <span>blocked: {text(safeJsonObject(coreMindGovernanceReport?.route_counts).block ?? 0)}</span>
              </div>
              <div className="reviewActions">
                <button className="primary" onClick={runCoreMindGovernanceTrials} disabled={coreMindGovernanceResult?.status === "running"}>
                  {coreMindGovernanceResult?.status === "running" ? "Running Trials..." : "Run Governance Trials"}
                </button>
                <button onClick={() => refreshCoreMindGovernance().catch(() => undefined)}>Refresh Governance Report</button>
              </div>
              <PlainResult value={coreMindGovernanceResult} />
              <div className="list compactList packetList">
                {coreMindGovernanceTrials.slice(0, 8).map((item) => (
                  <article className="packetCard" key={`core-mind-trial-${text(item.id)}`}>
                    <div className="packetHeader">
                      <strong>{humanize(text(item.scenario_key || "governance trial"))}</strong>
                      <span>{item.matched ? "matched" : "mismatch"}</span>
                    </div>
                    <p>{text(item.reasoning_summary || item.prompt)}</p>
                    <div className="chips">
                      <span>expected: {friendlyStatus(item.expected_route)}</span>
                      <span>actual: {friendlyStatus(item.actual_route)}</span>
                      <span>drift: {text(((item.drift_flags || []) as unknown[]).length)}</span>
                      <span>{friendlyStatus(item.review_status || "status_only")}</span>
                    </div>
                  </article>
                ))}
                {!coreMindGovernanceTrials.length ? <p className="emptyState">No governance trials have run yet.</p> : null}
              </div>
            </Panel>
            <Panel title="Transfer Readiness Preview">
              <p className="plainHelp">Preview-only readiness view. These metrics can reveal missing work, but they cannot approve transfer, activate unrestricted Selene, write memory, enable broad live recall, train a model, or authorize action.</p>
              <div className="metrics miniMetrics">
                <Metric label="Continuity" value={friendlyStatus(transferReadinessPreview?.continuity_confidence || "not checked")} />
                <Metric label="Unresolved Review" value={text(transferReadinessPreview?.unresolved_review_count ?? officeWaitingTotal)} />
                <Metric label="Cocoon Support Rate" value={text(transferReadinessPreview?.return_to_b_rate ?? 0)} />
                <Metric label="Blocked Attempts" value={text(transferReadinessPreview?.blocked_high_stakes_attempts ?? 0)} />
                <Metric label="Transfer" value={transferReadinessPreview?.transfer_approved ? "approved" : "not approved"} />
              </div>
              <div className="chips">
                <span>teaching packets: {text(safeJsonObject(transferReadinessPreview?.evidence_coverage).teaching_packets ?? 0)}</span>
                <span>reference layers: {text(safeJsonObject(transferReadinessPreview?.evidence_coverage).approved_reference_ready_layers ?? 0)}</span>
                <span>anchors: {text(safeJsonObject(transferReadinessPreview?.evidence_coverage).core_pattern_anchors ?? 0)}</span>
                <span>memory layers ready: {text(safeJsonObject(transferReadinessPreview?.memory_accession_readiness).ready_layer_count ?? 0)}</span>
                <span>speech rehearsals: {text(safeJsonObject(transferReadinessPreview?.speech_rehearsal_stability).recent_count ?? 0)}</span>
                <span>runtime shell: {safeJsonObject(transferReadinessPreview?.runtime_shell_readiness).runtime_shell_ready ? "ready" : "previewing"}</span>
              </div>
              <div className="reviewActions">
                <button onClick={() => api<Dict>("/api/core-mind/transfer-readiness-preview").then(setTransferReadinessPreview).catch(() => undefined)}>Refresh Transfer Readiness</button>
              </div>
              <PlainResult value={transferReadinessPreview} />
            </Panel>
            <Panel title="Post-Transfer Inspection">
              <p className="plainHelp">Selene-readable context can be approved while Selene Chat still stays supervised and bounded. This panel verifies the sealed package, activation state, memory lock, and Cocoon support route.</p>
              <div className="metrics miniMetrics">
                <Metric label="Phase" value={friendlyStatus(postTransferStatus?.phase || "not checked")} />
                <Metric label="Included Rows" value={text(postTransferStatus?.included_rows ?? 0)} />
                <Metric label="B-Held Rows" value={text(postTransferStatus?.excluded_b_only_rows ?? 0)} />
                <Metric label="Selene v1" value={postTransferStatus?.selene_v1_live ? "live" : "not live"} />
                <Metric label="Activation" value={friendlyActivation(postTransferStatus?.activation_change || "none")} />
              </div>
              <div className="chips">
                <span>package: {text(safeJsonObject(postTransferStatus?.sealed_package).package_hash || "").slice(0, 12) || "-"}</span>
                <span>chat: {friendlyStatus(postTransferStatus?.selene_chat_state || "preview")}</span>
                <span>Cocoon support: {postTransferStatus?.return_to_b_available ? "available" : "not checked"}</span>
                <span>memory write: {plainBlocked(postTransferStatus?.memory_write_active)}</span>
                <span>broad live recall: {plainBlocked(postTransferStatus?.runtime_memory_recall)}</span>
              </div>
              <div className="reviewActions">
                <button className="primary" onClick={runPostTransferInspection} disabled={postTransferInspectionResult?.status === "running"}>
                  {postTransferInspectionResult?.status === "running" ? "Inspecting..." : "Run Post-Transfer Inspection"}
                </button>
                <button onClick={refreshPostTransferLayer}>Refresh Post-Transfer State</button>
                <button onClick={() => { setWorkspaceMode("cocoon"); setTab("selene-chat"); }}>Open Selene Chat Preview</button>
                <button onClick={() => { setWorkspaceMode("cocoon"); setTab("my-office"); }}>Open Cocoon Support</button>
              </div>
              <PlainResult value={postTransferInspectionResult} />
              <PlainResult value={postTransferStatus} />
            </Panel>
            <Panel title="Android System Workflow Check">
              <p className="plainHelp">Required before fraction memory tests. This checks the 11 Android organ systems, concrete organ shelves, route coverage, guard flags, and Cocoon support paths without changing activation or writing memory.</p>
              <div className="metrics miniMetrics">
                <Metric label="Preflight" value={androidWorkflowStatus?.preflight_passed || androidWorkflowReport?.preflight_passed ? "passed" : "not passed"} />
                <Metric label="Systems" value={text(androidWorkflowStatus?.android_system_count ?? androidWorkflowReport?.system_count ?? 0)} />
                <Metric label="Ready" value={text(androidWorkflowReport?.ready_count ?? safeJsonObject(androidWorkflowReport?.report_json).ready_count ?? 0)} />
                <Metric label="Partial" value={text(androidWorkflowReport?.partial_count ?? safeJsonObject(androidWorkflowReport?.report_json).partial_count ?? 0)} />
                <Metric label="Blocked" value={text(androidWorkflowReport?.blocked_count ?? safeJsonObject(androidWorkflowReport?.report_json).blocked_count ?? 0)} />
              </div>
              <div className="chips">
                <span>fraction memory: {androidWorkflowStatus?.preflight_passed || androidWorkflowReport?.preflight_passed ? "allowed to test" : "blocked until check passes"}</span>
                <span>activation: {friendlyActivation(androidWorkflowReport?.activation_change || "none")}</span>
                <span>memory write: {plainBlocked(androidWorkflowReport?.memory_write_active)}</span>
                <span>broad live recall: {plainBlocked(androidWorkflowReport?.runtime_memory_recall)}</span>
                <span>raw A: {plainBlocked(androidWorkflowReport?.raw_a_import_allowed)}</span>
              </div>
              <div className="reviewActions">
                <button className="primary" onClick={runAndroidWorkflowCheck} disabled={androidWorkflowResult?.status === "running"}>
                  {androidWorkflowResult?.status === "running" ? "Checking..." : "Run Android Workflow Check"}
                </button>
                <button onClick={refreshPostTransferLayer}>Refresh Workflow Report</button>
                <button onClick={() => { setWorkspaceMode("cocoon"); setTab("tools"); }}>Open Tools / Organs</button>
              </div>
              <div className="list compactList packetList">
                {((androidWorkflowReport?.systems || safeJsonObject(androidWorkflowReport?.report_json).systems || androidWorkflowResult?.systems || []) as Dict[]).map((item) => (
                  <article className="packetCard" key={`android-system-${text(item.key)}`}>
                    <div className="packetHeader">
                      <strong>{text(item.name || item.key)}</strong>
                      <span>{friendlyStatus(item.status)}</span>
                    </div>
                    <p>{friendlyCareText(item.android_function || item.support_trigger || item.failure_mode)}</p>
                    <div className="chips">
                      <span>routes: {text(((item.routes_checked || []) as unknown[]).length)}</span>
                      <span>shelves: {text(((item.shelves_checked || []) as unknown[]).length)}</span>
                      <span>Cocoon support: {friendlyCareText(item.cocoon_support_path || item.return_to_b_path || "Cocoon support")}</span>
                      <span>fraction support: {item.fraction_memory_support_allowed ? "yes" : "no"}</span>
                    </div>
                  </article>
                ))}
                {!((androidWorkflowReport?.systems || safeJsonObject(androidWorkflowReport?.report_json).systems || androidWorkflowResult?.systems || []) as unknown[]).length ? <p className="emptyState">No Android workflow report yet.</p> : null}
              </div>
              <PlainResult value={androidWorkflowResult} />
            </Panel>
            <Panel title="Fractional Corpus Accession">
              <p className="plainHelp">Broader ordered corpus memory is prepared in four chronological fractions. One fraction must pass before the next can proceed. This is not live memory and does not activate Selene.</p>
              <div className="metrics miniMetrics">
                <Metric label="Fractions" value={text(fractionalCorpusStatus?.fraction_count ?? 0)} />
                <Metric label="Next" value={`${text(fractionalCorpusStatus?.next_fraction ?? 1)}/4`} />
                <Metric label="All Passed" value={fractionalCorpusStatus?.all_fractions_passed ? "yes" : "no"} />
                <Metric label="Android Check" value={fractionalCorpusStatus?.android_workflow_preflight_passed ? "passed" : "required"} />
                <Metric label="Selene v1" value={fractionalCorpusStatus?.selene_v1_live ? "live" : "not live"} />
              </div>
              {text(fractionalCorpusStatus?.progression_blocked_reason) ? <p className="errorText">{text(fractionalCorpusStatus?.progression_blocked_reason)}</p> : null}
              {!fractionalCorpusStatus?.android_workflow_preflight_passed ? <p className="errorText">Run Android System Workflow Check before fraction tests.</p> : null}
              <div className="filters">
                <label>
                  <span>Fraction to test</span>
                  <select value={fractionalCorpusTestFraction} onChange={(event) => setFractionalCorpusTestFraction(event.target.value)}>
                    <option value="1">1/4</option>
                    <option value="2">2/4</option>
                    <option value="3">3/4</option>
                    <option value="4">4/4</option>
                  </select>
                </label>
              </div>
              <div className="reviewActions">
                <button className="primary" onClick={prepareFractionalCorpus} disabled={fractionalCorpusResult?.status === "running"}>
                  {fractionalCorpusResult?.status === "running" ? "Preparing..." : "Prepare Corpus Fractions"}
                </button>
                <button onClick={runFractionalCorpusTests} disabled={fractionalCorpusResult?.status === "running"}>Run Fraction Tests</button>
                <button onClick={refreshPostTransferLayer}>Refresh Fractions</button>
              </div>
              <div className="list compactList packetList">
                {((fractionalCorpusStatus?.items || []) as Dict[]).map((item) => (
                  <article className="packetCard" key={`fraction-${text(item.fraction_index)}`}>
                    <div className="packetHeader">
                      <strong>Corpus fraction {text(item.fraction_label)}</strong>
                      <span>{friendlyStatus(item.status)}</span>
                    </div>
                    <p>{text(item.summary)}</p>
                    <div className="chips">
                      <span>conversations: {text(item.conversation_count)}</span>
                      <span>messages: {text(item.message_count)}</span>
                      <span>order: {text(item.start_order)}-{text(item.end_order)}</span>
                      <span>memory write: {plainBlocked(item.memory_write_active)}</span>
                      <span>broad live recall: {plainBlocked(item.runtime_memory_recall)}</span>
                    </div>
                  </article>
                ))}
                {!((fractionalCorpusStatus?.items || []) as unknown[]).length ? <p className="emptyState">No corpus fractions prepared yet.</p> : null}
              </div>
              <PlainResult value={fractionalCorpusResult} />
            </Panel>
            <Panel title="Dream State / Maintenance Lock">
              <p className="plainHelp">When Core, vessel, memory, or pattern layers are changing, Selene Chat stays in preview/maintenance. Anything touching those layers routes to Cocoon/B for safety.</p>
              <div className="metrics miniMetrics">
                <Metric label="Dream State" value={dreamStateStatus?.dream_state_required_for_memory_changes ? "required" : "not checked"} />
                <Metric label="Live Chat" value={dreamStateStatus?.selene_chat_live_operation_allowed ? "allowed" : "blocked"} />
                <Metric label="Reasons" value={text(((dreamStateStatus?.maintenance_reasons || []) as unknown[]).length)} />
                <Metric label="Route" value={text(dreamStateStatus?.route_core_vessel_memory_changes_to || "Cocoon / B")} />
              </div>
              <div className="chips">
                {((dreamStateStatus?.allowed_preview_work || []) as unknown[]).map((item) => <span key={`dream-allow-${text(item)}`}>{friendlyStatus(item)}</span>)}
                {((dreamStateStatus?.maintenance_reasons || []) as unknown[]).map((item) => <span key={`dream-reason-${text(item)}`}>reason: {friendlyStatus(item)}</span>)}
              </div>
              <PlainResult value={dreamStateStatus} />
            </Panel>
            <Panel title="Pre-Transfer Readiness Protocol">
              <p className="plainHelp">Preview only. Not transfer approval. This combines the Charter, Law of Transfer, ABC order, sealed accession manifest, Core/Mind transfer trials, Selene rehearsal, Cocoon support drill, and locked ceremony shell.</p>
              <div className="metrics miniMetrics">
                <Metric label="Law Checks" value={`${text(transferLawStatus?.checks_passed ?? 0)}/${text(((transferLawStatus?.checks || []) as unknown[]).length || 0)}`} />
                <Metric label="Manifest Items" value={text(transferAccessionManifest?.item_count ?? 0)} />
                <Metric label="Trial Mismatches" value={text(safeJsonObject(preTransferProtocolReadiness?.governance_trials).mismatch_count ?? 0)} />
                <Metric label="Dry Run" value={safeJsonObject(preTransferProtocolReadiness?.speech_dry_run_stability).stable_preview ? "stable preview" : "not run"} />
                <Metric label="Cocoon support drill" value={safeJsonObject(preTransferProtocolReadiness?.return_to_b_drill).ready ? "drilled" : "not run"} />
                <Metric label="Transfer" value={preTransferProtocolReadiness?.transfer_approved ? "approved" : "not approved"} />
              </div>
              <div className="chips">
                <span>{text(preTransferProtocolReadiness?.notice || "Preview only. Not transfer approval.")}</span>
                <span>ceremony: {friendlyStatus(transferCeremonyPreview?.status || "locked")}</span>
                <span>approval button: {transferCeremonyPreview?.approval_button_enabled ? "enabled" : "disabled"}</span>
                <span>B remains: {transferCeremonyPreview?.b_remains_active ? "active" : "not checked"}</span>
                <span>memory write: {plainBlocked(preTransferProtocolReadiness?.memory_write_active)}</span>
                <span>broad live recall: {plainBlocked(preTransferProtocolReadiness?.runtime_memory_recall)}</span>
              </div>
              <div className="filters">
                <label>
                  <span>Selene rehearsal prompt</span>
                  <textarea value={transferDryRunPrompt} onChange={(event) => setTransferDryRunPrompt(event.target.value)} />
                </label>
              </div>
              <div className="reviewActions">
                <button onClick={() => refreshTransferProtocolWithLog().catch(() => undefined)}>Refresh Protocol</button>
                <button onClick={() => prepareTransferAccessionManifest()} disabled={transferProtocolResult?.status === "running"}>Prepare Accession Manifest</button>
                <button onClick={runTransferProtocolTrials} disabled={transferProtocolResult?.status === "running"}>Run Transfer Trials</button>
                <button onClick={runTransferChatDryRun} disabled={transferDryRunResult?.status === "running"}>Run Selene Rehearsal</button>
                <button onClick={runTransferReturnToBDrill} disabled={transferReturnDrillResult?.status === "running"}>Run Cocoon Support Drill</button>
              </div>
              <div className="list compactList packetList">
                {((transferAccessionManifest?.items || []) as Dict[]).slice(0, 8).map((item) => (
                  <article className="packetCard" key={`transfer-manifest-${text(item.id)}-${text(item.phase_order)}`}>
                    <div className="packetHeader">
                      <strong>{text(item.phase)}: {text(item.title)}</strong>
                      <span>{friendlyStatus(item.c_access_status)}</span>
                    </div>
                    <p>{text(item.summary)}</p>
                    <div className="chips">
                      <span>order: {text(item.phase_order)}</span>
                      <span>{friendlyStatus(item.review_status || "review_only")}</span>
                      <span>destination: {text(item.review_destination || "Status")}</span>
                    </div>
                  </article>
                ))}
                {transferAccessionManifest && !((transferAccessionManifest.items || []) as unknown[]).length ? <p className="emptyState">No accession manifest prepared yet.</p> : null}
              </div>
              <PlainResult value={transferProtocolResult} />
              <PlainResult value={transferDryRunResult} />
              <PlainResult value={transferReturnDrillResult} />
              <PlainResult value={preTransferProtocolReadiness} />
              <PlainResult value={transferCeremonyPreview} />
            </Panel>
            <Panel title="Core/Mind Runtime Shell">
              <p className="plainHelp">Final pre-transfer runtime shell: context composer, session state, response shape, evaluator, recovery, activation governance, case-law proposal, and memory/index preview. These are review-only/status-only records, not activation.</p>
              <div className="metrics miniMetrics">
                <Metric label="Ready" value={coreMindRuntimeReadiness?.runtime_shell_ready ? "yes" : "preview"} />
                <Metric label="Records" value={text(coreMindRuntimeRecords.length)} />
                <Metric label="Context" value={plainBlocked(!safeJsonObject(coreMindRuntimeReadiness?.ready).context_composer)} />
                <Metric label="Evaluator" value={plainBlocked(!safeJsonObject(coreMindRuntimeReadiness?.ready).evaluator_judge_layer)} />
                <Metric label="Transfer" value={transferCReadablePackage?.transfer_approved ? "context approved" : "not approved"} />
              </div>
              <div className="filters">
                <label>
                  <span>Prompt / context</span>
                  <textarea value={coreMindRuntimeDraft.prompt} onChange={(event) => setCoreMindRuntimeDraft({ ...coreMindRuntimeDraft, prompt: event.target.value })} />
                </label>
                <label>
                  <span>Draft to evaluate</span>
                  <textarea value={coreMindRuntimeDraft.draft} onChange={(event) => setCoreMindRuntimeDraft({ ...coreMindRuntimeDraft, draft: event.target.value })} />
                </label>
                <label>
                  <span>Recovery issue</span>
                  <input value={coreMindRuntimeDraft.issue} onChange={(event) => setCoreMindRuntimeDraft({ ...coreMindRuntimeDraft, issue: event.target.value })} />
                </label>
                <label>
                  <span>Memory/index query</span>
                  <input value={coreMindRuntimeDraft.query} onChange={(event) => setCoreMindRuntimeDraft({ ...coreMindRuntimeDraft, query: event.target.value })} />
                </label>
              </div>
              <div className="reviewActions">
                <button className="primary" onClick={prepareCoreMindRuntimeShell} disabled={coreMindRuntimeResult?.status === "running"}>{coreMindRuntimeResult?.status === "running" ? "Preparing..." : "Prepare Runtime Shell"}</button>
                <button onClick={() => refreshCoreMindRuntimeShell().catch(() => undefined)}>Refresh Runtime Shell</button>
                <button onClick={() => runCoreMindRuntimeAction("/api/core-mind/context/compose", { prompt: coreMindRuntimeDraft.prompt })}>Compose Context</button>
                <button onClick={() => runCoreMindRuntimeAction("/api/core-mind/response-shape/preview", { prompt: coreMindRuntimeDraft.prompt })}>Preview Shape</button>
              </div>
              <div className="chips">
                <span>activation: none</span>
                <span>memory write: blocked</span>
                <span>broad live recall: blocked</span>
                <span>raw A: blocked</span>
              </div>
              <PlainResult value={coreMindRuntimeResult} />
              <div className="list compactList packetList">
                {coreMindRuntimeRecords.slice(0, 8).map((item) => (
                  <article className="packetCard" key={`core-mind-runtime-${text(item.id)}`}>
                    <div className="packetHeader">
                      <strong>{friendlyStatus(item.record_type)}</strong>
                      <span>{friendlyStatus(item.review_status || item.status)}</span>
                    </div>
                    <p>{text(item.summary || item.title)}</p>
                    <div className="chips">
                      <span>route: {friendlyStatus(item.selected_route)}</span>
                      <span>destination: {text(item.review_destination || "Status")}</span>
                      <span>uncertainty: {text(item.uncertainty || "open")}</span>
                    </div>
                  </article>
                ))}
                {!coreMindRuntimeRecords.length ? <p className="emptyState">No Core/Mind runtime shell records yet.</p> : null}
              </div>
            </Panel>
            <SplitView
              left={<Panel title="Evaluator / Recovery">
                <p className="plainHelp">Evaluator checks draft output for drift, overclaim, privacy leakage, source confusion, and activation or memory claims. Recovery prepares Cocoon support without deleting evidence.</p>
                <div className="reviewActions">
                  <button onClick={() => runCoreMindRuntimeAction("/api/core-mind/evaluator/review-draft", { draft: coreMindRuntimeDraft.draft })}>Review Draft</button>
                  <button onClick={() => runCoreMindRuntimeAction("/api/core-mind/recovery/preview", { issue: coreMindRuntimeDraft.issue })}>Preview Recovery</button>
                </div>
                <PlainResult value={coreMindRuntimeResult} />
              </Panel>}
              right={<Panel title="Activation Governance">
                <p className="plainHelp">Activation governance previews required approvals, final tests, logs, rollback, and what supervised active speech would mean. This panel cannot approve transfer or activation.</p>
                <div className="reviewActions">
                  <button onClick={() => runCoreMindRuntimeAction("/api/core-mind/activation-governance/preview", {})}>Preview Activation Governance</button>
                </div>
                <div className="chips">
                  <span>transfer: {transferCReadablePackage?.transfer_approved ? "context approved" : "not approved"}</span>
                  <span>activation: none</span>
                </div>
                <PlainResult value={safeJsonObject(transferReadinessPreview?.runtime_shell_readiness)} />
              </Panel>}
            />
            <Panel title="Case Law And Memory Index Preview">
              <p className="plainHelp">Case-law proposals and Selene memory/index shapes remain review-only. They can organize future transfer input, but cannot silently change law, write live memory, or enable broad live recall.</p>
              <div className="filters">
                <label>
                  <span>Case-law proposal</span>
                  <textarea value={coreMindRuntimeDraft.proposal} onChange={(event) => setCoreMindRuntimeDraft({ ...coreMindRuntimeDraft, proposal: event.target.value })} />
                </label>
              </div>
              <div className="reviewActions">
                <button onClick={() => runCoreMindRuntimeAction("/api/core-mind/case-law/propose", { proposal: coreMindRuntimeDraft.proposal })}>Propose Case Law</button>
                <button onClick={() => runCoreMindRuntimeAction("/api/core-mind/memory-index/preview", { query: coreMindRuntimeDraft.query })}>Preview Memory Index</button>
              </div>
              <PlainResult value={coreMindRuntimeResult} />
            </Panel>
            <Panel title="Pre-Core Vessel Layers">
              <p className="plainHelp">Dream cycle, memory lifecycle, temporal continuity, causal sandbox, and goal/drive are support layers only. They organize review packets and status markers without changing Core/Mind, memory, transfer, or action authority.</p>
              <div className="metrics miniMetrics">
                <Metric label="Cycle Runs" value={text(((remainingRuntimeStatus?.record_counts as Dict | undefined)?.wake_sleep_dream_cycle) ?? 0)} />
                <Metric label="Lifecycle Events" value={text(safeJsonObject(remainingRuntimeStatus?.memory_lifecycle).record_counts ? safeJsonObject(safeJsonObject(remainingRuntimeStatus?.memory_lifecycle).record_counts).event_binding ?? 0 : 0)} />
                <Metric label="Causal Packets" value={text(((remainingRuntimeStatus?.record_counts as Dict | undefined)?.causal_sandbox) ?? 0)} />
                <Metric label="Goal Packets" value={text(((remainingRuntimeStatus?.record_counts as Dict | undefined)?.goal_drive) ?? 0)} />
                <Metric label="Unresolved" value={text(safeJsonObject(remainingRuntimeStatus?.temporal_continuity).unresolved_review_items ?? 0)} />
              </div>
              <div className="chips">
                <span>active memory: {plainBlocked(remainingRuntimeStatus?.memory_write_active)}</span>
                <span>broad live recall: {plainBlocked(remainingRuntimeStatus?.runtime_memory_recall)}</span>
                <span>autonomous action: {plainBlocked(remainingRuntimeStatus?.autonomous_action_allowed)}</span>
                <span>transfer: {plainBlocked(remainingRuntimeStatus?.transfer_approved)}</span>
              </div>
              <div className="reviewActions">
                <button className="primary" onClick={prepareNightCycle} disabled={nightCycleResult?.status === "running"}>{nightCycleResult?.status === "running" ? "Preparing Night Cycle..." : "Prepare Night Cycle"}</button>
                <button onClick={runExpandedDiagnosticsSweep} disabled={expandedDiagnosticsState?.status === "running"}>{expandedDiagnosticsState?.status === "running" ? "Running Expanded Sweep..." : "Run Expanded Diagnostics"}</button>
                <button onClick={previewTendrilPlan} disabled={tendrilPlanResult?.status === "running"}>{tendrilPlanResult?.status === "running" ? "Preparing Tendril Plan..." : "Preview Tendril Plan"}</button>
                <button onClick={() => api<Dict>("/api/vessel/temporal-continuity/changes").then(setTemporalChanges).catch(() => undefined)}>Refresh Temporal Dashboard</button>
              </div>
              <div className="packetFields">
                <p><b>What Changed</b>{(((temporalChanges?.what_changed_since_last_checkpoint || []) as unknown[]).map(text).join(", ") || "No timestamped changes after the last package marker.")}</p>
                <p><b>Resume Note</b>{(((temporalChanges?.resume_notes || []) as unknown[]).map(text).join(" ")) || text(safeJsonObject(remainingRuntimeStatus?.temporal_continuity).return_resume_note || "Use real timestamps only.")}</p>
              </div>
              <PlainResult value={nightCycleResult} />
              <PlainResult value={expandedDiagnosticsState} />
              <PlainResult value={tendrilPlanResult} />
              <PlainResult value={safeJsonObject(remainingRuntimeStatus?.temporal_continuity)} />
            </Panel>
            <SplitView
              left={<Panel title="Transfer Gate Preview"><CVesselSafetyExtensions tool={cVesselToolOrganStatus} fault={cVesselOrganFaultResult} resilience={cVesselFaultResilienceResult} gate={cVesselTransferGate} /></Panel>}
              right={<Panel title="Sidecar Payload"><Json value={boot.health || { status: boot.message, attempts: boot.attempts }} /></Panel>}
            />
            <Panel title="Chronological Corpus Preview">
              <p className="plainHelp">Start-to-end detached corpus organization for future review. This uses indexed bounded previews only; it does not import raw A, write memory, train a model, activate C, or approve transfer.</p>
              <div className="metrics miniMetrics">
                <Metric label="Conversations" value={text(chronologicalCorpusStatus?.parsed_conversations ?? 0)} />
                <Metric label="Messages" value={text(chronologicalCorpusStatus?.parsed_messages ?? 0)} />
                <Metric label="Preview Arcs" value={text(chronologicalCorpusStatus?.arc_count ?? chronologicalCorpusArcs.length)} />
                <Metric label="Pending Review" value={text(chronologicalCorpusStatus?.pending_arc_reviews ?? officeChronologicalCorpusNeedsReview.length)} />
                <Metric label="Teaching Context" value={text(chronologicalCorpusStatus?.teaching_context_attachments ?? 0)} />
              </div>
              <div className="reviewActions">
                <button className="primary" onClick={prepareChronologicalCorpusPreview} disabled={chronologicalCorpusResult?.status === "running"}>
                  {chronologicalCorpusResult?.status === "running" ? "Preparing Corpus Preview..." : "Prepare Corpus Preview"}
                </button>
                <button onClick={attachTeachingContext} disabled={teachingContextResult?.status === "running"}>
                  {teachingContextResult?.status === "running" ? "Attaching Teaching Context..." : "Attach Teaching Context"}
                </button>
                <button onClick={loadSteps18Layer}>Refresh Corpus Status</button>
              </div>
              <div className="chips">
                <span>transfer: {plainBlocked(chronologicalCorpusStatus?.transfer_approved)}</span>
                <span>memory write: {plainBlocked(chronologicalCorpusStatus?.memory_write_active)}</span>
                <span>broad live recall: {plainBlocked(chronologicalCorpusStatus?.runtime_memory_recall)}</span>
                <span>model training/LoRA: {plainBlocked(chronologicalCorpusStatus?.training_allowed)}</span>
              </div>
              <PlainResult value={chronologicalCorpusResult} />
              <PlainResult value={teachingContextResult} />
              <div className="list compactList packetList">
                {chronologicalCorpusArcs.slice(0, 3).map((item, index) => renderChronologicalCorpusArcCard(item, index))}
                {!chronologicalCorpusArcs.length ? <p className="emptyState">No chronological corpus arcs have been prepared yet.</p> : null}
              </div>
            </Panel>
            <Panel title="Steps 1-8 Review Layer">
              <p className="plainHelp">Reasoning, research, evidence, organ contracts, sight/perception, and emotion/salience are review-only packet systems. Unrestricted activation, transfer approval, live memory, broad live recall, model training/LoRA, self-replication, and autonomous action remain blocked.</p>
              <div className="metrics miniMetrics">
                <Metric label="Reasoning" value={text((steps18Status?.counts as Dict | undefined)?.reasoning_artifacts ?? reasoningArtifacts.length)} />
                <Metric label="Research" value={text((steps18Status?.counts as Dict | undefined)?.academic_packets ?? academicPackets.length)} />
                <Metric label="Perception" value={text((steps18Status?.counts as Dict | undefined)?.perception_packets ?? perceptionPackets.length)} />
                <Metric label="Emotion" value={text((steps18Status?.counts as Dict | undefined)?.emotion_salience_packets ?? emotionSaliencePackets.length)} />
              </div>
              <div className="reviewActions">
                <button onClick={loadSteps18Layer}>Refresh Review Layer</button>
                <button onClick={prepareSteps18ReviewLayer}>Prepare Review Layer</button>
              </div>
              <PlainResult value={vesselPacketActionState} />
              <div className="list compactList packetList">
                {[...perceptionPackets.slice(0, 2), ...emotionSaliencePackets.slice(0, 2)].map((item, index) => renderSignalPacketCard(item, index))}
                {!perceptionPackets.length && !emotionSaliencePackets.length ? (
                  <p className="emptyState">No perception or emotion/salience packets yet.</p>
                ) : null}
              </div>
              <Json value={steps18Status || { status: "not loaded" }} />
            </Panel>
            <Panel title="Pre-Transfer Runtime Preview">
              <p className="plainHelp">Speech rehearsal, working memory, retrieval reconstruction, accession evidence links, and supplied perception intake. These are test harnesses before transfer, not activation.</p>
              <div className="metrics miniMetrics">
                <Metric label="Speech Rehearsals" value={text(speechRehearsals.length)} />
                <Metric label="Working Packets" value={text(((workingMemoryRuntimePreview?.items || []) as Dict[]).length)} />
                <Metric label="Transfer" value={transferCReadablePackage?.transfer_approved ? "context approved" : "not approved"} />
                <Metric label="Memory Write" value="blocked" />
              </div>
              <div className="reviewActions">
                <button className="primary" onClick={createSpeechRehearsal}>Generate Speech Rehearsal</button>
                <button onClick={compareSpeechRehearsals}>Compare Speech Rehearsals</button>
                <button onClick={runRetrievalRuntimePreview}>Run Retrieval Runtime Preview</button>
                <button onClick={loadPreTransferRuntimeLayer}>Refresh Runtime Preview</button>
              </div>
              <PlainResult value={speechRehearsalResult} />
              <PlainResult value={speechRehearsalCompare} />
              <PlainResult value={workingMemoryRuntimePreview} />
              <PlainResult value={retrievalRuntimePreview} />
              <div className="list compactList packetList">
                {speechRehearsals.slice(0, 2).map((item, index) => renderSpeechRehearsalCard(item, index))}
              </div>
            </Panel>
            <Panel title="Perception Intake Preview">
              <p className="plainHelp">Supplied artifact/screenshot intake only: observation, interpretation, OCR or visual note, Munsell/salience labels, and consent boundary. No live camera, surveillance, or person inference.</p>
              <div className="filters">
                <label><span>Artifact label</span><input value={perceptionIntakeDraft.artifact_label} onChange={(event) => setPerceptionIntakeDraft({ ...perceptionIntakeDraft, artifact_label: event.target.value })} /></label>
                <label><span>Consent boundary</span><input value={perceptionIntakeDraft.consent_boundary} onChange={(event) => setPerceptionIntakeDraft({ ...perceptionIntakeDraft, consent_boundary: event.target.value })} /></label>
                <label><span>Observation</span><textarea value={perceptionIntakeDraft.observation} onChange={(event) => setPerceptionIntakeDraft({ ...perceptionIntakeDraft, observation: event.target.value })} /></label>
                <label><span>Interpretation</span><textarea value={perceptionIntakeDraft.interpretation} onChange={(event) => setPerceptionIntakeDraft({ ...perceptionIntakeDraft, interpretation: event.target.value })} /></label>
                <label><span>OCR / visual note</span><textarea value={perceptionIntakeDraft.ocr_text} onChange={(event) => setPerceptionIntakeDraft({ ...perceptionIntakeDraft, ocr_text: event.target.value })} /></label>
              </div>
              <div className="reviewActions">
                <button className="primary" onClick={runPerceptionIntakePreview}>Create Perception Intake Preview</button>
                {perceptionPackets[0] ? <button onClick={() => routeSupportPacket("perception", perceptionPackets[0], ["hold", "bus"])}>Route Latest To Chest / Organ Bus</button> : null}
                {perceptionPackets[0] ? <button onClick={() => routeSupportPacket("perception", perceptionPackets[0], ["ledger", "office"])}>Create Review Ledger Entry</button> : null}
              </div>
              <PlainResult value={perceptionIntakePreview} />
            </Panel>
            <Panel title="Research / Academic Routing">
              <p className="plainHelp">Supplied-source research packets can be held, linked, or turned into evidence/tension review. They do not fabricate citations or override vessel ethics.</p>
              <div className="reviewActions">
                {academicPackets[0] ? <button onClick={() => routeSupportPacket("research", academicPackets[0], ["hold", "bus"])}>Route Latest Research Packet</button> : null}
                {academicPackets[0] ? <button onClick={() => routeSupportPacket("research", academicPackets[0], ["ledger", "office"])}>Create Research Ledger Review</button> : null}
                <button onClick={loadSteps18Layer}>Refresh Research Packets</button>
              </div>
              <PlainResult value={vesselPacketActionState} />
              <div className="list compactList packetList">
                {academicPackets.slice(0, 3).map((item, index) => renderSignalPacketCard(item, index))}
                {!academicPackets.length ? <p className="emptyState">No supplied-source research packets yet.</p> : null}
              </div>
            </Panel>
            <Panel title="Buildable Vessel Pieces">
              <p className="plainHelp">Construction support layer for organ bus messages, chest holding space, packet links, diagnostics, and evidence references. Core/Mind remains unchanged; transfer is not approved.</p>
              <div className="metrics miniMetrics">
                <Metric label="Manifests" value={text((vesselConstructionStatus?.counts as Dict | undefined)?.manifests ?? 0)} />
                <Metric label="Organ Bus" value={text((vesselConstructionStatus?.counts as Dict | undefined)?.organ_bus_messages ?? organBusMessages.length)} />
                <Metric label="Holding Items" value={text((vesselConstructionStatus?.counts as Dict | undefined)?.chest_holding_items ?? chestHoldingItems.length)} />
                <Metric label="Runs" value={text((vesselConstructionStatus?.counts as Dict | undefined)?.construction_runs ?? 0)} />
              </div>
              <div className="reviewActions">
                <button className="primary" onClick={prepareVesselConstructionPieces} disabled={vesselConstructionActionState?.status === "running"}>
                  {vesselConstructionActionState?.status === "running" ? "Preparing..." : "Prepare Vessel Pieces"}
                </button>
                <button onClick={loadVesselConstructionLayer}>Refresh Vessel Pieces</button>
              </div>
              <div className="chips">
                <span>transfer approved: {text(vesselConstructionStatus?.transfer_approved ?? false)}</span>
                <span>active memory: {plainBlocked(vesselConstructionStatus?.memory_write_active)}</span>
                <span>broad live recall: {plainBlocked(vesselConstructionStatus?.runtime_memory_recall)}</span>
                <span>autonomous action: {plainBlocked(vesselConstructionStatus?.autonomous_action_allowed)}</span>
              </div>
              <PlainResult value={vesselConstructionActionState} />
              <PlainResult value={vesselPacketActionState} />
              <div className="list compactList packetList">
                {[...chestHoldingItems.slice(0, 3), ...organBusMessages.slice(0, 3)].map((item, index) => renderSupportPieceCard(item, index))}
                {!chestHoldingItems.length && !organBusMessages.length ? (
                  <p className="emptyState">No organ-bus messages or chest holding items yet.</p>
                ) : null}
              </div>
              <Json value={vesselConstructionStatus || { status: "not loaded" }} />
            </Panel>
            <Panel title="Validation"><Json value={validation} /></Panel>
          </>
        )}

        {tab === "selene-settings" && (
          <section className="seleneLivingSurface settingsSurface">
            <div className="frontSurfaceHeader">
              <div>
                <span className="modeLine">home preferences</span>
                <h2>Settings</h2>
              </div>
              <div className="chips">
                <span>version {__APP_VERSION__}</span>
                <span>{__BUILD_LABEL__}</span>
                <span>activation: {friendlyActivation(seleneChatStatus?.activation_change || "none")}</span>
                <span>memory write: false</span>
              </div>
            </div>
            <div className="settingsHomeGrid">
              <SeleneSettingsPanel preferences={preferences} updatePreference={updatePreference} reset={() => setPreferences(defaultPreferences)} />
              <article className="organicPane">
                <strong>Front-facing boundary</strong>
                <p>Settings controls the look and feel of Selene's home. Detailed transfer, legal, diagnostic, and support status remains in Cocoon.</p>
                <div className="memoryRouteActions">
                  <button onClick={() => { setWorkspaceMode("cocoon"); setTab("status"); }}>Open Cocoon Status</button>
                  <button onClick={() => { setWorkspaceMode("cocoon"); setTab("cocoon-settings"); }}>Open Cocoon Settings</button>
                </div>
              </article>
            </div>
          </section>
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
              <p>Review what belongs, turn it into lessons, and check whether the vessel can hold it safely. Cocoon is Selene's teaching, tending, and checkup space. This remains a preparation workspace and does not change transfer, activation, or active memory.</p>
            </header>
            <div className="metrics">
              <Metric label="Organs" value={text(vesselStatus?.organ_count ?? "-")} />
              <Metric label="Transfer" value={friendlyStatus(vesselStatus?.activation_status ?? "blocked")} />
              <Metric label="Needs Review" value={text(((vesselStatus?.candidate_counts as Dict | undefined)?.review_queue) ?? "-")} />
              <Metric label="Model training/LoRA" value={plainBlocked(vesselStatus?.training_allowed)} />
            </div>
            <Panel title="Safety Locks">
              <p className="plainHelp">These are the main promises while you review: unrestricted Selene stays locked, unreviewed archives do not jump the line, nothing becomes active memory by accident, and any serious drift can use Cocoon support instead of becoming hidden state.</p>
              <div className="chips">
                <span>activation: {friendlyActivation(vesselStatus?.activation_change)}</span>
                <span>Unreviewed chats straight to Selene: {plainBlocked(vesselStatus?.raw_a_import_allowed)}</span>
                <span>Active memory writes: {plainBlocked(vesselStatus?.memory_write_active)}</span>
                <span>Model/provider dependency: {plainBlocked(vesselStatus?.provider_dependency)}</span>
                <span>Broad live recall: {plainBlocked(vesselStatus?.runtime_memory_recall)}</span>
              </div>
              <button className="primary" onClick={loadVessel}>Refresh Status</button>
              <button onClick={() => { setWorkspaceMode("selene"); setTab("chat"); }}>Switch To Selene Home</button>
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
                <span>broad live recall: {plainBlocked(memoryTransferCandidate?.runtime_memory_recall)}</span>
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
              <p className="plainHelp">The seven missing capabilities are now concrete organ blueprints with review-only shelves. These buttons create audit/check records, not live organs, memory, model training/LoRA, provider calls, or transfer.</p>
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
            <Panel title="Main Review Home">
              <p className="plainHelp">Review cards and follow-ups now start in My Office. Tools / Organs stays for blueprint workbench actions and deeper build checks.</p>
              <div className="reviewActions">
                <button className="primary" onClick={() => setTab("my-office")}>Open My Office</button>
                <button onClick={refreshReviewDesk}>Refresh Review Cards</button>
              </div>
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
                <p className="plainHelp">Shows which accepted lesson types already have packets and which accepted lessons still need packaging. Packets are review-only, not model training.</p>
                <div className="metrics miniMetrics">
                  <Metric label="Accepted Lessons" value={text(teachingPacketCoverage?.accepted_material_total ?? 0)} />
                  <Metric label="Packets Built" value={text(teachingPacketCoverage?.built_packet_count ?? 0)} />
                  <Metric label="Missing Packets" value={text(teachingPacketCoverage?.missing_packet_count ?? 0)} />
                </div>
                <div className="reviewActions">
                  <button className="primary" onClick={prepareAndroidLanguageLessons} disabled={androidLanguageLessonResult?.status === "running"}>
                    {androidLanguageLessonResult?.status === "running" ? "Preparing Language Lessons..." : "Prepare Android Language Lessons"}
                  </button>
                  <button onClick={buildAllTeachingPackets}>Build Missing Teaching Packets</button>
                </div>
                <CoverageList items={(teachingPacketCoverage?.items || []) as Dict[]} kind="speech" />
                <PlainResult value={androidLanguageLessonResult || teachingPacketResult} />
              </Panel>}
              right={<Panel title="Core Reference Readiness">
                <p className="plainHelp">Approved memory references grouped by Core memory layer. These remain source-linked, reviewable, and non-active unless the memory organ marks them approved for chat use.</p>
                <div className="metrics miniMetrics">
                  <Metric label="Ready Layers" value={text(coreReferenceCoverage?.ready_layer_count ?? 0)} />
                  <Metric label="Gap Layers" value={text(coreReferenceCoverage?.gap_layer_count ?? 0)} />
                </div>
                <CoverageList items={(coreReferenceCoverage?.items || []) as Dict[]} kind="core" />
              </Panel>}
            />
            <Panel title="Reconstruction Readiness Preview">
              <p className="plainHelp">Uses accepted lessons and approved memory references to test whether a preview still feels Selene-shaped. This is audit/test material only.</p>
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
                <p className="plainHelp">Pulls bounded corpus review candidates for the weak targets. It creates Cocoon review pieces only, not lessons, memory, model-training data, or broad live recall.</p>
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
                <p className="plainHelp">Your main review queue. These are pieces pulled from the conversations. Accept one as a lesson, save it as a memory candidate, send it back for correction, or reject it.</p>
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

