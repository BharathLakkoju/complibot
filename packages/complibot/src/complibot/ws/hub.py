import asyncio
import json
from dataclasses import dataclass, field
from typing import Any

from fastapi import WebSocket


@dataclass
class SocketState:
    websocket: WebSocket
    user_id: str
    last_ack_seq: int = 0


class ReviewHub:
    def __init__(self) -> None:
        self._rooms: dict[str, dict[str, SocketState]] = {}
        self._lock = asyncio.Lock()

    async def join(self, review_id: str, connection_id: str, ws: WebSocket, user_id: str) -> None:
        async with self._lock:
            self._rooms.setdefault(review_id, {})[connection_id] = SocketState(
                websocket=ws, user_id=user_id
            )

    async def leave(self, review_id: str, connection_id: str) -> None:
        async with self._lock:
            room = self._rooms.get(review_id)
            if room:
                room.pop(connection_id, None)
                if not room:
                    self._rooms.pop(review_id, None)

    async def broadcast(self, review_id: str, message: dict[str, Any]) -> None:
        data = json.dumps(message)
        async with self._lock:
            room = list(self._rooms.get(review_id, {}).values())
        for state in room:
            try:
                await state.websocket.send_text(data)
            except Exception:
                pass

    async def broadcast_ephemeral(self, review_id: str, message: dict[str, Any]) -> None:
        await self.broadcast(review_id, message)


review_hub = ReviewHub()
