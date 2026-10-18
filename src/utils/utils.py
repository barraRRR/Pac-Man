from typing import Tuple


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

    def set_at(self, xy: Tuple[int, int]) -> None:
        """
        """
        self.x, self.y = xy
        

class Color:
    """
    """
    def __init__(self, r: int, g: int, b: int, alpha: int) -> None:
        self.r: int = r
        self.g: int = g
        self.b: int = b
        self.alpha: int = alpha

    def get(self) -> Tuple[int, int, int, int]:
        """
        """
        return (self.r, self.g, self.b, self.alpha)

    def set(self, color: Tuple[int, int, int, int]) -> None:
        self.r, self.g, self.b, self.alpha = color
