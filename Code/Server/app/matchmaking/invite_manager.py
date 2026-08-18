import threading
import time
from typing import Callable, Optional

from app.matchmaking.models import PlayerStatus
from app.matchmaking.player_manager import PlayerManager
from app.matchmaking.room_manager import RoomManager


class InviteManager:
    def __init__(self, player_manager: PlayerManager, room_manager: RoomManager):
        self.player_manager = player_manager
        self.room_manager = room_manager
        self._pending_invites: dict[str, dict] = {}
        self._lock = threading.Lock()

    def send_invite(self, from_id: str, to_id: str) -> dict:
        target = self.player_manager.get_player(to_id)

        if not target:
            return {"success": False, "reason": "player_not_found"}
        if target.status != PlayerStatus.IDLE:
            return {"success": False, "reason": "player_busy"}

        with self._lock:
            invite_id = f"{from_id}_{to_id}_{int(time.time() * 1000)}"
            self._pending_invites[invite_id] = {
                "from": from_id,
                "to": to_id,
                "timestamp": time.time(),
            }
        return {"success": True, "invite_id": invite_id}

    def accept_invite(self, invite_id: str, board_factory: Callable) -> dict:
        with self._lock:
            invite = self._pending_invites.pop(invite_id, None)

        if not invite:
            return {"success": False, "reason": "invite_not_found_or_expired"}

        room = self.room_manager.create_room(invite["from"], invite["to"])
        room.board_instance = board_factory()

        self.player_manager.set_status(invite["from"], PlayerStatus.PLAYING)
        self.player_manager.set_status(invite["to"], PlayerStatus.PLAYING)
        self.player_manager.set_current_room(invite["from"], room.room_id)
        self.player_manager.set_current_room(invite["to"], room.room_id)

        return {
            "success": True,
            "room_id": room.room_id,
            "player_x": invite["from"],
            "player_o": invite["to"],
        }

    def reject_invite(self, invite_id: str) -> dict:
        with self._lock:
            invite = self._pending_invites.pop(invite_id, None)

        if not invite:
            return {"success": False, "reason": "invite_not_found"}

        return {"success": True, "from": invite["from"], "to": invite["to"]}