"""Create text surfaces for drawing in the interface."""

import pygame
from pygame import Surface
from typing import Tuple


_FONT_BODY_SIZE = 15
_FONT_COLOR = (255, 255, 255, 255)
_FONT_PATH = "assets/font/font_emulogic.ttf"


class Title:
    """
    Create text to display in the interface.
    """

    def __init__(
        self,
        text: str,
        size: int = _FONT_BODY_SIZE,
        color: Tuple[int, int, int, int] = _FONT_COLOR,
    ) -> None:
        """Render the specified text with the selected size and color."""
        self.sur: pygame.Surface = self._render(text, color, size)

    def _render(
        self,
        text: str,
        color: Tuple[int, int, int, int] = _FONT_COLOR,
        size: int = _FONT_BODY_SIZE,
    ) -> pygame.Surface:
        """Create and return the text surface."""
        if not pygame.font.get_init():
            pygame.font.init()
        font = pygame.font.Font(_FONT_PATH, size)
        return font.render(text, True, color)

    def blit_title(
        self,
        window: Surface,
        dest: Tuple[int, int]
    ) -> None:
        """Draw the text in the window at the specified position."""
        window.blit(self.sur, dest)
