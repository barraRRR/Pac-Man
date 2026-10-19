from enum import Enum
from src.utils.utils import Coord, Color, UP, RIGHT, DOWN, LEFT
from src.core.entity import Entity, State
from src.maze.bitmap import BitMap
from typing import List, Tuple, Set, Dict
from collections import deque
import pygame


BLINKY_COLOR = (223, 0, 36, 255)
PINKY_COLOR = (255, 192, 203, 255)
INKY_COLOR = (46, 109, 180, 255)
CLYDE_COLOR = (238, 70, 36, 255)
BLINKY_SPEED = 100
PINKY_SPEED = 100
INKY_SPEED = 100
CLYDE_SPEED = 100


class Ghost(Entity):
    """
    """
    path_map: Dict[Tuple[Coord, Coord], List[Coord]] = {}

    def __init__(self, name: str) -> None:
        super().__init__()
        self.name: str = name
        self.delta: Coord = Coord()

    def _find_path(
            self,
            start: Coord,
            target: Coord,
            bitmap: BitMap
            )-> List[Coord]:
        """Find shortest path from entry to exit using BFS.

        Returns:
            List of coordinates from entry to exit, or empty list if no path.
        """
        if start == target:
            return []
        if (start, target) in self.path_map:
            return self.path_map[(start, target)]

        queue: deque[Coord] = deque([start])
        visited: Set[Coord] = {start}
        parent_map: Dict[Coord, Coord] = {}
        found: bool = False

        while queue:
            curr_xy: Coord = queue.pop()

            if current == target:
                found = True
                break

            for dir in [UP, RIGHT, DOWN, LEFT]:
                if not bitmap.grid[curr_xy.y][curr_xy.x] & dir:
                    new_xy: Coord = curr_xy.step(dir)

                    if (new_xy) not in visited:
                        visited.add(new_xy)
                        parent_map[new_xy] = curr_xy
                        queue.append(new_xy)

        path: List[Coord] = []
        if not found:
            return []  # No path found, return empty list
        current: Coord = target
        while current != start:
            path.append(current)
            current = parent_map[current]
        path.append(start)
        path.reverse()
        self.path_map[(start, target)] = path
        return path

    def _move(
            self,
            clock: pygame.time.Clock,
            tile_size: int,
            fps: int = 60
        ) -> None:
        """
        """
        dt: float = clock.tick(fps) / 1000


class Blinky(Ghost):
    """
    Blinky (Rojo): Conocido como Shadow ("Sombra"), es el más agresivo y persigue directamente a Pac-Man.
    """
    def __init__(self) -> None:
        super().__init__(name="Blinky")
        self.color.set(BLINKY_COLOR)
        self.speed: int = BLINKY_SPEED


class Pinky(Ghost):
    """
    Pinky (Rosa): Conocida como Speedy ("Rápida"), intenta emboscar a Pac-Man posicionándose por delante de él.
    """
    def __init__(self) -> None:
        super().__init__(name="Pinky")
        self.color.set(PINKY_COLOR)
        self.speed: int = PINKY_SPEED


class Inky(Ghost):
    """
    Inky (Cian / Azul claro): Conocido como Bashful ("Tímido"), tiene un comportamiento impredecible que combina las posiciones de Blinky y Pac-Man.
    """
    def __init__(self) -> None:
        super().__init__(name="Inky")
        self.color.set(INKY_COLOR)
        self.speed: int = INKY_SPEED


class Clyde(Ghost):
    """
    Clyde (Naranja): Conocido como Pokey ("Lento"), persigue a Pac-Man cuando está lejos, pero se aleja a su rincón cuando se acerca demasiado.
    """
    def __init__(self) -> None:
        super().__init__(name="Clyde")
        self.color.set(CLYDE_COLOR)
        self.speed: int = CLYDE_SPEED

