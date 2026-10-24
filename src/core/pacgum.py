from enum import Enum
from src.utils.utils import Coord, Color
from src.core.entity import Entity


PACGUM_COLOR = (255, 255, 255, 255)
SUPER_COLOR = (255, 255, 255, 255)


class PacGum(Entity):
    """
    """
    def __init__(self, pos: Coord, points: int) -> None:
        super().__init__()
        self.pos.set_at(pos)
        self.color.set(PACGUM_COLOR)
        self.points: int = points

class SuperPacGum(PacGum):
    """
    """
    def __init__(self, pos: Coord, points: int) -> None:
        super().__init__(pos, points)
        self.color.set(SUPER_COLOR)
