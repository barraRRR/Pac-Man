"""Implementa el movimiento, las colisiones y las vidas de Pac-Man."""

from src.utils.utils import Dir
from src.core.entity import Entity, State, ANI_SPEED
from src.core.ghost import Ghost
from src.core.pacgum import SuperPacGum
from src.score.highscore import Score
import pygame
from pygame import Surface
from pathlib import Path


PLAYER_COLOR = (243, 195, 0, 255)
PLAYER_ANI_PATH = "assets/animations/player"
PLAYER_DEATH_DURATION_MS = 16 * ANI_SPEED
PLAYER_MOVEMENT_INTERVAL = 220


class Player(Entity):
    """Representa al jugador y gestiona su puntuación y estado de muerte."""

    def __init__(self, lives: int, score: Score) -> None:
        """Crea Pac-Man con las vidas y el marcador de la partida."""
        super().__init__()
        self.color.set(PLAYER_COLOR)
        self.images: dict[str, list[Surface]] = self._load_images()
        self._score: Score = score
        self._lives: int = lives
        self._dying: bool = False

        self.ani_path: str = PLAYER_ANI_PATH
        self.set_movement_interval(PLAYER_MOVEMENT_INTERVAL)

        # ==== MODO TRUCO ====
        # Si es True, los fantasmas no pueden matar a Pac-Man (issue #124).
        self.invincible: bool = False

    @staticmethod
    def _load_images() -> dict[str, list[Surface]]:
        """Carga los frames PNG de cada animacion del jugador."""
        base = Path("assets/animations/player")
        images = {}

        for dir in ("down", "left", "right", "up", "death"):
            frames_dir = base / f"pac-man_{dir}"
            images[dir] = [
                pygame.image.load(str(frame_path))
                for frame_path in sorted(frames_dir.glob("frame_*.png"))
            ]
        return images

    def _die(self) -> None:
        """Inicia la muerte del jugador, salvo que sea invencible."""
        if self.invincible:
            return
        if self._dying:
            return
        self._lives -= 1
        self._dying = True
        self.alive = False
        self.delta = Dir.DEATH
        self._cur_direction = None
        self._cur_frame = None
        self._frame_index = 0
        self._timer_frame = 0

    def finish_death(self) -> None:
        """Termina la animacion y deja al jugador listo para continuar."""
        self._set_position(self.spawn_pos)
        self.alive = True
        self._dying = False
        self.delta = Dir.RIGHT
        self._cur_direction = None
        self._cur_frame = None
        self._frame_index = 0
        self._timer_frame = 0

    @property
    def dying(self) -> bool:
        """Indica si el jugador esta reproduciendo su animacion de muerte."""
        return self._dying

    def _eat(self, target: Entity) -> None:
        """Resuelve qué ocurre cuando Pac-Man toca otra entidad."""
        if isinstance(target, Ghost):
            if not target.alive:
                return
            if not target.edible:
                if self.invincible:
                    return
                self._die()
                return

        if target.alive:
            self.kill(target)
            self._score.add(target.points)
            if isinstance(target, SuperPacGum):
                self.state = State.HUNT
                Ghost.edible = True

    def resolve_tile(self) -> None:
        """Resuelve las colisiones con las entidades de la casilla."""
        for ent in list(Entity.entity_map.get(self.pos.get(), [])):
            if ent == self:
                continue
            self._eat(ent)

    @property
    def lives(self) -> int:
        """Devuelve las vidas actuales del jugador."""
        return self._lives

    def _reset_lives(self, lives: int) -> None:
        """Restaura las vidas al valor inicial de una partida nueva."""
        self._lives = lives
