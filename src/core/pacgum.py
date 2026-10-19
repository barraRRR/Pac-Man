from enum import Enum
from src.utils.utils import Coord, Color
from src.core.entity import Entity


PACGUM_COLOR = (255, 255, 255, 255)
SUPER_COLOR = (255, 255, 255, 255)


class PGType(Enum):
    """
    """
    NORMAL = "normal"
    SUPER = "super"
    EATEN = "eaten"


class PacGum(Entity):
    """
    """
    def __init__(self, pg_type: PGType, pos: Coord) -> None:
        super().__init__()
        self.pos.set_at(pos)
        self.pg_type: PGType = pg_type
        self.color.set(SUPER_COLOR if pg_type == PGType.SUPER else PACGUM_COLOR)
