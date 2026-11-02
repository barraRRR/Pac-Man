from enum import Enum
from src.utils.utils import Coord, Color, Dir
from src.core.entity import Entity, State, ANI_SPEED
from src.utils.error import UnreachableTileError
import pygame
from pygame import Surface
from src.maze.bitmap import BitMap
from typing import List, Tuple, Set, Dict
from collections import deque
import pygame
import time
import random
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

SCARED_GHOST = "assets/animations/ghosts/scared_ghost"


class Ghost(Entity):
    """
    """
    path_map: Dict[
        Tuple[Tuple[int, int], Tuple[int, int]],
        List[Coord]
    ] = {}
    edible: bool = False
    RESPAWN_DURATION_MS: int = 10_000
    RESPAWN_FLASH_DURATION_MS: int = 5_000

    _frames_scared: List[Surface] = []
    _frames_flashing: List[Surface] = []

    _scaled_scared_frames: Dict[Tuple[int, int], Tuple[List[Surface], List[Surface]]] = {}
    show_white: bool = False


    def __init__(self, name: str, points: int) -> None:
        super().__init__()
        self.name: str = name
        self._timer_ms: int = 0
        self._respawn_timer_ms: int = 0
        self.points: int = points
        self.current_corridor: List[Coord] = []
        # Huida por cuartos: salidas del nivel y estado del ciclo.
        self._ghost_spawns: List[Tuple[int, int]] = []
        self._flee_spawn: Coord | None = None   # ancla: salida del cuarto opuesto
        self._flee_target: Coord | None = None  # destino actual de la huida
        self._scared_frame_timer_ms: int = 0
        self._scared_frame_index: int = 0

    @classmethod
    def _load_scared_frames(cls) -> None:
        """Carga una unica vez los frames asustados que comparten los 4 fantasmas."""
        if cls._frames_scared:
            return

        frames: List[Surface] = []
        for png in sorted(Path(SCARED_GHOST).glob("*.png")):
            frames.append(pygame.image.load(str(png)).convert_alpha())

        if not frames:
            print(f"[WARN] No scared frames found in {SCARED_GHOST}")
            return

        cls._frames_scared = frames[0::2]    # azules: frames 00 y 02
        cls._frames_flashing = frames[1::2]  # blancos: frames 01 y 03

    def get_frame(self, dt: int) -> Surface:
        """Devuelve el frame asustado azul o blanco, escalado al tamaño normal."""
        if not self.edible or not self._frames_scared:
            return super().get_frame(dt)

        if self.delta is None:
            self.delta = Dir.RIGHT

        normal_frames = self._frames.get(self.delta)
        if not normal_frames:
            return super().get_frame(dt)

        frame_size = normal_frames[0].get_size()

        if frame_size not in Ghost._scaled_scared_frames:
            blue_frames = [
                pygame.transform.scale(frame, frame_size)
                for frame in Ghost._frames_scared
            ]
            white_frames = [
                pygame.transform.scale(frame, frame_size)
                for frame in Ghost._frames_flashing
            ]
            Ghost._scaled_scared_frames[frame_size] = (
                blue_frames,
                white_frames,
            )

        blue_frames, white_frames = Ghost._scaled_scared_frames[frame_size]
        frames = (
            white_frames
            if Ghost.show_white and white_frames
            else blue_frames
        )

        self._scared_frame_timer_ms += dt
        if self._scared_frame_timer_ms >= ANI_SPEED:
            self._scared_frame_timer_ms %= ANI_SPEED
            self._scared_frame_index = (
                self._scared_frame_index + 1
            ) % len(frames)

        return frames[self._scared_frame_index]


    def _find_path(
            self,
            start: Coord,
            target: Coord,
            bitmap: BitMap
    ) -> List[Coord]:
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

    def _update_delta(self, step: Coord) -> None:
        """
        Actualiza el delta según la siguiente casilla
        """
        try:
            self.delta = self.pos._get_delta(step)
        except UnreachableTileError:
            pass

    def _get_corridor(self, path: List[Coord]) -> None:
        """
        Devuelve la lista de casillas del pasillo que tiene por delante
        """
        self.current_corridor.clear()
        if len(path) < 2:
            return

        corridor_direction = self.pos._get_delta(path[1])
        self.delta = corridor_direction
        self.current_corridor.append(path[0])

        for previous, step in zip(path, path[1:]):
            step_direction = previous._get_delta(step)
            if step_direction != corridor_direction:
                break
            self.current_corridor.append(step)

    def _follow_corridor(self) -> None:
        """
        """
        self._set_position(self.current_corridor[1])
        self._update_delta(self.current_corridor[1])
        self.current_corridor.pop(0)

    def _die(self) -> None:
        """
        El jugador alcanza o es aclanzado por un Ghost not edible
        """
        self.current_corridor.clear()
        self._set_position(self.spawn_pos)
        self.alive = True
        # implementar cooldown

    def _update_respawn(self, dt: int) -> None:
        """Espera 10 segundos y reactiva al fantasma en su esquina."""
        if self.state != State.EATEN:
            self.state = State.EATEN
            self._respawn_timer_ms = 0

        self._respawn_timer_ms += dt

        if self._respawn_timer_ms >= self.RESPAWN_DURATION_MS:
            self._respawn_timer_ms = 0
            self.state = State.NORMAL
            self._die()

    def resolve_tile(self) -> None:
        """
        Interactua con el resto de Entity de la casilla
        """
        if not self.alive:
            return
        from src.core.player import Player
        for ent in list(Entity.entity_map.get(self.pos.get(), [])):
            if isinstance(ent, Player) and not self.edible and ent.alive:
                ent._die()

    def _reset(self) -> None:
        """Deja el fantasma listo para una partida nueva: visible y con su reloj a cero."""
        self.alive = True
        self._timer_ms = 0
        self.current_corridor.clear()
        self._respawn_timer_ms = 0
        self.state = State.NORMAL
        self._flee_spawn = None
        self._flee_target = None

    def _get_quadrant(
        self,
        pos: Coord,
        bitmap: BitMap,
        opposite: bool = False
    ) -> int:
        """Devuelve el cuarto de una casilla, o el diagonal si opposite es True."""
        middle_x: int = len(bitmap.grid[0]) // 2
        middle_y: int = len(bitmap.grid) // 2

        is_left: bool = pos.x < middle_x
        is_top: bool = pos.y < middle_y

        if is_top and is_left:
            quadrant: int = 1    # arriba-izquierda
        elif is_top:
            quadrant = 2         # arriba-derecha
        elif is_left:
            quadrant = 4         # abajo-izquierda
        else:
            quadrant = 3         # abajo-derecha

        if opposite:
            # Diagonal del mapa: 1 <-> 3 y 2 <-> 4
            quadrant = quadrant + 2 if quadrant <= 2 else quadrant - 2

        return quadrant

    def _get_opposite_spawn(
        self,
        target: Coord,
        bitmap: BitMap,
        ghost_spawns: List[Tuple[int, int]]
    ) -> Coord | None:
        """Busca una salida de fantasma en el cuarto opuesto a Pac-Man."""
        target_quadrant: int = self._get_quadrant(target, bitmap, opposite=True)

        for spawn_x, spawn_y in ghost_spawns:
            spawn_quadrant: int = self._get_quadrant(
                Coord((spawn_x, spawn_y)), bitmap
            )
            if spawn_quadrant == target_quadrant:
                return Coord((spawn_x, spawn_y))

        return None

    def _get_nearby_cell(self, center: Coord, bitmap: BitMap) -> Coord | None:
        """Elige al azar una casilla transitable a 1-3 pasos de center."""
        candidates: List[Coord] = []
        visited: Set[Coord] = {center}
        frontier: List[Coord] = [center]

        for _ in range(3):   # tres anillos de expansion
            next_frontier: List[Coord] = []
            for cell in frontier:
                for dir in [Dir.UP, Dir.RIGHT, Dir.DOWN, Dir.LEFT]:
                    if bitmap.grid[cell.y][cell.x] & dir.value:
                        continue   # pared en esa direccion
                    neighbour: Coord = Coord(cell.get())
                    neighbour.step(dir)
                    if neighbour in visited:
                        continue
                    visited.add(neighbour)
                    candidates.append(neighbour)
                    next_frontier.append(neighbour)
            frontier = next_frontier

        if not candidates:
            return None
        return random.choice(candidates)

    def _move_superpacgum(
        self,
        target: Coord,
        dt: int,
        tile_size: int,
        bitmap: BitMap
    ) -> None:
        """Huida por cuartos mientras dura la super-pacgum."""

        self.current_corridor.clear()

        # Sin salidas del nivel no hay destino posible: quieto.
        if not self._ghost_spawns:
            return

        # Mismo latido que la caza: un paso cada `speed` ms.
        self._timer_ms += dt
        if self._timer_ms < self.speed:
            return
        self._timer_ms -= self.speed

        # Ancla de la huida: salida del cuarto opuesto a Pac-Man.
        # Si Pac-Man cambia de cuarto, se cambia de esquina.
        flee_spawn: Coord | None = self._get_opposite_spawn(
            target, bitmap, self._ghost_spawns)
        
        if flee_spawn is None:
            return
        
        if self._flee_spawn is None or self._flee_spawn != flee_spawn:
            self._flee_spawn = flee_spawn
            self._flee_target = Coord(flee_spawn.get())

        path: List[Coord] = self._find_path(
            start=self.pos,
            target=self._flee_target,
            bitmap=bitmap
        )
        if len(path) >= 2:
            self.delta = self.pos._get_delta(path[1])
            self._set_position(path[1])
            return

        # Llegada al destino: alternar salida <-> casilla cercana.
        if self._flee_target == self._flee_spawn:
            nearby: Coord | None = self._get_nearby_cell(
                self._flee_spawn, bitmap
            )
            if nearby is not None:
                self._flee_target = nearby
        else:
            self._flee_target = Coord(self._flee_spawn.get())






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
        fps: int = 60,
        directions: List[Dir] | None = None
    ) -> None:
        """
        """
        if not self.alive:
            self._update_respawn(dt)
            return
        # if self.alive == False:
        #     self._die()
        # mientras dura la super-pacgum: misma huida por cuartos que Pinky.
        if self.edible:
            self._move_superpacgum(target, dt, tile_size, bitmap)
            return
        self._timer_ms += dt
        if self._timer_ms >= self.speed:
            self._timer_ms -= self.speed
            curr_target: Coord = (
                target if self.edible == False else self.spawn_pos
            )
            if len(self.current_corridor) >= 2:
                self._follow_corridor()

            else:
                self._get_corridor(
                    self._find_path(
                        start=self.pos,
                        target=curr_target,
                        bitmap=bitmap
                    )
                )
                if len(self.current_corridor) >= 2:
                    self._follow_corridor()


class Pinky(Ghost):
    """
    Pinky (Rosa): Conocida como Speedy ("Rápida"), intenta emboscar a Pac-Man posicionándose por delante de él.
    """

    def __init__(self, points: int) -> None:
        super().__init__(name="Pinky", points=points)
        self.color.set(PINKY_COLOR)
        self.speed: int = PINKY_SPEED
        self.ani_path: str = PINKY_ANI_PATH


    def _move(
        self,
        target: Coord,
        dt: int,
        tile_size: int,
        bitmap: BitMap,
        fps: int = 60,
        directions: List[Dir] | None = None
    ) -> None:
        """Mueve a Pinky: respawn, huida con la super-pacgum o caza por BFS."""
        # sollo corre su reloj10 s.
        if not self.alive:
            self._update_respawn(dt)
            return

        # mientras dura la super-pacgum, huida por cuartos.
        if self.edible:
            self._move_superpacgum(target, dt, tile_size, bitmap)
            return

        # un paso de BFS cada `speed` ms hacia la casilla predicha.
        self._timer_ms += dt
        if self._timer_ms >= self.speed:
            self._timer_ms -= self.speed
            curr_target: Coord = self._predict_pinky_target(
                target, directions, bitmap
            )
            path: List[Coord] = self._find_path(
                start=self.pos,
                target=curr_target,
                bitmap=bitmap
            )
            if len(path) >= 2:
                self.delta = self.pos._get_delta(path[1])
                self._set_position(path[1])


    def _predict_pinky_target(
        self,
        target: Coord,
        directions: List[Dir] | None,
        bitmap: BitMap
    ) -> Coord:
        """Predice hasta cuatro casillas de la ruta prevista de Pac-Man."""
        # Copia: la prediccion no puede pisar la posicion real del jugador.
        predicted: Coord = Coord(target.get())

        # SI NO TENGO datos, voy a por ti
        if not directions:
            return predicted

        current_direction: Dir = directions[0]
        pending_direction: Dir | None = (
            directions[1] if len(directions) == 2 else None
        )

        for _ in range(4):
            walls: int = bitmap.grid[predicted.y][predicted.x]

            # Intenta la segunda tecla pendiente antes de seguir recto.
            if pending_direction is not None:
                if not walls & pending_direction.value:
                    current_direction = pending_direction
                    pending_direction = None

            # Si no puede avanzar en la dirección elegida, termina aquí.
            if walls & current_direction.value:
                break

            predicted.step(current_direction)

        return predicted


class Inky(Ghost):
    """
    Inky (Cian / Azul claro): Conocido como Bashful ("Tímido"), tiene un comportamiento impredecible que combina las posiciones de Blinky y Pac-Man.
    """

    def __init__(self, points: int) -> None:
        super().__init__(name="Inky", points=points)
        self.color.set(INKY_COLOR)
        self.speed: int = INKY_SPEED
        self.ani_path: str = INKY_ANI_PATH

    def _move(
        self,
        target: Coord,
        dt: int,
        tile_size: int,
        bitmap: BitMap,
        fps: int = 60,
        directions: List[Dir] | None = None
    ) -> None:
        """Mueve a Inky: respawn, huida con la super-pacgum o pinza con Blinky."""
        # sollo corre su reloj10 s.
        if not self.alive:
            self._update_respawn(dt)
            return

        # mientras dura la super-pacgum, huida por cuartos.
        if self.edible:
            self._move_superpacgum(target, dt, tile_size, bitmap)
            return

        # un paso de BFS cada `speed` ms hacia el punto de emboscada.
        self._timer_ms += dt
        if self._timer_ms >= self.speed:
            self._timer_ms -= self.speed
            curr_target: Coord = self._get_inky_target(target, directions, bitmap)
            path: List[Coord] = self._find_path(
                start=self.pos,
                target=curr_target,
                bitmap=bitmap
            )
            # el punto doblado puede caer en pared o fuera del mapa:
            # sin ruta posible, Inky caza directo como Blinky.
            if len(path) < 2:
                path = self._find_path(
                    start=self.pos,
                    target=target,
                    bitmap=bitmap
                )
            if len(path) >= 2:
                self.delta = self.pos._get_delta(path[1])
                self._set_position(path[1])

    def _find_blinky(self) -> Coord | None:
        """Localiza a Blinky en el mapa de entidades y copia su posicion.
        Mismo acceso entre iguales que usa resolve_tile con el jugador:
        Inky no mira dentro de App ni de Maze.
        """
        for entities in Entity.entity_map.values():
            for ent in entities:
                if isinstance(ent, Blinky):
                    return Coord(ent.pos.get())
        return None
    
    def _get_pacman_ahead(
        self,
        target: Coord,
        directions: List[Dir] | None,
        bitmap: BitMap
    ) -> Coord | None:
        """Avanza hasta dos casillas desde Pac-Man en su direccion actual,
        parando en pared. Devuelve None si no se conoce su direccion."""
        if not directions:
            return None
        # Copia: la prediccion no puede pisar la posicion real del jugador.
        pac_ahead: Coord = Coord(target.get())
        current_direction: Dir = directions[0]
        for _ in range(2):
            # Pared en esa direccion: el punto de mira se queda aqui.
            if bitmap.grid[pac_ahead.y][pac_ahead.x] & current_direction.value:
                break
            pac_ahead.step(current_direction)
        return pac_ahead
    
    def _get_inky_target(
        self,
        target: Coord,
        directions: List[Dir] | None,
        bitmap: BitMap
    ) -> Coord:
        """Calcula el punto de emboscada: el vector de Blinky a dos casillas
        por delante de Pac-Man, doblado desde Blinky (Inky clasico)."""
        blinky_pos: Coord | None = self._find_blinky()
        pac_ahead: Coord | None = self._get_pacman_ahead(
            target, directions, bitmap
        )

        # Sin socio o sin rumbo conocido, no hay pinza: caza directa.
        if blinky_pos is None or pac_ahead is None:
            return target

        # Vector de Blinky al punto de mira, doblado desde Blinky.
        vector: Coord = pac_ahead - blinky_pos
        return blinky_pos + vector + vector
    

class Clyde(Ghost):
    """
    Clyde (Naranja): Conocido como Pokey ("Lento"), persigue a Pac-Man cuando está lejos, pero se aleja a su rincón cuando se acerca demasiado.
    """

    def __init__(self, points: int) -> None:
        super().__init__(name="Clyde", points=points)
        self.color.set(CLYDE_COLOR)
        self.speed: int = CLYDE_SPEED
        self.ani_path: str = CLYDE_ANI_PATH

    def _move(
            self,
            target: Coord,
            dt: int,
            tile_size: int,
            bitmap: BitMap,
            fps: int = 60,
            directions: List[Dir] | None = None
        ) -> None:
        """
        """
        if not self.alive:
            self._update_respawn(dt)
            return

        # mientras dura la super-pacgum, huida por cuartos.
        if self.edible:
            self._move_superpacgum(target, dt, tile_size, bitmap)
            return
        
        self._timer_ms += dt
        if self._timer_ms >= self.speed:
            self._timer_ms -= self.speed

            path_to_target: List[Coord] = self._find_path(
                start=self.pos,
                target=target,
                bitmap=bitmap
            )
            curr_target: Coord = (
                self.spawn_pos if self.edible == True or
                len(path_to_target) < 8
                else target
            )
            if len(self.current_corridor) >= 2:
                self._follow_corridor()

            else:
                path_to_target = (
                    path_to_target if curr_target == target else
                    self._find_path(
                        start=self.pos,
                        target=curr_target,
                        bitmap=bitmap
                    )
                )
                self._get_corridor(path_to_target)
                if len(self.current_corridor) >= 2:
                    self._follow_corridor()


"""
def direct_chase(ghost: Ghost, target: Coord, bitmap: BitMap) -> None:

    if len(ghost.current_corridor) >= 2:
        ghost._follow_corridor()

    else:
        ghost._get_corridor(
            ghost._find_path(
                start=ghost.pos,
                target=target,
                bitmap=bitmap
            )
        )
        if len(ghost.current_corridor) >= 2:
            ghost._follow_corridor()
"""
