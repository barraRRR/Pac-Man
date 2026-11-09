from src.utils.class_config import Config, Level
from src.utils.class_maze import Maze
from src.utils.class_config import Config
from src.core.player import Player, PLAYER_DEATH_DURATION_MS
from src.core.entity import Entity
from src.core.ghost import Ghost, Blinky, Pinky, Inky, Clyde
from src.core.pacgum import PacGum, SuperPacGum
from src.core.engine import GraphicEngine, _PADDING
from src.maze.bitmap import BitMap, UP, RIGHT, DOWN, LEFT
from src.utils.utils import Coord, Color, Dir
from src.ux_ui.menu import Item, ItemType, Menu, MenuInit
from typing import List, Dict, Callable
from src.utils.error import HitWallError
import sys
import pygame
import random
from src.score.highscore import HighScore, Score, PlayerName
from src.ux_ui.instructions import Instructions
from src.utils.logger import logger
from enum import Enum


_FPS = 60
# Duracion del efecto de la super-pacgum (10 s de prueba)
_SUPER_PACGUM_DURATION_MS = 10000

_UI_SIZE = (600, 800)

# Nombre que se guarda si el jugador no escribe ninguno.
_DEFAULT_PLAYER_NAME = "PLAYER"


class AppState(Enum):
    INIT = "init"
    NEWLEVEL = "newlevel"
    RUN = "run"
    PAUSE = "pause"
    CONGRAT = "congratulations"
    GAMEOVER = "gameover"
    PLAYER_NAME = "player_name"
    HIGHSCORE = "highscore"


class App:
    """Coordina la lógica del juego y prepara el estado de cada nivel."""

    def __init__(self, config: Config) -> None:
        """Construye la App con la configuración y deja el estado vacío."""
        self.config: Config = config                                  # Configuración ya validada y acotada.
        self.maze: Maze = Maze(config.seed)
        self.pacman_start: tuple[int, int] | None = None
        self.ghost_spawns: list[tuple[int, int]] = []
        self.super_pacgum_spawns: list[tuple[int, int]] = []
        self.pacgum_spawns: list[tuple[int, int]] = []
        self.current_level: int = 0
        self.lives: int = config.lives
        self.score: Score = Score()
        self.player_name: PlayerName = PlayerName()

        self.state: AppState = AppState.INIT

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
        self._death_timer_ms: int = 0
        self._death_in_progress: bool = False
        self._level_timer_ms: int = 0 #Tiempo de juego por nivel

        # HighScore: el nombre del archivo lo manda la config y el ranking
        # se carga una sola vez al arrancar (alta en #35, conexión con App).
        HighScore.filename = self.config.highscore_filename
        HighScore.security = False   # TEMPORAL: probar salida en claro
        HighScore.load()
        self._engine._set_highscore(HighScore.top())
        logger.info("Highscores loaded: %s", len(HighScore.scores))

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
        Ghost._load_scared_frames()

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
                self._return_to_menu = False
                self.state = AppState.RUN
                self.player_name.set_name("")
                self.player._reset_lives(self.config.lives)
                self.score.reset()
                self.player.invincible = False
                Ghost.edible = False
                self._super_timer_ms = 0
                for ghost in self.ghosts.values():
                    ghost._reset()
                for number, level in enumerate(self.config.level, start=1):
                    # try:
                    # Momento 1: preparar el nivel (mapa)
                    self._start_level(number, level)
                    self._spawn_entities()  # Momento 2: colocar Pac-Man y fantasmas (aún no existe)
                    if number != 1:
                        self._level_intro(number)
                    self._game_loop()      # Momento 3: mover, comer, morir (aún no existe)

                    # Último nivel superado (ganado o saltado con ESC): toca guardar el nombre.
                    if (number == len(self.config.level)
                        and self.state == AppState.RUN
                        and not self._return_to_menu
                    ):
                        if self._level_completed():
                            self._congratulations()
                        self.state = AppState.PLAYER_NAME

                    if self.state == AppState.PLAYER_NAME:
                        self._enter_player_name()
                        if self.state == AppState.HIGHSCORE:
                            self._highscores_loop()
                        self._return_to_menu = True
                        break

                    if not self._return_to_menu and self._level_completed():
                        self._congratulations()

                    if self._return_to_menu:
                        break
                else:
                    break

            elif option == ItemType.HIGHSCORES:
                self._highscores_loop()  # Pantalla Top 10: siguiente bloque
                # self._engine._blit_highscores_rows(HighScore.scores)
                
            elif option == ItemType.INSTRUCTIONS:
                self._instructions_loop()
                # pass  # Pantalla de controles y reglas: luego
        self._end_game()       # Momento 4: guardar puntuación, despedida
        return 0

    def _start_level(self, number: int, level: Level) -> None:
        """Prepara el nivel actual: genera el mapa y deja el estado listo."""
        # Genero el mapa de este nivel con el tamaño que dice la config.
        self.maze.generate_level(
            number=number,
            width=level.width,
            height=level.height,
        )
        Ghost.path_map.clear()   # mapa nuevo: caduca la cache de caminos BFS
        Coord._set_frontier(self.maze.frontier)

        self.current_level = number
        self.list_key.clear()   # nivel nuevo: sin giros pendientes del anterior
        Ghost.edible = False
        self._super_timer_ms = 0
        self._level_timer_ms = 0
        self._engine._set_time(self.remaining_seconds)
        self._pause = False
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

        level_label: str = f"Level {number:02d}"
        logger.info("[%s] Generating level", level_label)
        logger.info("[%s] Pacgum cell values: %s",
                    level_label, dict(sorted(counts.items())))
        logger.info("[%s] Pac-Man: %s", level_label, self.pacman_start)
        logger.info("[%s] Ghosts: %s", level_label, self.ghost_spawns)
        logger.info("[%s] Super-pacgums: %s",
                    level_label, self.super_pacgum_spawns)
        logger.info("[%s] Pacgums: %s placed",
                    level_label, len(self.pacgum_spawns))
        logger.info("[%s] Pacgum positions: %s",
                    level_label, self.pacgum_spawns)

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

    def _start_player_death(self) -> None:
        """
        Oculta los fantasmas mientras Pac-Man reproduce su muerte
        """
        self._death_in_progress = True
        self._death_timer_ms = 0
        for ghost in self.ghosts.values():
            ghost.alive = False
            ghost.current_corridor.clear()

    def _update_player_death(self, dt: int) -> None:
        """Reproduce la muerte y recoloca los fantasmas en sus esquinas."""
        self._death_timer_ms += dt
        if self._death_timer_ms < PLAYER_DEATH_DURATION_MS:
            return

        for ghost in self.ghosts.values():
            ghost._set_position(ghost.spawn_pos)
            ghost._reset()
        self.player.finish_death()
        self._death_timer_ms = 0
        self._death_in_progress = False

    def _push_direction(self, dir: Dir) -> None:
        """
        Apunta la direccion pulsada: si hay hueco se apila, si esta llena se sustituye la pendiente
        """
        if dir in self.list_key:
            return
        if len(self.list_key) < 2:
            self.list_key.append(dir)
        else:
            # lista llena: la nueva tecla sustituye a la pendiente
            self.list_key[1] = dir

    def _confirm_menu_pause(self) -> None:
        """
        Ejecuta la opcion marcada del menu de pausa
        """
        option = self._engine.menu_pause._active_item._item_type
        if option == ItemType.RESUME:
            self._pause = False
            self.state = AppState.RUN
            logger.info("Game resumed")
        elif option == ItemType.MAIN_MENU:
            self._pause = False  # aquí u a donde vamos, apreniciar todo
            self.state = AppState.INIT
            self._return_to_menu = True
            logger.info("Return to main menu")

    def _toggle_pause(self) -> None:
        """Pausa la partida o confirma la opción seleccionada."""
        if self._pause:
            self._confirm_menu_pause()
        else:
            self._pause = True
            self.state = AppState.PAUSE
            logger.info("Game pause")

    # ==== MODO TRUCO ====
    def _toggle_invincible(self) -> None:
        """Activa o desactiva la invencibilidad del jugador (issue #124)."""
        self.player.invincible = not self.player.invincible
        state = "ON" if self.player.invincible else "OFF"
        logger.info(f"Cheat mode - invincible: {state}")
        
    def _handle_events(
        self,
        key_dict: Dict[int, Callable[[], None]],
    ) -> bool:
        """Ejecuta la acción asociada a cada tecla pulsada."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                # ESC solo salta de nivel en partida y con el modo truco activo.
                if self.state == AppState.RUN and self.player.invincible:
                    return False
                continue

            action = key_dict.get(event.key)
            if action is not None:
                try:
                    action()
                except HitWallError:
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
            self._engine._blit_elements(dt, number)          # escena + HUD, como en juego
            self._engine._blit_level_info(title_str=f"LEVEL {number}", sub_str="Push SPACE to play")  # banda encima de la escena
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    waiting = False
            pygame.display.flip()
            self._engine.window.fill((0, 0, 0, 0))

    def _congratulations(self) -> None:
        """Muestra la banda de nivel completado y espera SPACE.

        Igual que _level_intro pero sin preparar nada: se repinta la
        escena tal como quedó al comerse la ultima pacgum.
        """
        waiting: bool = True
        while waiting:
            dt: int = self.clock.tick(_FPS)
            self._engine._blit_elements(dt, self.current_level)
            self._engine._blit_level_info(title_str="CONGRATULATIONS!", sub_str="'space'")
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    waiting = False
            pygame.display.flip()
            self._engine.window.fill((0, 0, 0, 0))

    def _enter_player_name(self) -> None:
        """Muestra la pantalla de nombre hasta confirmar o cancelar."""
        self.player_name.set_name("")
        self.state = AppState.PLAYER_NAME

        while self.state == AppState.PLAYER_NAME:
            dt: int = self.clock.tick(_FPS)
            self._engine._blit_elements(dt, self.current_level)
            self._engine._blit_level_info(
                title_str="ENTER NAME",
                sub_str=self.player_name.get_prompt(dt),
            )
            if not self._handle_events(get_keys(self)):
                self.state = AppState.INIT
                self._return_to_menu = True
                break
            pygame.display.flip()
            self._engine.window.fill((0, 0, 0, 0))

    def _finish_player_name(self) -> None:
        """Guarda la puntuación y termina la entrada del nombre.

        Si el nombre queda vacío tras limpiarlo (nada escrito o solo
        espacios), se guarda con el nombre por defecto.
        """
        name: str = self.player_name.get_name()
        if not HighScore.clean_name(name):
            name = _DEFAULT_PLAYER_NAME
        HighScore.register(name, self.score.points)
        self.state = AppState.HIGHSCORE

    def _highscores_loop(self) -> None:
        """Muestra la pantalla de highscores hasta pulsar SPACE.

        Misma idea que la intro de nivel: se repite el dibujo en cada
        frame y se espera la barra para volver al menú principal.
        """
        waiting = True
        while waiting:
            self.clock.tick(_FPS)

            self._engine.window.blit(self._engine.background, (0, 0))
            self._engine._blit_highscores_title()
            self._engine._blit_highscores_rows(HighScore.scores)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    waiting = False

            pygame.display.flip()
        self.state = AppState.INIT

    def _instructions_loop(self) -> None:
        """Muestra la pantalla de instrucciones hasta pulsar SPACE.

        Misma idea que la intro de nivel: se repite el dibujo y se
        espera la barra para volver al menú principal.
        """
        waiting: bool = True
        while waiting:
            self.clock.tick(_FPS)
            self._engine.window.blit(self._engine.background, (0, 0))
            self._engine._blit_instructions()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    waiting = False
            pygame.display.flip()

    @property
    def remaining_seconds(self) -> int:
        """Devuelve los segundos restantes del nivel, sin bajar de cero."""
        remaining_ms = max(
            0,
            self.config.level_max_time * 1000 - self._level_timer_ms
        )
        return (remaining_ms + 999) // 1000

    def _game_loop(self):
        """
        TO-DO
        """
        self._engine._update_maze(self.maze)
        self._engine._put_maze(self.maze)
        self._engine._put_entities()
        self.state = AppState.RUN

        # mantiene el programa en ejecución hasta que haya un evento de cierre
        running = True
        while running and not self._return_to_menu and not self._level_completed():
            dt: int = self.clock.tick(_FPS)

            if not self._pause and not self._death_in_progress:
                self._level_timer_ms += dt
                time_limit_ms = self.config.level_max_time * 1000

                if self._level_timer_ms >= time_limit_ms:
                    logger.info("Time limit reached - game over")
                    self.state = AppState.PLAYER_NAME
                    running = False
            self._engine._set_time(self.remaining_seconds)

            self._engine._blit_elements(dt, self.current_level)  # blit siemrpe pinta

            if self._death_in_progress:
                self._update_player_death(dt)
                if not self._death_in_progress and self.player.lives <= 0:
                    logger.info("GAME OVER")
                    self.state = AppState.PLAYER_NAME
                    running = False
            elif not self._pause:
                # ========PLAYER============
                # El reloj de Entity conserva el tiempo sobrante entre frames.
                for _ in range(self.player.movement_ticks(dt)):
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

                # Super-pacgums vivas antes de comer (#110)
                super_pacgums_before: int = sum(
                    isinstance(pacgum, SuperPacGum) and pacgum.alive
                    for pacgum in self.pacgum
                )

                self.player.resolve_tile()

                # Super-pacgums vivas despues de comer (#110)
                super_pacgums_after: int = sum(
                    isinstance(pacgum, SuperPacGum) and pacgum.alive
                    for pacgum in self.pacgum
                )

                if super_pacgums_after < super_pacgums_before:
                    # Se acaba de comer una super: el efecto vuelve a empezar
                    self._super_timer_ms = 0
                
                #eliminar direciones guardadas si pierdes una vida
                if self.player.lives < lives_before:
                    self.list_key.clear()
                    self._start_player_death()

                # ========GHOST============
                if not self._death_in_progress:
                    for ghost in self.ghosts.values():      # movement
                        ghost._move(
                            target=self.player.pos,
                            dt=dt,
                            tile_size=self._engine.tile_size,
                            bitmap=self.maze._bitmap,
                            directions=self.list_key,
                        )
                        ghost.resolve_tile()
                        if self._death_in_progress:
                            break

                # ====SUPER PACGUM====
                if Ghost.edible and not self._death_in_progress:
                    self._super_timer_ms += dt

                    # Durante los últimos 2 segundos, los fantasmas se ven blancos.
                    warning_time_ms: int = 2_000
                    Ghost.show_white = (
                        self._super_timer_ms
                        >= _SUPER_PACGUM_DURATION_MS - warning_time_ms
                    )

                    if self._super_timer_ms >= _SUPER_PACGUM_DURATION_MS:
                        Ghost.edible = False
                        Ghost.show_white = False
                        self._super_timer_ms = 0
                
                # Si perdió una vida durante este frame, borra la dirección pendiente.
                if self.player.lives < lives_before:
                    self.list_key.clear()
                    if not self._death_in_progress:
                        self._start_player_death()

                # Game over: sin vidas, volvemos al menú.
                if self.player.lives <= 0 and not self._death_in_progress:
                    self.state = AppState.PLAYER_NAME
                    running = False


            else:
                self._engine._blit_menu_pause(self._engine.menu_pause)
            
            if running:
                running = self._handle_events(get_keys(self))
            # actualiza frame
            pygame.display.flip()
            self._engine.window.fill((0, 0, 0, 0))

    def _end_game(self) -> None:
        """
        TO-DO
        """
        # cierra el programa
        pygame.quit()

    def _level_completed(self) -> bool:
        """True cuando ya no queda ninguna pacgum viva en el nivel."""
        return all(not pacgum.alive for pacgum in self.pacgum)



def get_keys(app: App) -> Dict[int, Callable[[], None]]:
    """Devuelve las acciones de teclado correspondientes a una pantalla."""
    if app.state == AppState.INIT:
        menu = app._engine.menu_init
        return {
            pygame.K_UP: lambda: menu._select_item(False),
            pygame.K_w: lambda: menu._select_item(False),
            pygame.K_DOWN: lambda: menu._select_item(True),
            pygame.K_s: lambda: menu._select_item(True),
        }

    if app.state == AppState.RUN:
        return {
            pygame.K_UP: lambda: app._push_direction(Dir.UP),
            pygame.K_w: lambda: app._push_direction(Dir.UP),
            pygame.K_RIGHT: lambda: app._push_direction(Dir.RIGHT),
            pygame.K_d: lambda: app._push_direction(Dir.RIGHT),
            pygame.K_DOWN: lambda: app._push_direction(Dir.DOWN),
            pygame.K_s: lambda: app._push_direction(Dir.DOWN),
            pygame.K_LEFT: lambda: app._push_direction(Dir.LEFT),
            pygame.K_a: lambda: app._push_direction(Dir.LEFT),
            pygame.K_SPACE: app._toggle_pause,
            pygame.K_k: app._toggle_invincible,
        }

    if app.state == AppState.PAUSE:
        menu = app._engine.menu_pause
        return {
            pygame.K_UP: lambda: menu._select_item(False),
            pygame.K_w: lambda: menu._select_item(False),
            pygame.K_DOWN: lambda: menu._select_item(True),
            pygame.K_s: lambda: menu._select_item(True),
            pygame.K_SPACE: app._toggle_pause,
        }
    
    if app.state == AppState.PLAYER_NAME:
        keys = {
            getattr(pygame, f"K_{char}"):
            lambda char=char: app.player_name.build_name(char)
            for char in "abcdefghijklmnopqrstuvwxyz0123456789"
        }
        keys[pygame.K_BACKSPACE] = app.player_name.delete_last
        keys[pygame.K_RETURN] = app._finish_player_name
        return keys

    if app.state in (
        AppState.NEWLEVEL,
        AppState.CONGRAT,
        AppState.GAMEOVER,
        AppState.HIGHSCORE,
    ):
        return {}

    raise ValueError(f"Unknown application state: {app.state}")
