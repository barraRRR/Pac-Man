"""Types and utilities shared by entities and the interface."""

from collections.abc import Callable
from typing import Tuple, Union
from types import NotImplementedType
from src.utils.error import UnreachableTileError
from pygame import Surface
import pygame
from enum import Enum


_LOGO_PATH = "assets/logo/pacman_logo.png"


class Dir(Enum):
    """Movement directions and animation states."""

    UP = 1
    RIGHT = 2
    DOWN = 4
    LEFT = 8
    DEATH = "death"
    SCARED = "scared"


class Coord:
    """Represent an integer position in the maze."""

    frontier: Tuple[int, int] = (0, 0)

    def __init__(self, xy: Tuple[int, int] | None = None) -> None:
        """Initialize the coordinate from an optional tuple."""
        self.x: int = xy[0] if xy else 0
        self.y: int = xy[1] if xy else 0

    def __eq__(self, other: object) -> bool:
        """Compare this coordinate with another."""
        if not isinstance(other, Coord):
            return False
        return self.x == other.x and self.y == other.y

    def __hash__(self) -> int:
        """Return a hash based on the coordinates."""
        return hash((self.x, self.y))

    def __add__(self, other: object) -> "Coord | NotImplementedType":
        """Add two coordinates and return a new position."""
        if not isinstance(other, Coord):
            return NotImplemented
        return Coord((self.x + other.x, self.y + other.y))

    def __sub__(self, other: object) -> "Coord | NotImplementedType":
        """Subtract two coordinates and return a new position."""
        if not isinstance(other, Coord):
            return NotImplemented
        return Coord((self.x - other.x, self.y - other.y))

    @classmethod
    def _set_frontier(cls, maze_size: Tuple[int, int]) -> None:
        """Update the maze coordinate boundary."""
        cls.frontier = maze_size

    def get(self) -> Tuple[int, int]:
        """Return the coordinates as an ``(x, y)`` tuple."""
        return (self.x, self.y)

    def off_get(
        self,
        tile_size: int,
        top_padding: int,
        left_padding: int
    ) -> Tuple[int, int]:
        """
        Return the coordinates with the window padding offset.
        """
        return (
            (self.x * tile_size) + left_padding,
            (self.y * tile_size) + top_padding
        )

    def set_at(self, xy: Union['Coord', Tuple[int, int]]) -> None:
        """Copy the coordinates from another position or a tuple."""
        if isinstance(xy, Coord):
            self.y = xy.y
            self.x = xy.x
        else:
            self.x, self.y = xy

    def step(self, dir: Dir) -> None:
        """Move one tile in the specified direction."""
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
        Return the direction toward ``target``.
        """

        directions = {
            (0, -1): Dir.UP,
            (1, 0): Dir.RIGHT,
            (0, 1): Dir.DOWN,
            (-1, 0): Dir.LEFT,
        }
        delta = directions.get((target.x - self.x, target.y - self.y))
        if delta is None:
            raise UnreachableTileError

        return delta


class Color:
    """Store an RGBA color with components limited to 0-255."""

    def __init__(self, r: int, g: int, b: int, alpha: int) -> None:
        """Initialize the color and clamp its components."""
        self._r: int = 0
        self._g: int = 0
        self._b: int = 0
        self._alpha: int = 0
        self.set((r, g, b, alpha))

    def get(self) -> Tuple[int, int, int, int]:
        """Return the RGBA components."""
        return (self._r, self._g, self._b, self._alpha)

    def set(self, color: Tuple[int, int, int, int]) -> None:
        """Update the RGBA components and clamp them to 0-255."""
        self._r, self._g, self._b, self._alpha = tuple(
            min(255, max(0, c)) for c in color
        )


class Logo:
    """Load the logo from the specified image file."""

    img: Surface | None = None

    def __init__(self, path: str = _LOGO_PATH) -> None:
        """Store the path to the logo to be loaded."""
        self._path: str = path

    @classmethod
    def _load_logo(cls, path: str = _LOGO_PATH) -> Surface:
        """Load the logo image and cache it on the class."""
        image = pygame.image.load(path).convert()
        cls.img = image
        return image


def make_interval_ticker(interval: float) -> Callable[[float], int]:
    """Create a callable that counts elapsed intervals without losing remainder.

    Each call adds its ``dt`` to a retained accumulator, returns the number of
    complete ``interval`` periods, and carries any leftover time into the
    next call. Raise ``ValueError`` if ``interval`` is not positive.
    """
    if interval <= 0:
        raise ValueError("interval must be greater than zero")

    accumulator = 0.0

    def update(dt: float) -> int:
        """Accumulate elapsed time and return the available ticks."""
        nonlocal accumulator
        accumulator += dt
        ticks = 0
        while accumulator >= interval:
            accumulator -= interval
            ticks += 1
        return ticks

    return update
