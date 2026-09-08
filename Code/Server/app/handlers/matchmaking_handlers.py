from typing import Callable

from matchmaking.player_manager import PlayerManager
from matchmaking.room_manager import RoomManager
from matchmaking.invite_manager import InviteManager
from models.matchmaking_models import PlayerStatus, RoomStatus


class MatchmakingHandlers:
    def __init__(self, player_manager: PlayerManager, room_manager: RoomManager, invite_manager: InviteManager):
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

    def handle_spectate(self, player_id: str, payload: dict) -> dict:
        room_id = payload.get("room_id")

        if not room_id:
            return {
                "type": "spectate_result",
                "success": False,
                "reason": "room_id_required"
            }

        room = self.rm.get_room(room_id)

        if not room:
            return {
                "type": "spectate_result",
                "success": False,
                "reason": "room_not_found"
            }

        player = self.pm.get_player(player_id)

        if not player:
            return {
                "type": "spectate_result",
                "success": False,
                "reason": "player_not_found"
            }

        # Người đang thi đấu trong room không được spectate chính trận của mình
        if player_id in (room.player_x, room.player_o):
            return {
                "type": "spectate_result",
                "success": False,
                "reason": "already_in_room_as_player"
           }

        # Người đang chơi trận khác không được vào xem
        if player.status == PlayerStatus.PLAYING:
            return {
                "type": "spectate_result",
                "success": False,
                "reason": "player_busy"
            }

        # Nếu đang xem một room khác thì rời room cũ trước
        if player.status == PlayerStatus.SPECTATING:
            if player.current_room_id and player.current_room_id != room_id:
                self.rm.remove_spectator(
                    player.current_room_id,
                    player_id
                )

        # Thêm vào danh sách khán giả
        self.rm.add_spectator(room_id, player_id)

        # Cập nhật trạng thái player
        self.pm.set_status(player_id, PlayerStatus.SPECTATING)
        self.pm.set_current_room(player_id, room_id)

        return {
            "type": "spectate_result",
            "success": True,
            "room_id": room_id,
            "role": "spectator"
        }

    def handle_leave_room(self, player_id: str, payload: dict) -> dict:
        room_id = payload["room_id"]
        room = self.rm.get_room(room_id)

        if not room:
            return {"type": "leave_room_result", "success": False, "reason": "room_not_found"}

        if player_id in room.spectators:
            self.rm.remove_spectator(room_id, player_id)
            self.pm.set_current_room(player_id, None)
            self.rm.cleanup_if_done(room_id)
            return {"type": "leave_room_result", "success": True, "role": "spectator"}

        if player_id in (room.player_x, room.player_o):
            from app.models.matchmaking_models import RoomStatus
            room.status = RoomStatus.FINISHED
            self.pm.set_current_room(player_id, None)
            self.rm.mark_player_left(room_id, player_id)
            opponent_id = room.player_o if player_id == room.player_x else room.player_x

            self.rm.cleanup_if_done(room_id)

            return {
                "type": "leave_room_result",
                "success": True,
                "role": "player",
                "winner": opponent_id,
            }

        return {"type": "leave_room_result", "success": False, "reason": "player_not_in_room"}      