from src.utils.utils import Color
from typing import Tuple, List
from enum import Enum
import pygame
from pygame import Surface


_MENU_BACKGROUND = (3, 18, 15, 255)
_FONT = "Arial"
_FONT_COLOR = (255, 255, 255, 255)
_FONT_BODY_SIZE = 10


class ItemType(Enum):
    """
    """
    START = "START"
    QUIT = "QUIT"


class Item:
    """
    Items del menu
    """
    def __init__(self, item_type: ItemType) -> None:
        self._item_type: ItemType = item_type
        self.sur: Surface | None = None

    def _render_item(self) -> None:
        """
        """
        font = pygame.font.SysFont(_FONT, _FONT_BODY_SIZE)
        self.sur = font.render(self._item_type.__str__(), True, _FONT_COLOR)


class Menu:
    """
    """
    def __init__(
            self,
            ui_size: Tuple[int, int],
            bg_color: Color = _MENU_BACKGROUND
        ) -> None:
        self._ui_size: Tuple[int, int] = ui_size
        self._bg_color: Color = bg_color
        self._items: List[Item] = []
        self._active_item: Item | None = None

    def _render_item_list(self) -> None:
        """
        Crea las superficies de los items del menú y las almacena
        """
        for item in self._items:
            item._render_item()

    def _select_item(self, next_item: bool) -> None:
        """
        controla el item seleccionado. proteger con try-except
        """
        if self._active_item is None:
            self._active_item = self._items[0]
        else:
            idx = self._items.index(self._active_item)
            idx = (idx + 1 if next_item else -1) % len(self._items)
            self._active_item = self._items[idx]


class MenuInit(Menu):
    """
    """
    def __init__(self) -> None:
        super().__init__()
        self._items.append(
            Item.START,
            Item.QUIT
        )
