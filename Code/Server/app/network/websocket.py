import asyncio
from websockets.server import serve


async def echo(websocket):
    print(f"Client connected {websocket.remote_address}")
    try:
        async for message in websocket:
            print(f"Received from client: {message}")
            await websocket.send(f"Echo: {message}")
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        print(f"Client disconnected: {websocket.remote_address}")


async def main():
    async with serve(echo, "localhost", 8765) as server:
        print("Websocket server is running on ws://localhost:8765")
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
