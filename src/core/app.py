from src.utils.class_config import Config, Level
from src.utils.class_maze import Maze
import sys


class App:
    """Coordina la lógica del juego y prepara el estado de cada nivel."""

    def __init__(self, config: Config) -> None:
        """Construye la App con la configuración y deja el estado vacío."""
        self.config = config                                  # Configuración ya validada y acotada.
        self.maze = Maze(config.seed)                         # Adaptador del laberinto; semilla para el nivel 1.
        self.pacman_start: tuple[int, int] | None = None      # Salida de Pac-Man (x, y); None hasta generar un nivel.
        self.ghost_spawns: list[tuple[int, int]] = []         # Salidas de los 4 fantasmas (x, y).
        self.super_pacgum_spawns: list[tuple[int, int]] = []  # Las 4 super-pacgums, una por esquina (x, y).
        self.pacgum_spawns: list[tuple[int, int]] = []        # Pacgums normales colocadas (x, y).
        self.current_level: int = 0                           # Número del nivel en curso (0 = ninguno iniciado).
        self.lives: int = config.lives                        # Vidas restantes; el game loop las gasta.
        self.score: int = 0                                   # Puntos acumulados; sube al comer.

    def run(self) -> int:
        """Recorre los niveles en orden y ejecuta los momentos del juego."""
        for number, level in enumerate(self.config.level, start=1):
            try:
                self._start_level(number, level)   # Momento 1: preparar el nivel (mapa)
                # self._spawn_entities() # Momento 2: colocar Pac-Man y fantasmas (aún no existe)
                # self._game_loop()      # Momento 3: mover, comer, morir (aún no existe)
                # self._end_game()       # Momento 4: guardar puntuación, despedida
            except Exception:
                print(
                    f"Error: Could not generate level {number}.",
                    file=sys.stderr,
                )
                return 1

        return 0

    def _start_level(self, number: int, level: Level) -> None:
        """Prepara el nivel actual: genera el mapa y deja el estado listo."""
        # Genero el mapa de este nivel con el tamaño que dice la config.
        self.maze.generate_level(
            number=number,
            width=level.width,
            height=level.height,
        )
        # Apunto qué nivel estamos preparando (para el HUD, errores y highscore).
        self.current_level = number

        # Pacman nace en la casilla andable más cercana al centro del mapa.
        self.pacman_start = self.maze.center_comecocos()

        # BFS una sola vez por nivel: guardo aquí todas las casillas alcanzables desde Pacman.
        # Esas casillas ya descartan muros (15) y zonas cortadas, no hace falta restar nada a mano.
        reachable = self.maze.reachable_cells(self.pacman_start)

        # A partir de aquí coloco en orden: cada colocación depende de las anteriores.
        # 1º fantasmas, uno por esquina elegidos entre las casillas alcanzables.
        self.ghost_spawns = self.maze.select_ghost_spawns(reachable)
        # 2º super-pacgums, una por esquina, sin pisar a los fantasmas que acabo de poner.
        self.super_pacgum_spawns = self.maze.select_super_pacgum_spawns(
            reachable,
            self.ghost_spawns,
        )
        # 3º pacgums normales, al final porque no pueden pisar a nadie de lo de arriba.
        self.pacgum_spawns = self.maze.select_pacgum_spawns(reachable, self.pacman_start, self.ghost_spawns, self.super_pacgum_spawns, self.config.pacgum)

        print(f"Level {number}:")
        print(f"  Pac-Man: {self.pacman_start}")
        print(f"  Ghosts: {self.ghost_spawns}")
        print(f"  Super-pacgums: {self.super_pacgum_spawns}")
        # print(f"  Pacgums: {self.pacgum_spawns}")
        print(f"  Pacgums: {len(self.pacgum_spawns)} placed")
        print()










