from network.server import handler
import asyncio


if __name__ == "__main__":
    HOST = "localhost"
    PORT = 8765
    MyServer = handler(HOST, PORT)
    asyncio.run(MyServer.serverAction())
