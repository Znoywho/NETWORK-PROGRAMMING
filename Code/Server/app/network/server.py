import asyncio
import json
import logging

from app.handlers.message import MessageHandler
from app.matchmaking.invite_manager import InviteManager
from app.matchmaking.player_manager import PlayerManager
from app.matchmaking.room_manager import RoomManager
from websockets.exceptions import ConnectionClosed
from websockets.server import serve

logger = logging.getLogger(__name__)


class ServerHandler:
    def __init__(self, addr, port):
        self.HOST = addr
        self.PORT = port
        self.connected_users = PlayerManager()
        self.rooms = RoomManager()
        self.invitation = InviteManager(self.connected_users, self.rooms)
        self.message_handler = MessageHandler(self.connected_users, self.rooms, self.invitation)

    async def ServerAction(self, websocket):
        logger.info("Client connected: %s", websocket.remote_address)
        try:
            async for raw_message in websocket:
                try:
                    message = json.loads(raw_message)
                except (TypeError, json.JSONDecodeError):
                    deliveries = [
                        {
                            "targets": [],
                            "payload": {
                                "type": "error",
                                "code": "INVALID_JSON",
                                "message": "Message must be valid JSON.",
                            },
                        }
                    ]
                else:
                    deliveries = self.message_handler.handle(message, websocket)
                await self._send_deliveries(deliveries, websocket)
        except ConnectionClosed:
            pass
        except Exception:
            logger.exception("Error handling client %s", websocket.remote_address)
        finally:
            deliveries = self.message_handler.disconnect(websocket)
            await self._send_deliveries(deliveries, websocket)
            logger.info("Client disconnected. Remaining clients: %d", len(self.connected_users.list_online()))

    async def _send_deliveries(self, deliveries, origin_websocket) -> None:
        for delivery in deliveries:
            targets = delivery["targets"]
            if targets is None:
                connections = [
                    player.connection
                    for info in self.connected_users.list_online()
                    if (player := self.connected_users.get_player(info["player_id"])) is not None
                ]
            elif targets:
                connections = [
                    player.connection
                    for player_id in targets
                    if (player := self.connected_users.get_player(player_id)) is not None
                ]
            else:
                connections = [origin_websocket]

            payload = json.dumps(delivery["payload"])
            sent_connections = set()
            for connection in connections:
                connection_id = id(connection)
                if connection_id in sent_connections:
                    continue
                sent_connections.add(connection_id)
                try:
                    await connection.send(payload)
                except ConnectionClosed:
                    logger.debug("Skipped closed WebSocket while sending a delivery.")

    async def serverAction(self):
        async with serve(self.ServerAction, self.HOST, self.PORT) as ser:
            print(f"Websocket server is running on ws://{self.HOST}:{self.PORT}")
            # unsafe thread. await new session of connection in the future
            await asyncio.Future()
