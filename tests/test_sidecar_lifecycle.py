from __future__ import annotations

import http.client
import json
import threading

from selene.sidecar import SeleneHandler, SeleneServer


def test_sidecar_shutdown_endpoint_stops_server(tmp_path):
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "selene.db")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
    conn.request("POST", "/shutdown", body="{}", headers={"Content-Type": "application/json"})
    response = conn.getresponse()
    payload = json.loads(response.read().decode("utf-8"))
    conn.close()

    thread.join(timeout=5)
    server.server_close()
    server.conn.close()

    assert response.status == 200
    assert payload["status"] == "shutting_down"
    assert payload["activation_change"] == "none"
    assert payload["memory_write_active"] is False
    assert not thread.is_alive()
