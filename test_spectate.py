import asyncio
import json
import websockets


async def test():
    uri = "ws://localhost:8765"

    async with websockets.connect(uri) as ws:

        # Login
        await ws.send(json.dumps({
            "type": "login",
            "playerId": "spectator_test"
        }))

        response = await ws.recv()
        print("LOGIN:", response)

        # Spectate
        await ws.send(json.dumps({
            "type": "spectate",
            "room_id": "test-room"
        }))

        response = await ws.recv()
        print("SPECTATE:", response)


asyncio.run(test())