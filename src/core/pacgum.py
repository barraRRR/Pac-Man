from enum import Enum
from src.utils.utils import Coord, Color


PACGUM_COLOR = (0, 0, 0, 0)
SUPER_COLOR = (0, 0, 0, 0)


class PGType(Enum):
    """
    """
    NORMAL = "normal"
    SUPER = "super"
    EATEN = "eaten"


class PacGum:
    """
    """
    def __init__(self, pg_type: PGType, pos: Coord) -> None:
        self.pg_type: PGType = pg_type
        self.pos: Coord = pos
        self.color: Color = Color(SUPER_COLOR if pg_type == PGType.SUPER else PACGUM_COLOR)
