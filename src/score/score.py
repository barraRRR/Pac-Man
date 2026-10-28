import pygame


_FONT_BODY_SIZE = 15
_FONT_COLOR = (255, 255, 255, 255)
_FONT_PATH = "assets/font/font_emulogic.ttf"


class Title:
    """
    Crea textos para mostrar en la interfaz
    """
    def __init__(self, text: str, size: int = _FONT_BODY_SIZE) -> None:
        self.sur: pygame.Surface = self._render(text, size)

    def _render(self, text: str, size: int = _FONT_BODY_SIZE) -> pygame.Surface:
        if not pygame.font.get_init():
            pygame.font.init()
        font = pygame.font.Font(_FONT_PATH, size)        # Proteger
        return font.render(text, True, _FONT_COLOR)


class Score(Title):
    """
    Registra el score de la partida en curso
    """
    def __init__(self) -> None:
        self._points: int = 0
        super().__init__(text=str(self._points))

    def add(self, points) -> None:
        self._points += points
        self.sur = self._render(text=str(self._points))

    @property
    def points(self) -> int:
        return self._points

    def reset(self) -> None:
        """Vuelve el marcador a cero y refresca lo que se pinta en el HUD."""
        self._points = 0
        self.sur = self._render(text=str(self._points))
