import json
import asyncio
from websockets.client import connect


async def hello():
    uri = "ws://localhost:8765"

    async with connect(uri) as websocket:
        message = {
                "type": "create_user",
                "username": "Hao",
                "password": "12345",
                }
        print(f"Already sent message: {message}")
        await websocket.send(json.dumps(message))

        response = await websocket.recv()

        response = json.loads(response)

        print(f" Received Message from server: {response}")


if __name__ == "__main__":
    asyncio.run(hello())
