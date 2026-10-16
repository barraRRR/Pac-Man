from typing import Tuple


class Coord:
    """
    """
    def __init__(self, xy: Tuple[int, int] = None) -> None:
        self.x: int = xy[0] if xy else None
        self.y: int = xy[1] if xy else None

    def get(self) -> Tuple[int, int]:
        """
        """
        return (self.x, self.y)

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
