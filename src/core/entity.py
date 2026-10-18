from enum import Enum
from src.utils.utils import Coord, Color
from pygame import Surface


class State(Enum):
    """
    """
    INIT = "init"
    NORMAL = "normal"
    HUNT = "hunt"
    FLEE = "flee"
    EATEN = "eaten"
    PAUSE = "pause"


class Entity:
    """
    """
    def __init__(self) -> None:
        self.state: State = State.INIT
        self.pos: Coord = Coord()
        self.color: Color = Color(0, 0, 0, 0)

    def _init_surface(self, coord: Coord, tile_size: int) -> None:
        self.sur: Surface = Surface(coord.off_get(tile_size))
