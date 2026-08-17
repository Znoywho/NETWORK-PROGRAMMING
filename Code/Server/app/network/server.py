from typing import Dict
import random
import asyncio
import json
from websockets.server import serve
from models.match import Role, Match


class handler:
    def __init__(self, addr, port):
        self.HOST = addr
        self.PORT = port
        self.connected_users = set()
        # List of matched are opened currently
        self.matches: Dict[int, Match] = {}

    def create_new_match(self, player1, player2):
        # NOTE: random ID
        new_match = Match(player1, player2, 123)
        self.matches[new_match.match_id] = new_match
        print(f"Create new match!: ID {new_match.match_id}")

    def searching_match(self, match_id: int):
        if match_id not in self.matches:
            return None
        if self.matches[match_id].player2 is None:
            return False
        return True

    def message_handler(self, websocket, message: dict):

        if message["message_type"] == "create_match":
            self.create_new_match(message["user"], None)
            return "Match created successfully"

        if message["message_type"] == "make_move":
            match_id = message["match_id"]
            current_match = self.matches[match_id]
            current_match.game._make_move(message["x"], message["y"])
            current_match.game._visualize_grid()

        if message["message_type"] == "searching_match":
            match_id = message["match_id"]
            if self.searching_match(match_id):
                self.matches[match_id].player2 = message["user"]
            elif self.searching_match(match_id) is None:
                print("Match Not Found")
                return "Match Not Found"
            else:
                print("The match is already occupied")
                return "The match is already occupied"

    # def match_state(self, match_id):
    #     if match_id
    async def ServerAction(self, websocket):
        self.connected_users.add(websocket)
        print(f"Number of clients are active: {len(self.connected_users)}")
        print(f"current_match: {len(self.matches)}")

        try:
            print(f"Connected by: {websocket.remote_address}")
            async for message in websocket:
                print(f"Received raw data:\n{json.loads(message)}\nfrom {websocket.remote_address}")
                message = json.loads(message)
                response = self.message_handler(websocket, message)
                await websocket.send(f"Server Already received message from you\nResponse: {response}")
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            # unregister client
            self.connected_users.remove(websocket)
            print(f"Client disconnected. Remaining clients {len(self.connected_users)}")
            print(f"current_match: {len(self.matches)}")

    async def serverAction(self):
        async with serve(self.ServerAction, self.HOST, self.PORT) as ser:
            print(f"Websocket server is running on ws://{self.HOST}:{self.PORT}")
            self.create_new_match(123, None)

            # unsafe thread. await new session of connection in the future
            await asyncio.Future()


if __name__ == "__main__":
    HOST = "localhost"
    PORT = 8765
    MyServer = handler(HOST, PORT)
    asyncio.run(MyServer.serverAction())
