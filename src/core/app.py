from src.utils.class_config import Config, Level
from src.utils.class_maze import Maze
from src.utils.class_config import Config
from src.core.player import Player
from src.core.ghost import Ghost, Blinky, Pinky, Inky, Clyde
from src.core.pacgum import PacGum, SuperPacGum
from src.core.engine import GraphicEngine, _PADDING
from src.maze.bitmap import BitMap, UP, RIGHT, DOWN, LEFT
from src.utils.utils import Coord, Color
from typing import List, Dict
from src.utils.error import HitWallError
import sys
import pygame
import random


_FPS = 60


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

        # Entity instancies
        self.player: Player = Player()
        self.ghosts: Dict[str, Ghost] = {
            "blinky": Blinky(),
            "pinky": Pinky(),
            "inky": Inky(),
            "clyde": Clyde()
        }
        self.pacgum: List[PacGum] = []

        # Graphic Engine
        self._engine: GraphicEngine = GraphicEngine(
            player=self.player,
            ghosts=self.ghosts,
            pacgum=self.pacgum
        )

    @property
    def blinky(self) -> Blinky:
        return self.ghosts["blinky"]

    @property
    def pinky(self) -> Pinky:
        return self.ghosts["pinky"]

    @property
    def inky(self) -> Inky:
        return self.ghosts["inky"]

    @property
    def clyde(self) -> Clyde:
        return self.ghosts["clyde"]

    def run(self) -> int:
        """Recorre los niveles en orden y ejecuta los momentos del juego."""
        pygame.init()
        self.clock: pygame.time.Clock = pygame.time.Clock()
        for number, level in enumerate(self.config.level, start=1):
            # try:
            self._start_level(number, level, True)   # Momento 1: preparar el nivel (mapa)
            self._spawn_entities() # Momento 2: colocar Pac-Man y fantasmas (aún no existe)
            self._game_loop()      # Momento 3: mover, comer, morir (aún no existe)
            self._end_game()       # Momento 4: guardar puntuación, despedida
            """
            except Exception:
                print(
                    f"Error: Could not generate level {number}.",
                    file=sys.stderr,
                )
                return 1
            """

        return 0

    def _start_level(self, number: int, level: Level, debug: bool = False) -> None:
        """Prepara el nivel actual: genera el mapa y deja el estado listo."""
        # Genero el mapa de este nivel con el tamaño que dice la config.
        self.maze.generate_level(
            number=number,
            width=level.width,
            height=level.height,
        )
        print(f"\nLevel {number}:")

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

        if debug:
            print(f"Level {number}:")
            print(f"  Pac-Man: {self.pacman_start}")
            print(f"  Ghosts: {self.ghost_spawns}")
            print(f"  Super-pacgums: {self.super_pacgum_spawns}")
            # print(f"  Pacgums: {self.pacgum_spawns}")
            print(f"  Pacgums: {len(self.pacgum_spawns)} placed")
            print(f"  Pacgums: {self.pacgum_spawns}")
            print()

    def _spawn_entities(self) -> None:
        """
        Momento 2: colocar Pac-Man y fantasmas (aún no existe)
        """
        # colocamos al player
        self.player.pos.set_at(self.pacman_start)

        # colocamos a los fantasmas cogiendo los puntos aleatoriamente
        random_ghost_spawn = random.sample(self.ghost_spawns, 4)
        for ghost, spawn in zip(self.ghosts.values(), random_ghost_spawn):
            ghost.pos.set_at(spawn)

        #colocamos los gums
        for spawn in self.super_pacgum_spawns:
            self.pacgum.append(SuperPacGum(Coord(spawn)))
        for spawn in self.pacgum_spawns:
            self.pacgum.append(PacGum(Coord(spawn)))

    def _handle_events(self) -> bool:
        """
        """
        for event in pygame.event.get():
            # pulsar el boton X con el raton
            if event.type == pygame.QUIT:
                return False
            # pulsar la tecla ESC
            elif event.type == pygame.KEYDOWN:
                try:
                    if event.key == pygame.K_ESCAPE:
                        return False
                    elif event.key == pygame.K_UP:
                        self.player._move(self.maze._bitmap, UP)
                    elif event.key == pygame.K_RIGHT:
                        self.player._move(self.maze._bitmap, RIGHT)
                    elif event.key == pygame.K_DOWN:
                        self.player._move(self.maze._bitmap, DOWN)
                    elif event.key == pygame.K_LEFT:
                        self.player._move(self.maze._bitmap, LEFT)

                except HitWallError:
                    pass #definir

        return True

    def _game_loop(self):
        """
        TO-DO
        """
        
        # render de surfaces
        self._engine._update_size(self.maze)
        window = self._engine._init_window()
        maze = self._engine._put_maze(self.maze._bitmap)
        self._engine._put_entities()

        # mantiene el programa en ejecución hasta que haya un evento de cierre
        running = True
        while running:
            window.blit(self._engine._put_background(), (0, 0))
            window.blit(maze, (_PADDING, _PADDING))
            for pacgum in self.pacgum:
                window.blit(pacgum.sur, pacgum.pos.off_get(self._engine.tile_size))
            for ghost in self.ghosts.values():
                window.blit(ghost.sur, ghost.pos.off_get(self._engine.tile_size))
            window.blit(self.player.sur, self.player.pos.off_get(self._engine.tile_size))
            running = self._handle_events()
            # actualiza frame
            pygame.display.flip()
            window.fill((0, 0, 0, 0))
            self.clock.tick(_FPS)

    def _end_game(self) -> None:
        """
        TO-DO
        """
        # cierra el programa
        pygame.quit()
