from typing import Callable

from app.matchmaking.player_manager import PlayerManager
from app.matchmaking.room_manager import RoomManager
from app.matchmaking.invite_manager import InviteManager
from app.matchmaking.models import RoomStatus


class MatchmakingHandlers:
    def __init__(
        self,
        player_manager: PlayerManager,
        room_manager: RoomManager,
        invite_manager: InviteManager,
    ):
        self.pm = player_manager
        self.rm = room_manager
        self.im = invite_manager

    def handle_online_players(self) -> dict:
        return {"type": "online_players", "players": self.pm.list_online()}

    def handle_invite(self, from_id: str, payload: dict) -> dict:
        to_id = payload["to"]
        result = self.im.send_invite(from_id, to_id)
        return {"type": "invite_result", **result}

    def handle_accept_invite(self, payload: dict, board_factory: Callable) -> dict:
        result = self.im.accept_invite(payload["invite_id"], board_factory)
        return {"type": "accept_invite_result", **result}

    def handle_reject_invite(self, payload: dict) -> dict:
        result = self.im.reject_invite(payload["invite_id"])
        return {"type": "reject_invite_result", **result}

    def handle_leave_room(self, player_id: str, payload: dict) -> dict:
        room_id = payload["room_id"]
        room = self.rm.get_room(room_id)

        if not room:
            return {"type": "leave_room_result", "success": False, "reason": "room_not_found"}

        if player_id in room.spectators:
            self.rm.remove_spectator(room_id, player_id)
            self.pm.set_current_room(player_id, None)
            return {"type": "leave_room_result", "success": True, "role": "spectator"}

        if player_id in (room.player_x, room.player_o):
            room.status = RoomStatus.FINISHED
            self.pm.set_current_room(player_id, None)
            opponent_id = room.player_o if player_id == room.player_x else room.player_x
            return {
                "type": "leave_room_result",
                "success": True,
                "role": "player",
                "winner": opponent_id,
            }

        return {"type": "leave_room_result", "success": False, "reason": "player_not_in_room"}