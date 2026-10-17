import json
import uuid
from datetime import UTC, datetime
from typing import Any

import jwt
from complibot.config import get_settings
from complibot.db.models import ProjectMember, Review, ReviewEvent
from complibot.db.session import SessionLocal
from complibot.services.events import append_review_event
from complibot.ws.decisions import decision_validation_error
from complibot.ws.hub import review_hub
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

router = APIRouter()


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


async def _receive_text_limited(websocket: WebSocket) -> str:
    raw = await websocket.receive_text()
    if len(raw.encode("utf-8")) > _max_ws_bytes():
        raise ValueError("message_too_large")
    return raw


@router.websocket("/v1/reviews/{review_id}/ws")
async def review_ws(websocket: WebSocket, review_id: str) -> None:
    connection_id = str(uuid.uuid4())
    user_id: str | None = None
    role = "viewer"
    joined = False
    try:
        await websocket.accept()
        raw = await _receive_text_limited(websocket)
        hello = json.loads(raw)
        if hello.get("type") != "client.hello":
            await websocket.close(code=4400)
            return
        payload = hello.get("payload", hello)
        token = payload.get("token", "")
        last_seq = int(payload.get("lastSeq") or 0)
        try:
            claims = _decode_token(token)
        except jwt.PyJWTError:
            await websocket.close(code=4401)
            return
        user_id = str(claims["sub"])
        tenant_id = str(claims.get("tenant_id", ""))
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
        while True:
            msg = await _receive_text_limited(websocket)
            data = json.loads(msg)
            mtype = data.get("type")
            if mtype == "client.ping":
                await websocket.send_text(
                    json.dumps(
                        {
                            "v": 1,
                            "type": "server.pong",
                            "id": f"evt_{uuid.uuid4().hex[:20]}",
                            "reviewId": review_id,
                            "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                            "payload": {"nonce": data.get("payload", {}).get("nonce", "")},
                        }
                    )
                )
            elif mtype == "decision.submit":
                await _handle_decision(review_id, user_id or "", role, data)
            elif mtype == "presence.update":
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
                                    "state": data.get("payload", {}).get("state", "viewing"),
                                    "focusFindingId": data.get("payload", {}).get("focusFindingId"),
                                }
                            ]
                        },
                    },
                )
    except WebSocketDisconnect:
        pass
    except (json.JSONDecodeError, ValueError):
        await websocket.close(code=4400)
    except jwt.PyJWTError:
        await websocket.close(code=4401)
    finally:
        if joined:
            await review_hub.leave(review_id, connection_id)


async def _reject_decision(review_id: str, payload: dict[str, Any], code: str) -> None:
    await review_hub.broadcast(
        review_id,
        {
            "v": 1,
            "type": "decision.rejected",
            "id": f"evt_{uuid.uuid4().hex[:20]}",
            "reviewId": review_id,
            "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "correlationId": payload.get("clientMsgId"),
            "payload": {"clientMsgId": payload.get("clientMsgId"), "code": code},
        },
    )


async def _handle_decision(review_id: str, user_id: str, role: str, data: dict[str, Any]) -> None:
    payload = data.get("payload", {})
    action = payload.get("action")
    if role == "viewer":
        await _reject_decision(review_id, payload, "forbidden")
        return
    if action == "override" and role != "owner":
        await _reject_decision(review_id, payload, "forbidden")
        return
    async with SessionLocal() as db:
        from complibot.db.models import FindingRow
        from complibot.ids import new_decision_id
        from complibot.schemas import Finding, ReviewDecision

        finding_id = payload.get("findingId")
        res = await db.execute(select(FindingRow).where(FindingRow.id == finding_id))
        row = res.scalar_one_or_none()
        if row is None:
            return
        finding = Finding.model_validate(row.payload)
        if finding.version != int(payload.get("findingVersion", -1)):
            await review_hub.broadcast(
                review_id,
                {
                    "v": 1,
                    "type": "decision.rejected",
                    "id": f"evt_{uuid.uuid4().hex[:20]}",
                    "reviewId": review_id,
                    "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                    "correlationId": payload.get("clientMsgId"),
                    "payload": {
                        "clientMsgId": payload.get("clientMsgId"),
                        "code": "version_conflict",
                        "current": finding.model_dump(by_alias=True),
                    },
                },
            )
            return
        invalid = decision_validation_error(action, payload, finding)
        if invalid:
            await _reject_decision(review_id, payload, invalid)
            return
        before = finding.model_dump()
        if action == "accept":
            finding.status = "accepted"
        elif action == "reject":
            finding.status = "rejected"
        elif action == "escalate":
            finding.status = "escalated"
            finding.assignee_id = payload.get("assigneeId")
        elif action == "edit":
            finding.status = "edited"
            edits = payload.get("edits") or {}
            for key in ("title", "severity", "rationale", "remediation"):
                if key in edits:
                    setattr(finding, key, edits[key])
        finding.version += 1
        row.payload = finding.model_dump(by_alias=True, mode="json")
        row.version = finding.version
        decision = ReviewDecision(
            id=new_decision_id(),
            tenant_id=finding.tenant_id,
            finding_id=finding.id,
            review_id=review_id,
            action=action,
            actor_id=user_id,
            at=datetime.now(UTC),
            reason=payload.get("reason"),
            before=before,
            after=finding.model_dump(),
            finding_version=int(payload.get("findingVersion")),
            client_msg_id=payload.get("clientMsgId", ""),
        )
        from complibot.db.models import ReviewDecisionRow

        db.add(
            ReviewDecisionRow(
                id=decision.id,
                tenant_id=decision.tenant_id,
                review_id=review_id,
                finding_id=finding.id,
                payload=decision.model_dump(by_alias=True),
            )
        )
        await append_review_event(
            db,
            tenant_id=finding.tenant_id,
            review_id=review_id,
            event_type="finding.updated",
            payload={"finding": finding.model_dump(by_alias=True), "decisionId": decision.id},
        )
        await append_review_event(
            db,
            tenant_id=finding.tenant_id,
            review_id=review_id,
            event_type="decision.applied",
            payload={"decision": decision.model_dump(by_alias=True)},
        )
        await db.commit()
