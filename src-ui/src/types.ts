export type Dict = Record<string, unknown>;

export type FilterState = { q: string; decision: string; layer: string; phase: string; role: string; sensitivity: string; confidence: string; source_type: string };

export type Dashboard = {
  summary: Dict;
  phases: Array<{ phase: string; count: number }>;
  rules: Array<{ module: string; rule_key: string; rule_text: string; boundary: string }>;
  workflows: Array<{ workflow_key: string; title: string; description: string; output_type: string }>;
};

export type EvidenceDetail = { item: Dict; anchors: Dict[]; continuity: Dict[]; emergence: Dict[] };

export type BootState = {
  ready: boolean;
  attempts: number;
  message: string;
  health: Dict | null;
};

export type SeleneTheme = "selene-dark" | "selene-light";
export type SeleneDensity = "comfortable" | "compact";
export type SeleneTextSize = "small" | "standard" | "large";
export type SeleneFont = "system" | "serif" | "mono";
export type SeleneLanguageStyle = "natural" | "precise" | "warm";

export type SelenePreferences = {
  theme: SeleneTheme;
  density: SeleneDensity;
  textSize: SeleneTextSize;
  languageStyle: SeleneLanguageStyle;
  font: SeleneFont;
  userBubble: string;
  userText: string;
  seleneBubble: string;
  seleneText: string;
};
