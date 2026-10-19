from typing import Tuple, Union, Dict
from src.maze.bitmap import UP, RIGHT, DOWN, LEFT


class Coord:
    """
    """
    def __init__(self, xy: Tuple[int, int] = None) -> None:
        self.x: int = xy[0] if xy else 0
        self.y: int = xy[1] if xy else 0

    def get(self) -> Tuple[int, int]:
        """
        """
        return (self.x, self.y)

    def off_get(self, tile_size: int) -> Tuple[int, int]:
        """
        Devuelve las coords con offset (margen de ventana)
        """
        from src.core.engine import _PADDING
        return ((self.x * tile_size) + _PADDING, (self.y * tile_size) + _PADDING)

    def set_at(self, xy: Union['Coord', Tuple[int, int]]) -> None:
        """
        """
        if isinstance(xy, Coord):
            self.y = xy.y
            self.x = xy.x
        else:
            self.x, self.y = xy

    def step(self, dir: int) -> None:
        """
        """
        if dir == UP:
            self.y -= 1
        elif dir == RIGHT:
            self.x += 1
        elif dir == DOWN:
            self.y += 1
        elif dir == LEFT:
            self.x -= 1

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
