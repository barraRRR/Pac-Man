import pygame
from pygame import Surface
from typing import Tuple, List
from src.maze.bitmap import BitMap
from src.utils.utils import Coord, Color

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

_TEST_BACKGROUND_COLOR = (255, 219, 88, 255)
_TEST_WALL_COLOR = (0, 0, 0, 255)


class ImageRender:
    """
    Pinta pixeles en display y superficies.
    """
    def __init__(self) -> None:
        self.tile_size: int = None
        self.map_px: Coord = Coord()
        self.line: int = None
        
    def update(
            self,
            tile_size: int,
            map_px: Coord,
            line: int
        ) -> None:
        self.tile_size: int = tile_size
        self.map_px: Coord = map_px
        self.line: int = line

    def _put_pixel(
            self,
            surface: Surface,
            coord: Coord,
            color: Color = None
        ) -> None:
        """
        """
        if not color:
            color = Color(*_TEST_WALL_COLOR)

        # quita posibles coordenadas fuera de la ventana
        if (coord.x < 0 or coord.x >= surface.get_width() or
            coord.y < 0 or coord.y >= surface.get_height()):
            return

        # coloca el pixel en la superficie
        surface.set_at(coord.get(), color.get())

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

    def _render_map(
            self,
            map_surface: Surface,
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

        if not color:
            color = Color((0, 0, 0, 0))

        for y, row in enumerate(bitmap.grid):
            for x, cell_value in enumerate(row):
                self._render_cell(map_surface, (x, y), cell_value, color)
        

class GraphicEngine():
    """
    """
    def __init__(self) -> None:
        # size = (col, row)
        self.map_size: Coord = Coord()
        self.tile_size: int = None
        self.line: int = None
        self.map_px: Coord = Coord()
        self.win_px: Coord = Coord()
        self.paint: ImageRender = ImageRender()

    def _update_size(self, size: Coord) -> None:
        """
        Fija el tamaño del mapa
        """
        self.map_size.set_at(size.get())

    def _calculate_map_size_px(self) -> None:
        """
        """
        # calculamos el tamaño que va a tener cada celda (tile) según los tamaños máximos y mínimos de pantalla que configuremos
        self._calculate_dynamic_tile_size()
        # calculamos en una tupla el tamaño que debe tener el maze (suma de todas las celdas) | ancho x alto
        self.map_px.set_at((self.map_size[0] * self.tile_size), (self.map_size[1] * self.tile_size))
    
    def _calculate_window_size_px(self) -> None:
        """
        """
        # calculamos el tamaño que debe tener la ventana del programa, de primeras será lo que ocupe el maze + margen (padding) | ancho x alto
        self.win_px.set_at(
            (max(_MIN_SCREEN_W, (self.map_px[0] + (_PADDING * 2)))),
            (self.map_px[1] + (_PADDING * 2))
        )

    def _calculate_dynamic_tile_size(self) -> None:
        """Calculate optimal tile size based on window and maze dimensions.

        Returns:
            Tile size in pixels (10-45 range).
        """

        # Esto son operaciones para que el tamaño de las celdas se ajuste al tamaño de la pantalla
        safe_w: int = _MAX_SCREEN_W - (_PADDING * 2)
        safe_h: int = _MAX_SCREEN_H - (_PADDING * 2)

        ideal_tile_w: int = safe_w // self.map_size[0]
        ideal_tile_h: int = safe_h // self.map_size[1]

        tile_size: int = min(ideal_tile_w, ideal_tile_h)
        self.tile_size: int = max(
            _MIN_TILE_SIZE, min(tile_size, _MAX_TILE_SIZE)
        )
        # Establecemos el grosor de la línea según el tamaño de la celda
        self.line = _LINE if self.tile_size >= _STD_TILE_SIZE else _SAFE_LINE

    def _px_with_padding(self, x_px: int, y_px: int) -> Coord:
        """Convert pixel coordinates with padding offset.

        Args:
            x_px: X pixel coordinate.
            y_px: Y pixel coordinate.

        Returns:
            Adjusted (x, y) coordinates.
        """

        # Esto es para poner pixeles calculando los margenes que dejamos por los bordes del mapa
        extra_x = (self.win_px.x - self.map_px.x) // 2
        return Coord((x_px + extra_x, y_px + _PADDING))

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
        background.fill(_TEST_BACKGROUND_COLOR)
        return background

    def put_map(
            self,
            bitmap: BitMap,
            color: Tuple[int, int, int, int] = _TEST_WALL_COLOR
        ) -> Surface:
        """
        """
        self.paint.update(self.tile_size, self.map_px, self.line)
        map_surface = Surface(self.map_px, pygame.SRCALPHA)
        map_surface.fill((0, 0, 0, 0)) 
        self.paint._render_map(map_surface, bitmap, color)
        # Imprime la ventana entera en pantalla
        return map_surface

    