import pygame
from pygame import Surface
from typing import Tuple


_FONT_BODY_SIZE = 15
_FONT_COLOR = (255, 255, 255, 255)
_FONT_PATH = "assets/font/font_emulogic.ttf"


class Title:
    """
    Crea textos para mostrar en la interfaz
    """
    def __init__(self, text: str, size: int = _FONT_BODY_SIZE, color: Tuple[int, int, int, int] = _FONT_COLOR) -> None:
        self.sur: pygame.Surface = self._render(text, color, size)

    def _render(self, text: str, color: Tuple[int, int, int, int] = _FONT_COLOR, size: int = _FONT_BODY_SIZE) -> pygame.Surface:
        if not pygame.font.get_init():
            pygame.font.init()
        font = pygame.font.Font(_FONT_PATH, size)        # Proteger
        return font.render(text, True, color)

    def blit_title(
            self,
            window: Surface,
            dest: Tuple[int, int]
        ) -> None:
        window.blit(self.sur, dest)

