from src.utils.class_config import Config, Level
from src.utils.class_maze import Maze
import sys
import random


class App:
    """
    """
    def __init__(self, config: Config) -> None:
        self.config = config
        self.maze = Maze(config.seed)
        self.pacman_start: tuple[int, int] | None = None
        self.ghost_spawns: list[tuple[int, int]] = []

    def run(self) -> None:
        """Recorre los niveles en orden y ejecuta los momentos del juego."""
        for number, level in enumerate(self.config.level, start=1):
            try:
                self._start_level(number, level)   # Momento 1: preparar el nivel (mapa)
            except Exception:
                print(
                    f"Error: Could not generate level {number}.",
                    file=sys.stderr,
                )
                return 1
            # self._spawn_entities() # Momento 2: colocar Pac-Man y fantasmas (aún no existe)
            # self._game_loop()      # Momento 3: mover, comer, morir (aún no existe)
            # self._end_game()       # Momento 4: guardar puntuación, despedida
        return 0

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

        self.pacman_start = self.maze.center_comecocos()
        # self.ghost_spawns = self.maze.ghost_corners()
        self.ghost_spawns = self.maze.select_ghost_spawns(self.pacman_start)
        # print(f"Level {number}: Pac-Man starts at {self.pacman_start} - Ghosts start at {self.ghost_spawns}")
        reachable = self.maze.reachable_cells(self.pacman_start)
        # print(f"Level {number}: reachable cells: {len(reachable)}")
        print(f"Level {number}: Ghosts start at {self.ghost_spawns}")
        zones = self.maze.corner_zone_cells()
        reachability = self.maze.corner_zone_reachability(self.pacman_start)

        corner_names = (
            "Top-left",
            "Top-right",
            "Bottom-left",
            "Bottom-right",
        )
        print()










