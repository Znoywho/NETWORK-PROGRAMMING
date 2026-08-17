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
                # movement = {"user": 123, "message_type": "make_move", "match_id": 123, "x": int(x), "y": int(y)}
                searching_match = {"user": 23, "message_type": "searching_match", "match_id": 23}
                message = json.dumps(searching_match)
            await websocket.send(message)
            response = await websocket.recv()
            print(response)


if __name__ == "__main__":
    asyncio.run(hello())
