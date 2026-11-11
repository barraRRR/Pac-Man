"""Store the wall map as a bit grid."""

from typing import List


UP = 1
RIGHT = 2
DOWN = 4
LEFT = 8


class BitMap:
    """Wrap the wall masks for each maze tile."""

    def __init__(self, grid: List[List[int]] | None = None) -> None:
        """Initialize the map with an optional grid."""
        self._grid: List[List[int]] = grid if grid is not None else []

    @property
    def grid(self) -> List[List[int]]:
        """Return the grid of wall masks."""
        return self._grid
