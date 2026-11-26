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
    _HINT_LETTER_SPACING = 8   # Extra spacing between hint characters.
    _HINT_TOP_GAP = 16         # Blank line above the hint.
    # Colors.
    _TEXT_COLOR = (255, 255, 255, 255)
    _KEYCAP_COLOR = (255, 255, 255, 255)    # Keycap background.
    _KEYCAP_TEXT_COLOR = (0, 0, 0, 255)     # Text on the keycap.
    # Keycap padding.
    _KEYCAP_PAD_X = 14
    _KEYCAP_PAD_Y = 8

    # Arrow glyphs drawn inside a keycap.
    _ARROW_W = 9
    _ARROW_H = 11
    _ARROW_HEAD_H = 6
    _ARROW_STEM_W = 3
    _ARROW_GAP = 6

    # Arrow sets: the four movement keys, and the vertical pair.
    _DIRECTIONS = ("UP", "DOWN", "LEFT", "RIGHT")
    _ARROWS_4 = ("LEFT", "UP", "DOWN", "RIGHT")
    _ARROWS_V = ("UP", "DOWN")

    _ENTRIES: list[tuple[str | tuple[str, ...], str]] = [
        (_ARROWS_4 + ("/ WASD",), "MOVE PAC-MAN"),
        ("SPACE", "PAUSE / CONFIRM"),
        (_ARROWS_V, "SELECT MENU OPTION"),
        ("K", "SUPER MODE: ON / OFF"),
        ("ESC", "SKIP LEVEL (SUPER MODE)"),
    ]

    def __init__(self) -> None:
        """Render all screen surfaces at once."""
        caps: list[Surface] = [
            self._render_key(spec) for spec, _ in self._ENTRIES
        ]
        texts: list[Surface] = [
            self._render_text(description, self._TEXT_SIZE, self._TEXT_COLOR)
            for _, description in self._ENTRIES
        ]
        cap_w: int = max(cap.get_width() for cap in caps)
        text_w: int = max(text.get_width() for text in texts)

        self.rows: list[tuple[Surface, Surface]] = [
            (self._pad(cap, cap_w, True), self._pad(text, text_w, False))
            for cap, text in zip(caps, texts)
        ]
        self.hint: Surface = self._pad_top(
            self._render_spaced_text(
                "PRESS SPACE TO GO TO MAIN MENU", self._HINT_SIZE,
                self._TEXT_COLOR, self._HINT_LETTER_SPACING
            ),
            self._HINT_TOP_GAP
        )

    @staticmethod
    def _pad(surface: Surface, width: int, right: bool) -> Surface:
        """Pad a surface to a common width with transparent pixels.

        Right-aligned padding keeps the keycaps sharing their right edge;
        left-aligned padding keeps the descriptions starting at the same x.
        """
        if surface.get_width() >= width:
            return surface
        slot: Surface = Surface(
            (width, surface.get_height()), pygame.SRCALPHA)
        slot.blit(surface, (width - surface.get_width() if right else 0, 0))
        return slot

    @staticmethod
    def _pad_top(surface: Surface, gap: int) -> Surface:
        """Add transparent padding above a surface.

        This adds height and moves the content down without changing the
        position assigned by the engine.
        """
        slot: Surface = Surface(
            (surface.get_width(), surface.get_height() + gap), pygame.SRCALPHA)
        slot.blit(surface, (0, gap))
        return slot

    def _render_key(self, spec: str | tuple[str, ...]) -> Surface:
        """Draw a keycap from a text label or from a set of parts."""
        if isinstance(spec, tuple):
            return self._render_parts_keycap(spec)
        return self._render_keycap(spec)

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

    def _render_spaced_text(
        self,
        text: str,
        size: int,
        color: tuple[int, int, int, int],
        spacing: int
    ) -> Surface:
        """Render text with extra spacing between characters.

        Render each character separately and place it after the previous
        character plus the spacing. The result is wider than regular text
        while keeping the same height.
        """
        glyphs: list[Surface] = [
            self._render_text(char, size, color) for char in text
        ]
        w: int = (
            sum(glyph.get_width() for glyph in glyphs)
            + spacing * (len(glyphs) - 1)
        )
        h: int = max(glyph.get_height() for glyph in glyphs)

        line: Surface = Surface((w, h), pygame.SRCALPHA)
        x: int = 0
        for glyph in glyphs:
            line.blit(glyph, (x, 0))
            x += glyph.get_width() + spacing
        return line

    def _render_keycap(self, label: str) -> Surface:
        """Draw a key as a keycap with its label centered."""
        text: Surface = self._render_text(
            label, self._KEYCAP_SIZE, self._KEYCAP_TEXT_COLOR
        )
        return self._keycap_from(text)

    def _keycap_from(self, content: Surface) -> Surface:
        """Wrap a content surface in a keycap with padding."""
        w: int = content.get_width() + self._KEYCAP_PAD_X * 2
        h: int = content.get_height() + self._KEYCAP_PAD_Y * 2

        cap: Surface = Surface((w, h))
        cap.fill(self._KEYCAP_COLOR)
        cap.blit(
            content,
            (
                (w - content.get_width()) // 2,
                (h - content.get_height()) // 2,
            ),
        )
        return cap

    def _render_parts_keycap(self, parts: tuple[str, ...]) -> Surface:
        """Draw a keycap holding arrows and text in a single row.

        Each part is either a direction, drawn as an arrow, or a label,
        rendered with the keycap font. Any number of parts is accepted, so
        the four movement keys, the vertical pair and the arrow-plus-WASD
        keycap share the same code path.
        """
        items: list[Surface] = [
            self._render_arrow(part) if part in self._DIRECTIONS
            else self._render_text(
                part, self._KEYCAP_SIZE, self._KEYCAP_TEXT_COLOR)
            for part in parts
        ]
        w: int = (
            sum(item.get_width() for item in items)
            + self._ARROW_GAP * (len(items) - 1)
        )
        h: int = max(item.get_height() for item in items)

        content: Surface = Surface((w, h), pygame.SRCALPHA)
        x: int = 0
        for item in items:
            content.blit(item, (x, (h - item.get_height()) // 2))
            x += item.get_width() + self._ARROW_GAP
        return self._keycap_from(content)

    def _render_arrow(self, direction: str) -> Surface:
        """Draw one arrow glyph inside a fixed-size box.

        Every direction is drawn in the same _ARROW_W x _ARROW_H box so the
        layout maths stay uniform; rotating a surface would swap its width
        and height.
        """
        w: int = self._ARROW_W
        h: int = self._ARROW_H
        head: int = self._ARROW_HEAD_H
        stem: int = self._ARROW_STEM_W
        color: tuple[int, int, int, int] = self._KEYCAP_TEXT_COLOR

        arrow: Surface = Surface((w, h), pygame.SRCALPHA)
        if direction in ("UP", "DOWN"):
            cx: int = w // 2
            up: bool = direction == "UP"
            tip: int = 0 if up else h - 1
            base: int = head - 1 if up else h - head
            pygame.draw.polygon(arrow, color, [
                (cx, tip), (0, base), (w - 1, base)
            ])
            pygame.draw.rect(arrow, color, (
                cx - stem // 2, base if up else 0, stem, h - head + 1
            ))
        else:
            cy: int = h // 2
            left: bool = direction == "LEFT"
            tip = 0 if left else w - 1
            base = head - 1 if left else w - head
            pygame.draw.polygon(arrow, color, [
                (tip, cy), (base, 0), (base, h - 1)
            ])
            pygame.draw.rect(arrow, color, (
                base if left else 0, cy - stem // 2, w - head + 1, stem
            ))
        return arrow
