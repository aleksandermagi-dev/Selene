from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
import json
import os
from typing import Any
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest
from uuid import uuid4


PROTOCOL_VERSION = "gloa-tendril/1"
ALLOWED_ACTIONS = {"overview", "list_records", "read_record", "query", "validate", "list_proposals", "create_proposal"}
ALLOWED_PURPOSES = {"research", "architecture", "implementation", "continuity-reference", "library-governance"}


@dataclass(frozen=True, slots=True)
class LibraryTendrilConfig:
    enabled: bool
    service_url: str
    token: str = field(repr=False)
    actor_id: str = "selene"
    timeout_seconds: float = 5.0

    @classmethod
    def from_env(cls) -> "LibraryTendrilConfig":
        return cls(
            enabled=os.getenv("SELENE_LIBRARY_TENDRIL_ENABLED", "").lower() == "true",
            service_url=os.getenv("GLOA_TENDRIL_URL", "http://127.0.0.1:47832").rstrip("/"),
            token=os.getenv("GLOA_TENDRIL_TOKEN", ""),
        )


class LibraryTendrilClient:
    """Disabled-by-default shared Library reference/proposal adapter.

    This does not activate Selene C, Tendril execution, memory writes, archive
    access, training, or identity transfer. Returned records remain attributed
    external Library material under Selene's own laws.
    """

    def __init__(self, config: LibraryTendrilConfig | None = None):
        self.config = config or LibraryTendrilConfig.from_env()

    def available(self) -> bool:
        return self.config.enabled and bool(self.config.token) and self._is_loopback(self.config.service_url)

    def query(self, text: str, *, purpose: str = "research") -> dict[str, Any]:
        return self._send(
            action="query",
            mode="observe",
            purpose=purpose,
            risk_level="low",
            expected_output="Attributed shared Library records permitted for Selene",
            payload={"query": text},
        )

    def list_records(self, *, purpose: str = "research") -> dict[str, Any]:
        return self._send(
            action="list_records",
            mode="observe",
            purpose=purpose,
            risk_level="low",
            expected_output="Permitted shared Library record summaries for Selene",
            payload={},
        )

    def create_proposal(
        self,
        *,
        title: str,
        summary: str,
        source_ids: list[str],
        proposal_type: str = "admission",
        purpose: str = "research",
    ) -> dict[str, Any]:
        return self._send(
            action="create_proposal",
            mode="propose",
            purpose=purpose,
            risk_level="medium",
            expected_output="A shared proposal awaiting Aleks review",
            payload={
                "title": title,
                "summary": summary,
                "sourceIds": source_ids,
                "proposalType": proposal_type,
            },
            reversal_conditions=["Aleks may reject or archive the proposal"],
        )

    def _send(
        self,
        *,
        action: str,
        mode: str,
        purpose: str,
        risk_level: str,
        expected_output: str,
        payload: dict[str, Any],
        reversal_conditions: list[str] | None = None,
    ) -> dict[str, Any]:
        if action not in ALLOWED_ACTIONS or mode not in {"observe", "propose"}:
            raise ValueError("Library Tendril action is outside Selene's adapter boundary")
        if purpose not in ALLOWED_PURPOSES:
            raise ValueError("Library Tendril purpose is outside Selene's adapter boundary")
        if not self.config.enabled:
            raise RuntimeError("Selene Library Tendril adapter is disabled")
        if not self.config.token:
            raise RuntimeError("Selene Library Tendril credential is not configured")
        if not self._is_loopback(self.config.service_url):
            raise RuntimeError("Selene Library Tendril requires a loopback-only service URL")
        request_id = f"selene-lib-{uuid4().hex}"
        envelope = {
            "protocolVersion": PROTOCOL_VERSION,
            "requestId": request_id,
            "taskId": f"selene-library-task-{uuid4().hex}",
            "planId": f"selene-library-plan-{uuid4().hex}",
            "stepId": f"selene-library-step-{uuid4().hex}",
            "actor": {"id": self.config.actor_id, "kind": "agent"},
            "purpose": purpose,
            "mode": mode,
            "action": action,
            "riskLevel": risk_level,
            "expectedOutput": expected_output,
            "fallbackBehavior": "pause_and_report",
            "reversalConditions": list(reversal_conditions or []),
            "approval": None,
            "payload": payload,
            "requestedAt": datetime.now(UTC).isoformat(),
        }
        request = urlrequest.Request(
            f"{self.config.service_url}/v1/tendril/requests",
            data=json.dumps(envelope).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.config.token}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlrequest.urlopen(request, timeout=self.config.timeout_seconds) as response:
                result = json.loads(response.read().decode("utf-8"))
                if result.get("protocolVersion") != PROTOCOL_VERSION:
                    raise RuntimeError("Library Tendril response used an unexpected protocol")
                return result
        except urlerror.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Library Tendril request was rejected ({exc.code}): {detail}") from exc
        except urlerror.URLError as exc:
            raise RuntimeError(f"Library Tendril service is unavailable: {exc.reason}") from exc

    @staticmethod
    def _is_loopback(value: str) -> bool:
        parsed = urlparse.urlparse(value)
        return parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost", "::1"}
