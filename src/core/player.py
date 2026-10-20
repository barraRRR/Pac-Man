from enum import Enum
from src.utils.utils import Coord, Color
from src.core.entity import Entity
import pygame
from pygame import Surface


PLAYER_COLOR = (243, 195, 0, 255)


class Player(Entity):
    """
    """
    def __init__(self) -> None:
        super().__init__()
        self.color.set(PLAYER_COLOR)
        self.images: dict[str, Surface] = self._load_images()

    @staticmethod
    def _load_images() -> dict[str, Surface] :
        base = "assets/player/pac-man"
        images = {}

        for dir in ("down", "left", "right", "up", "death"):
            images[dir] = pygame.image.load(f"{base}_{dir}.gif")
        return images
