from enum import Enum
from dataclasses import dataclass
from typing import List, Set
from game.caro import Caro


class Role(str, Enum):
    PLAYER = "player"
    SPECTATOR = "spectator"


class Match:
    def __init__(self, player1: int, player2: int, match_id: int):
        self.player1 = player1
        self.player2 = player2
        self.match_id = match_id
        self.spectator: Set[int] = set()
        self.game = Caro(rows=15, cols=15)
