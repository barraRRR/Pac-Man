from enum import Enum
from src.utils.utils import Coord, Color
from src.core.entity import Entity, State
from src.core.ghost import Ghost
from src.core.pacgum import PacGum, SuperPacGum
from src.score.score import Score
from src.utils.utils import Coord
import pygame
from pygame import Surface
from pathlib import Path
from enum import Enum
from pathlib import Path


PLAYER_COLOR = (243, 195, 0, 255)


class Player(Entity):
    """
    """
    def __init__(self, lives: int, score: Score) -> None:
        super().__init__()
        self.color.set(PLAYER_COLOR)
        self.images: dict[str, list[Surface]] = self._load_images()
        self._score: Score = score
        self._lives: int = lives

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
        self._lives -= 1
        self._set_position(self.spawn_pos)
        self.alive = True

    def _eat(self, target: Entity) -> None:
        """
        """
        if isinstance(target, Ghost) and not target.edible:
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
