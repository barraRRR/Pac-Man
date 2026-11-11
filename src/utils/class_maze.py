"""Adapt the external generator and select maze tiles."""

from mazegenerator import MazeGenerator
from src.maze.bitmap import BitMap
from collections import deque
from typing import Tuple
import random
from pygame import Surface
from src.utils.logger import logger


class Maze:
    """Maze adapter that wraps the ``mazegenerator`` package.

    This is the only project class that knows about the external package.
    App decides when to generate each level; Maze handles how to do it.
    """

    def __init__(self, seed: int):
        """Store the base seed and initialize an empty state.

        Args:
            seed: Configuration seed, used only for level 1.
        """
        self._seed = seed
        self._bitmap: BitMap = BitMap()
        self.sur: Surface | None = None

        self._col: int = 0
        self._row: int = 0
        self._size: Tuple[int, int] = (0, 0)
        self._frontier: Tuple[int, int] = (0, 0)

    @property
    def grid(self) -> list[list[int]]:
        """Return the current level's grid (read-only)."""
        return self._bitmap.grid

    @property
    def size(self) -> Tuple[int, int]:
        """Return the current maze dimensions."""
        return (len(self.grid), len(self.grid[0]))

    @property
    def col(self) -> int:
        """Return the number of maze columns."""
        return self._col

    @property
    def row(self) -> int:
        """Return the number of maze rows."""
        return self._row

    @property
    def frontier(self) -> Tuple[int, int]:
        """Return the coordinates of the maze boundary."""
        return (self._col - 1, self._row - 1)

    def generate_level(self, number: int, width: int, height: int) -> None:
        """Generate a level map and store its grid.

        Pass the configured seed to the generator only for level 1; later
        levels use seed 0.

        Args:
            number: Level number (starting at 1).
            width: Level width in tiles.
            height: Level height in tiles.
        """
        semilla = self._seed if number == 1 else 0

        generator_map = MazeGenerator(
            size=(width, height), perfect=False, seed=semilla)

        self._bitmap.grid.clear()
        self._bitmap.grid.extend(generator_map.maze)
        self._row = len(self._bitmap.grid)
        self._col = len(self._bitmap.grid[0])
        self._size = (self._col, self._row)

    def center_comecocos(self) -> tuple[int, int]:
        """
        Return the walkable cell closest to the center as ``(x, y)``.

        Search the grid and choose the non-solid (not 15) cell with the
        shortest squared Euclidean distance to the center. Ties resolve to
        the first cell encountered in row-major order.
        """
        height_map = len(self.grid)
        width = len(self.grid[0])
        center_x = width // 2
        center_y = height_map // 2

        best: tuple[int, int] | None = None
        best_dist: int | None = None

        for y in range(height_map):
            for x in range(width):
                if self.grid[y][x] == 15:
                    continue
                dist = (x - center_x) ** 2 + (y - center_y) ** 2
                if best_dist is None or dist < best_dist:
                    best = (x, y)
                    best_dist = dist
        if best is None:
            raise ValueError("Maze has no walkable cells.")
        return best

    def select_ghost_spawns(
        self,
        reachable: set[tuple[int, int]],
    ) -> list[tuple[int, int]]:
        """Choose a random reachable tile from each corner zone.

        The order matches ``corner_zone_cells``: top-left, top-right,
        bottom-left, and bottom-right.

        Args:
            reachable: Cells reachable from Pac-Man, calculated once per
                level and reused for all selections.
        """
        ghost_spawns: list[tuple[int, int]] = []

        for zone in self.corner_zone_cells():
            candidates = [cell for cell in zone if cell in reachable]

            if not candidates:
                raise ValueError("No reachable cell in a ghost corner zone.")

            ghost_spawns.append(random.choice(candidates))

        return ghost_spawns

    def reachable_cells(self, start: tuple[int, int]) -> set[tuple[int, int]]:
        """Return every tile reachable from ``start`` using breadth-first search.

        A neighboring tile is reachable only if the current tile has no wall
        in that direction and the neighbor has no wall on its opposite side.
        The result includes ``start``. Raise ``ValueError`` if the maze has
        not been generated or ``start`` is outside its bounds.
        """
        if not self.grid:
            raise ValueError("Maze has not been generated.")

        height = len(self.grid)
        width = len(self.grid[0])
        start_x, start_y = start

        if not (0 <= start_x < width and 0 <= start_y < height):
            raise ValueError("Starting position is outside the maze.")

        # Discovered cells, so no cell is visited more than once.
        visited = {start}

        # Discovered cells that still need to be checked.
        pending = deque([start])

        # (dx, dy, outgoing wall, opposite wall of the neighboring cell)
        directions = (
            (0, -1, 1, 4),   # Up: N=1 and S=4.
            (1, 0, 2, 8),    # Right: E=2 and W=8.
            (0, 1, 4, 1),    # Down: S=4 and N=1.
            (-1, 0, 8, 2),  # Left: W=8 and E=2.
        )

        while pending:
            x, y = pending.popleft()
            current_cell = self.grid[y][x]

            for dx, dy, wall, opposite_wall in directions:
                next_x = x + dx
                next_y = y + dy

                # Ignore neighbors outside the grid.
                if not (0 <= next_x < width and 0 <= next_y < height):
                    continue

                next_position = (next_x, next_y)

                # Skip cells that have already been discovered.
                if next_position in visited:
                    continue

                next_cell = self.grid[next_y][next_x]

                # Check that both cells are open.
                if current_cell & wall or next_cell & opposite_wall:
                    continue

                visited.add(next_position)
                pending.append(next_position)

        return visited

    def corner_zone_cells(self) -> list[list[tuple[int, int]]]:
        """Return the corner-zone tiles in a fixed order.

        The zones are ordered top-left, top-right, bottom-left, and
        bottom-right. Within each zone, tiles are traversed row by row,
        from left to right. Each zone covers one fifth of the maze's width
        and height, rounded down with a minimum of one tile.
        """
        if not self.grid:
            raise ValueError("Maze has not been generated.")

        height = len(self.grid)
        width = len(self.grid[0])

        zone_width = max(1, width // 5)
        zone_height = max(1, height // 5)

        top_left = [
            (x, y)
            for y in range(zone_height)
            for x in range(zone_width)
        ]

        top_right = [
            (x, y)
            for y in range(zone_height)
            for x in range(width - zone_width, width)
        ]

        bottom_left = [
            (x, y)
            for y in range(height - zone_height, height)
            for x in range(zone_width)
        ]

        bottom_right = [
            (x, y)
            for y in range(height - zone_height, height)
            for x in range(width - zone_width, width)
        ]

        return [top_left, top_right, bottom_left, bottom_right]

    def select_super_pacgum_spawns(
        self,
        reachable: set[tuple[int, int]],
        ghost_spawns: list[tuple[int, int]],
    ) -> list[tuple[int, int]]:
        """Choose a reachable super pac-gum tile in each corner zone.

        Randomly select from reachable cells that are not occupied by a
        ghost. Raise ``ValueError`` if any zone has no eligible cell.

        Args:
            reachable: Cells reachable from Pac-Man, calculated once per
                level and reused for all selections.
            ghost_spawns: Positions occupied by the ghosts.
        """
        ghost_positions = set(ghost_spawns)
        super_pacgum_spawns: list[tuple[int, int]] = []

        for zone in self.corner_zone_cells():
            candidates = [
                cell
                for cell in zone
                if cell in reachable and cell not in ghost_positions
            ]

            if not candidates:
                raise ValueError(
                    "No available reachable cell for a super-pacgum."
                )

            super_pacgum_spawns.append(random.choice(candidates))

        return super_pacgum_spawns

    def select_pacgum_spawns(
        self,
        reachable: set[tuple[int, int]],
        pacman_start: tuple[int, int],
        ghost_spawns: list[tuple[int, int]],
        super_pacgum_spawns: list[tuple[int, int]],
        requested: int,
    ) -> list[tuple[int, int]]:
        """Choose free, reachable tiles for regular pac-gums.

        Exclude cells occupied by Pac-Man, ghosts, and super pac-gums, and
        never select the same tile twice. If there is not enough room, log a
        warning and place as many as possible.
        """
        if requested <= 0:
            return []

        occupied = {pacman_start, *ghost_spawns, *super_pacgum_spawns}
        candidates = sorted(reachable - occupied)
        placed = random.sample(candidates, min(requested, len(candidates)))

        if len(placed) < requested:
            logger.error("Error: requested %s pacgums, only %s free cells, "
                         "using %s.", requested, len(placed), len(placed))

        return placed
