from enum import Enum
from src.utils.utils import Coord, Color
from src.core.entity import Entity
from src.core.ghost import Ghost
from src.core.pacgum import PacGum
from src.score.score import Score
from src.utils.utils import Coord
import pygame
from pygame import Surface


PLAYER_COLOR = (243, 195, 0, 255)


class Player(Entity):
    """
    """
    def __init__(self, lives: int, score: Score) -> None:
        super().__init__()
        self.color.set(PLAYER_COLOR)
        self.images: dict[str, Surface] = self._load_images()
        self._score: Score = score
        self._lives: int = lives

    @staticmethod
    def _load_images() -> dict[str, Surface] :
        base = "assets/player/pac-man"
        images = {}

        for dir in ("down", "left", "right", "up", "death"):
            images[dir] = pygame.image.load(f"{base}_{dir}.gif")
        return images

    def _die(self) -> None:
        """
        El jugador alcanza o es aclanzado por un Ghost not edible
        """
        self._lives -= 1
        self.pos = self.spawn_pos

    def _eat(self, target: Entity) -> None:
        """
        """
        if isinstance(target, Ghost) and not target.edible:
            self._die()
            return

        if target.alive:
            self.kill(target)
            self._score.add(target.points)

    def resolve_tile(self) -> None:
        """
        Interactua con el resto de Entity de la casilla
        """
        for ent in list(Entity.entity_map.get(self.pos.get(), [])):
            if ent == self:
                continue
            self._eat(ent)

