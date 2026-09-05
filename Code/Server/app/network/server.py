from typing import Dict
import random
import asyncio
import json
import time
from websockets.server import serve
from matchmaking.invite_manager import InviteManager
from matchmaking.player_manager import PlayerManager
from matchmaking.room_manager import RoomManager
from handlers.matchmaking_handlers import MatchmakingHandlers

class ServerHandler:
    def __init__(self, addr, port):
        self.HOST = addr
        self.PORT = port
        self.connected_users = PlayerManager()      # List of matched are opened currently
        self.rooms = RoomManager()
        self.invitation = InviteManager(
            self.connected_users,
            self.rooms
        )
        self.matchmaking_handlers = MatchmakingHandlers(
            self.connected_users,
            self.rooms,
            self.invitation
        )
    def login(self, username, password):
        pass



    def message_handler(self, message):
        if message["type"] == "login":
            pass
        if message["type"] == "invite":
            pass

    def add_user(self):
        pass 

    async def ServerAction(self, websocket):
        print(
            f"Number of clients are active: "
            f"{len(self.connected_users.list_online())}"
        )

        player_id = None

        try:
            print(f"Connected by: {websocket.remote_address}")

            async for message in websocket:
                message = json.loads(message)

                print(
                    f"Received raw data:\n{message}\n"
                    f"from {websocket.remote_address}"
                )

                # Client đăng nhập
                if message.get("type") == "login":
                    player_id = message.get("playerId")

                    if not player_id:
                        await websocket.send(json.dumps({
                            "type": "error",
                            "reason": "player_id_required"
                        }))
                        continue

                    self.connected_users.add_player(
                        player_id,
                        player_id,
                        websocket
                    )

                    await websocket.send(json.dumps({
                        "type": "login_result",
                        "success": True,
                        "playerId": player_id
                    }))
                    continue

                # Client yêu cầu xem trận
                if message.get("type") == "spectate":
                    player = self.connected_users.get_player_by_connection(
                        websocket
                    )

                    if not player:
                        await websocket.send(json.dumps({
                            "type": "spectate_result",
                            "success": False,
                            "reason": "player_not_found"
                        }))
                        continue

                    result = self.matchmaking_handlers.handle_spectate(
                        player.player_id,
                        message
                    )

                    await websocket.send(json.dumps(result))
                    continue

                await websocket.send(
                    "Server Already received message from you"
                )

        except Exception as e:
            print(f"Error handling client: {e}")

        finally:
            if player_id:
                self.connected_users.remove_player(player_id)

            print(
                f"Client disconnected. "
                f"Remaining clients "
                f"{len(self.connected_users.list_online())}"
            )

    async def serverAction(self):
        async with serve(self.ServerAction, self.HOST, self.PORT) as ser:
            print(f"Websocket server is running on ws://{self.HOST}:{self.PORT}")

            # unsafe thread. await new session of connection in the future
            await asyncio.Future()


