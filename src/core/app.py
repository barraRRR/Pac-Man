from src.utils.class_config import Config, Level
from src.utils.class_maze import Maze


class App:
    """
    """
    def __init__(self, config: Config) -> None:
        self.config = config
        self.maze = Maze(config.seed)

    def run(self) -> None:
        """Recorre los niveles en orden y ejecuta los momentos del juego."""
        for number, level in enumerate(self.config.level, start=1):
            self._start_level(number, level)   # Momento 1: preparar el nivel (mapa)
            # self._spawn_entities() # Momento 2: colocar Pac-Man y fantasmas (aún no existe)
            # self._game_loop()      # Momento 3: mover, comer, morir (aún no existe)
            # self._end_game()       # Momento 4: guardar puntuación, despedida

    def _start_level(self, number: int, level: Level) -> None:
        """Prepara el nivel actual: genera el mapa y deja el estado listo."""
        self.maze.generate_level(
            number=number,
            width=level.width,
            height=level.height,
        )
        # print()           #print de prueba para impresion mapa, imprime los 10, el primero semilla resto aleatorio
        # for row in self.maze.grid:
        #     print(row)











