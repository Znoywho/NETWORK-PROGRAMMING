from connections.server import server

import asyncio


if __name__ == "__main__":
    HOST = "localhost"
    PORT = "8765"
    MyServer = server(HOST, PORT)
    asyncio.run(MyServer.serverAction())
