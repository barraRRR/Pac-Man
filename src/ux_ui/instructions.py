"""Renderiza la pantalla de ayuda y los controles disponibles."""

from pygame import Surface
import pygame


class Instructions:
    """Guarda el contenido de la pantalla de instrucciones.
    """
    # Fuente del proyecto y tamaños
    _FONT_PATH = "assets/font/font_emulogic.ttf"
    _TEXT_SIZE = 12            # texto de las funciones
    _KEYCAP_SIZE = 10          # texto dentro de la placa
    _HINT_SIZE = 10            # pista de salida de abajo
    # Colores:
    _TEXT_COLOR = (255, 255, 255, 255)
    _KEYCAP_COLOR = (255, 255, 255, 255)    # placa de la tecla
    _KEYCAP_TEXT_COLOR = (0, 0, 0, 255)     # texto sobre la placa
    # Margen
    _KEYCAP_PAD_X = 14                      # margen horizontal dentro de la placa
    _KEYCAP_PAD_Y = 8                       # margen vertical dentro de la placa
    
    _ENTRIES = {
        "ARROWS / WASD": "MOVE PAC-MAN",
        "SPACE": "PAUSE / CONFIRM",
        "UP / DOWN": "SELECT MENU OPTION",
    }

    def __init__(self) -> None:
        """Renderiza de una vez todas las superficies de la pantalla."""
        self.rows: list[tuple[Surface, Surface]] = []
        for keys, description in self._ENTRIES.items():
            self.rows.append((
                self._render_keycap(keys),
                self._render_text(description, self._TEXT_SIZE, self._TEXT_COLOR),
            ))
        self.hint: Surface = self._render_text(
            "PRESS SPACE TO GO TO MAIN MENU", self._HINT_SIZE, self._TEXT_COLOR
        )

    def _render_text(
            self,
            text: str,
            size: int,
            color: tuple[int, int, int, int]
        ) -> Surface:
        """Renderiza un texto con la fuente del proyecto."""
        if not pygame.font.get_init():
            pygame.font.init()
        font = pygame.font.Font(self._FONT_PATH, size)
        return font.render(text, True, color)

    def _render_keycap(self, label: str) -> Surface:
        """Dibuja una tecla como placa con su nombre centrado.

        La anchura sale del texto mas los margenes, asi la barra
        espaciadora queda mas ancha que una tecla normal a mano.
        """
        text: Surface = self._render_text(
            label, self._KEYCAP_SIZE, self._KEYCAP_TEXT_COLOR
        )
        w: int = text.get_width() + self._KEYCAP_PAD_X * 2
        h: int = text.get_height() + self._KEYCAP_PAD_Y * 2

        cap: Surface = Surface((w, h))
        cap.fill(self._KEYCAP_COLOR)
        cap.blit(text, ((w - text.get_width()) // 2,
                        (h - text.get_height()) // 2))
        return cap
