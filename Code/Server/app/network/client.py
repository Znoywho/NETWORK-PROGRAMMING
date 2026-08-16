import json
import asyncio
from websockets.client import connect


async def hello():
    uri = "ws://localhost:8765"

    async with connect(uri) as websocket:
        while True:
            message = str(input("Enter your message: \n/exit: out session\n/move: check in caro\n"))
            message = message.strip()
            if message == "/exit":
                print("Connection from server is stopped!!")
                break
            if message == "/move":
                x, y = input("(X, Y)").split()
                movement = {"player": websocket.remote_address, "x": x, "y": y}
                message = json.dumps(movement)
            await websocket.send(message)

            response = await websocket.recv()
            print(f"Received from server: {response}")


if __name__ == "__main__":
    asyncio.run(hello())
