"""Implement the game's menu elements and options."""

from src.utils.utils import Color
from typing import Tuple, List
from enum import Enum
import pygame
from pygame import Surface


_MENU_BACKGROUND = (3, 18, 15, 255)
_FONT = 'Arial'
_FONT_COLOR = (255, 255, 255, 255)
_FONT_BODY_SIZE = 10
FONT_MENU_INIT_SIZE = 20
SELECTOR_SIZE = 20


class ItemType(str, Enum):
    """Options available in the menus."""

    START = "START GAME"
    HIGHSCORES = "VIEW HIGHSCORES"
    INSTRUCTIONS = "INSTRUCTIONS"
    QUIT = "EXIT"
    RESUME = "RESUME"
    MAIN_MENU = "MAIN MENU"


class Item:
    """Represent a selectable menu option."""

    def __init__(self, item_type: ItemType) -> None:
        """Create an item associated with an option."""
        self._item_type: ItemType = item_type
        self.sur: Surface = Surface((1, 1))
        self.xy: Tuple[int, int] = (0, 0)

    def __hash__(self) -> int:
        """Return the hash of the item's option."""
        return hash(self._item_type)

    def _render_item(
            self,
            font_path: str | None = None,
            size_font: int | None = None,
    ) -> None:
        """Render the item's text with the selected font."""
        if not pygame.font.get_init():
            pygame.font.init()

        size: int = size_font if size_font is not None else _FONT_BODY_SIZE
        if font_path is None:
            font = pygame.font.SysFont(font_path, size)
        else:
            font = pygame.font.Font(font_path, size)
        self.sur = font.render(self._item_type, True, _FONT_COLOR)


class Menu:
    """Manage a menu's options and active selection."""

    selector: Surface | None = None

    def __init__(
        self,
        bg_color: Color | tuple[int, int, int, int] = _MENU_BACKGROUND
    ) -> None:
        """Initialize the menu and create the selector if needed."""
        self._bg_color: Color | tuple[int, int, int, int] = bg_color
        self._items: List[Item] = []
        self._active_item: Item | None = None
        if self.selector is None:
            self._render_selector()

    @classmethod
    def _render_selector(cls) -> None:
        """Render the indicator for the active option."""
        if not pygame.font.get_init():
            pygame.font.init()
        font = pygame.font.SysFont(_FONT, SELECTOR_SIZE)
        cls.selector = font.render(">", True, _FONT_COLOR)

    def _render_item_list(
        self,
        font_path: str | None = None,
        size_font: int | None = None
    ) -> None:
        """Render and store the surfaces for the menu items."""
        for item in self._items:
            item._render_item(font_path, size_font)

    def _select_item(self, next_item: bool) -> None:
        """Select the next or previous option, wrapping around."""
        if self._active_item is None:
            self._active_item = self._items[0]
        else:
            idx = self._items.index(self._active_item)
            idx = (idx + 1 if next_item else idx - 1) % len(self._items)
            self._active_item = self._items[idx]


class MenuInit(Menu):
    """Main menu for starting, viewing scores, instructions, or exiting."""

    def __init__(self) -> None:
        """Create and render the main menu options."""
        super().__init__()
        self._items.extend([
            Item(ItemType.START),
            Item(ItemType.HIGHSCORES),
            Item(ItemType.INSTRUCTIONS),
            Item(ItemType.QUIT)
        ])
        self._render_item_list(
            "assets/font/font_emulogic.ttf", FONT_MENU_INIT_SIZE)
        self._active_item = self._items[0]


class MenuPause(Menu):
    """Menu available while the game is paused."""

    def __init__(self) -> None:
        """Create and render the options to resume or exit."""
        super().__init__()
        self._items.extend([
            Item(ItemType.RESUME),
            Item(ItemType.MAIN_MENU)
        ])
        self._render_item_list("assets/font/font_emulogic.ttf", 16)
        self._active_item = self._items[0]
