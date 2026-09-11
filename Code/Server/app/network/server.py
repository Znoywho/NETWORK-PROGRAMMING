from typing import Dict
import random
import asyncio
import json
from app.models.match import Role, match

class ServerHandler:
    def __init__(self, addr, port):
        self.HOST = addr
        self.PORT = int(port)

    def create_new_match(self, player1, player2):
        # NOTE: random ID
        self.current_match = match(player1, player2, 100)
        print(f"Create new match!: ID {self.current_match.match_id}")

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info("peername")
        try:
            print(f"Connected by: {addr}")
            while True:
                data = await reader.readuntil(b'\n')
                if not data:
                    break

                message = data.decode("utf-8").strip()
                if not message:
                    continue

                print(f"Received raw data:\n{message}\nfrom {addr}")

                response = {
                    "type": "game_state",
                    "matchId": "match-1",
                    "board": [
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                    ],
                    "currentPlayerId": "p1",
                    "status": "playing"
                }

                writer.write((json.dumps(response) + "\n").encode("utf-8"))
                await writer.drain()
        except asyncio.IncompleteReadError:
            print(f"Client {addr} đóng socket.")
        except Exception as e:
            print(f"Error handling client {addr}: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def serverAction(self):
        server = await asyncio.start_server(self.handle_client, self.HOST, self.PORT)
        addr = server.sockets[0].getsockname()
        print(f"TCP server is running on tcp://{addr[0]}:{addr[1]}")

        async with server:
            await server.serve_forever()


if __name__ == "__main__":
    HOST = "0.0.0.0"
    PORT = 8765
    MyServer = server(HOST, PORT)
    asyncio.run(MyServer.serverAction())
