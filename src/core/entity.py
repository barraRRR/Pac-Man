from enum import Enum
from typing import Dict
from src.utils.utils import Coord, Color
from pygame import Surface, SRCALPHA
from src.maze.bitmap import BitMap, UP, RIGHT, DOWN, LEFT
from src.utils.error import HitWallError


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
        self.delta: int = None

    def _init_surface(self, coord: Coord, tile_size: int) -> None:
        """
        """
        self.sur: Surface = Surface((tile_size, tile_size), SRCALPHA)
        self.sur.fill((0, 0, 0, 0))

    def _move(self, bitmap: BitMap, dir: int) -> None:
        """
        """
        if bitmap.grid[self.pos.y][self.pos.x] & dir:
            raise HitWallError

        else:
            self.pos.step(dir)