import random
import asyncio
import json
from websockets.server import serve
from models.match import Role, match


class handler:
    def __init__(self, addr, port):
        self.HOST = addr
        self.PORT = port
        self.connected_users = set()
        self.matches = {}

    def create_new_match(self, player1, player2):
        # NOTE: random ID
        new_match = match(player1, player2, random.random())
        self.matches[new_match.match_id] = new_match
        print(f"Create new match!: ID {new_match.match_id}")

    # def match_state(self, match_id):
    #     if match_id

    async def ServerAction(self, websocket):
        self.connected_users.add(websocket)
        print(f"Number of clients are active: {len(self.connected_users)}")
        try:
            print(f"Connected by: {websocket.remote_address}")
            async for message in websocket:
                print(f"Received raw data:\n{json.loads(message)}\nfrom {websocket.remote_address}")
                await websocket.send("Server Already received message from you")
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            # unregister client
            self.connected_users.remove(websocket)
            print(f"Client disconnected. Remaining clients {len(self.connected_users)}")

    async def serverAction(self):
        async with serve(self.ServerAction, self.HOST, self.PORT) as ser:
            print(f"Websocket server is running on ws://{self.HOST}:{self.PORT}")
            # unsafe thread. await new session of connection in the future
            await asyncio.Future()


if __name__ == "__main__":
    HOST = "localhost"
    PORT = 8765
    MyServer = handler(HOST, PORT)
    asyncio.run(MyServer.serverAction())
