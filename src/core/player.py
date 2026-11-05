from enum import Enum
from src.utils.utils import Coord, Color, Dir
from src.core.entity import Entity, State, ANI_SPEED
from src.core.ghost import Ghost
from src.core.pacgum import PacGum, SuperPacGum
from src.score.highscore import Score
from src.utils.utils import Coord
import pygame
from pygame import Surface
from pathlib import Path
from enum import Enum
from pathlib import Path


PLAYER_COLOR = (243, 195, 0, 255)
PLAYER_ANI_PATH = "assets/animations/player"
PLAYER_DEATH_DURATION_MS = 16 * ANI_SPEED


class Player(Entity):
    """
    """
    def __init__(self, lives: int, score: Score) -> None:
        super().__init__()
        self.color.set(PLAYER_COLOR)
        self.images: dict[str, list[Surface]] = self._load_images()
        self._score: Score = score
        self._lives: int = lives
        self._dying: bool = False

        self.ani_path: str = PLAYER_ANI_PATH

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
        """
        El jugador alcanza o es aclanzado por un Ghost not edible
        """
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
        """
        Come pacgum, Fantasmas, superPacgum, de todo.
        """
        if isinstance(target, Ghost):
            if not target.alive:
                return
            if not target.edible:
                if self.inivincible:
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
        """
        Interactua con el resto de Entity de la casilla
        """
        for ent in list(Entity.entity_map.get(self.pos.get(), [])):
            if ent == self:
                continue
            self._eat(ent)

    @property
    def lives(self) -> int:
        """Devuelve las vidas actuales del jugador."""
        return self._lives

    def _reset_lives(self, lives:int) -> None:
        """Restaura las vidas al valor inicial de una partida nueva."""
        self._lives = lives
