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
    """
    """
    START = "START GAME"
    HIGHSCORES = "VIEW HIGHSCORES"
    INSTRUCTIONS = "INSTRUCTIONS"
    QUIT = "EXIT"
    RESUME = "RESUME"
    MAIN_MENU = "MAIN MENU"
    


class Item:
    """
    Items del menu
    """
    def __init__(self, item_type: ItemType) -> None:
        self._item_type: ItemType = item_type
        self.sur: Surface | None = None
        self.xy: Tuple[int, int] = None

    def __hash__(self):
        return hash(self._item_type)

    def _render_item(
            self,
            font_path: str | None = None,
            size_font: int | None = None,
            ) -> None:
        """
        """
        if not pygame.font.get_init():
            pygame.font.init()

        size: int = size_font if size_font is not None else _FONT_BODY_SIZE
        if font_path is None:
            font = pygame.font.SysFont(font_path, size)
        else:
            font = pygame.font.Font(font_path, size)
        self.sur = font.render(self._item_type, True, _FONT_COLOR)


class Menu:
    """
    """
    selector: Surface = None

    def __init__(
            self,
            bg_color: Color = _MENU_BACKGROUND
        ) -> None:
        self._bg_color: Color = bg_color
        self._items: List[Item] = []
        self._active_item: Item | None = None
        if self.selector is None:
            self._render_selector()

    @classmethod
    def _render_selector(cls) -> None:
        """
        """
        if not pygame.font.get_init():
            pygame.font.init()
        font = pygame.font.SysFont(_FONT, SELECTOR_SIZE)
        cls.selector = font.render(">", True, _FONT_COLOR)

    def _render_item_list(
        self,
        font_path: str | None = None,
        size_font: int | None = None
        ) -> None:
        """
        Crea las superficies de los items del menú y las almacena
        """
        for item in self._items:
            item._render_item(font_path, size_font)

    def _select_item(self, next_item: bool) -> None:
        """
        controla el item seleccionado. proteger con try-except
        """
        if self._active_item is None:
            self._active_item = self._items[0]
        else:
            idx = self._items.index(self._active_item)
            idx = (idx + 1 if next_item else idx - 1) % len(self._items)
            self._active_item = self._items[idx]


class MenuInit(Menu):
    """
    """
    def __init__(self) -> None:
        super().__init__()
        self._items.extend([
            Item(ItemType.START),
            Item(ItemType.HIGHSCORES),
            Item(ItemType.INSTRUCTIONS),
            Item(ItemType.QUIT)
        ])
        self._render_item_list("assets/font/font_emulogic.ttf", FONT_MENU_INIT_SIZE)
        self._active_item = self._items[0]


class MenuPause(Menu):
    """
    """
    def __init__(self) -> None:
        super().__init__()
        self._items.extend([
            Item(ItemType.RESUME),
            Item(ItemType.MAIN_MENU)
        ])
        self._render_item_list("assets/font/font_emulogic.ttf", 16)
        self._active_item = self._items[0]
