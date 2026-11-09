"""Define la entidad base compartida por el jugador, fantasmas y pacgums."""

from enum import Enum
from collections.abc import Callable
from typing import Dict, List, Optional, Tuple
from src.utils.utils import Coord, Color, Dir
from pygame import Surface, SRCALPHA
from src.maze.bitmap import BitMap
from src.utils.error import HitWallError
from src.utils.utils import make_interval_ticker
from src.utils.logger import logger
from pathlib import Path
import pygame


ANI_SPEED = 100


class State(Enum):
    """Estados de comportamiento que puede tener una entidad."""

    INIT = "init"
    NORMAL = "normal"
    HUNT = "hunt"
    FLEE = "flee"
    EATEN = "eaten"
    PAUSE = "pause"


class Entity:
    """Mantiene posición, aspecto y colisiones de una entidad del juego."""

    entity_map: Dict[Tuple[int, int], List["Entity"]] = {}

    def __init__(self) -> None:
        """Inicializa el estado, posición y animación de la entidad."""
        self.state: State = State.INIT
        self.pos: Coord = Coord()
        self.color: Color = Color(0, 0, 0, 0)
        self.delta: Dir = None
        self.alive: bool = True
        self.spawn_pos: Coord = Coord(self.pos.get())
        self._update_entity_map(True)

        # ***** ANIMATION *****
        self._frames: Dict[Dir, List[Surface]] = {}
        self._timer_frame: int = 0
        self._frame_index: int = 0
        self._cur_direction: Optional[Dir] = None
        self._cur_frame: Optional[Surface] = None
        self.timer: Optional[Callable[[float], int]] = None

    def set_movement_interval(self, interval: float) -> None:
        """Configura el reloj de movimiento de la entidad."""
        self.timer = make_interval_ticker(interval)

    def movement_ticks(self, dt: float) -> int:
        """Devuelve los pasos de movimiento acumulados durante `dt`."""
        if self.timer is None:
            return 0
        return self.timer(dt)

    def _load_frames(self, asset_path: str, tile_size: int) -> None:
        """Carga los frames a ``Surface`` y falla con contexto si faltan."""
        try:
            dir_path = Path(asset_path)
            for subfolder in dir_path.iterdir():
                if subfolder.is_dir():
                    frame_list_str = sorted(
                        f for f in subfolder.glob("*.png") if f.is_file()
                    )
                    frame_list_raw = [
                        pygame.image.load(f).convert_alpha()
                        for f in frame_list_str
                    ]
                    frame_list_sur = [
                        pygame.transform.scale(
                            frame, (tile_size, tile_size)
                        )
                        for frame in frame_list_raw
                    ]
                    sub_fol_name = subfolder.name.lower()
                    if "up" in sub_fol_name:
                        self._frames[Dir.UP] = frame_list_sur
                    elif "right" in sub_fol_name:
                        self._frames[Dir.RIGHT] = frame_list_sur
                    elif "down" in sub_fol_name:
                        self._frames[Dir.DOWN] = frame_list_sur
                    elif "left" in sub_fol_name:
                        self._frames[Dir.LEFT] = frame_list_sur
                    elif "death" in sub_fol_name:
                        self._frames[Dir.DEATH] = frame_list_sur
                    elif "scared" in sub_fol_name:
                        self._frames[Dir.SCARED] = frame_list_sur
        except (OSError, pygame.error) as error:
            logger.exception("Could not load entity frames from %s: %s",
                             asset_path, error)
            raise RuntimeError(
                f"Could not load entity frames from {asset_path}"
            ) from error

    def get_frame(self, dt: int) -> Surface:
        """Devuelve el fotograma de animación correspondiente a ``dt``."""
        if self.delta is None:
            self.delta = Dir.RIGHT

        frames = self._frames.get(self.delta)
        if not frames:
            frames = self._frames.get(Dir.RIGHT, [])
        if not frames:
            return self.sur

        if self._cur_direction != self.delta or self._cur_frame is None:
            self._cur_direction = self.delta
            self._frame_index = 0
            self._cur_frame = frames[self._frame_index]

        self._timer_frame += dt
        if self._timer_frame >= ANI_SPEED:
            self._timer_frame %= ANI_SPEED
            if self.delta == Dir.DEATH:
                self._frame_index = min(self._frame_index + 1, len(frames) - 1)
            else:
                self._frame_index = (self._frame_index + 1) % len(frames)
            self._cur_frame = frames[self._frame_index]

        return self._cur_frame

    def animation_finished(self) -> bool:
        """Indica si una animacion no circular ha llegado a su ultimo frame."""
        frames = self._frames.get(self.delta, [])
        return (
            self.delta == Dir.DEATH
            and bool(frames)
            and self._frame_index == len(frames) - 1
            and self._timer_frame >= ANI_SPEED
        )


    def _init_surface(self, tile_size: int) -> None:
        """Crea una superficie transparente del tamaño de una casilla."""
        self.sur: Surface = Surface((tile_size, tile_size), SRCALPHA)
        self.sur.fill((0, 0, 0, 0))

    def _move(self, bitmap: BitMap, dir: Dir) -> None:
        """Avanza una casilla si el mapa no bloquea la dirección."""
        if bitmap.grid[self.pos.y][self.pos.x] & dir.value:
            raise HitWallError

        else:
            self._update_entity_map(False)
            self.pos.step(dir)
            self.delta = dir
            self._update_entity_map(True)

    def _set_position(self, position: Coord) -> None:
        """Cambia la posición manteniendo actualizado el mapa de entidades."""
        self._update_entity_map(False)
        self.pos.set_at(position)
        self._update_entity_map(True)

    def _update_entity_map(self, add: bool) -> None:
        """Añade o elimina la entidad del índice de posiciones."""
        pos = self.pos.get()
        if pos not in Entity.entity_map:
            Entity.entity_map[pos] = []
        if add:
            Entity.entity_map[pos].append(self)
        elif not add and self in Entity.entity_map[pos]:
            Entity.entity_map[pos].remove(self)

    def kill(self, other: "Entity") -> None:
        """Marca otra entidad como eliminada y la devuelve a su salida."""
        other.alive = False
        other._set_position(other.spawn_pos)
