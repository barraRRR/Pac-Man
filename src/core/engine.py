"""Prepara la ventana y dibuja los elementos de la interfaz del juego."""

import pygame
from pygame import Surface
from typing import Tuple, List, Dict, Callable
from src.maze.bitmap import BitMap
from src.core.player import Player
from src.core.ghost import Ghost
from src.core.pacgum import PacGum, SuperPacGum
from src.score.highscore import Score
from src.utils.title import Title
from src.utils.utils import Coord, Color, Logo, Dir
from src.utils.class_maze import Maze
from src.ux_ui.menu import Menu, MenuInit, MenuPause
from src.ux_ui.instructions import Instructions

_WINDOW_WIDTH = 600
_WINDOW_HEIGHT = 800
_PADDING = 30
_LINE = 2
_SAFE_LINE = 1

_LOGO_AREA = (510, 130)
_FOOTER_AREA = 60

_ITEM_LINE_SPACING = 60

_MIN_TILE_SIZE = 10
_STD_TILE_SIZE = 20
_MAX_TILE_SIZE = 45

_BACKGROUND_COLOR = (3, 18, 15, 255)
_WALL_COLOR = (5, 4, 170, 255)
_HEADER_AREA = 220
_HUD_TITLE_GAP = 48
_HUD_SCORE_GAP = 28

_INTRO_TEXT_COLOR = (255, 255, 255, 255)
_INTRO_TITLE_SIZE = 24
_INTRO_SUB_SIZE = 10
_INTRO_PAD = 20
_INTRO_GAP = 30

_INSTR_FIRST_ROW_Y = 350
_INSTR_ROW_SPACING = 70
_INSTR_PAIR_GAP = 30
_INSTR_HINT_Y = 700

_PAGE_TITLE_GAP = 70

_TARGET_TILE_SIZE = 25
_WINDOW_MARGIN = 1.10
_MAX_WINDOW = (1600, 950)
_SCREEN_MARGIN = 0.90


class GraphicEngine:
    """Calcula dimensiones y renderiza los elementos visuales del juego."""

    def __init__(
            self,
            player: Player,
            ghosts: Dict[str, Ghost],
            pacgum: List[PacGum],
            score: Score) -> None:
        """Guarda las entidades y prepara el estado gráfico inicial."""
        self.player: Player = player
        self.ghosts: Dict[str, Ghost] = ghosts
        self.pacgum: List[PacGum] = pacgum
        self.maze: Maze | None = None

        self.maze_size: Tuple[int, int] = (0, 0)
        self.tile_size: int = 0
        self.line: int = 0
        self.maze_px: Tuple[int, int] = (0, 0)
        self.win_px: Tuple[int, int] = (_WINDOW_WIDTH, _WINDOW_HEIGHT)

        self.logo: Logo = Logo()
        self.background: Surface = Surface((1, 1))
        self.window: Surface = Surface((1, 1))
        self.menu_init: MenuInit = MenuInit()
        self.menu_pause: MenuPause = MenuPause()
        self.instructions: Instructions = Instructions()
        self.band: Surface | None = None
        self.credits: Title | None = None

        self.instructions_title: Title = Title("INSTRUCTIONS")
        self.page_highscores_title: Title | None = None
        self.time_title: Title = Title("00:00", size=14)
        self._time_text: str = "00:00"

        self.up_title: Title = Title("1UP")
        self.highscore_title: Title = Title("HIGH SCORE")
        self.highscore_int: Title = Title("0000")
        self.score: Score = score

    def _update_maze(self, new_maze: Maze) -> None:
        """Actualiza el laberinto y recalcula sus dimensiones en pantalla."""
        self.maze = new_maze
        self._calculate_dynamic_tile_size()
        self._calculate_line_px()
        self._calculate_maze_size_px()

    def _calculate_dynamic_tile_size(self) -> None:
        """Calcula el tamaño de casilla que mejor se ajusta a la ventana."""
        if self.maze is None:
            raise RuntimeError("The maze has not been initialized.")
        maze = self.maze
        safe_w: int = self.win_px[0] - (_PADDING * 2)
        safe_h: int = self.win_px[1] - _HEADER_AREA - _FOOTER_AREA - _PADDING

        ideal_tile_w: int = safe_w // maze.col
        ideal_tile_h: int = safe_h // maze.row

        ideal_tile_size: int = min(ideal_tile_w, ideal_tile_h)
        self.tile_size = max(
            _MIN_TILE_SIZE, min(ideal_tile_size, _MAX_TILE_SIZE)
        )

    def _calculate_line_px(self) -> None:
        """Ajusta el grosor de los muros al tamaño de las casillas."""
        self.line = _LINE if self.tile_size >= _STD_TILE_SIZE else _SAFE_LINE

    def _calculate_maze_size_px(self) -> None:
        """Calcula el ancho y alto en píxeles del laberinto."""
        if self.maze is None:
            raise RuntimeError("The maze has not been initialized.")
        self.maze_px = (
            (self.maze.col * self.tile_size),
            (self.maze.row * self.tile_size)
        )

    @staticmethod
    def _get_screen_limit() -> Tuple[int, int]:
        """
        Devuelve el tamaño máximo de ventana que admite la pantalla.

        Lee la resolución del monitor, le aplica _SCREEN_MARGIN y la limita
        con _MAX_WINDOW. Si no se puede leer, usa solo _MAX_WINDOW.
        """
        try:
            info = pygame.display.Info()
        except pygame.error:
            return _MAX_WINDOW
        if info.current_w <= 0 or info.current_h <= 0:
            return _MAX_WINDOW
        return (
            min(_MAX_WINDOW[0], int(info.current_w * _SCREEN_MARGIN)),
            min(_MAX_WINDOW[1], int(info.current_h * _SCREEN_MARGIN)),
        )

    @staticmethod
    def _calculate_window_size(
        levels: List[Tuple[int, int]]
    ) -> Tuple[int, int]:
        """
        Calcula el tamaño de ventana a partir del mapa más grande.

        Busca el ancho y el alto máximos entre todos los niveles, calcula el
        espacio necesario con un tamaño de casilla objetivo, le suma un margen
        en porcentaje y lo acota entre el tamaño base y el tope máximo.
        """
        max_cols: int = max(cols for cols, _ in levels)
        max_rows: int = max(rows for _, rows in levels)

        need_w: int = max_cols * _TARGET_TILE_SIZE + _PADDING * 2
        need_h: int = (
            max_rows * _TARGET_TILE_SIZE
            + _HEADER_AREA + _FOOTER_AREA + _PADDING
        )

        limit_w, limit_h = GraphicEngine._get_screen_limit()

        width: int = int(need_w * _WINDOW_MARGIN)
        height: int = int(need_h * _WINDOW_MARGIN)

        return (
            min(max(_WINDOW_WIDTH, width), limit_w),
            min(max(_WINDOW_HEIGHT, height), limit_h),
        )

    @staticmethod
    def _px_with_padding(
        win_px: Coord,
        maze_px: Coord,
        x_px: int,
        y_px: int
    ) -> Coord:
        """Convert pixel coordinates with padding offset.

        Args:
            x_px: X pixel coordinate.
            y_px: Y pixel coordinate.

        Returns:
            Adjusted (x, y) coordinates.
        """
        extra_x = (win_px.x - maze_px.x) // 2
        return Coord((x_px + extra_x, y_px + _PADDING))

    @staticmethod
    def _put_pixel(
        surface: Surface,
        coord: Coord | Tuple[int, int],
        color: Color | Tuple[int, int, int, int]
    ) -> None:
        """Pinta un píxel usando coordenadas y color en formato compatible."""
        xy = coord.get() if isinstance(coord, Coord) else coord
        rgba = color.get() if isinstance(color, Color) else color

        surface.set_at(xy, rgba)

    def _render_cell(
        self,
        surface: Surface,
        coord: Coord,
        value: int,
        color: Color | Tuple[int, int, int, int]
    ) -> None:
        """Dibuja los muros de una casilla del laberinto."""
        x = coord.x * self.tile_size
        y = coord.y * self.tile_size

        walls: Dict[Dir, Callable[[int, int], Tuple[int, int]]] = {
            Dir.UP: lambda i, t: (x + i, y + t),
            Dir.RIGHT: lambda i, t: (x + self.tile_size - 1 - t, y + i),
            Dir.DOWN: lambda i, t: (x + i, y + self.tile_size - 1 - t),
            Dir.LEFT: lambda i, t: (x + t, y + i),
        }

        if value == 15:
            for i in range(self.tile_size):
                for t in range(self.tile_size):
                    self._put_pixel(surface, (x + t, y + i), color)
        else:
            for dir, get_coords in walls.items():
                if value & dir.value:
                    for i in range(self.tile_size):
                        for t in range(self.line):
                            self._put_pixel(surface, get_coords(i, t), color)

    """
    ╔═════════════════════════════════════════════════════════════════════════╗
    ║                                 ENTITIES                                ║
    ╚═════════════════════════════════════════════════════════════════════════╝
    """

    def _render_pacgum(
        self,
        pacgum: PacGum,
    ) -> None:
        """Dibuja la pacgum como un círculo centrado en su casilla."""
        size = 3 if isinstance(pacgum, SuperPacGum) else 8
        radius = max(1, self.tile_size // size // 2)
        center = self.tile_size // 2

        for y in range(-radius, radius + 1):
            for x in range(-radius, radius + 1):
                if x * x + y * y <= radius * radius:
                    self._put_pixel(
                        pacgum.sur,
                        (center + x, center + y),
                        pacgum.color
                    )

    def _init_entities(self) -> None:
        """Carga los fotogramas y prepara las superficies de las entidades."""
        self.player._load_frames(self.player.ani_path, self.tile_size)
        for ghost in self.ghosts.values():
            ghost._load_frames(ghost.ani_path, self.tile_size)
        for pacgum in self.pacgum:
            pacgum._init_surface(self.tile_size)

    def _put_entities(self) -> None:
        """Prepara y dibuja las pacgums del nivel."""
        self._init_entities()
        for pacgum in self.pacgum:
            self._render_pacgum(pacgum)

    """
    ╔═════════════════════════════════════════════════════════════════════════╗
    ║                               INTERFACE                                 ║
    ╚═════════════════════════════════════════════════════════════════════════╝
    """

    def _init_window(self) -> None:
        """Crea la ventana y la superficie de fondo."""
        self.window = pygame.display.set_mode(self.win_px)
        pygame.display.set_caption("Pac-Man")
        self.background = Surface(self.win_px)

    def _put_background(self) -> None:
        """Rellena la superficie de fondo con el color de la interfaz."""
        self.background.fill(_BACKGROUND_COLOR)

    def _put_logo(self) -> None:
        """Carga y dibuja el logotipo centrado en la parte superior."""
        logo = self.logo._load_logo()
        scaled_logo: Surface = pygame.transform.smoothscale(
            logo, _LOGO_AREA)
        logo_pos: Tuple[int, int] = (
            (self.win_px[0] - _LOGO_AREA[0]) // 2,
            _PADDING
        )
        self.window.blit(scaled_logo, logo_pos)

    """
    ╔═════════════════════════════════════════════════════════════════════════╗
    ║                                 MENU                                    ║
    ╚═════════════════════════════════════════════════════════════════════════╝
    """

    def _init_menu_init(self) -> None:
        """Prepara las superficies de texto del menú principal."""
        self.menu_init._render_item_list()

    def _window_center(self) -> Tuple[int, int]:
        """Centro de la ventana actual, no el de la constante de 600x800."""
        return (self.win_px[0] // 2, self.win_px[1] // 2)

    def _blit_menu_init(self, menu: Menu) -> None:
        """Dibuja el menú principal y el logotipo en la ventana."""
        if self.credits is None:
            self.credits = Title("Created by aitorres and jbarreir © 2026", 8)
        credits = self.credits
        self.window.blit(self.background, (0, 0))
        for i, item in enumerate(menu._items):
            x, y = (self.win_px[0] // 2, 330)
            y += (i * _ITEM_LINE_SPACING)
            x -= item.sur.get_width() // 2
            item.xy = (x, y)
            self.window.blit(item.sur, (x, y))
            if item == menu._active_item and menu.selector is not None:
                self.window.blit(menu.selector, (x - 12, y))
        self._put_logo()
        self.window.blit(
            credits.sur,
            ((self.win_px[0] - credits.sur.get_width()) // 2,
             self.win_px[1] - _PADDING - credits.sur.get_height())
        )

    def _blit_menu_pause(self, menu: MenuPause) -> None:
        """Muestra las opciones de pausa sobre la escena congelada."""
        for i, item in enumerate(menu._items):
            x, y = self._window_center()
            y += i * _ITEM_LINE_SPACING
            x -= item.sur.get_width() // 2
            item.xy = (x, y)
        pad: int = 20
        text_w: int = max(item.sur.get_width() for item in menu._items)
        text_h: int = menu._items[0].sur.get_height()
        panel_size: Tuple[int, int] = (
            text_w + pad * 2,
            _ITEM_LINE_SPACING + text_h + pad * 2
        )
        panel: Surface = Surface(panel_size)
        panel.fill(_BACKGROUND_COLOR)
        panel_x: int = (self.win_px[0] - panel_size[0]) // 2
        panel_y: int = menu._items[0].xy[1] - pad
        self.window.blit(panel, (panel_x, panel_y))
        for item in menu._items:
            self.window.blit(item.sur, item.xy)
            if item == menu._active_item and menu.selector is not None:
                self.window.blit(menu.selector, (item.xy[0] - 10, item.xy[1]))

    def _get_band_size(self, total_h: int) -> Tuple[int, int]:
        """Calcula el tamaño y la posición vertical de una banda."""
        band_h: int = (_INTRO_PAD + total_h + _INTRO_GAP + _INTRO_PAD)
        band_y: int = (self.win_px[1] - band_h) // 2
        return (band_h, band_y)

    def _get_title_x(self, title: Title) -> int:
        """Devuelve la coordenada horizontal para centrar un título."""
        return (self.win_px[0] - title.sur.get_width()) // 2

    def _blit_panel(
            self,
            band_h: int,
            band_y: int
    ) -> None:
        """Dibuja una banda opaca centrada verticalmente."""
        if (
            self.band is None
            or self.band.get_size() != (self.win_px[0], band_h)
        ):
            self.band = Surface((self.win_px[0], band_h))
        band = self.band
        band.fill(_BACKGROUND_COLOR)
        self.window.blit(band, (0, band_y))

    def _blit_level_info(
            self,
            title_str: str,
            sub_str: str,
            hint_str: str | None = None,
            title_size: int = _INTRO_TITLE_SIZE,
            sub_size: int = _INTRO_SUB_SIZE,
            hint_size: int = _INTRO_SUB_SIZE,
    ) -> None:
        """Dibuja el título, subtítulo y pista opcional en una banda."""
        title: Title = Title(
            text=title_str, size=title_size, color=_INTRO_TEXT_COLOR)
        sub: Title = Title(text=sub_str, size=sub_size,
                           color=_INTRO_TEXT_COLOR)
        hint = None
        if hint_str:
            hint = Title(text=hint_str, size=hint_size,
                         color=_INTRO_TEXT_COLOR)
        hint_h = hint.sur.get_height() + _INTRO_GAP if hint else 0

        band_h, band_y = self._get_band_size(
            title.sur.get_height() + sub.sur.get_height() + hint_h)
        self._blit_panel(
            band_h=band_h,
            band_y=band_y
        )
        self.window.blit(
            title.sur, (self._get_title_x(title), band_y + _INTRO_PAD))
        self.window.blit(sub.sur, (self._get_title_x(
            sub), band_y + _INTRO_PAD + title.sur.get_height() + _INTRO_GAP))
        if hint:
            hint_y = (
                band_y
                + _INTRO_PAD
                + title.sur.get_height()
                + _INTRO_GAP
                + sub.sur.get_height()
                + _INTRO_GAP
            )
            self.window.blit(hint.sur, (self._get_title_x(hint), hint_y))

    def _blit_instructions(self) -> None:
        """Pega la pantalla de instrucciones renderizada por su objeto."""
        self._put_logo()

        title_x: int = (
            self.win_px[0] - self.instructions_title.sur.get_width()) // 2
        title_y: int = _PADDING + _LOGO_AREA[1] + _PAGE_TITLE_GAP
        self.window.blit(self.instructions_title.sur, (title_x, title_y))

        for index, (cap, text) in enumerate(self.instructions.rows):
            pair_w: int = cap.get_width() + _INSTR_PAIR_GAP + text.get_width()
            x: int = (self.win_px[0] - pair_w) // 2
            y: int = _INSTR_FIRST_ROW_Y + index * _INSTR_ROW_SPACING
            self.window.blit(cap, (x, y))
            self.window.blit(
                text,
                (x + cap.get_width() + _INSTR_PAIR_GAP,
                 y + (cap.get_height() - text.get_height()) // 2)
            )

        hint: Surface = self.instructions.hint
        self.window.blit(hint, ((self.win_px[0] - hint.get_width()) // 2,
                                _INSTR_HINT_Y))

    def _blit_highscores_title(self) -> None:
        """Dibuja el logo y el título de la pantalla de puntuaciones."""
        self._put_logo()

        if self.page_highscores_title is None:
            self.page_highscores_title = Title("HIGH SCORES")
        page_title = self.page_highscores_title

        title_x: int = (
            self.win_px[0] - page_title.sur.get_width()) // 2
        title_y: int = _PADDING + _LOGO_AREA[1] + _PAGE_TITLE_GAP
        page_title.blit_title(self.window, (title_x, title_y))

    def _blit_highscores_rows(
        self,
        scores: List[Dict[str, str | int]]
    ) -> None:
        """Dibuja los nombres y puntuaciones del ranking."""
        first_row_y: int = 300
        row_spaccing: int = 35
        center_x: int = self.win_px[0] // 2
        left_x: int = center_x - 230
        right_x: int = center_x + 230

        for index, record in enumerate(scores, start=1):
            name: Title = Title(f"{index}. {record['name']}")
            score: Title = Title(str(record["score"]))
            y: int = first_row_y + (index - 1) * row_spaccing

            self.window.blit(name.sur, (left_x, y))
            score_x: int = right_x - score.sur.get_width()
            self.window.blit(score.sur, (score_x, y))

        hint: Surface = self.instructions.hint
        self.window.blit(
            hint,
            ((self.win_px[0] - hint.get_width()) // 2, _INSTR_HINT_Y)
        )

    def _render_maze(
        self,
        maze_surface: Surface,
        bitmap: BitMap,
        color: Color | Tuple[int, int, int, int]
    ) -> None:
        """Dibuja la cuadrícula en la superficie del laberinto."""
        for y, row in enumerate(bitmap.grid):
            for x, cell_value in enumerate(row):
                self._render_cell(
                    maze_surface, Coord((x, y)), cell_value, color
                )

    def _cal_left_padding(
        self,
        element_width: int,
        align: str = "center",
    ) -> int:
        """Calcula la posición horizontal de un elemento alineado."""
        free: int = self.win_px[0] - element_width

        if align == "left":
            return _PADDING
        elif align == "right":
            return free - _PADDING
        return free // 2

    def _cal_maze_top(self) -> int:
        """Calcula el inicio vertical del mapa debajo del encabezado."""
        free: int = self.win_px[1] - self.maze_px[1]
        return max(_HEADER_AREA, free // 2)

    def _cal_maze_offset(self) -> Tuple[int, int]:
        """Devuelve el desplazamiento del laberinto dentro de la ventana."""
        return (self._cal_left_padding(self.maze_px[0]), self._cal_maze_top())

    def _put_maze(
            self,
            new_maze: Maze,
            color: Color | Tuple[int, int, int, int] = _WALL_COLOR
    ) -> None:
        """Actualiza el laberinto y prepara su superficie de dibujo."""
        self._update_maze(new_maze)
        maze = self.maze
        if maze is None:
            raise RuntimeError("The maze has not been initialized.")
        maze.sur = Surface(self.maze_px, pygame.SRCALPHA)
        maze.sur.fill((0, 0, 0, 0))
        self._render_maze(maze.sur, maze._bitmap, color)

    def _blit_elements(self, dt: int, level: int = 1) -> None:
        """Dibuja el laberinto, las entidades, el HUD y las vidas."""
        maze = self.maze
        if maze is None or maze.sur is None:
            raise RuntimeError("The maze has not been rendered.")
        self.window.blit(self.background, (0, 0))
        self._put_logo()
        self.window.blit(maze.sur, (self._cal_maze_offset()))
        left: int = self._cal_left_padding(self.maze_px[0])
        top: int = self._cal_maze_top()

        right: int = left + self.maze_px[0]
        center_x: int = left + self.maze_px[0] // 2

        hud_y: int = top - _HUD_TITLE_GAP
        hud_score_y: int = top - _HUD_SCORE_GAP

        self.window.blit(self.up_title.sur, (left, hud_y))
        self.window.blit(self.score.sur, (left, hud_score_y))
        self.window.blit(
            self.highscore_title.sur,
            (center_x - self.highscore_title.sur.get_width() // 2, hud_y)
        )
        self.window.blit(
            self.highscore_int.sur,
            (center_x - self.highscore_int.sur.get_width() // 2, hud_score_y)
        )

        for pacgum in self.pacgum:
            if pacgum.alive:
                self.window.blit(
                    pacgum.sur,
                    pacgum.pos.off_get(self.tile_size, top, left))
        for ghost in self.ghosts.values():
            if ghost.alive:
                self.window.blit(ghost.get_frame(
                    dt), ghost.pos.off_get(self.tile_size, top, left))
        self.window.blit(self.player.get_frame(
            dt), self.player.pos.off_get(self.tile_size, top, left))

        frames = self.player.images.get("right", [])
        lives = self.player.lives

        if frames and lives > 0:
            icon_size = 16
            gap = 4
            total_width = lives * icon_size + (lives - 1) * gap
            start_x = right - _PADDING - total_width
            icon = pygame.transform.scale(frames[0], (icon_size, icon_size))

            for index in range(lives):
                self.window.blit(
                    icon,
                    (start_x + index * (icon_size + gap), hud_score_y)
                )

        time_x = (
            left
            + self.maze_px[0]
            - self.time_title.sur.get_width()
        )
        time_y = top + self.maze_px[1] + 12
        self.window.blit(self.time_title.sur, (time_x, time_y))

        level_preview: Title = Title(f"LEVEL {level}", size=14)
        self.window.blit(
            level_preview.sur,
            (left, time_y)
        )

    def _set_highscore(self, points: int) -> None:
        """Pinta en el HUD el HIGH SCORE que le entrega App.

        App es quien conoce el ranking (Engine nunca importa HighScore);
        aqui solo se regenera la superficie del texto con el nuevo valor.
        """
        self.highscore_int = Title(str(points).zfill(4))

    def _set_time(self, seconds: int) -> None:
        """Pinta en el HUD el tiempo restante que le entrega App.

        App cuenta los segundos; aqui solo se convierten a MM:SS y se
        regenera la superficie cuando el valor cambia.
        """
        minutes = seconds // 60
        rest = seconds % 60
        text = f"{minutes:02d}:{rest:02d}"

        if text != self._time_text:
            self._time_text = text
            self.time_title = Title(text, size=14)
