import asyncio
from websockets.server import serve
from app.models.match import Role, match


class server:
    def __init__(self, addr, port):
        self.HOST = addr
        self.PORT = port

    def create_new_match(self, player1, player2):
        # NOTE: random ID
        self.current_match = match(player1, player2, 100)
        print(f"Create new match!: ID {self.current_match.match_id}")

    async def server(self, addr, s):
        try:
            print(f"Connected by: {addr}")
            async for message in s:
                print(f"Received raw data:\n{message}\nfrom {addr}")
        except Exception as e:
            print(f"Error handling client: {e}")

    async def serverAction(self):
        async with serve(self.server, self.HOST, self.PORT) as ser:
            print(f"Websocket server is running on ws://{self.HOST}:{self.PORT}")
            await ser.serve_forever()


if __name__ == "__main__":
    HOST = "localhost"
    PORT = "8765"
    MyServer = server(HOST, PORT)
    asyncio.run(MyServer.serverAction())
