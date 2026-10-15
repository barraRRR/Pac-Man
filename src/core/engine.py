import pygame
from pygame import Surface
from typing import Tuple

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

_TEST_WINDOWN_WIDTH = 600
_TEST_WINDOW_HEIGHT = 800

_PADDING = 30
_LINE = 2
_SAFE_LINE = 1

_MIN_TILE_SIZE = 10
_STD_TILE_SIZE = 20
_MAX_TILE_SIZE = 45

_TEST_BACKGROUND_COLOR = 0xFFDB58


class Engine():
    """
    """
    def __init__(self) -> None:
        # size = (col, row)
        self.map_size: Tuple[int, int] = None
        self.tile_size: int = None
        self.line: int = None
        self.map_px: Tuple[int, int] = None
        self.win_px: Tuple[int, int] = None

    def _update_size(self, size: Tuple[int, int]) -> None:
        """
        Fija el tamaño de la v
        """
        self.map_size: Tuple[int, int] = size

    def _calculate_map_size_px(self) -> None:
        """
        """
        # calculamos el tamaño que va a tener cada celda (tile) según los tamaños máximos y mínimos de pantalla que configuremos
        self.tile_size: int = self._calculate_dynamic_tile_size()
        # calculamos en una tupla el tamaño que debe tener el maze (suma de todas las celdas) | ancho x alto
        self.map_px: Tuple[int, int] = ((self.map_size[0] * self.tile_size), (self.map_size[1] * self.tile_size))
    
    def _calculate_window_size_px(self) -> None:
        """
        """
        # calculamos el tamaño que debe tener la ventana del programa, de primeras será lo que ocupe el maze + margen (padding) | ancho x alto
        self.win_px: Tuple[int, int] = (
            (max(_MIN_SCREEN_W, (self.map_px[0] + (_PADDING * 2)))),
            (self.map_px[1] + (_PADDING * 2))
        )

    def _calculate_dynamic_tile_size(self) -> int:
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

        return max(_MIN_TILE_SIZE, min(tile_size, _MAX_TILE_SIZE))

    def _px_with_padding(self, x_px: int, y_px: int) -> Tuple[int, int]:
        """Convert pixel coordinates with padding offset.

        Args:
            x_px: X pixel coordinate.
            y_px: Y pixel coordinate.

        Returns:
            Adjusted (x, y) coordinates.
        """

        # Esto es para poner pixeles calculando los margenes que dejamos por los bordes del mapa
        extra_x = (self.win_px[0] - self.maze_px[0]) // 2
        return (x_px + extra_x, y_px + _PADDING)

    def put_window(self) -> Surface:
        """
        """
        # Imprime la ventana entera en pantalla
        return pygame.display.set_mode(self.win_px)

    def put_pixel(self, surface: Surface) -> None:
        """
        """

    def put_background(self) -> Surface:
        """
        """
        # pone el fondo de pantalla sobre la pantalla
        background = Surface(self.win_px)
        background.fill(_TEST_BACKGROUND_COLOR)
        return background
    
    def put_map(self, size: Tuple[int, int]) -> None:
        """
        """
        ...
    