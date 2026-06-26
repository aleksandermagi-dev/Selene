import type { SelenePreferences } from "./types";

export const SELENE_ICON = "/selenesIcon.png";
export const preferenceKey = "selene-ui-preferences";
export const defaultPreferences: SelenePreferences = {
  theme: "selene-dark",
  density: "comfortable",
  textSize: "standard",
  languageStyle: "warm",
  font: "system",
  userBubble: "#2f3a62",
  userText: "#f3f7ff",
  seleneBubble: "#171d3f",
  seleneText: "#f8f5ff"
};

export const navGroups: { label: string; items: { id: string; label: string }[] }[] = [
  { label: "Selene", items: [{ id: "selene-chat", label: "Selene Chat" }, { id: "chat", label: "Chat Preview" }, { id: "memory", label: "Memory / Future References" }, { id: "tendril", label: "Tendril" }, { id: "selene-settings", label: "Selene Settings" }] },
  { label: "Cocoon", items: [{ id: "my-office", label: "My Office" }, { id: "transfer-ceremony", label: "Transfer Ceremony" }, { id: "vessel", label: "B Cocoon Build" }, { id: "teaching", label: "Teaching / Lessons" }, { id: "tools", label: "Tools / Organs" }, { id: "status", label: "Status" }, { id: "cocoon-settings", label: "Cocoon Settings" }] },
  { label: "Evidence", items: [{ id: "dashboard", label: "Evidence Dashboard" }, { id: "evidence", label: "Evidence Browser" }, { id: "detached corpus", label: "Detached Corpus" }, { id: "chat gate", label: "Chat Gate" }] }
];

export const workspaceGroups = {
  selene: ["Selene"],
  cocoon: ["Cocoon", "Evidence"]
} as const;

export const workspaceTabs = {
  selene: ["selene-chat", "chat", "memory", "tendril", "selene-settings"],
  cocoon: ["my-office", "my-review", "transfer-ceremony", "vessel", "teaching", "tools", "status", "cocoon-settings", "dashboard", "evidence", "detached corpus", "chat gate"]
} as const;

export const vesselBackedTabs = ["selene-chat", "chat", "my-office", "my-review", "transfer-ceremony", "vessel", "memory", "teaching", "tendril", "tools", "status", "selene-settings", "cocoon-settings"];
export const statuses = ["", "usable_reviewed_evidence", "review_only", "excluded_from_use", "ambiguous"];
