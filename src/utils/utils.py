from typing import Tuple, Union, Dict
from src.utils.error import UnreachableTileError
from pygame import Surface
import pygame
from enum import Enum


_LOGO_PATH = "assets/logo/pacman_logo.png"


class Dir(Enum):
    UP = 1
    RIGHT = 2
    DOWN = 4
    LEFT = 8
    DEATH = "death"
    SCARED = "scared"


class Coord:
    """
    """
    frontier: Tuple[int, int] = (0, 0)

    def __init__(self, xy: Tuple[int, int] = None) -> None:
        self.x: int = xy[0] if xy else 0
        self.y: int = xy[1] if xy else 0

    def __eq__(self, other):
        if not isinstance(other, Coord):
            return False
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def __add__(self, other):
        if not isinstance(other, Coord):
            return NotImplemented
        return Coord((self.x + other.x, self.y + other.y))

    def __sub__(self, other):
        if not isinstance(other, Coord):
            return NotImplemented
        return Coord((self.x - other.x, self.y - other.y))

    @classmethod
    def _set_frontier(cls, maze_size: Tuple[int, int]) -> None:
        """
        Actualiza el limite del mapa del maze
        """
        cls.frontier = maze_size

    def get(self) -> Tuple[int, int]:
        """
        """
        return (self.x, self.y)

    def off_get(
            self,
            tile_size: int,
            top_padding: int,
            left_padding: int
        ) -> Tuple[int, int]:
        """
        Devuelve las coords con offset (margen de ventana)
        """
        return (
            (self.x * tile_size) + left_padding,
            (self.y * tile_size) + top_padding
        )

    def set_at(self, xy: Union['Coord', Tuple[int, int]]) -> None:
        """
        """
        if isinstance(xy, Coord):
            self.y = xy.y
            self.x = xy.x
        else:
            self.x, self.y = xy

    def step(self, dir: Dir) -> None:
        """
        """
        # pdt implementa off boundaries
        if dir == Dir.UP:
            self.y -= 1
        elif dir == Dir.RIGHT:
            self.x += 1
        elif dir == Dir.DOWN:
            self.y += 1
        elif dir == Dir.LEFT:
            self.x -= 1

    def _get_delta(self, target: "Coord") -> Dir:
        """
        Te dice hacia que direccion está target
        """

        directions = {
            (0, -1): Dir.UP,
            (1, 0): Dir.RIGHT,
            (0, 1): Dir.DOWN,
            (-1, 0): Dir.LEFT,
        }
        delta = directions.get(((target.x - self.x), (target.y - self.y)), -1)
        if delta == -1:
            raise UnreachableTileError
        
        return delta


class Color:
    """
    """
    def __init__(self, r: int, g: int, b: int, alpha: int) -> None:
        self._r: int = 0
        self._g: int = 0
        self._b: int = 0
        self._alpha: int = 0
        self.set((r, g, b, alpha))

    def get(self) -> Tuple[int, int, int, int]:
        """
        """
        return (self._r, self._g, self._b, self._alpha)

    def set(self, color: Tuple[int, int, int, int]) -> None:
        """
        """
        self._r, self._g, self._b, self._alpha = tuple(
            min(255, max(0, c)) for c in color
            )


class Logo:
    """
    Loads the logo asset
    """
    img: Surface | None = None

    def __init__(self, path: str = _LOGO_PATH) -> None:
        self._path: str = path
    
    @classmethod
    def _load_logo(cls, path: str = _LOGO_PATH) -> Surface:
        """
        proteger con try-except y pensar qué ocurre si no se encuentra el file
        """
        cls.img = pygame.image.load(path)
        cls.img.convert()