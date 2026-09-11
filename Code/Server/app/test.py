from network.server import ServerHandler
import asyncio


if __name__ == "__main__":
    HOST = "localhost"
    PORT = 8765
    MyServer = ServerHandler(HOST, PORT)
    asyncio.run(MyServer.serverAction())
