from src.utils.class_config import Config, Level
from src.utils.class_maze import Maze
import sys


class App:
    """
    """
    def __init__(self, config: Config) -> None:
        self.config = config
        self.maze = Maze(config.seed)
        self.pacman_start: tuple[int, int] | None = None
        self.ghost_spawns: list[tuple[int, int]] = []
        self.super_pacgum_spawns: list[tuple[int, int]] = []

    def run(self) -> int:
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

        self.pacman_start = self.maze.center_comecocos()
        reachable = self.maze.reachable_cells(self.pacman_start)

        self.ghost_spawns = self.maze.select_ghost_spawns(reachable)
        self.super_pacgum_spawns = self.maze.select_super_pacgum_spawns(
            reachable,
            self.ghost_spawns,
        )

        print(f"Level {number}:")
        print(f"  Pac-Man: {self.pacman_start}")
        print(f"  Ghosts: {self.ghost_spawns}")
        print(f"  Super-pacgums: {self.super_pacgum_spawns}")
        print()










