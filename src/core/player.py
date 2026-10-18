from enum import Enum
from src.utils.utils import Coord, Color
from src.core.entity import Entity


PLAYER_COLOR = (255, 255, 0, 255)


class Player(Entity):
    """
    """
    def __init__(self) -> None:
        super().__init__()
        self.color.set(PLAYER_COLOR)
