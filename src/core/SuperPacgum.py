from enum import Enum
from src.utils.utils import Coord, Color, PACGUM_COLOR, SUPER_COLOR
from src.core.pacgum import PacGum, PGType


class SuperPacGum(PacGum):
    """
    """
    def __init__(self, pos: Coord) -> None:
        super().__init__(PGType.SUPER, pos)
        self.color: Color = Color(*SUPER_COLOR)
