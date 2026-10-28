from enum import Enum
from src.utils.utils import Coord, Color, Dir
from src.core.entity import Entity, State
import pygame
from pygame import Surface
from src.maze.bitmap import BitMap
from typing import List, Tuple, Set, Dict
from collections import deque
import pygame
import time
from pathlib import Path


BLINKY_COLOR = (223, 0, 36, 255)
PINKY_COLOR = (255, 192, 203, 255)
INKY_COLOR = (46, 109, 180, 255)
CLYDE_COLOR = (238, 70, 36, 255)

# Cuanta menos, más rápido
BLINKY_SPEED = 300
PINKY_SPEED = 500
INKY_SPEED = 500
CLYDE_SPEED = 500

# ASSETS PATHS
BLINKY_ANI_PATH = "assets/animations/ghosts/blinky"
PINKY_ANI_PATH = "assets/animations/ghosts/pinky"
INKY_ANI_PATH = "assets/animations/ghosts/inky"
CLYDE_ANI_PATH = "assets/animations/ghosts/clyde"


class Ghost(Entity):
    """
    """
    path_map: Dict[
        Tuple[Tuple[int, int], Tuple[int, int]],
        List[Coord]
    ] = {}
    edible: bool = False

    def __init__(self, name: str, points: int) -> None:
        super().__init__()
        self.name: str = name
        self._timer_ms: int = 0
        self.points: int = points

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
        cache_key = (start.get(), target.get())
        if cache_key in self.path_map:
            return self.path_map[cache_key]

        queue: deque[Coord] = deque([start])
        visited: Set[Coord] = {start}
        parent_map: Dict[Coord, Coord] = {}
        found: bool = False

        while queue:
            curr_xy: Coord = queue.popleft()

            if curr_xy == target:
                found = True
                break

            for dir in [Dir.UP, Dir.RIGHT, Dir.DOWN, Dir.LEFT]:
                if not bitmap.grid[curr_xy.y][curr_xy.x] & dir.value:
                    new_xy = Coord(curr_xy.get())
                    new_xy.step(dir)

                    if new_xy not in visited:
                        visited.add(new_xy)
                        parent_map[new_xy] = curr_xy
                        queue.append(new_xy)

        path: List[Coord] = []
        if not found:
            return []  # No path found, return empty list
        current: Coord = target
        while current != start:
            path.append(Coord(current.get()))
            current = parent_map[current]
        path.append(Coord(start.get()))
        path.reverse()
        self.path_map[cache_key] = path
        return path

    def _move(
            self,
            target: Coord,
            dt: int,
            tile_size: int,
            bitmap: BitMap,
            fps: int = 60
        ) -> None:
        pass

    def _die(self) -> None:
        """
        El jugador alcanza o es aclanzado por un Ghost not edible
        """
        self._set_position(self.spawn_pos)
        self.alive = True
        # implementar cooldown

    def resolve_tile(self) -> None:
        """
        Interactua con el resto de Entity de la casilla
        """
        from src.core.player import Player
        for ent in list(Entity.entity_map.get(self.pos.get(), [])):
            if isinstance(ent, Player) and not self.edible and ent.alive:
                ent._die()


class Blinky(Ghost):
    """
    Blinky (Rojo): Conocido como Shadow ("Sombra"), es el más agresivo y persigue directamente a Pac-Man.
    """

    def __init__(self, points: int) -> None:
        super().__init__(name="Blinky", points=points)
        self.color.set(BLINKY_COLOR)
        self.speed: int = BLINKY_SPEED

        # ***** LOAD_ANIMATION *****
        self.ani_path: str = BLINKY_ANI_PATH

    def _move(
            self,
            target: Coord,
            dt: int,
            tile_size: int,
            bitmap: BitMap,
            fps: int = 60
        ) -> None:
        """
        """
        if self.alive == False:
            self._die()
        self._timer_ms += dt
        if self._timer_ms >= self.speed:
            self._timer_ms -= self.speed
            curr_target: Coord = (
                target if self.edible == False else self.spawn_pos
            )
            path: List[Coord] = self._find_path(
                start=self.pos,
                target=curr_target,
                bitmap=bitmap
            )
            if len(path) >= 2:
                self.delta = self.pos._get_delta(path[1])
                self._set_position(path[1])

class Pinky(Ghost):
    """
    Pinky (Rosa): Conocida como Speedy ("Rápida"), intenta emboscar a Pac-Man posicionándose por delante de él.
    """

    def __init__(self, points: int) -> None:
        super().__init__(name="Pinky", points=points)
        self.color.set(PINKY_COLOR)
        self.speed: int = PINKY_SPEED
        self.ani_path: str = PINKY_ANI_PATH


class Inky(Ghost):
    """
    Inky (Cian / Azul claro): Conocido como Bashful ("Tímido"), tiene un comportamiento impredecible que combina las posiciones de Blinky y Pac-Man.
    """

    def __init__(self, points: int) -> None:
        super().__init__(name="Inky", points=points)
        self.color.set(INKY_COLOR)
        self.speed: int = INKY_SPEED
        self.ani_path: str = INKY_ANI_PATH


class Clyde(Ghost):
    """
    Clyde (Naranja): Conocido como Pokey ("Lento"), persigue a Pac-Man cuando está lejos, pero se aleja a su rincón cuando se acerca demasiado.
    """

    def __init__(self, points: int) -> None:
        super().__init__(name="Clyde", points=points)
        self.color.set(CLYDE_COLOR)
        self.speed: int = CLYDE_SPEED
        self.ani_path: str = CLYDE_ANI_PATH
