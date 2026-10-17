import asyncio
import json
import uuid
from datetime import UTC, datetime
from typing import Any

import jwt
from complibot.config import get_settings
from complibot.db.models import FindingRow, ProjectMember, Review, ReviewDecisionRow, ReviewEvent
from complibot.db.session import SessionLocal
from complibot.ids import new_decision_id
from complibot.schemas import Finding, ReviewDecision
from complibot.services.events import append_review_event
from complibot.ws.decisions import EDITABLE_FIELDS, decision_validation_error
from complibot.ws.hub import review_hub
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from sqlalchemy import select

router = APIRouter()

HELLO_TIMEOUT_S = 5.0
PRESENCE_STATES = frozenset({"viewing", "idle"})


class BadMessage(Exception):
    pass


def _decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(
        token,
        settings.dev_auth_secret,
        algorithms=["HS256"],
        audience=settings.jwt_audience,
        issuer=settings.jwt_issuer,
    )


def _max_ws_bytes() -> int:
    return get_settings().ws_max_message_bytes


async def _receive_json_limited(websocket: WebSocket) -> dict[str, Any]:
    message = await websocket.receive()
    if message["type"] == "websocket.disconnect":
        raise WebSocketDisconnect(message.get("code", 1000))
    raw = message.get("text")
    if raw is None or len(raw.encode("utf-8")) > _max_ws_bytes():
        raise BadMessage
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise BadMessage from exc
    if not isinstance(data, dict):
        raise BadMessage
    payload = data.get("payload", {})
    if not isinstance(payload, dict):
        raise BadMessage
    return data


@router.websocket("/v1/reviews/{review_id}/ws")
async def review_ws(websocket: WebSocket, review_id: str) -> None:
    connection_id = str(uuid.uuid4())
    user_id: str | None = None
    role = "viewer"
    joined = False
    try:
        await websocket.accept()
        try:
            hello = await asyncio.wait_for(_receive_json_limited(websocket), HELLO_TIMEOUT_S)
        except TimeoutError:
            await websocket.close(code=4401)
            return
        if hello.get("type") != "client.hello":
            await websocket.close(code=4400)
            return
        payload = hello.get("payload", hello)
        token = payload.get("token")
        last_seq = payload.get("lastSeq") or 0
        if not isinstance(token, str) or not isinstance(last_seq, int):
            raise BadMessage
        try:
            claims = _decode_token(token)
        except jwt.PyJWTError:
            await websocket.close(code=4401)
            return
        if not claims.get("sub") or not claims.get("tenant_id"):
            await websocket.close(code=4401)
            return
        user_id = str(claims["sub"])
        tenant_id = str(claims["tenant_id"])
        async with SessionLocal() as db:
            review_res = await db.execute(
                select(Review).where(Review.id == review_id, Review.tenant_id == tenant_id)
            )
            review = review_res.scalar_one_or_none()
            if review is None:
                await websocket.close(code=4404)
                return
            mem_res = await db.execute(
                select(ProjectMember).where(
                    ProjectMember.project_id == review.project_id,
                    ProjectMember.user_id == user_id,
                    ProjectMember.tenant_id == tenant_id,
                )
            )
            member = mem_res.scalar_one_or_none()
            if member is None:
                await websocket.close(code=4403)
                return
            role = member.role
            current_seq = int(review.last_seq)
            if last_seq > 0 and last_seq < current_seq:
                await websocket.send_text(
                    json.dumps(
                        {
                            "v": 1,
                            "type": "replay.begin",
                            "id": f"evt_{uuid.uuid4().hex[:20]}",
                            "reviewId": review_id,
                            "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                            "payload": {"fromSeq": last_seq + 1, "toSeq": current_seq},
                        }
                    )
                )
                ev_res = await db.execute(
                    select(ReviewEvent)
                    .where(ReviewEvent.review_id == review_id, ReviewEvent.seq > last_seq)
                    .order_by(ReviewEvent.seq)
                )
                for ev in ev_res.scalars().all():
                    await websocket.send_text(
                        json.dumps(
                            {
                                "v": 1,
                                "type": ev.type,
                                "id": ev.id,
                                "seq": ev.seq,
                                "reviewId": review_id,
                                "ts": ev.ts.isoformat().replace("+00:00", "Z"),
                                "payload": ev.payload,
                            }
                        )
                    )
                await websocket.send_text(
                    json.dumps(
                        {
                            "v": 1,
                            "type": "replay.end",
                            "id": f"evt_{uuid.uuid4().hex[:20]}",
                            "reviewId": review_id,
                            "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                            "payload": {"toSeq": current_seq},
                        }
                    )
                )
        await review_hub.join(review_id, connection_id, websocket, user_id or "")
        joined = True
        await websocket.send_text(
            json.dumps(
                {
                    "v": 1,
                    "type": "server.welcome",
                    "id": f"evt_{uuid.uuid4().hex[:20]}",
                    "reviewId": review_id,
                    "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                    "payload": {
                        "userId": user_id,
                        "serverVersion": "0.1.0",
                        "currentSeq": current_seq,
                        "heartbeatMs": 15000,
                        "role": role,
                    },
                }
            )
        )
        token_exp = claims.get("exp")
        while True:
            data = await _receive_json_limited(websocket)
            if isinstance(token_exp, int | float) and datetime.now(UTC).timestamp() >= token_exp:
                await websocket.send_text(
                    json.dumps(
                        {
                            "v": 1,
                            "type": "error",
                            "id": f"evt_{uuid.uuid4().hex[:20]}",
                            "reviewId": review_id,
                            "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                            "payload": {
                                "code": "auth_expired",
                                "message": "Token expired",
                                "retryable": True,
                                "fatal": True,
                            },
                        }
                    )
                )
                await websocket.close(code=4401)
                return
            mtype = data.get("type")
            msg_payload = data.get("payload", {})
            if mtype == "client.ping":
                await websocket.send_text(
                    json.dumps(
                        {
                            "v": 1,
                            "type": "server.pong",
                            "id": f"evt_{uuid.uuid4().hex[:20]}",
                            "reviewId": review_id,
                            "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                            "payload": {"nonce": str(msg_payload.get("nonce", ""))[:64]},
                        }
                    )
                )
            elif mtype == "decision.submit":
                await _handle_decision(
                    websocket, review_id, tenant_id, user_id or "", role, msg_payload
                )
            elif mtype == "presence.update":
                state = msg_payload.get("state", "viewing")
                focus = msg_payload.get("focusFindingId")
                if state not in PRESENCE_STATES or not (focus is None or isinstance(focus, str)):
                    raise BadMessage
                await review_hub.broadcast_ephemeral(
                    review_id,
                    {
                        "v": 1,
                        "type": "presence.diff",
                        "id": f"evt_{uuid.uuid4().hex[:20]}",
                        "reviewId": review_id,
                        "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                        "payload": {
                            "changed": [
                                {
                                    "userId": user_id,
                                    "state": state,
                                    "focusFindingId": focus[:64] if focus else None,
                                }
                            ]
                        },
                    },
                )
    except WebSocketDisconnect:
        pass
    except BadMessage:
        await websocket.close(code=4400)
    finally:
        if joined:
            await review_hub.leave(review_id, connection_id)


async def _reject_decision(
    websocket: WebSocket,
    review_id: str,
    payload: dict[str, Any],
    code: str,
    current: Finding | None = None,
) -> None:
    body: dict[str, Any] = {"clientMsgId": payload.get("clientMsgId"), "code": code}
    if current is not None:
        body["current"] = current.model_dump(by_alias=True, mode="json")
    await websocket.send_text(
        json.dumps(
            {
                "v": 1,
                "type": "decision.rejected",
                "id": f"evt_{uuid.uuid4().hex[:20]}",
                "reviewId": review_id,
                "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "correlationId": payload.get("clientMsgId"),
                "payload": body,
            }
        )
    )


def _apply_decision(finding: Finding, action: str, payload: dict[str, Any]) -> Finding:
    data = finding.model_dump()
    if action == "accept":
        data["status"] = "accepted"
    elif action == "reject":
        data["status"] = "rejected"
    elif action == "reopen":
        data["status"] = "open"
    elif action == "escalate":
        data["status"] = "escalated"
        data["assignee_id"] = str(payload["assigneeId"])
    elif action == "edit":
        data["status"] = "edited"
        edits = payload["edits"]
        for key in EDITABLE_FIELDS:
            if key in edits:
                data[key] = edits[key]
    data["version"] = finding.version + 1
    return Finding.model_validate(data)


async def _handle_decision(
    websocket: WebSocket,
    review_id: str,
    tenant_id: str,
    user_id: str,
    role: str,
    payload: dict[str, Any],
) -> None:
    action = payload.get("action")
    if role == "viewer":
        await _reject_decision(websocket, review_id, payload, "forbidden")
        return
    if action == "override" and role != "owner":
        await _reject_decision(websocket, review_id, payload, "forbidden")
        return
    finding_id = payload.get("findingId")
    finding_version = payload.get("findingVersion")
    if not isinstance(finding_id, str) or not isinstance(finding_version, int):
        await _reject_decision(websocket, review_id, payload, "invalid")
        return
    async with SessionLocal() as db:
        res = await db.execute(
            select(FindingRow).where(
                FindingRow.id == finding_id,
                FindingRow.review_id == review_id,
                FindingRow.tenant_id == tenant_id,
            )
        )
        row = res.scalar_one_or_none()
        if row is None:
            await _reject_decision(websocket, review_id, payload, "invalid")
            return
        finding = Finding.model_validate(row.payload)
        if finding.version != finding_version:
            await _reject_decision(websocket, review_id, payload, "version_conflict", finding)
            return
        invalid = decision_validation_error(action, payload, finding)
        if invalid:
            await _reject_decision(websocket, review_id, payload, invalid)
            return
        effective = payload["overrideAction"] if action == "override" else action
        try:
            updated = _apply_decision(finding, effective, payload)
        except ValidationError:
            await _reject_decision(websocket, review_id, payload, "invalid")
            return
        row.payload = updated.model_dump(by_alias=True, mode="json")
        row.version = updated.version
        decision = ReviewDecision(
            id=new_decision_id(),
            tenant_id=tenant_id,
            finding_id=updated.id,
            review_id=review_id,
            action=action,
            actor_id=user_id,
            at=datetime.now(UTC),
            reason=payload.get("reason"),
            before=finding.model_dump(mode="json"),
            after=updated.model_dump(mode="json"),
            finding_version=finding_version,
            client_msg_id=str(payload.get("clientMsgId", "")),
        )
        decision_json = decision.model_dump(by_alias=True, mode="json")
        db.add(
            ReviewDecisionRow(
                id=decision.id,
                tenant_id=tenant_id,
                review_id=review_id,
                finding_id=updated.id,
                payload=decision_json,
            )
        )
        await append_review_event(
            db,
            tenant_id=tenant_id,
            review_id=review_id,
            event_type="finding.updated",
            payload={"finding": row.payload, "decisionId": decision.id},
        )
        await append_review_event(
            db,
            tenant_id=tenant_id,
            review_id=review_id,
            event_type="decision.applied",
            payload={"decision": decision_json},
        )
        await db.commit()
