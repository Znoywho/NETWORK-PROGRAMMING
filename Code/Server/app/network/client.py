import asyncio
from websockets.client import connect


async def hello():
    uri = "ws://localhost:8765"

    async with connect(uri) as websocket:
        message = "Hello, Websocket Server!"
        print(f"Sending to sever: {message}")
        await websocket.send(message)

        response = await websocket.recv()
        print(f"Received from server: {response}")


if __name__ == "__main__":
    asyncio.run(hello())
