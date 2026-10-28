from enum import Enum
from typing import Dict, List, Optional, Tuple
from src.utils.utils import Coord, Color, Dir
from pygame import Surface, SRCALPHA
from src.maze.bitmap import BitMap
from src.utils.error import HitWallError
from pathlib import Path
import pygame
import random


ANI_SPEED = 200


class State(Enum):
    """
    """
    INIT = "init"
    NORMAL = "normal"
    HUNT = "hunt"
    FLEE = "flee"
    EATEN = "eaten"
    PAUSE = "pause"


class Entity:
    """
    """
    entity_map: Dict[Tuple[int, int], List["Entity"]] = {}

    def __init__(self) -> None:
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

    def _load_frames(self, asset_path: str, tile_size: int) -> None:
        """
        Carga los frames a Surfaces
        """
        dir_path = Path(asset_path)
        for subfolder in dir_path.iterdir():
            if subfolder.is_dir():
                frame_list_str = sorted([f for f in subfolder.glob("*.png") if f.is_file()])
                frame_list_raw = [pygame.image.load(f).convert_alpha() for f in frame_list_str]
                frame_list_sur = [pygame.transform.scale(f, (tile_size, tile_size)) for f in frame_list_raw]
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

    def get_frame(self, dt: int) -> Surface:
        """
        Devuelve el frame que toque seegún el tiempo dt
        """
        if self.delta is None:
            self.delta = Dir.RIGHT

        frames = self._frames.get(self.delta)
        # proteger bien

        if self._cur_direction != self.delta or self._cur_frame is None:
            self._cur_direction = self.delta
            self._frame_index = 0
            self._cur_frame = frames[self._frame_index]

        self._timer_frame += dt
        if self._timer_frame >= ANI_SPEED:
            self._timer_frame %= ANI_SPEED
            self._frame_index = (self._frame_index + 1) % len(frames)
            self._cur_frame = frames[self._frame_index]

        return self._cur_frame


    def _init_surface(self, coord: Coord, tile_size: int) -> None:
        """
        """
        self.sur: Surface = Surface((tile_size, tile_size), SRCALPHA)
        self.sur.fill((0, 0, 0, 0))

    def _move(self, bitmap: BitMap, dir: Dir) -> None:
        """
        """
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
        """
        Actualiza el dict de posiciones de las entidades
        """
        pos = self.pos.get()
        if pos not in Entity.entity_map:
            Entity.entity_map[pos] = []
        if add:
            Entity.entity_map[pos].append(self)
        elif not add and self in Entity.entity_map[pos]:
            Entity.entity_map[pos].remove(self)

    def kill(self, other: "Entity") -> None:
        """
        Elimina a la otra entidad
        """
        other.alive = False
        other._set_position(other.spawn_pos)
