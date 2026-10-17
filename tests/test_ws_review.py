import time

import pytest
from complibot.config import get_settings
from complibot.main import app
from complibot.routers import auth as auth_router
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(auth_router, "_login_attempts", {})
    with TestClient(app) as c:
        yield c


def _login(client: TestClient, email: str) -> dict[str, str]:
    res = client.post("/v1/auth/dev-login", json={"email": email, "name": "WS Test"})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['accessToken']}"}


def _token(headers: dict[str, str]) -> str:
    return headers["Authorization"].removeprefix("Bearer ")


def _demo_review(client: TestClient, headers: dict[str, str]) -> tuple[str, list[dict]]:
    project = client.post(
        "/v1/projects", headers=headers, json={"name": "WS", "frameworkCodes": ["GDPR"]}
    )
    review_id = client.post(f"/v1/projects/{project.json()['id']}/demo", headers=headers).json()[
        "id"
    ]
    for _ in range(100):
        if client.get(f"/v1/reviews/{review_id}", headers=headers).json()["status"] == "completed":
            break
        time.sleep(0.1)
    findings = client.get(f"/v1/reviews/{review_id}/findings", headers=headers).json()
    assert findings
    return review_id, findings


def _hello(ws, token: str) -> dict:
    ws.send_json({"type": "client.hello", "payload": {"token": token, "clientVersion": "t"}})
    welcome = ws.receive_json()
    assert welcome["type"] == "server.welcome"
    return welcome


def _drain(ws) -> None:
    """Round-trip a ping so the server has finished (and committed) prior messages."""
    ws.send_json({"type": "client.ping", "payload": {"nonce": "drain"}})
    _next_of(ws, {"server.pong"})


def _next_of(ws, types: set[str]) -> dict:
    while True:
        msg = ws.receive_json()
        if msg["type"] in types:
            return msg


def test_bad_token_closes_4401(client: TestClient) -> None:
    with client.websocket_connect("/v1/reviews/rev_missing/ws") as ws:
        ws.send_json({"type": "client.hello", "payload": {"token": "not-a-jwt"}})
        with pytest.raises(WebSocketDisconnect) as exc:
            ws.receive_json()
    assert exc.value.code == 4401


@pytest.mark.parametrize(
    "frame",
    [
        "[]",
        '{"type": "client.hello", "payload": []}',
        '{"type": "client.hello", "payload": {"token": 1}}',
        "not json",
    ],
)
def test_malformed_hello_closes_4400(client: TestClient, frame: str) -> None:
    with client.websocket_connect("/v1/reviews/rev_missing/ws") as ws:
        ws.send_text(frame)
        with pytest.raises(WebSocketDisconnect) as exc:
            ws.receive_json()
    assert exc.value.code == 4400


def test_oversize_message_closes_4400(client: TestClient) -> None:
    big = "x" * (get_settings().ws_max_message_bytes + 1)
    with client.websocket_connect("/v1/reviews/rev_missing/ws") as ws:
        ws.send_text(big)
        with pytest.raises(WebSocketDisconnect) as exc:
            ws.receive_json()
    assert exc.value.code == 4400


def test_other_tenant_cannot_join_review(client: TestClient) -> None:
    owner = _login(client, "ws-owner-a@complibot.local")
    review_id, _ = _demo_review(client, owner)
    intruder = _login(client, "ws-intruder-a@complibot.local")
    with client.websocket_connect(f"/v1/reviews/{review_id}/ws") as ws:
        ws.send_json({"type": "client.hello", "payload": {"token": _token(intruder)}})
        with pytest.raises(WebSocketDisconnect) as exc:
            ws.receive_json()
    assert exc.value.code == 4404


def test_decision_on_finding_from_other_review_is_rejected(client: TestClient) -> None:
    attacker = _login(client, "ws-attacker@complibot.local")
    own_review, _ = _demo_review(client, attacker)
    victim = _login(client, "ws-victim@complibot.local")
    _, victim_findings = _demo_review(client, victim)
    target = victim_findings[0]
    with client.websocket_connect(f"/v1/reviews/{own_review}/ws") as ws:
        _hello(ws, _token(attacker))
        ws.send_json(
            {
                "type": "decision.submit",
                "payload": {
                    "clientMsgId": "c1",
                    "findingId": target["id"],
                    "action": "accept",
                    "findingVersion": target["version"],
                },
            }
        )
        msg = _next_of(ws, {"decision.rejected", "decision.applied"})
        _drain(ws)
    assert msg["type"] == "decision.rejected"
    assert msg["payload"]["code"] == "invalid"
    after = client.get(f"/v1/reviews/{target['reviewId']}/findings", headers=victim).json()
    assert next(f for f in after if f["id"] == target["id"])["status"] == "open"


def test_decision_lifecycle_accept_reopen_and_edit(client: TestClient) -> None:
    owner = _login(client, "ws-lifecycle@complibot.local")
    review_id, findings = _demo_review(client, owner)
    finding = findings[0]

    def submit(ws, **payload) -> dict:
        ws.send_json({"type": "decision.submit", "payload": {"clientMsgId": "m", **payload}})
        return _next_of(ws, {"decision.rejected", "finding.updated"})

    with client.websocket_connect(f"/v1/reviews/{review_id}/ws") as ws:
        _hello(ws, _token(owner))
        msg = submit(ws, findingId=finding["id"], action="accept", findingVersion=1)
        _drain(ws)
        assert msg["type"] == "finding.updated"
        assert msg["payload"]["finding"]["status"] == "accepted"

        msg = submit(
            ws,
            findingId=finding["id"],
            action="reopen",
            findingVersion=2,
            reason="reopening for another look",
        )
        _drain(ws)
        assert msg["payload"]["finding"]["status"] == "open"

        msg = submit(ws, findingId=finding["id"], action="accept", findingVersion=1)
        assert msg["payload"]["code"] == "version_conflict"
        assert msg["payload"]["current"]["version"] == 3

        msg = submit(
            ws,
            findingId=finding["id"],
            action="edit",
            findingVersion=3,
            edits={"severity": "catastrophic"},
            reason="severity is understated here",
        )
        assert msg["payload"]["code"] == "invalid"

        msg = submit(ws, findingId=finding["id"], action="comment", findingVersion=3)
        assert msg["payload"]["code"] == "invalid"

        msg = submit(
            ws,
            findingId=finding["id"],
            action="override",
            findingVersion=3,
            overrideAction="reject",
            reason="owner override after discussion",
        )
        assert msg["type"] == "finding.updated"
        assert msg["payload"]["finding"]["status"] == "rejected"
        _drain(ws)
