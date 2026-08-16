from enum import Enum
from game.caro import Caro


class Role(str, Enum):
    PLAYER = "player"
    SPECTATOR = "spectator"


class match:
    def __init__(self, player1, player2, match_id):
        self.player1 = player1
        self.player2 = player2
        self.spectater: list[str] = []
        self.match_id = match_id

        self.game = Caro(15, 15)
