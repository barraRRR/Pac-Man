from enum import Enum
from typing import Dict, List, Tuple
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
    entity_map: Dict[Tuple[int, int], List["Entity"]] = {}

    def __init__(self) -> None:
        self.state: State = State.INIT
        self.pos: Coord = Coord()
        self.color: Color = Color(0, 0, 0, 0)
        self.delta: int = None
        self.alive: bool = True
        self.spawn_pos: Coord = self.pos
        self._update_entity_map(True)

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
            self._update_entity_map(False)
            self.pos.step(dir)
            self._update_entity_map(True)

    def kill(self, other: "Entity") -> None:
        """
        Elimina a la otra entidad
        """
        other.alive = False

    def _update_entity_map(self, add: bool) -> None:
        """
        Actualiza el dict de posiciones de las entidades
        """
        pos = self.pos.get()
        if pos not in Entity.entity_map:
            Entity.entity_map[pos] = []
        if add:
            Entity.entity_map[pos].append(self)
        elif not add and self in Entity.entity_map[pos]:
            Entity.entity_map[pos].remove(self)



