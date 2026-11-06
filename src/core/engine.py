import pygame
from pygame import Surface
from typing import Tuple, List, Dict
from src.maze.bitmap import BitMap
from src.core.entity import Entity
from src.core.player import Player
from src.core.ghost import Ghost, Blinky, Pinky, Inky, Clyde
from src.core.pacgum import PacGum, SuperPacGum
from src.score.highscore import Score, PlayerName
from src.utils.title import Title
from src.utils.utils import Coord, Color, Logo, Dir
from src.utils.class_maze import Maze
from src.ux_ui.menu import Menu, MenuInit, MenuPause
from src.ux_ui.instructions import Instructions

"""

Estas son las funciones que podemos utilizar con el equivalente de MLX

Función MinilibX (MLX)	    Equivalente estricto en Pygame	    Propósito en el motor gráfico
|--------------------------|-----------------------------------|----------------------------------------------------|
mlx_init()	                pygame.init()	                    Inicializa los módulos internos del entorno gráfico.
mlx_new_window()	        pygame.display.set_mode((w, h))	    Crea la ventana principal donde se renderizará el juego.
mlx_new_image()	            pygame.Surface((w, h))	            Crea un lienzo en memoria para dibujar antes de volcar a pantalla.
mlx_xpm_file_to_image()	    pygame.image.load(ruta)	            Carga una textura o sprite desde un archivo local a la memoria.
mlx_pixel_put()	            Surface.set_at((x, y), color)	    Cambia el color de un único píxel específico.
mlx_put_image_to_window()	Display.blit(image, (x, y))	        Vuelca una imagen o buffer en unas coordenadas concretas de la pantalla.
mlx_hook() / mlx_key_hook()	pygame.event.get()	                Captura eventos crudos del sistema (teclas, ratón, cierre de ventana).
mlx_loop()	                while loop: + pygame.display.flip()	Mantiene el programa en ejecución y actualiza los fotogramas.
mlx_destroy_window()	    pygame.display.quit()	            Destruye el contexto gráfico y cierra la ventana de forma segura.

"""

_WINDOW_WIDTH = 600
_WINDOW_HEIGHT = 800
_WINDOW_CENTER = ((_WINDOW_WIDTH // 2), (_WINDOW_HEIGHT // 2))

_PADDING = 30
_LINE = 2
_SAFE_LINE = 1

_LOGO_AREA = (510, 130)
_SCORE_AREA = (600, 100)
_FOOTER_AREA = 100

_ITEM_LINE_SPACING = 60

_MIN_TILE_SIZE = 10
_STD_TILE_SIZE = 20
_MAX_TILE_SIZE = 45

_BACKGROUND_COLOR = (3, 18, 15, 255)
_WALL_COLOR = (5, 4, 170, 255)
_TEST_COLOR = (0, 0, 0, 255)

_LOGO_POS = (45, 20)
_1UP_POS = (100, 160)
_HIGHSCORE = (210, 160)
_1UP_SCORE_POS = (140, 180)
_HIGHSCORE_SCORE_POS = (280, 180)
_FOOTER_POS = (40, 740)

_HEADER_AREA = 220

# ==== INTRO DE NIVEL ====
_INTRO_FONT_PATH = "assets/font/font_emulogic.ttf"
_INTRO_TEXT_COLOR = (255, 255, 255, 255)
_INTRO_TITLE_SIZE = 24   # Tamaño del título "LEVEL X"
_INTRO_SUB_SIZE = 10     # Tamaño del "Push SPACE to play"
_INTRO_PAD = 20          # Margen interior de la banda
_INTRO_GAP = 30          # Hueco entre título y subtítulo

# ==== INSTRUCCIONES ====
_INSTR_FIRST_ROW_Y = 290               # primera fila, debajo del logo
_INSTR_ROW_SPACING = 70                # hueco entre filas
_INSTR_PAIR_GAP = 30                   # hueco entre placa y texto
_INSTR_HINT_Y = 700                    # pista de salida, zona del pie

_TITLE_SIZE = 24


class GraphicEngine():
    """
    """
    def __init__(
            self,
            player: Player,
            ghosts: Dict[str, Ghost],
            pacgum: List[PacGum],
            score: Score) -> None:

        # ***** ENTITIES *****
        self.player: Player = player
        self.ghosts: Dict[Ghost] = ghosts
        self.pacgum: List[PacGum] = pacgum
        self.maze: Maze | None = None

        # ***** PARAMETERS *****
        # size = (col, row) / px = pixeles (x, y) / se invierten
        self.maze_size: Tuple[int, int] = None
        self.tile_size: int = None
        self.line: int = None
        self.maze_px: Tuple[int, int] = None
        self.win_px: Tuple[int, int] = (_WINDOW_WIDTH, _WINDOW_HEIGHT)

        # ***** UX-UI *****
        self.logo: Logo = Logo()
        self.background: Surface = None
        self.window: Surface = None
        self.menu_init: MenuInit = MenuInit()
        self.menu_pause: MenuPause = MenuPause()
        self.instructions: Instructions = Instructions()
        self.band: Surface = None

        # ***** TÍTULOS *****
        self.instructions_title: Title = Title("INSTRUCTIONS", _TITLE_SIZE)
        self.page_highscores_title: Title = Title("HIGH SCORES", _TITLE_SIZE)
        self.time_title: Title = Title("00:00", size=14)
        self._time_text: str = "00:00"

        # ***** SCORE *****
        self.up_title: Title = Title("1UP")
        self.highscore_title: Title = Title("HIGH SCORE")
        self.highscore_int: Title = Title("0000")
        self.score: Score = score

    """
    ╔═════════════════════════════════════════════════════════════════════════╗
    ║                         DYNAMIC CALTULATIONS                            ║
    ╚═════════════════════════════════════════════════════════════════════════╝
    """

    def _update_maze(self, new_maze: Maze) -> None:
        """
        Fija el tamaño del mapa
        """
        self.maze = new_maze
        self._calculate_dynamic_tile_size()
        self._calculate_line_px()
        self._calculate_maze_size_px()
        # self._calculate_window_size_px()

    def _calculate_dynamic_tile_size(self) -> int:
        """Calculate optimal tile size based on window and maze dimensions.

        Returns:
            Tile size in pixels (10-45 range).
        """
        # Esto son operaciones para que el tamaño de las celdas se ajuste
        # al tamaño de la pantalla
        safe_w: int = _WINDOW_WIDTH - (_PADDING * 2)
        safe_h: int = _WINDOW_HEIGHT - _HEADER_AREA - _FOOTER_AREA - _PADDING

        ideal_tile_w: int = safe_w // self.maze.col
        ideal_tile_h: int = safe_h // self.maze.row

        ideal_tile_size: int = min(ideal_tile_w, ideal_tile_h)
        self.tile_size = max(
            _MIN_TILE_SIZE, min(ideal_tile_size, _MAX_TILE_SIZE)
        )

    def _calculate_line_px(self) -> int:
        """
        Establecemos el grosor de la línea según el tamaño de la celda
        """
        self.line = _LINE if self.tile_size >= _STD_TILE_SIZE else _SAFE_LINE

    def _calculate_maze_size_px(self) -> Tuple[int, int]:
        """
        calculamos el tamaño que va a tener cada celda (tile)
        según los tamaños máximos y mínimos de pantalla que configuremos
        calculamos en una tupla el tamaño que debe tener el maze
        (suma de todas las celdas) | ancho x alto
        """
        self.maze_px = (
            (self.maze.col * self.tile_size),
            (self.maze.row * self.tile_size)
        )

    """
    @staticmethod
    def _calculate_window_size_px(maze_px: Coord) -> Tuple[int, int]:
        
        calculamos el tamaño que debe tener la ventana del programa,
        de primeras será lo que ocupe el maze + margen (padding) | ancho x alto
        
        return(
            max(_MIN_SCREEN_W,
                (maze_px.x + (_PADDING * 2)))),(maze_px.y + (_PADDING * 2)
        )
    """

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

    """
    ╔═════════════════════════════════════════════════════════════════════════╗
    ║                              PIXEl RENDER                               ║
    ╚═════════════════════════════════════════════════════════════════════════╝
    """

    @staticmethod
    def _put_pixel(
            surface: Surface,
            coord: Coord | Tuple[int, int],
            color: Color | Tuple[int, int, int, int]
        ) -> None:
        """
        coloca el pixel en la superficie. buscar excepcion si la coord
        cae fuera de la ventana.
        """
        xy = coord.get() if isinstance(coord, Coord) else coord
        rgba = color.get() if isinstance(color, Color) else color

        surface.set_at(xy, rgba)

    def _render_cell(
            self,
            surface: Surface,
            coord: Coord,
            value: int,
            color: Color
        ) -> None:
        """
        Draw a tile at the specified grid coordinates.

        Renders a square tile of size tile_size×tile_size pixels at the given
        grid position. Each pixel in the tile is set to the specified color.
        Colors are automatically extended with alpha channel if needed.

        Args:
            coord: X coordinates in the grid
            value: Tile Value in the maze grid
            color: Color value in hexadecimal format (RGB or ARGB)
        """
        x = coord.x * self.tile_size
        y = coord.y * self.tile_size

        walls = {
            Dir.UP: lambda i, t: (x + i, y + t),
            Dir.RIGHT: lambda i, t: (x + self.tile_size - 1 - t, y + i),
            Dir.DOWN: lambda i, t: (x + i, y + self.tile_size - 1 - t),
            Dir.LEFT: lambda i, t: (x + t, y + i),
        }

        # CLOSED
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

    def _render_entity_block(
            self,
            entity: Entity,
            px: int = 0
        ) -> None:
        """
        """
        for i in range(self.tile_size - px):
            for t in range(self.tile_size - px):
                self._put_pixel(entity.sur, (i + px, t + px), entity.color)

    def _render_pacgum(
            self,
            pacgum: PacGum,
        ) -> None:
        """
        """
        size = 2 if isinstance(pacgum, SuperPacGum) else 5
        pg_size = self.tile_size // size
        offset = (self.tile_size - pg_size) // 2
        for i in range(pg_size):
            for t in range(pg_size):
                self._put_pixel(
                    pacgum.sur, (i + offset, t + offset), pacgum.color
                )

    def _init_entities(self) -> None:
        """
        Inicializa las entities en las posiciones iniciales del mapa
        """
        self.player._load_frames(self.player.ani_path, self.tile_size)
        for ghost in self.ghosts.values():
            ghost._load_frames(ghost.ani_path, self.tile_size)
        for pacgum in self.pacgum:
            pacgum._init_surface(pacgum.pos, self.tile_size)

    def _put_entities(self) -> None:
        """
        Dibuja las entities en el mapa
        """
        self._init_entities()
        """
        self._render_entity_block(self.player)
        
        for ghost in self.ghosts.values():
            self._render_entity_block(ghost)
        """
        for pacgum in self.pacgum:
            self._render_pacgum(pacgum)
        
        # map(self._render_entity_block, self.ghosts.values())
        # map(self._render_pacgum, self.pacgum)


    """
    ╔═════════════════════════════════════════════════════════════════════════╗
    ║                               INTERFACE                                 ║
    ╚═════════════════════════════════════════════════════════════════════════╝
    """

    def _init_window(self) -> None:
        """
        Imprime la ventana entera en pantalla
        """
        self.window = pygame.display.set_mode(self.win_px)
        self.background = Surface(self.win_px)

    def _put_background(self) -> None:
        """
        pone el fondo de pantalla sobre la pantalla
        """
        self.background.fill(_BACKGROUND_COLOR)

    def _put_logo(self) -> None:
        """
        """
        self.logo._load_logo()
        scaled_logo: Surface = pygame.transform.smoothscale(self.logo.img, _LOGO_AREA)
        logo_pos: Tuple[int, int] = (
            (_WINDOW_WIDTH - _LOGO_AREA[0]) // 2,
            _PADDING
        )
        self.window.blit(scaled_logo, logo_pos)
    
    
    """
    ╔═════════════════════════════════════════════════════════════════════════╗
    ║                                 MENU                                    ║
    ╚═════════════════════════════════════════════════════════════════════════╝
    """

    def _init_menu_init(self) -> None:
        """
        Crea el menu de inicio
        """
        self.menu_init._render_item_list()


    def _blit_menu_init(self, menu: Menu) -> None:
        """
        Muestra el menú de inicio en pantalla
        """
        self.window.blit(self.background, (0, 0))
        for i, item in enumerate(menu._items):
            x, y = _WINDOW_CENTER
            y += (i * _ITEM_LINE_SPACING)
            x -= item.sur.get_width() // 2
            item.xy = (x, y)
            self.window.blit(item.sur, (x, y))
            if item == menu._active_item:
                self.window.blit(menu.selector, (x - 10, y))
        self._put_logo()
                
    def _blit_menu_pause(self, menu: MenuPause) -> None:
        """Muestra las opciones de pausa sobre la escena congelada."""
        for i, item in enumerate(menu._items):
            x, y = _WINDOW_CENTER
            y += i * _ITEM_LINE_SPACING
            x -= item.sur.get_width() // 2
            item.xy = (x, y)
        #tirita (los ajsutes pro al ia 100%)
        pad : int = 20
        text_w: int = max(item.sur.get_width() for item in menu._items)
        text_h: int = menu._items[0].sur.get_height()
        panel_size: Tuple[int, int] = (
            text_w + pad * 2,
            _ITEM_LINE_SPACING + text_h + pad * 2
        )
        panel: Surface = Surface(panel_size)
        panel.fill(_BACKGROUND_COLOR)
        panel_x: int = (_WINDOW_WIDTH - panel_size[0]) // 2
        panel_y: int = menu._items[0].xy[1] - pad
        self.window.blit(panel, (panel_x, panel_y))
        # self.window.blit(item.sur, (x, y))
        # if item == menu._active_item:
        #     self.window.blit(menu.selector, (x - 10, y))

        # las opciones encima de la tira
        for item in menu._items:
            self.window.blit(item.sur, item.xy)
            if item == menu._active_item:
                self.window.blit(menu.selector, (item.xy[0] - 10, item.xy[1]))

    @staticmethod
    def _get_band_size(total_h: int) -> Tuple[int, int]:
        band_h: int = (_INTRO_PAD + total_h + _INTRO_GAP + _INTRO_PAD)
        band_y: int = (_WINDOW_HEIGHT - band_h) // 2
        return (band_h, band_y)

    @staticmethod
    def _get_title_x(title: Title) -> int:
        return (_WINDOW_WIDTH - title.sur.get_width()) // 2

    def _blit_cropped_bg(
            self,
            band_h: int,
            band_y: int
            ) -> None:
        if self.band is None:
            self.band: Surface = Surface((_WINDOW_WIDTH, band_h))
        self.band.fill(_BACKGROUND_COLOR)
        self.window.blit(self.band, (0, band_y))
    
    def _blit_level_info(self, title_str: str, sub_str: str) -> None:
        """Dibuja la banda de inicio de nivel a todo el ancho de la ventana.

        Muestra "LEVEL <n>" en grande y "Push SPACE to play" en letra
        pequeña, sobre una banda opaca que ocupa el ancho completo,
        igual que la tira del menú de pausa pero extendida.

        HE JUNTADO VARIAS FUNCIONES EN UNA - REFACTOR
        """
        title: Title = Title(text=title_str, size=_INTRO_TITLE_SIZE, color=_INTRO_TEXT_COLOR)
        sub: Title = Title(text=sub_str, size=_INTRO_SUB_SIZE, color=_INTRO_TEXT_COLOR)

        # banda a todo el ancho, alto = margen + titulo + hueco + subtitulo + margen
        band_h, band_y = self._get_band_size(title.sur.get_height() + sub.sur.get_height())
        self._blit_cropped_bg(
            band_h=band_h,
            band_y=band_y
        )
        # textos centrados, como en los menus: se resta media superficie
        self.window.blit(title.sur, (self._get_title_x(title), band_y + _INTRO_PAD))
        self.window.blit(sub.sur, (self._get_title_x(sub), band_y + _INTRO_PAD + title.sur.get_height() + _INTRO_GAP))

    def _blit_instructions(self) -> None:
        """Pega la pantalla de instrucciones renderizada por su objeto."""
        self._put_logo()

        # ===TITULO===
        title_x: int = (_WINDOW_WIDTH - self.instructions_title.sur.get_width()) // 2
        self.window.blit(self.instructions_title.sur, (title_x, 200))

        # ===CONTENIDO===
        for index, (cap, text) in enumerate(self.instructions.rows):
            pair_w: int = cap.get_width() + _INSTR_PAIR_GAP + text.get_width()
            x: int = (_WINDOW_WIDTH - pair_w) // 2
            y: int = _INSTR_FIRST_ROW_Y + index * _INSTR_ROW_SPACING
            self.window.blit(cap, (x, y))
            self.window.blit(
                text,
                (x + cap.get_width() + _INSTR_PAIR_GAP,
                 y + (cap.get_height() - text.get_height()) // 2)
            )

        # pista de salida, como el "Push SPACE to play" de la intro
        hint: Surface = self.instructions.hint
        self.window.blit(hint, ((_WINDOW_WIDTH - hint.get_width()) // 2,
                                _INSTR_HINT_Y))

    def _blit_highscores_title(self) -> None:
        """Dibuja el logo y el título de la pantalla de puntuaciones."""
        self._put_logo()

        title_x: int = (_WINDOW_WIDTH - self.page_highscores_title.sur.get_width()) // 2
        title_y: int = 200
        self.window.blit(self.page_highscores_title.sur, (title_x, title_y))

    def _blit_highscores_rows(
        self,
        scores: List[Dict[str, str | int]]
    ) -> None:
        """
        """
        first_row_y: int = 300
        row_spaccing: int = 35
        left_x:int = 70
        right_x: int = 530

        for index, record in enumerate(scores, start = 1):
            name: Title = Title(f"{index}. {record['name']}")
            score: Title = Title(str(record["score"]))
            y: int = first_row_y + (index - 1) * row_spaccing

            self.window.blit(name.sur, (left_x, y))
            score_x: int = right_x - score.sur.get_width()
            self.window.blit(score.sur, (score_x, y))
            pass

        # ---- exit--
        hint: Surface = self.instructions.hint
        self.window.blit(
            hint,
            ((_WINDOW_WIDTH - hint.get_width()) // 2, _INSTR_HINT_Y)
        )


    """
    ╔═════════════════════════════════════════════════════════════════════════╗
    ║                                  MAZE                                   ║
    ╚═════════════════════════════════════════════════════════════════════════╝
    """

    def _render_maze(
            self,
            maze_surface: Surface,
            bitmap: BitMap,
            color: Color
        ) -> None:
        """
        Render a maze grid to the screen.

        Iterates through the maze 2D array and renders each cell as a tile.
        Cells with value > 0 are drawn in white, others in background color.
        Does not automatically flush the image; call flush_image() to display.

        Args:
            maze: 2D list where each element is an int representing a cell.
        """
        for y, row in enumerate(bitmap.grid):
            for x, cell_value in enumerate(row):
                self._render_cell(
                    maze_surface, Coord((x, y)), cell_value, color
                )

    def _cal_left_padding(self) -> int:
        """
        """
        return (_WINDOW_WIDTH - self.maze_px[0]) // 2

    def _cal_maze_offset(
            self,
            h: int = _HEADER_AREA
        ) -> Tuple[int, int]:
        """
        """
        return (self._cal_left_padding(), h)
    
    def _put_maze(
            self,
            new_maze: Maze,
            color: Color | Tuple[int, int, int, int] = _WALL_COLOR
        ) -> None:
        """
        Imprime la ventana entera en pantalla
        """
        self._update_maze(new_maze)
        self.maze.sur = Surface(self.maze_px, pygame.SRCALPHA)
        self.maze.sur.fill((0, 0, 0, 0)) 
        self._render_maze(self.maze.sur, self.maze._bitmap, color)


    """
    ╔═════════════════════════════════════════════════════════════════════════╗
    ║                             RENDER_GHOSTS                               ║
    ╚═════════════════════════════════════════════════════════════════════════╝
    """





    """
    ╔═════════════════════════════════════════════════════════════════════════╗
    ║                             RENDER_PLAYER                               ║
    ╚═════════════════════════════════════════════════════════════════════════╝
    """




    """
    ╔═════════════════════════════════════════════════════════════════════════╗
    ║                           RENDER_FULL_FRAME                             ║
    ╚═════════════════════════════════════════════════════════════════════════╝
    """



    def _blit_elements(self, dt: int, level: int = 1) -> None:
        """
        """
        self.window.blit(self.background, (0, 0))
        self._put_logo()
        self.window.blit(self.maze.sur, (self._cal_maze_offset()))
        self.window.blit(self.score.sur, _1UP_SCORE_POS)
        self.window.blit(self.up_title.sur, _1UP_POS)
        self.window.blit(self.highscore_title.sur, _HIGHSCORE)
        self.window.blit(self.highscore_int.sur, _HIGHSCORE_SCORE_POS)
        for pacgum in self.pacgum:
            if pacgum.alive:
                self.window.blit(
                    pacgum.sur,
                    pacgum.pos.off_get(self.tile_size, _HEADER_AREA, self._cal_left_padding()))
        for ghost in self.ghosts.values():
            if ghost.alive:
                self.window.blit(ghost.get_frame(dt), ghost.pos.off_get(self.tile_size, _HEADER_AREA, self._cal_left_padding()))
        self.window.blit(self.player.get_frame(dt), self.player.pos.off_get(self.tile_size, _HEADER_AREA, self._cal_left_padding()))

                # --- vidas ---
        # Vidas restantes como iconos estáticos, alineados a la derecha.
        frames = self.player.images.get("right", [])
        lives = self.player.lives

        if frames and lives > 0:
            icon_size = 16
            gap = 4
            total_width = lives * icon_size + (lives - 1) * gap
            start_x = _WINDOW_WIDTH - _PADDING - total_width
            icon = pygame.transform.scale(frames[0], (icon_size, icon_size))

            for index in range(lives):
                self.window.blit(
                    icon,
                    (start_x + index * (icon_size + gap), _1UP_SCORE_POS[1])
                )

        # Reloj
        time_x = (
            self._cal_left_padding()
            + self.maze_px[0]
            - self.time_title.sur.get_width()
        )
        time_y = _HEADER_AREA + self.maze_px[1] + 12
        self.window.blit(self.time_title.sur, (time_x, time_y))

        # Nivel
        level_preview: Title = Title(f"LEVEL {level}", size=14)
        self.window.blit(
            level_preview.sur,
            (self._cal_left_padding(), time_y)
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





