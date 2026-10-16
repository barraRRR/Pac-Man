from enum import Enum
from src.utils.utils import Coord, Color


PLAYER_COLOR = (0, 0, 0, 0)


class PState(Enum):
    """
    """
    NORMAL = "normal"
    POWER = "power"
    DEAD = "dead"
    PAUSE = "pause"


class Player:
    """
    """
    def __init__(self) -> None:
        self.state: PState = PState.PAUSE
        self.pos: Coord = Coord()
        self.color: Color = Color(*PLAYER_COLOR)
