from __future__ import annotations
from typing import Set
from fastapi import WebSocket


class WSManager:
    def __init__(self) -> None:
        self.connections: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.connections.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self.connections:
            self.connections.remove(ws)

    async def broadcast_json(self, data) -> None:
        for ws in list(self.connections):
            try:
                await ws.send_json(data)
            except Exception:
                self.disconnect(ws)


manager = WSManager()
