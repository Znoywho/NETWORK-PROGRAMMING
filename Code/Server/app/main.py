import asyncio

from network.server import ServerHandler

if __name__ == "__main__":
    myserver = ServerHandler("localhost", 8765)
    asyncio.run(myserver.serverAction())
