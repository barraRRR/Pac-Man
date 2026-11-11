"""Render the help screen and available controls."""

from pygame import Surface
import pygame


class Instructions:
    """Store the contents of the instructions screen.
    """
    # Project font and text sizes.
    _FONT_PATH = "assets/font/font_emulogic.ttf"
    _TEXT_SIZE = 12            # Instruction text.
    _KEYCAP_SIZE = 10          # Text inside the keycap.
    _HINT_SIZE = 10            # Bottom navigation hint.
    # Colors.
    _TEXT_COLOR = (255, 255, 255, 255)
    _KEYCAP_COLOR = (255, 255, 255, 255)    # Keycap background.
    _KEYCAP_TEXT_COLOR = (0, 0, 0, 255)     # Text on the keycap.
    # Keycap padding.
    _KEYCAP_PAD_X = 14
    _KEYCAP_PAD_Y = 8

    _ENTRIES = {
        "ARROWS / WASD": "MOVE PAC-MAN",
        "SPACE": "PAUSE / CONFIRM",
        "UP / DOWN": "SELECT MENU OPTION",
    }

    def __init__(self) -> None:
        """Render all screen surfaces at once."""
        self.rows: list[tuple[Surface, Surface]] = []
        for keys, description in self._ENTRIES.items():
            self.rows.append((
                self._render_keycap(keys),
                self._render_text(
                    description, self._TEXT_SIZE, self._TEXT_COLOR),
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
        """Render text with the project font."""
        if not pygame.font.get_init():
            pygame.font.init()
        font = pygame.font.Font(self._FONT_PATH, size)
        return font.render(text, True, color)

    def _render_keycap(self, label: str) -> Surface:
        """Draw a key as a keycap with its label centered.

        Calculate the width from the text and padding so the space bar is
        wider than a regular key.
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
