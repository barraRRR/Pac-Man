import pygame


_FONT, _FONT_BODY_SIZE = "Arial", 30
_FONT_COLOR = (255, 255, 255, 255)


class Score:
    """
    Registra el score de la partida en curso
    """
    def __init__(self) -> None:
        self._points: int = 0
        self.sur: pygame.Surface = self._render()

    def add(self, points) -> None:
        self._points += points
        self.sur = self._render()

    @property
    def points(self) -> int:
        return self._points

    def _render(self) -> pygame.Surface:
        if not pygame.font.get_init():
            pygame.font.init()
        font = pygame.font.SysFont(_FONT, _FONT_BODY_SIZE)
        return font.render(str(self._points), True, _FONT_COLOR)