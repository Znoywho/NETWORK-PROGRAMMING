import asyncio

from app.network.server import ServerHandler

if __name__ == "__main__":
    myserver = ServerHandler("0.0.0.0", 8765)
    print("========Running Server========")
    asyncio.run(myserver.serverAction())
