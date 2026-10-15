import pygame


# Valores provisionales
MAX_WINDOWN_WIDTH = 1080
MAX_WINDOW_HEIGHT = 720

# Test window values
TEST_WINDOWN_WIDTH = 600
TEST_WINDOW_HEIGHT = 800


"""

Estas son las funciones que podemos utilizar con el equivalente de MLX

Función MinilibX (MLX)	    Equivalente estricto en Pygame	    Propósito en el motor gráfico
|--------------------------|-----------------------------------|----------------------------------------------------|
mlx_init()	                pygame.init()	                    Inicializa los módulos internos del entorno gráfico.
mlx_new_window()	        pygame.display.set_mode((w, h))	    Crea la ventana principal donde se renderizará el juego.
mlx_new_image()	            pygame.Surface((w, h))	            Crea un lienzo en memoria para dibujar antes de volcar a pantalla.
mlx_xpm_file_to_image()	    pygame.image.load(ruta)	            Carga una textura o sprite desde un archivo local a la memoria.
mlx_pixel_put()	            superficie.set_at((x, y), color)	Cambia el color de un único píxel específico.
mlx_put_image_to_window()	ventana.blit(imagen, (x, y))	    Vuelca una imagen o buffer en unas coordenadas concretas de la pantalla.
mlx_hook() / mlx_key_hook()	pygame.event.get()	                Captura eventos crudos del sistema (teclas, ratón, cierre de ventana).
mlx_loop()	                while loop: + pygame.display.flip()	Mantiene el programa en ejecución y actualiza los fotogramas.
mlx_destroy_window()	    pygame.display.quit()	            Destruye el contexto gráfico y cierra la ventana de forma segura.

"""


class Engine():
    """
    """
    def __init__(self) -> None:
        self.w: int = TEST_WINDOWN_WIDTH
        self.h: int = TEST_WINDOW_HEIGHT

    def run(self):
        pygame.init()
        window = pygame.display.set_mode((self.w, self.h))
        running = True

        # mantiene el programa en ejecución hasta que haya un evento de cierre
        while running:
            for event in pygame.event.get():
                # pulsar el boton X con el raton
                if event.type == pygame.QUIT:
                    running = False
                # pulsar la tecla ESC
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running == False
            # actualiza frame
            pygame.display.flip()

        # cierra el programa
        pygame.quit()
