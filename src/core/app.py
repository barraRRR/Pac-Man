from src.utils.class_config import Config
from src.core.engine import Engine, _PADDING
from typing import List
import pygame


class App:
    """
    """
    def __init__(self, config: Config) -> None:
        self._config = config

        # test
        self._test_level = self._config.level[0]
        ###

        self._engine = Engine()
        self._engine._update_size(
            (self._test_level.width, self._test_level.height)
        )
        self._engine._calculate_map_size_px()
        self._engine._calculate_window_size_px()

    def run(self):
        pygame.init()
        window = self._engine.put_window()
        running = True
        map = self._engine.put_map(self.test_maze_generator())

        # mantiene el programa en ejecución hasta que haya un evento de cierre
        while running:
            window.blit(self._engine.put_background(), (0, 0))
            window.blit(map, (_PADDING, _PADDING))
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

    # metodo provisional para probar el mapa
    def test_maze_generator(self) -> List[List[int]]:
        from tests.generator import MazeGenerator
        generator = MazeGenerator(15, 15, (0, 0), (14, 14))
        generator.generate(is_perfect=False)
        return generator.grid
