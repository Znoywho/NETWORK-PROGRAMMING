"""Interactive WebSocket client for manually testing Caro WebSocket flows.

``auto_match`` opens two connections, creates a game through invite/accept,
then makes random legal moves until the game finishes.
"""

import argparse
import asyncio
import json
import random
import uuid

from websockets.client import connect


class ClientUnitTest:
    def __init__(self, host: str, port: int):
        self.uri = f"ws://{host}:{port}"

    async def run(self, mode: str) -> None:
        if mode == "auto_match":
            await self._run_automatic_match()
            return

        async with connect(self.uri) as websocket:
            player_id = await self._login(websocket)
            if player_id is None:
                return

            if mode == "invite":
                await self._send_invite(websocket)
            elif mode == "accept":
                await self._accept_invite(websocket)

            # Keep the client online and print its responses/notifications.
            async for raw_message in websocket:
                self._print_message(json.loads(raw_message))

    async def _login(self, websocket, label: str = "") -> str | None:
        prefix = f"{label} " if label else ""
        username = input(f"{prefix}username: ").strip()
        password = input(f"{prefix}password: ").strip()
        await self._send(websocket, {"type": "login", "username": username, "password": password})

        while True:
            response = json.loads(await websocket.recv())
            self._print_message(response, label)
            if response.get("type") == "login":
                player_id = response.get("playerId")
                return player_id if isinstance(player_id, str) else None
            if response.get("type") == "error":
                return None

    async def _send_invite(self, websocket) -> None:
        to_player_id = input("Player ID to invite: ").strip()
        invite_id = str(uuid.uuid4())
        await self._send(
            websocket,
            {"type": "invite", "inviteId": invite_id, "toPlayerId": to_player_id},
        )
        print(f"Sent inviteId: {invite_id}")

    async def _accept_invite(self, websocket) -> None:
        invite_id = input("Invite ID to accept: ").strip()
        await self._send(websocket, {"type": "accept_invite", "inviteId": invite_id})

    async def _run_automatic_match(self) -> None:
        """Create a game between two existing users and play random moves."""
        async with connect(self.uri) as player_x_socket, connect(self.uri) as player_o_socket:
            player_x_id = await self._login(player_x_socket, "Player X")
            player_o_id = await self._login(player_o_socket, "Player O")
            if player_x_id is None or player_o_id is None:
                print("Both players must log in successfully before starting a match.")
                return

            invite_id = str(uuid.uuid4())
            await self._send(
                player_x_socket,
                {"type": "invite", "inviteId": invite_id, "toPlayerId": player_o_id},
            )
            print(f"Player X sent inviteId: {invite_id}")

            invite = await self._receive_until(
                player_o_socket,
                lambda message: message.get("type") == "invite" and message.get("inviteId") == invite_id,
                "Player O",
            )
            if invite.get("fromPlayerId") != player_x_id:
                raise RuntimeError("Received an invitation from an unexpected player.")

            await self._send(player_o_socket, {"type": "accept_invite", "inviteId": invite_id})
            state_x, state_o = await asyncio.gather(
                self._receive_until(
                    player_x_socket,
                    lambda message: message.get("type") == "game_state",
                    "Player X",
                ),
                self._receive_until(
                    player_o_socket,
                    lambda message: message.get("type") == "game_state",
                    "Player O",
                ),
            )
            if state_x.get("room_id") != state_o.get("room_id"):
                raise RuntimeError("Players received different room IDs.")

            print(f"Match created successfully: room_id={state_x['room_id']}")
            await self._play_random_game(
                player_x_socket,
                player_o_socket,
                player_x_id,
                player_o_id,
                state_x,
            )

    async def _play_random_game(
        self,
        player_x_socket,
        player_o_socket,
        player_x_id: str,
        player_o_id: str,
        state: dict,
    ) -> None:
        sockets = {player_x_id: (player_x_socket, "Player X"), player_o_id: (player_o_socket, "Player O")}
        move_number = 0

        while state.get("status") == "playing":
            current_player_id = state.get("currentPlayerId")
            current_player = sockets.get(current_player_id)
            if current_player is None:
                raise RuntimeError("The game state has an unknown currentPlayerId.")

            empty_cells = [
                (row, col)
                for row, board_row in enumerate(state["board"])
                for col, cell in enumerate(board_row)
                if cell == 0
            ]
            if not empty_cells:
                raise RuntimeError("The game is still playing but its board has no empty cells.")

            row, col = random.choice(empty_cells)
            socket, label = current_player
            move_number += 1
            print(f"Move {move_number}: {label} -> row={row}, col={col}")
            await self._send(
                socket,
                {
                    "type": "make_move",
                    "room_id": state["room_id"],
                    "playerId": current_player_id,
                    "row": row,
                    "col": col,
                },
            )

            state_x, state_o = await asyncio.gather(
                self._receive_until(
                    player_x_socket,
                    lambda message: message.get("type") == "game_state",
                    "Player X",
                ),
                self._receive_until(
                    player_o_socket,
                    lambda message: message.get("type") == "game_state",
                    "Player O",
                ),
            )
            if state_x != state_o:
                raise RuntimeError("Players received different game states.")
            state = state_x

        results = await asyncio.gather(
            self._receive_until(
                player_x_socket,
                lambda message: message.get("type") == "game_result",
                "Player X",
            ),
            self._receive_until(
                player_o_socket,
                lambda message: message.get("type") == "game_result",
                "Player O",
            ),
        )
        print(f"Match finished after {move_number} moves: {results}")

    async def _receive_until(self, websocket, predicate, label: str) -> dict:
        while True:
            message = json.loads(await websocket.recv())
            self._print_message(message, label)
            if message.get("type") == "error":
                raise RuntimeError(f"{label} received an error: {message}")
            if predicate(message):
                return message

    @staticmethod
    async def _send(websocket, message: dict) -> None:
        await websocket.send(json.dumps(message))

    @staticmethod
    def _print_message(message: dict, label: str = "") -> None:
        sender = f" ({label})" if label else ""
        print(f"Received from server{sender}:")
        print(json.dumps(message, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manual Caro WebSocket tester")
    parser.add_argument("--host", default="localhost", help="Server host (default: localhost)")
    parser.add_argument("--port", type=int, default=8765, help="Server port (default: 8765)")
    parser.add_argument(
        "-c",
        "--type",
        choices=("listen", "invite", "accept", "auto_match"),
        default="listen",
        help="listen, send/accept an invite, or create and play an automatic random match",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    client = ClientUnitTest(args.host, args.port)
    asyncio.run(client.run(args.type))
