"""Almacena el mapa de paredes como una cuadrícula de bits."""

from typing import List


UP = 1
RIGHT = 2
DOWN = 4
LEFT = 8


class BitMap:
    """Envuelve las máscaras de pared de cada casilla del laberinto."""

    def __init__(self, grid: List[List[int]] = None) -> None:
        """Inicializa el mapa con una cuadrícula opcional."""
        self._grid: List[List[int]] = grid if grid is not None else []

    @property
    def grid(self) -> List[List[int]]:
        """Devuelve la cuadrícula de máscaras de pared."""
        return self._grid