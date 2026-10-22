import pygame
from pygame import Surface
from typing import Tuple, List, Dict
from src.maze.bitmap import BitMap, UP, RIGHT, DOWN, LEFT
from src.core.entity import Entity
from src.core.player import Player
from src.core.ghost import Ghost, Blinky, Pinky, Inky, Clyde
from src.core.pacgum import PacGum, SuperPacGum
from src.utils.utils import Coord, Color, Logo
from src.utils.class_maze import Maze
from src.ux_ui.menu import MenuInit

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

# Valores provisionales
_MAX_SCREEN_W = 1200
_MAX_SCREEN_H = 800
_MIN_SCREEN_W = 400
# MIN_SCREEN_H = 400

_WINDOW_WIDTH = 600
_WINDOW_HEIGHT = 800

_LOGO_AREA = 200
_LOGO_DIMENSIONS = (450, 117)

_PADDING = 30
_LINE = 2
_SAFE_LINE = 1

_MIN_TILE_SIZE = 10
_STD_TILE_SIZE = 20
_MAX_TILE_SIZE = 45

_BACKGROUND_COLOR = (3, 18, 15, 255)
_WALL_COLOR = (5, 4, 170, 255)
_TEST_COLOR = (0, 0, 0, 255)


class GraphicEngine():
    """
    """
    def __init__(
            self,
            player: Player,
            ghosts: Dict[str, Ghost],
            pacgum: List[PacGum]) -> None:

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
        self.init_menu: MenuInit = None

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
        safe_h: int = _WINDOW_HEIGHT - _LOGO_AREA - _PADDING

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

        # Draw walls based on bits
        if value & 1:  # NORTH
            for i in range(self.tile_size):
                for t in range(self.line):
                    self._put_pixel(surface, (x + i, y + t), color)

        if value & 2:  # EAST
            for i in range(self.tile_size):
                for t in range(self.line):
                    self._put_pixel(surface,
                                    (x + self.tile_size - 1 - t, y + i), color)

        if value & 4:  # SOUTH
            for i in range(self.tile_size):
                for t in range(self.line):
                    self._put_pixel(surface,
                                    (x + i, y + self.tile_size - 1 - t), color)

        if value & 8:  # WEST
            for i in range(self.tile_size):
                for t in range(self.line):
                    self._put_pixel(surface, (x + t, y + i), color)

        if value == 15:  # CLOSED
            for i in range(self.tile_size):
                for t in range(self.tile_size):
                    self._put_pixel(surface, (x + t, y + i), color)

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
            h: int = _LOGO_AREA
        ) -> Tuple[int, int]:
        """
        """
        return (self._cal_left_padding(), h)

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
        self.player._init_surface(self.player.pos, self.tile_size)
        for ghost in self.ghosts.values():
            ghost._init_surface(ghost.pos, self.tile_size)
        for pacgum in self.pacgum:
            pacgum._init_surface(pacgum.pos, self.tile_size)

    def _free_entities(self) -> None:
        """
        Libera la memoria de las surfaces de las entities
        """
        self.player.sur.convert(self.player.sur, None)
        for ghost in self.ghosts.values():
            ghost.sur.convert(ghost.sur, None)
        for pacgum in self.pacgum:
            pacgum.sur.convert(pacgum.sur, None)

    """
    ╔═════════════════════════════════════════════════════════════════════════╗
    ║                                UX-UI                                    ║
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
        scaled_logo: Surface = pygame.transform.smoothscale(self.logo.img, _LOGO_DIMENSIONS)
        self.window.blit(scaled_logo, (75, _PADDING))

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

    def _put_entities(self) -> None:
        """
        Dibuja las entities en el mapa
        """
        self._init_entities()
        self._render_entity_block(self.player)
        
        for ghost in self.ghosts.values():
            self._render_entity_block(ghost)
        for pacgum in self.pacgum:
            self._render_pacgum(pacgum)
        
        # map(self._render_entity_block, self.ghosts.values())
        # map(self._render_pacgum, self.pacgum)

    def _blit_elements(self) -> None:
        """
        """
        self.window.blit(self.background, (0, 0))
        self._put_logo()
        self.window.blit(self.maze.sur, (self._cal_maze_offset()))
        for pacgum in self.pacgum:
            self.window.blit(
                pacgum.sur,
                pacgum.pos.off_get(self.tile_size, _LOGO_AREA, self._cal_left_padding()))
        for ghost in self.ghosts.values():
            self.window.blit(ghost.sur, ghost.pos.off_get(self.tile_size, _LOGO_AREA, self._cal_left_padding()))
        self.window.blit(self.player.sur, self.player.pos.off_get(self.tile_size, _LOGO_AREA, self._cal_left_padding()))