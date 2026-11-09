"""Implementa los elementos y las opciones de los menús del juego."""

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
    """Opciones disponibles en los menús."""

    START = "START GAME"
    HIGHSCORES = "VIEW HIGHSCORES"
    INSTRUCTIONS = "INSTRUCTIONS"
    QUIT = "EXIT"
    RESUME = "RESUME"
    MAIN_MENU = "MAIN MENU"
    


class Item:
    """Representa una opción seleccionable del menú."""

    def __init__(self, item_type: ItemType) -> None:
        """Crea un elemento asociado a una opción."""
        self._item_type: ItemType = item_type
        self.sur: Surface | None = None
        self.xy: Tuple[int, int] = None

    def __hash__(self):
        """Devuelve el hash de la opción del elemento."""
        return hash(self._item_type)

    def _render_item(
            self,
            font_path: str | None = None,
            size_font: int | None = None,
            ) -> None:
        """Renderiza el texto del elemento con la fuente seleccionada."""
        if not pygame.font.get_init():
            pygame.font.init()

        size: int = size_font if size_font is not None else _FONT_BODY_SIZE
        if font_path is None:
            font = pygame.font.SysFont(font_path, size)
        else:
            font = pygame.font.Font(font_path, size)
        self.sur = font.render(self._item_type, True, _FONT_COLOR)


class Menu:
    """Mantiene las opciones y la selección activa de un menú."""

    selector: Surface = None

    def __init__(
            self,
            bg_color: Color = _MENU_BACKGROUND
        ) -> None:
        """Inicializa el menú y crea el selector si aún no existe."""
        self._bg_color: Color = bg_color
        self._items: List[Item] = []
        self._active_item: Item | None = None
        if self.selector is None:
            self._render_selector()

    @classmethod
    def _render_selector(cls) -> None:
        """Renderiza el indicador de la opción activa."""
        if not pygame.font.get_init():
            pygame.font.init()
        font = pygame.font.SysFont(_FONT, SELECTOR_SIZE)
        cls.selector = font.render(">", True, _FONT_COLOR)

    def _render_item_list(
        self,
        font_path: str | None = None,
        size_font: int | None = None
        ) -> None:
        """Renderiza y guarda las superficies de sus elementos."""
        for item in self._items:
            item._render_item(font_path, size_font)

    def _select_item(self, next_item: bool) -> None:
        """Selecciona la opción siguiente o anterior de forma circular."""
        if self._active_item is None:
            self._active_item = self._items[0]
        else:
            idx = self._items.index(self._active_item)
            idx = (idx + 1 if next_item else idx - 1) % len(self._items)
            self._active_item = self._items[idx]


class MenuInit(Menu):
    """Menú principal con inicio, récords, instrucciones y salida."""

    def __init__(self) -> None:
        """Crea y renderiza las opciones del menú principal."""
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
    """Menú disponible mientras la partida está pausada."""

    def __init__(self) -> None:
        """Crea y renderiza las opciones para reanudar o salir."""
        super().__init__()
        self._items.extend([
            Item(ItemType.RESUME),
            Item(ItemType.MAIN_MENU)
        ])
        self._render_item_list("assets/font/font_emulogic.ttf", 16)
        self._active_item = self._items[0]
