from src.utils.class_config import Config, Level
from src.utils.class_maze import Maze
from src.utils.class_config import Config
from src.core.player import Player
from src.core.ghost import Ghost, Blinky, Pinky, Inky, Clyde
from src.core.pacgum import PacGum, SuperPacGum
from src.core.engine import GraphicEngine, _PADDING
from src.maze.bitmap import BitMap, UP, RIGHT, DOWN, LEFT
from src.utils.utils import Coord, Color
from src.ux_ui.menu import Item, ItemType, Menu, MenuInit
from typing import List, Dict, Callable
from src.utils.error import HitWallError
import sys
import pygame
import random


_FPS = 60
_MOVEMENT_INTERVAL = 150

_UI_SIZE = (600, 800)


class App:
    """Coordina la lógica del juego y prepara el estado de cada nivel."""

    def __init__(self, config: Config) -> None:
        """Construye la App con la configuración y deja el estado vacío."""
        self.config: Config = config                                  # Configuración ya validada y acotada.
        self.maze: Maze = Maze(config.seed)                         # Adaptador del laberinto; semilla para el nivel 1.
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
        self.list_key = []
        self._paused: bool = False

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
        self._engine._init_window()
        if self._menu_loop(
            self._engine.menu_init,
            lambda: self._engine._blit_menu_init(self._engine.menu_init)
        ) == ItemType.QUIT:
            return 0

        for number, level in enumerate(self.config.level, start=1):
            # try:
            self._start_level(number, level, True)   # Momento 1: preparar el nivel (mapa)
            self._spawn_entities() # Momento 2: colocar Pac-Man y fantasmas (aún no existe)
            self._game_loop()      # Momento 3: mover, comer, morir (aún no existe)
            
            """
            except Exception:
                print(
                    f"Error: Could not generate level {number}.",
                    file=sys.stderr,
                )
                return 1
            """
        self._end_game()       # Momento 4: guardar puntuación, despedida
        return 0

    def _start_level(self, number: int, level: Level, debug: bool = False) -> None:
        """Prepara el nivel actual: genera el mapa y deja el estado listo."""
        # Genero el mapa de este nivel con el tamaño que dice la config.
        self.maze.generate_level(
            number=number,
            width=level.width,
            height=level.height,
        )
        Coord._set_frontier(self.maze.frontier)
        print(f"\nLevel {number}:")

        self.current_level = number
        self.pacman_start = self.maze.center_comecocos()
        reachable = self.maze.reachable_cells(self.pacman_start)
        self.ghost_spawns = self.maze.select_ghost_spawns(reachable)
        self.super_pacgum_spawns = self.maze.select_super_pacgum_spawns(
            reachable,
            self.ghost_spawns,
        )
        self.pacgum_spawns = self.maze.select_pacgum_spawns(reachable, self.pacman_start, self.ghost_spawns, self.super_pacgum_spawns, self.config.pacgum)
        counts = {}
        for cell in self.pacgum_spawns:
            value = self.maze.grid[cell[1]][cell[0]]
            counts[value] = counts.get(value, 0) + 1
        print(f"  Pacgum cell values: {dict(sorted(counts.items()))}")

        if debug:
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

        #limpiamos antes de colocar.  --> Reparado por Javi
        self.pacgum.clear()
        for spawn in self.super_pacgum_spawns:
            self.pacgum.append(SuperPacGum(Coord(spawn)))
        for spawn in self.pacgum_spawns:
            self.pacgum.append(PacGum(Coord(spawn)))

        # TEMPORAL: comprobar que cada fantasma tiene sus sprites cargados. Quitar al cerrar la #51.
        for name, ghost in self.ghosts.items():
            print(f"  {name}: {len(ghost.images)} sprites -> {ghost.images['right']}")

        # TEMPORAL: comprobar sprites del player. Quitar al cerrar la #51.
        print(f"  player: {len(self.player.images)} sprites -> {self.player.images['right']}")


    def _push_direction(self, dir:int) ->None:
        """Apunta la direccion pulsada: si hay hueco se apila, si esta llena se sustituye la pendiente."""
        if dir in self.list_key:
            return
        if len(self.list_key) < 2:
            self.list_key.append(dir)
        else:
            self.list_key[1] = dir      # lista llena: la nueva tecla sustituye a la pendiente



    def _handle_events(self) -> bool:
        """Gestiona los eventos de pygame y traduce las teclas a direcciones.

        La tecla no mueve a Pac-Man: apunta su direccion en list_key.
        Devuelve False si se pide cerrar el juego (boton X o ESC),
        True mientras la partida siga en marcha.
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
                    elif event.key == pygame.K_SPACE:
                        self._paused = not self._paused
                        if self._paused:
                            print("Game Pauseeeeed")
                        else:
                            print("Game resumed")
                    elif event.key == pygame.K_UP:
                        self._push_direction(UP)
                        # self.player._move(self.maze._bitmap, UP)
                    elif event.key == pygame.K_RIGHT:
                        self._push_direction(RIGHT)
                        # self.player._move(self.maze._bitmap, RIGHT)
                    elif event.key == pygame.K_DOWN:
                        self._push_direction(DOWN)
                        # self.player._move(self.maze._bitmap, DOWN)
                    elif event.key == pygame.K_LEFT:
                        self._push_direction(LEFT)
                        # self.player._move(self.maze._bitmap, LEFT)

                except HitWallError:
                    # return False #definir
                    pass

        return True

    def _menu_loop(self, menu: Menu, func: Callable[[Menu], None]) -> ItemType:
        """
        """
        while True:
            dt: int = self.clock.tick(_FPS)
            func()
            for event in pygame.event.get():
                # pulsar el boton X con el raton
                if event.type == pygame.QUIT:
                    return ItemType.QUIT
                # pulsar la tecla ESC
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        menu._select_item(False)
                    elif event.key == pygame.K_DOWN:
                        menu._select_item(True)
                    elif event.key == pygame.K_RETURN:
                        return menu._active_item._item_type
            pygame.display.flip()
            self._engine.window.fill((0, 0, 0, 0))


    def _game_loop(self):
        """
        TO-DO
        """
        
        # render de surfaces
        self._engine._update_maze(self.maze)
        self._engine._put_maze(self.maze)
        self._engine._put_entities()

        # mantiene el programa en ejecución hasta que haya un evento de cierre
        running = True
        move_timer: int = 0
        while running:
            dt: int = self.clock.tick(_FPS)
            if not self._paused:
                #========PLAYER============
                # movimiento del player: un paso cada _MOVEMENT_INTERVAL ms
                move_timer += dt
                if move_timer >= _MOVEMENT_INTERVAL:
                    move_timer -= _MOVEMENT_INTERVAL   # resto en vez de cero, igual que la hucha de Blinky
                    if self.list_key:
                        moved: bool = False     # giro anticipado: si la pendiente ya se puede, se ejecuta al instante
                        if len(self.list_key) == 2:
                            try:
                                self.player._move(self.maze._bitmap, self.list_key[1])
                                self.list_key.pop(0)
                                moved = True
                            except HitWallError:
                                pass
                            # paso normal con la actual, si no acabamos de girar
                        if not moved:
                            try:
                                self.player._move(self.maze._bitmap, self.list_key[0])
                            except HitWallError:
                                # pared: cae la actual y la pendiente manda en el proximo latido
                                if len(self.list_key) == 2:
                                    self.list_key.pop(0)

                # window.blit(self.player.sur, self.player.pos.off_get(self._engine.tile_size))   #player, me ha costado, blit dibuja pos mueve

                #========GHOST============
                self._engine._blit_elements()

                for ghost in self.ghosts.values():      # movement
                    ghost._move(
                        target=self.player.pos,
                        dt=dt,
                        tile_size=self._engine.tile_size,
                        bitmap=self.maze._bitmap
                    )
            running = self._handle_events()
            # actualiza frame
            pygame.display.flip()
            self._engine.window.fill((0, 0, 0, 0))

    def _end_game(self) -> None:
        """
        TO-DO
        """
        # cierra el programa
        pygame.quit()
