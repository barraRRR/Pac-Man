import pygame
from pygame import Surface
from typing import Tuple, List, Dict
from src.maze.bitmap import BitMap
from src.core.entity import Entity
from src.core.player import Player
from src.core.ghost import Ghost, Blinky, Pinky, Inky, Clyde
from src.core.pacgum import PacGum, PGType
from src.utils.utils import Coord, Color
from src.utils.class_maze import Maze

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

_TEST_WINDOW_WIDTH = 600
_TEST_WINDOW_HEIGHT = 800

_PADDING = 30
_LINE = 2
_SAFE_LINE = 1

_MIN_TILE_SIZE = 10
_STD_TILE_SIZE = 20
_MAX_TILE_SIZE = 45

_BACKGROUND_COLOR = (0, 0, 0, 255)
_WALL_COLOR = (128, 128, 128, 255)
_TEST_COLOR = (0, 0, 0, 255)


class SizeCalculator:
    """
    """
    @staticmethod
    def _calculate_dynamic_tile_size(maze_size: Coord) -> int:
        """Calculate optimal tile size based on window and maze dimensions.

        Returns:
            Tile size in pixels (10-45 range).
        """
        # Esto son operaciones para que el tamaño de las celdas se ajuste al tamaño de la pantalla
        safe_w: int = _MAX_SCREEN_W - (_PADDING * 2)
        safe_h: int = _MAX_SCREEN_H - (_PADDING * 2)

        ideal_tile_w: int = safe_w // maze_size.x
        ideal_tile_h: int = safe_h // maze_size.y

        tile_size: int = min(ideal_tile_w, ideal_tile_h)

        return max(_MIN_TILE_SIZE, min(tile_size, _MAX_TILE_SIZE))

    @staticmethod
    def _calculate_line_px(tile_size: int) -> int:
        """
        """
        # Establecemos el grosor de la línea según el tamaño de la celda
        line: int = _LINE if tile_size >= _STD_TILE_SIZE else _SAFE_LINE
        return line

    @staticmethod
    def _calculate_maze_size_px(maze_size: Coord) -> Tuple[int, int]:
        """
        """
        # calculamos el tamaño que va a tener cada celda (tile) según los tamaños máximos y mínimos de pantalla que configuremos
        tile_size: int = SizeCalculator._calculate_dynamic_tile_size(maze_size)
        # calculamos en una tupla el tamaño que debe tener el maze (suma de todas las celdas) | ancho x alto
        return (maze_size.x * tile_size), (maze_size.y * tile_size)

    @staticmethod
    def _calculate_window_size_px(maze_px: Coord) -> Tuple[int, int]:
        """
        """
        # calculamos el tamaño que debe tener la ventana del programa, de primeras será lo que ocupe el maze + margen (padding) | ancho x alto
        return(max(_MIN_SCREEN_W, (maze_px.x + (_PADDING * 2)))), (maze_px.y + (_PADDING * 2))

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
        # Esto es para poner pixeles calculando los margenes que dejamos por los bordes del mapa
        extra_x = (win_px.x - maze_px.x) // 2
        return Coord((x_px + extra_x, y_px + _PADDING))


class PixelRender:
    """
    Pinta pixeles en display y superficies.
    """
    def __init__(self) -> None:
        self.tile_size: int = None
        self.maze_px: Coord = Coord()
        self.line: int = None
        
    def update(
            self,
            tile_size: int,
            maze_px: Coord,
            line: int
        ) -> None:
        self.tile_size: int = tile_size
        self.maze_px: Coord = maze_px
        self.line: int = line

    def _put_pixel(
            self,
            surface: Surface,
            coord: Coord,
            color: Color
        ) -> None:
        """
        coloca el pixel en la superficie
        """

        try:
            surface.set_at(coord.get(), color.get())

        except Exception:   # buscar excepcion si la coord cae fuera de la ventana.
            pass

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
                    self._put_pixel(surface, (x + self.tile_size - 1 - t, y + i), color)

        if value & 4:  # SOUTH
            for i in range(self.tile_size):
                for t in range(self.line):
                    self._put_pixel(surface, (x + i, y + self.tile_size - 1 - t), color)

        if value & 8:  # WEST
            for i in range(self.tile_size):
                for t in range(self.line):
                    self._put_pixel(surface, (x + t, y + i), color)

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
                self._render_cell(maze_surface, Coord((x, y)), cell_value, color)

    def _render_entity_block(
            self,
            entity: Entity,
            px: int = 0
        ) -> None:
        """
        """
        start_x, start_y = entity.pos.off_get(self.tile_size)
        for i in range(self.tile_size - px):
            for t in range(self.tile_size - px):
                self._put_pixel(start_x + i + px, start_y + t + px, entity.color)


class GraphicEngine():
    """
    """
    def __init__(
            self,
            player: Player,
            ghosts: Dict[str, Ghost],
            pacgum: List[PacGum]) -> None:
        self.player: Player = player
        self.ghosts: Dict[Ghost] = ghosts
        self.pacgum: List[PacGum] = pacgum

        # size = (col, row) / px = pixeles
        self.maze_size: Coord = Coord()
        self.tile_size: int = None
        self.line: int = None
        self.maze_px: Coord = Coord()
        self.win_px: Coord = Coord()

        self.render: PixelRender = PixelRender()
        self.resize: SizeCalculator = SizeCalculator()

    def _update_size(self, maze: Maze) -> None:
        """
        Fija el tamaño del mapa
        """
        w = len(maze.grid[0])
        h = len(maze.grid)
        self.maze_size.set_at((w, h))
        self.tile_size = self.resize._calculate_dynamic_tile_size(self.maze_size)
        self.line = self.resize._calculate_line_px(self.tile_size)
        self.maze_px.set_at(self.resize._calculate_maze_size_px(self.maze_size))
        self.win_px.set_at(self.resize._calculate_window_size_px(self.maze_size))

    def put_window(self) -> Surface:
        """
        """
        # Imprime la ventana entera en pantalla
        return pygame.display.set_mode(self.win_px.get())

    def put_background(self) -> Surface:
        """
        """
        # pone el fondo de pantalla sobre la pantalla
        background = Surface(self.win_px.get())
        background.fill(_BACKGROUND_COLOR)
        return background

    def put_maze(
            self,
            bitmap: BitMap,
            color: Tuple[int, int, int, int] = _WALL_COLOR
        ) -> Surface:
        """
        """
        self.render.update(self.tile_size, self.maze_px, self.line)
        maze_surface = Surface(self.maze_px.get(), pygame.SRCALPHA)
        maze_surface.fill((0, 0, 0, 0)) 
        self.render._render_maze(maze_surface, bitmap, color)
        # Imprime la ventana entera en pantalla
        return maze_surface

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

    def _put_entities(self) -> None:
        """
        Dibuja las entities en el mapa
        """
        self._init_entities()
        self.render._render_entity_block(self.player, px=2)
        for ghost in self.ghosts.values():
            self.render._render_entity_block(ghost, px=2)
        for pacgum in self.pacgum:
            self.render._render_entity_block(pacgum, px=4)
    