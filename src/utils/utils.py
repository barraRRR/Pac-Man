from typing import Tuple


class Coord:
    """
    """
    def __init__(self, x: int = None, y: int = None) -> None:
        self.x: int = x
        self.y: int = y

    def get(self) -> Tuple[int, int]:
        """
        """
        return (self.x, self.y)


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
