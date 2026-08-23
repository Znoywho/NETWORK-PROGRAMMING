from typing import Dict
import random
import asyncio
import json
import time
from websockets.server import serve
from models.matchmaking_models import Player, Room
from handlers.matchmaking_handlers import PlayerManager, RoomManager

class handler:
    def __init__(self, addr, port):
        self.HOST = addr
        self.PORT = port
        self.connected_users = PlayerManager()      # List of matched are opened currently
        self.rooms = RoomManager()

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
        print(f"Number of clients are active: {len(self.connected_users.list_online())}")
        # print(f"current_room: {len(self.rooms.lis)}")

        try:
            print(f"Connected by: {websocket.remote_address}")
            async for message in websocket:
                print(f"Received raw data:\n{json.loads(message)}\nfrom {websocket.remote_address}")
                message = json.loads(message)
                await websocket.send("Server Already received message from you")
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            # unregister client
            self.connected_users.remove_player(websocket)
            print(f"Client disconnected. Remaining clients {len(self.connected_users.list_online())}")
            # print(f"current_room: {len(self.rooms)}")

    async def serverAction(self):
        async with serve(self.ServerAction, self.HOST, self.PORT) as ser:
            print(f"Websocket server is running on ws://{self.HOST}:{self.PORT}")

            # unsafe thread. await new session of connection in the future
            await asyncio.Future()


