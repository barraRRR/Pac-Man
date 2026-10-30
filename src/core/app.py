from src.utils.class_config import Config, Level
from src.utils.class_maze import Maze
from src.utils.class_config import Config
from src.core.player import Player
from src.core.entity import Entity
from src.core.ghost import Ghost, Blinky, Pinky, Inky, Clyde
from src.core.pacgum import PacGum, SuperPacGum
from src.core.engine import GraphicEngine, _PADDING
from src.maze.bitmap import BitMap, UP, RIGHT, DOWN, LEFT
from src.score.score import Score
from src.utils.utils import Coord, Color, Dir
from src.ux_ui.menu import Item, ItemType, Menu, MenuInit
from typing import List, Dict, Callable
from src.utils.error import HitWallError
import sys
import pygame
import random
from src.score.highscore import HighScore
from src.ux_ui.instructions import Instructions


_FPS = 60
_MOVEMENT_INTERVAL = 220

# Duracion del efecto de la super-pacgum (10 s de prueba)
_SUPER_PACGUM_DURATION_MS = 10000

_UI_SIZE = (600, 800)


class App:
    """Coordina la lógica del juego y prepara el estado de cada nivel."""

    def __init__(self, config: Config) -> None:
        """Construye la App con la configuración y deja el estado vacío."""
        self.config: Config = config                                  # Configuración ya validada y acotada.
        # Adaptador del laberinto; semilla para el nivel 1.
        self.maze: Maze = Maze(config.seed)
        # Salida de Pac-Man (x, y); None hasta generar un nivel.
        self.pacman_start: tuple[int, int] | None = None
        # Salidas de los 4 fantasmas (x, y).
        self.ghost_spawns: list[tuple[int, int]] = []
        # Las 4 super-pacgums, una por esquina (x, y).
        self.super_pacgum_spawns: list[tuple[int, int]] = []
        # Pacgums normales colocadas (x, y).
        self.pacgum_spawns: list[tuple[int, int]] = []
        # Número del nivel en curso (0 = ninguno iniciado).
        self.current_level: int = 0
        # Vidas restantes; el game loop las gasta.
        self.lives: int = config.lives
        # Puntos acumulados; sube al comer.
        self.score: Score = Score()


        pygame.init()
        # Entity instancies
        self.player: Player = Player(
            lives=self.config.lives,
            score=self.score
        )
        self.ghosts: Dict[str, Ghost] = {
            "blinky": Blinky(points=self.config.points_per_ghost),
            "pinky": Pinky(points=self.config.points_per_ghost),
            "inky": Inky(points=self.config.points_per_ghost),
            "clyde": Clyde(points=self.config.points_per_ghost)
        }
        self.pacgum: List[PacGum] = []

        # Graphic Engine
        self._engine: GraphicEngine = GraphicEngine(
            player=self.player,
            ghosts=self.ghosts,
            pacgum=self.pacgum,
            score=self.score
        )
        self.list_key: Dir = []
        self._pause: bool = False
        self._return_to_menu: bool = False
        # Tiempo acumulado del efecto de la super-pacgum (ms)
        self._super_timer_ms: int = 0

        # HighScore: el nombre del archivo lo manda la config y el ranking
        # se carga una sola vez al arrancar (alta en #35, conexión con App).
        HighScore.filename = self.config.highscore_filename
        HighScore.security = False   # TEMPORAL: probar salida en claro
        HighScore.load()
        print(f"  highscores loaded: {len(HighScore.scores)}")
        # HighScore.register("TEST", 100)   # TEMPORAL: probar guardado, quitar

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
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self._engine._init_window()
        while True:
            option: ItemType = self._menu_loop(
                self._engine.menu_init,
                lambda: self._engine._blit_menu_init(self._engine.menu_init)
            )
            if option == ItemType.QUIT:
                break
                # return 0
            elif option == ItemType.START:
                # Partida nueva: vidas de vuelta al valor que manda la config.
                self.player._reset_lives(self.config.lives)
                self.score.reset()
                Ghost.edible = False
                self._super_timer_ms = 0
                for ghost in self.ghosts.values():
                    ghost._reset()
                for number, level in enumerate(self.config.level, start=1):
                    # try:
                    # Momento 1: preparar el nivel (mapa)
                    self._start_level(number, level, True)
                    self._spawn_entities()  # Momento 2: colocar Pac-Man y fantasmas (aún no existe)
                    if number != 1:
                        self._level_intro(number)
                    self._game_loop()      # Momento 3: mover, comer, morir (aún no existe)

                    if self._return_to_menu:
                        self._return_to_menu = False
                        break
                else:
                    break
                """
                except Exception:
                    print(
                        f"Error: Could not generate level {number}.",
                        file=sys.stderr,
                    )
                    return 1
                """
            elif option == ItemType.HIGHSCORES:
                self._highscores_loop()  # Pantalla Top 10: siguiente bloque
                # self._engine._blit_highscores_rows(HighScore.scores)
                
            elif option == ItemType.INSTRUCTIONS:
                self._instructions_loop()
                # pass  # Pantalla de controles y reglas: luego
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
        Ghost.path_map.clear()   # mapa nuevo: caduca la cache de caminos BFS
        Coord._set_frontier(self.maze.frontier)
        print(f"\nLevel {number}:")

        self.current_level = number
        self.list_key.clear()   # nivel nuevo: sin giros pendientes del anterior
        self.pacman_start = self.maze.center_comecocos()
        reachable = self.maze.reachable_cells(self.pacman_start)
        self.ghost_spawns = self.maze.select_ghost_spawns(reachable)
        self.super_pacgum_spawns = self.maze.select_super_pacgum_spawns(
            reachable,
            self.ghost_spawns,
        )
        self.pacgum_spawns = self.maze.select_pacgum_spawns(
            reachable, self.pacman_start, self.ghost_spawns, self.super_pacgum_spawns, self.config.pacgum)
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
        Coloca a Pac-Man, los fantasmas y las pacgums del nivel.
        """
        # colocamos al player
        self.player.pos.set_at(self.pacman_start)
        self.player.spawn_pos.set_at(self.pacman_start)

        # Salida aleatoria por fantasma y estado limpio al empezar el nivel.
        random_ghost_spawn = random.sample(self.ghost_spawns, 4)
        for ghost, spawn in zip(self.ghosts.values(), random_ghost_spawn):
            ghost.pos.set_at(spawn)
            ghost.spawn_pos.set_at(spawn)
            ghost._reset()
        
            # Todos los fantasmas guardan las salidas del nivel (huida por cuartos).
            ghost._ghost_spawns = self.ghost_spawns

        # limpiamos antes de colocar.
        self.pacgum.clear()
        for spawn in self.super_pacgum_spawns:
            self.pacgum.append(SuperPacGum(
                Coord(spawn), points=self.config.points_per_super_pacgum))
        for spawn in self.pacgum_spawns:
            self.pacgum.append(
                PacGum(Coord(spawn), points=self.config.points_per_pacgum))

        Entity.entity_map.clear()
        for entity in [self.player, *self.ghosts.values(), *self.pacgum]:
            entity._update_entity_map(True)

    def _push_direction(self, dir: Dir) -> None:
        """Apunta la direccion pulsada: si hay hueco se apila, si esta llena se sustituye la pendiente."""
        if dir in self.list_key:
            return
        if len(self.list_key) < 2:
            self.list_key.append(dir)
        else:
            # lista llena: la nueva tecla sustituye a la pendiente
            self.list_key[1] = dir

    def _confirm_menu_pause(self) -> None:
        """Ejecuta la opcion marcada del menu de pausa."""
        option = self._engine.menu_pause._active_item._item_type
        if option == ItemType.RESUME:
            self._pause = False
            print("Game resumed")
        elif option == ItemType.MAIN_MENU:
            self._pause = False  # aquí u a donde vamos, apreniciar todo
            self._return_to_menu = True
            print("Return to main menu")

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
                    # Barra pausa y confirma la elección
                    elif event.key == pygame.K_SPACE:
                        # self._pause = not self._pause
                        if self._pause:
                            self._confirm_menu_pause()
                        else:
                            self._pause = True
                            print("Game pause")
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        if self._pause:
                            self._engine.menu_pause._select_item(False)
                        else:
                            self._push_direction(Dir.UP)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self._push_direction(Dir.RIGHT)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        if self._pause:
                            self._engine.menu_pause._select_item(True)
                        else:
                            self._push_direction(Dir.DOWN)
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        self._push_direction(Dir.LEFT)

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
                    elif event.key == pygame.K_SPACE:
                        return menu._active_item._item_type
            pygame.display.flip()
            self._engine.window.fill((0, 0, 0, 0))

    def _level_intro(self, number: int) -> None:
        """Muestra la banda de inicio de nivel y espera SPACE para jugar.

        Pinta la escena del nivel nuevo con la banda encima y no deja
        entrar al game loop hasta que se pulse la barra espaciadora.
        """
        # escena del nivel nuevo, lo mismo que pinta _game_loop antes de arrancar
        self._engine._put_maze(self.maze)
        self._engine._put_entities()

        waiting: bool = True
        while waiting:
            dt: int = self.clock.tick(_FPS)
            self._engine._blit_elements(dt)           # escena + HUD, como en juego
            self._engine._blit_level_intro(number)  # banda encima de la escena
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    waiting = False
            pygame.display.flip()
            self._engine.window.fill((0, 0, 0, 0))

    def _highscores_loop(self) -> None:
        """Muestra la pantalla de highscores hasta pulsar SPACE.

        Misma idea que la intro de nivel: se repite el dibujo en cada
        frame y se espera la barra para volver al menú principal.
        """
        waiting: bool = True
        while waiting:
            self.clock.tick(_FPS)
            self._engine._blit_highscores_title()
            self._engine._blit_highscores_rows(HighScore.scores)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    waiting = False
            pygame.display.flip()
            self._engine.window.fill((0, 0, 0, 0))

    def _instructions_loop(self) -> None:
        """Muestra la pantalla de instrucciones hasta pulsar SPACE.

        Misma idea que la intro de nivel: se repite el dibujo y se
        espera la barra para volver al menú principal.
        """
        waiting: bool = True
        while waiting:
            self.clock.tick(_FPS)
            self._engine._blit_instructions()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    waiting = False
            pygame.display.flip()
            self._engine.window.fill((0, 0, 0, 0))

    def _game_loop(self):
        """
        TO-DO
        """

        # render de surfaces
        self._engine._update_maze(self.maze)
        # self._engine._put_background()
        self._engine._put_maze(self.maze)
        self._engine._put_entities()

        # mantiene el programa en ejecución hasta que haya un evento de cierre
        running = True
        move_timer: int = 0

        while running and not self._return_to_menu:
            dt: int = self.clock.tick(_FPS)
            self._engine._blit_elements(dt)  # blit siemrpe pinta

            if not self._pause:
                # ========PLAYER============
                # movimiento del player: un paso cada _MOVEMENT_INTERVAL ms
                move_timer += dt
                if move_timer >= _MOVEMENT_INTERVAL:
                    # resto en vez de cero, igual que la hucha de Blinky
                    move_timer -= _MOVEMENT_INTERVAL
                    if self.list_key:
                        # giro anticipado: si la pendiente ya se puede, se ejecuta al instante
                        moved: bool = False
                        if len(self.list_key) == 2:
                            try:
                                self.player._move(
                                    self.maze._bitmap, self.list_key[1])
                                self.list_key.pop(0)
                                moved = True
                            except HitWallError:
                                pass
                            # paso normal con la actual, si no acabamos de girar
                        if not moved:
                            try:
                                self.player._move(
                                    self.maze._bitmap, self.list_key[0])
                            except HitWallError:
                                # pared: cae la actual y la pendiente manda en el proximo latido
                                if len(self.list_key) == 2:
                                    self.list_key.pop(0)

                lives_before: int = self.player.lives
                self.player.resolve_tile()
                
                    #eliminar direciones guardadas si pierdes una vida
                if self.player.lives < lives_before:
                    self.list_key.clear()

                # Game over: sin vidas cortamos el bucle y run() lleva al menú, mas adelante a game over
                if self.player.lives <= 0:          # <--------------   MODIFICAR SI SE QUIERE PROBAR COSAS DEL JUEGO  a -100 por ejemplo
                    print("Game over")
                    self._return_to_menu = True
                # ========GHOST============
                for ghost in self.ghosts.values():      # movement
                    ghost._move(
                        target=self.player.pos,
                        dt=dt,
                        tile_size=self._engine.tile_size,
                        bitmap=self.maze._bitmap,
                    )
                    ghost.resolve_tile()

                # ====SUPER PACGUM====
                if Ghost.edible:
                    self._super_timer_ms += dt
                    if self._super_timer_ms >= _SUPER_PACGUM_DURATION_MS:
                        Ghost.edible = False
                        self._super_timer_ms = 0
                
                # Si perdió una vida durante este frame, borra la dirección pendiente.
                if self.player.lives < lives_before:
                    self.list_key.clear()

                # Game over: sin vidas, volvemos al menú.
                if self.player.lives <= 0:
                    print("Game over")
                    self._return_to_menu = True

            else:
                self._engine._blit_menu_pause(self._engine.menu_pause)
            
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










