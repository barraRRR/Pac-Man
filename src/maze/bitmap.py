from typing import List


UP = 1
RIGHT = 2
DOWN = 4
LEFT = 8


class BitMap:
    """
    Lista de integers que conforman el mapa con sus celdas tratadas como bytes
    """
    def __init__(self, grid: List[List[int]] = None) -> None:
        self._grid: List[List[int]] = grid if grid is not None else []

    @property
    def grid(self) -> List[List[int]]:
        return self._grid