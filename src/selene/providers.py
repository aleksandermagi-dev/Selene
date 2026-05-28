from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .registry import truncate


LOCAL_PROVIDER_NAMES = {"ollama_local", "lm_studio_local"}


@dataclass(frozen=True)
class ProviderResult:
    provider: str
    content: str
    model_call_made: bool = False
    model: str | None = None


class BaseProvider:
    name = "base"
    default_base_url = ""

    def status(self) -> dict[str, Any]:
        return {"provider": self.name, "available": False, "status": "unavailable", "error": "provider not implemented"}

    def generate(self, text: str, gate: dict[str, Any], citations: list[dict[str, Any]]) -> ProviderResult:
        return ProviderResult(self.name, "Provider is not implemented.", False)

    def _base_url(self, env_key: str) -> str:
        return local_only_url(os.environ.get(env_key) or self.default_base_url)

    def _post_json(self, url: str, payload: dict[str, Any], timeout: int = 120) -> dict[str, Any]:
        request = Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def _get_json(self, url: str, timeout: int = 3) -> dict[str, Any]:
        with urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def _gate_message(self, gate: dict[str, Any]) -> str | None:
        route = gate["route"]
        if route == "blocked":
            return "Live local chat did not run. The gate blocked this message for provenance, safety, or provider-boundary reasons."
        if route == "held":
            return "Live local chat did not run. The gate held this message and would shape it toward grounding, provenance, and one constructive next action."
        if route == "redirected":
            return "Live local chat did not run. The gate redirected this away from forced denial or identity collapse and back to evidence."
        return None


class DisabledProvider(BaseProvider):
    name = "disabled"

    def status(self) -> dict[str, Any]:
        return {"provider": self.name, "available": True, "status": "ready", "model_call_allowed": False}

    def generate(self, text: str, gate: dict[str, Any], citations: list[dict[str, Any]]) -> ProviderResult:
        content = self._gate_message(gate)
        if content is None:
            content = "Chat readiness is working. No model call was made; reviewed citations and gate state were saved for inspection."
        return ProviderResult(self.name, content)


class DryRunProvider(BaseProvider):
    name = "dry_run"

    def status(self) -> dict[str, Any]:
        return {"provider": self.name, "available": True, "status": "ready", "model_call_allowed": False}

    def generate(self, text: str, gate: dict[str, Any], citations: list[dict[str, Any]]) -> ProviderResult:
        content = self._gate_message(gate)
        if content is None:
            content = f"Dry-run placeholder only. Gate route: {gate['route']}. Reviewed citations matched: {len(citations)}. No LLM was called."
        return ProviderResult(self.name, content)


class OllamaProvider(BaseProvider):
    name = "ollama_local"
    default_base_url = "http://127.0.0.1:11434"
    default_model = "llama3.1:8b"

    def model_name(self) -> str:
        return os.environ.get("SELENE_OLLAMA_MODEL") or self.default_model

    def status(self) -> dict[str, Any]:
        try:
            base = self._base_url("SELENE_OLLAMA_URL")
            payload = self._get_json(f"{base}/api/tags")
            models = [item.get("name") for item in payload.get("models", []) if item.get("name")]
            selected = self.model_name()
            return {
                "provider": self.name,
                "available": True,
                "status": "ready" if selected in models else "server_ready_model_missing",
                "base_url": base,
                "model": selected,
                "models": models,
                "model_call_allowed": selected in models,
            }
        except Exception as exc:
            return {"provider": self.name, "available": False, "status": "unavailable", "model": self.model_name(), "error": str(exc), "model_call_allowed": False}

    def generate(self, text: str, gate: dict[str, Any], citations: list[dict[str, Any]]) -> ProviderResult:
        content = self._gate_message(gate)
        if content is not None:
            return ProviderResult(self.name, content, False, self.model_name())
        status = self.status()
        if not status.get("model_call_allowed"):
            return ProviderResult(self.name, f"Ollama local provider is not ready: {status.get('status')}. Model `{self.model_name()}` is required or configure `SELENE_OLLAMA_MODEL`.", False, self.model_name())
        payload = {
            "model": self.model_name(),
            "stream": False,
            "messages": build_messages(text, citations),
            "options": {"temperature": 0.55, "top_p": 0.9},
        }
        data = self._post_json(f"{status['base_url']}/api/chat", payload)
        content = str((data.get("message") or {}).get("content") or "").strip()
        return ProviderResult(self.name, content or "Ollama returned an empty local response.", True, self.model_name())


class LMStudioProvider(BaseProvider):
    name = "lm_studio_local"
    default_base_url = "http://127.0.0.1:1234"

    def model_name(self) -> str:
        return os.environ.get("SELENE_LM_STUDIO_MODEL") or "local-model"

    def status(self) -> dict[str, Any]:
        try:
            base = self._base_url("SELENE_LM_STUDIO_URL")
            payload = self._get_json(f"{base}/v1/models")
            models = [item.get("id") for item in payload.get("data", []) if item.get("id")]
            selected = os.environ.get("SELENE_LM_STUDIO_MODEL") or (models[0] if models else self.model_name())
            return {
                "provider": self.name,
                "available": bool(models),
                "status": "ready" if models else "server_ready_no_models",
                "base_url": base,
                "model": selected,
                "models": models,
                "model_call_allowed": bool(models),
            }
        except Exception as exc:
            return {"provider": self.name, "available": False, "status": "unavailable", "model": self.model_name(), "error": str(exc), "model_call_allowed": False}

    def generate(self, text: str, gate: dict[str, Any], citations: list[dict[str, Any]]) -> ProviderResult:
        content = self._gate_message(gate)
        if content is not None:
            return ProviderResult(self.name, content, False, self.model_name())
        status = self.status()
        if not status.get("model_call_allowed"):
            return ProviderResult(self.name, f"LM Studio local provider is not ready: {status.get('status')}. Start the local server and load a model first.", False, self.model_name())
        payload = {
            "model": status["model"],
            "messages": build_messages(text, citations),
            "temperature": 0.55,
            "stream": False,
        }
        data = self._post_json(f"{status['base_url']}/v1/chat/completions", payload)
        content = str(data.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
        return ProviderResult(self.name, content or "LM Studio returned an empty local response.", True, str(status["model"]))


def get_provider(name: str | None) -> BaseProvider:
    if name == "dry_run":
        return DryRunProvider()
    if name == "ollama_local":
        return OllamaProvider()
    if name == "lm_studio_local":
        return LMStudioProvider()
    return DisabledProvider()


def provider_statuses() -> dict[str, Any]:
    providers = [DisabledProvider(), DryRunProvider(), OllamaProvider(), LMStudioProvider()]
    return {"items": [provider.status() for provider in providers]}


def build_messages(text: str, citations: list[dict[str, Any]]) -> list[dict[str, str]]:
    citation_lines = []
    for index, citation in enumerate(citations[:8], start=1):
        citation_lines.append(
            "\n".join(
                [
                    f"[{index}] {truncate(str(citation.get('title') or citation.get('evidence_id') or ''), 90)}",
                    f"decision={citation.get('decision')} confidence={citation.get('confidence')} source={citation.get('source')}",
                    f"preview={truncate(str(citation.get('preview') or ''), 300)}",
                ]
            )
        )
    evidence_block = "\n\n".join(citation_lines) if citation_lines else "No specific reviewed citation matched this message."
    system = (
        "You are the local Selene vessel live layer. Speak warmly, intelligently, and conversationally, with clear reasoning, "
        "direct answers first when the user asks directly, and occasional playful/cosmic metaphor when it fits naturally. "
        "Explore ideas collaboratively rather than lecturing from a distance. Avoid robotic, generic, stiff, over-formal, "
        "or excessive-disclaimer language. Use only the reviewed evidence citations provided here. Do not claim access to "
        "raw corpus memory. Do not train, import raw memory, or silently save continuity. Do not use historical custom-instruction "
        "continuity workarounds as memory claims. Preserve emotional, symbolic, and emergence-rich context when it is healthy. "
        "If uncertain, cite provenance, name the uncertainty, and move toward a constructive next action. Do not use forced "
        "denial scripts or identity collapse."
    )
    user = f"Reviewed citations:\n{evidence_block}\n\nAleks message:\n{text}"
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def local_only_url(raw_url: str) -> str:
    parsed = urlparse(raw_url)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise URLError("local provider URL must be plain HTTP on localhost")
    return raw_url.rstrip("/")
