from enum import Enum
from src.utils.utils import Coord, Color
from src.core.pacgum import PacGum


PACGUM_COLOR = (0, 0, 0, 0)
SUPER_COLOR = (0, 0, 0, 0)


class PGType(Enum):
    """
    """
    NORMAL = "normal"
    SUPER = "super"
    EATEN = "eaten"


class SuperPacGum(PacGum):
    """
    """
    def __init__(self, pos: Coord) -> None:
        super().__init__(PGType.SUPER, pos)
        self.color: Color = Color(*SUPER_COLOR)
