from __future__ import annotations

import json

import pytest

from selene.library_tendril import LibraryTendrilClient, LibraryTendrilConfig


class _Response:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode()


def test_adapter_is_disabled_without_explicit_enable(monkeypatch) -> None:
    monkeypatch.delenv("SELENE_LIBRARY_TENDRIL_ENABLED", raising=False)
    monkeypatch.setenv("GLOA_TENDRIL_TOKEN", "secret")
    client = LibraryTendrilClient()
    assert client.available() is False
    with pytest.raises(RuntimeError, match="disabled"):
        client.query("continuity")


def test_query_uses_bounded_observe_envelope(monkeypatch) -> None:
    captured = {}

    def fake_open(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return _Response({"protocolVersion": "gloa-tendril/1", "taskId": "task", "status": "ok", "authorityStatus": "non_mutating_observation"})

    monkeypatch.setattr("selene.library_tendril.urlrequest.urlopen", fake_open)
    client = LibraryTendrilClient(
        LibraryTendrilConfig(True, "http://127.0.0.1:47832", "selene-token")
    )
    result = client.query("memory boundary")
    envelope = json.loads(captured["request"].data)
    assert result["status"] == "ok"
    assert envelope["actor"] == {"id": "selene", "kind": "agent"}
    assert envelope["mode"] == "observe"
    assert envelope["action"] == "query"
    assert envelope["fallbackBehavior"] == "pause_and_report"
    assert captured["request"].headers["Authorization"] == "Bearer selene-token"
    assert envelope["requestedAt"]


def test_adapter_rejects_non_loopback_and_exposes_no_publish() -> None:
    client = LibraryTendrilClient(LibraryTendrilConfig(True, "https://example.com", "secret"))
    assert client.available() is False
    with pytest.raises(RuntimeError, match="loopback-only"):
        client.query("anything")
    assert not hasattr(client, "publish")
    assert "secret" not in repr(client.config)


def test_adapter_rejects_personal_memory_purpose() -> None:
    client = LibraryTendrilClient(
        LibraryTendrilConfig(True, "http://127.0.0.1:47832", "selene-token")
    )
    with pytest.raises(ValueError, match="purpose"):
        client.query("anything", purpose="personal-memory")
