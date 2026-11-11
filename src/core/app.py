"""Coordinate the game's states, levels, entities, and events."""

from src.utils.class_config import Config, Level
from src.utils.class_maze import Maze
from src.core.player import Player, PLAYER_DEATH_DURATION_MS
from src.core.entity import Entity
from src.core.ghost import Ghost, Blinky, Pinky, Inky, Clyde
from src.core.pacgum import PacGum, SuperPacGum
from src.core.engine import GraphicEngine
from src.utils.utils import Coord, Dir
from src.ux_ui.menu import ItemType, Menu
from typing import List, Dict, Callable, cast
from functools import partial
from src.utils.error import HitWallError
import pygame
import random
from src.score.highscore import HighScore, Score, PlayerName
from src.utils.logger import logger
from enum import Enum


_FPS = 60
_SUPER_PACGUM_DURATION_MS = 10000

_DEFAULT_PLAYER_NAME = "PLAYER"


class AppState(Enum):
    """Possible application states."""

    INIT = "init"
    NEWLEVEL = "newlevel"
    RUN = "run"
    PAUSE = "pause"
    CONGRAT = "congratulations"
    GAMEOVER = "gameover"
    PLAYER_NAME = "player_name"
    HIGHSCORE = "highscore"


class App:
    """Coordinate game logic and prepare each level's state."""

    def __init__(self, config: Config) -> None:
        """Build the app from the configuration with an empty game state."""
        self.config: Config = config
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

        self._engine: GraphicEngine = GraphicEngine(
            player=self.player,
            ghosts=self.ghosts,
            pacgum=self.pacgum,
            score=self.score
        )
        self.list_key: list[Dir] = []
        self._pause: bool = False
        self._return_to_menu: bool = False
        self._super_timer_ms: int = 0
        self._death_timer_ms: int = 0
        self._death_in_progress: bool = False
        self._level_timer_ms: int = 0  # Elapsed time in the current level.

        HighScore.filename = self.config.highscore_filename
        HighScore.security = False
        HighScore.load()
        self._engine._set_highscore(HighScore.top())
        logger.info("Highscores loaded: %s", len(HighScore.scores))

    @property
    def blinky(self) -> Blinky:
        """Return the Blinky instance."""
        return cast(Blinky, self.ghosts["blinky"])

    @property
    def pinky(self) -> Pinky:
        """Return the Pinky instance."""
        return cast(Pinky, self.ghosts["pinky"])

    @property
    def inky(self) -> Inky:
        """Return the Inky instance."""
        return cast(Inky, self.ghosts["inky"])

    @property
    def clyde(self) -> Clyde:
        """Return the Clyde instance."""
        return cast(Clyde, self.ghosts["clyde"])

    def run(self) -> int:
        """Run levels in order and execute each stage of the game."""
        self.clock: pygame.time.Clock = pygame.time.Clock()
        levels = [
            (level.width, level.height)
            for level in self.config.level
        ]
        self._engine.win_px = self._engine._calculate_window_size(levels)
        self._engine._init_window()
        Ghost._load_scared_frames()

        while True:
            option: ItemType = self._menu_loop(
                self._engine.menu_init,
                lambda: self._engine._blit_menu_init(
                    self._engine.menu_init
                )
            )
            if option == ItemType.QUIT:
                break
            elif option == ItemType.START:
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
                    self._start_level(number, level)
                    self._spawn_entities()
                    self._game_loop()

                    if (
                        number == len(self.config.level)
                        and self.state == AppState.RUN
                        and not self._return_to_menu
                    ):
                        if self._level_completed():
                            self._congratulations(
                                "YOU ARE THE WINNER!", "PRESS SPACE")
                        self.state = AppState.PLAYER_NAME

                    if self.state == AppState.PLAYER_NAME:
                        self._congratulations("GAME OVER", "PRESS SPACE")
                        player_name_state = self._enter_player_name()
                        if player_name_state == AppState.HIGHSCORE:
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
                self._highscores_loop()
            elif option == ItemType.INSTRUCTIONS:
                self._instructions_loop()
        self._end_game()
        return 0

    def _start_level(self, number: int, level: Level) -> None:
        """Generate the map and initialize state for a level.

        Reset per-level input and timers, then choose Pac-Man, ghost, and
        pac-gum positions. Reachable cells are calculated once and reused for
        all spawn selections.
        """
        self.maze.generate_level(
            number=number,
            width=level.width,
            height=level.height,
        )
        Ghost.path_map.clear()
        Coord._set_frontier(self.maze.frontier)

        self.current_level = number
        self.list_key.clear()
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
            reachable,
            self.pacman_start,
            self.ghost_spawns,
            self.super_pacgum_spawns,
            self.config.pacgum,
        )
        counts: dict[int, int] = {}
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
        """Place Pac-Man, the ghosts, and the level's pac-gums."""
        if self.pacman_start is None:
            raise RuntimeError("The level has not been initialized.")
        self.player.pos.set_at(self.pacman_start)
        self.player.spawn_pos.set_at(self.pacman_start)

        random_ghost_spawn = random.sample(self.ghost_spawns, 4)
        for ghost, spawn in zip(self.ghosts.values(), random_ghost_spawn):
            ghost.pos.set_at(spawn)
            ghost.spawn_pos.set_at(spawn)
            ghost._reset()
            ghost._ghost_spawns = self.ghost_spawns

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
        """Hide the ghosts while Pac-Man's death animation plays."""
        self._death_in_progress = True
        self._death_timer_ms = 0
        for ghost in self.ghosts.values():
            ghost.alive = False
            ghost.current_corridor.clear()

    def _update_player_death(self, dt: int) -> None:
        """Play the death animation and return the ghosts to their corners."""
        self._death_timer_ms += dt
        if self._death_timer_ms < PLAYER_DEATH_DURATION_MS:
            return

        if self.player.lives > 0:
            for ghost in self.ghosts.values():
                ghost._set_position(ghost.spawn_pos)
                ghost._reset()
        self.player.finish_death()
        self._death_timer_ms = 0
        self._death_in_progress = False

    def _push_direction(self, dir: Dir) -> None:
        """Queue a turn while keeping at most the current and next directions.

        Ignore a direction already in the queue. A new direction fills the
        second slot or replaces its previous value, so the latest pending
        turn is the one Pac-Man will try next.
        """
        if dir in self.list_key:
            return
        if len(self.list_key) < 2:
            self.list_key.append(dir)
        else:
            self.list_key[1] = dir

    def _confirm_menu_pause(self) -> None:
        """Apply the option selected in the pause menu."""
        active_item = self._engine.menu_pause._active_item
        if active_item is None:
            raise RuntimeError("The pause menu has no active item.")
        option = active_item._item_type
        if option == ItemType.RESUME:
            self._pause = False
            self.state = AppState.RUN
            logger.info("Game resumed")
        elif option == ItemType.MAIN_MENU:
            self._pause = False
            self.state = AppState.INIT
            self._return_to_menu = True
            logger.info("Return to main menu")

    def _toggle_pause(self) -> None:
        """Pause the game or confirm the selected option."""
        if self._pause:
            self._confirm_menu_pause()
        else:
            self._pause = True
            self.state = AppState.PAUSE
            logger.info("Game pause")

    def _toggle_invincible(self) -> None:
        """Toggle the player's invincibility."""
        self.player.invincible = not self.player.invincible
        state = "ON" if self.player.invincible else "OFF"
        logger.info(f"Cheat mode - invincible: {state}")

    def _handle_events(
        self,
        key_dict: Dict[int, Callable[[], object]],
    ) -> bool:
        """Process queued Pygame events and dispatch mapped key actions.

        Window-close events shut down Pygame and raise ``SystemExit``.
        Movement into a wall is ignored. Return ``False`` only when Escape is
        pressed during gameplay while invincibility is enabled; otherwise
        return ``True``.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._end_game()
                raise SystemExit(0)
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
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

    def _menu_loop(self, menu: Menu, func: Callable[[], None]) -> ItemType:
        """Keep the menu active until an option is confirmed or the game exits."""
        while True:
            self.clock.tick(_FPS)
            func()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return ItemType.QUIT
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        menu._select_item(False)
                    elif event.key == pygame.K_DOWN:
                        menu._select_item(True)
                    elif event.key == pygame.K_SPACE:
                        if menu._active_item is None:
                            raise RuntimeError("The menu has no active item.")
                        return menu._active_item._item_type
            pygame.display.flip()
            self._engine.window.fill((0, 0, 0, 0))

    def _level_intro(self, number: int) -> None:
        """Show the level intro banner and wait for SPACE to start.

        Draw the new level's scene with the banner and do not enter the game
        loop until the space bar is pressed.
        """
        self._engine._put_maze(self.maze)
        self._engine._put_entities()

        waiting: bool = True
        while waiting:
            dt: int = self.clock.tick(_FPS)
            self._engine._blit_elements(dt, number)
            self._engine._blit_level_info(
                title_str=f"LEVEL {number}", sub_str="Push SPACE to play"
            )
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._end_game()
                    raise SystemExit(0)
                if (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_SPACE
                ):
                    waiting = False
            pygame.display.flip()
            self._engine.window.fill((0, 0, 0, 0))

    def _congratulations(
        self,
        title_str: str = "LEVEL COMPLETE",
        sub_str: str = "PRESS SPACE FOR NEXT LEVEL",
    ) -> None:
        """Show the level-complete banner and wait for SPACE.

        Redraw the scene as it appeared when the level was completed.
        """
        waiting: bool = True
        while waiting:
            dt: int = self.clock.tick(_FPS)
            self._engine._blit_elements(dt, self.current_level)
            self._engine._blit_level_info(title_str, sub_str)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._end_game()
                    raise SystemExit(0)
                if (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_SPACE
                ):
                    waiting = False
            pygame.display.flip()
            self._engine.window.fill((0, 0, 0, 0))

    def _enter_player_name(self) -> AppState:
        """Show the name-entry screen until the player confirms or cancels."""
        self.player_name.set_name("")
        self.state = AppState.PLAYER_NAME

        while self.state == AppState.PLAYER_NAME:
            dt: int = self.clock.tick(_FPS)
            self._engine._blit_elements(dt, self.current_level)
            self._engine._blit_level_info(
                title_str="ENTER NAME",
                sub_str=self.player_name.get_prompt(dt),
                hint_str="PRESS SPACE TO SAVE YOUR SCORE",
                hint_size=8
            )
            if not self._handle_events(get_keys(self)):
                self.state = AppState.INIT
                self._return_to_menu = True
                break
            pygame.display.flip()
            self._engine.window.fill((0, 0, 0, 0))
        return self.state

    def _finish_player_name(self) -> None:
        """Save the score and finish name entry.

        If the cleaned name is empty (nothing entered or only spaces), save
        the score with the default name.
        """
        name: str = self.player_name.get_name()
        if not HighScore.clean_name(name):
            name = _DEFAULT_PLAYER_NAME
        HighScore.register(name, self.score.points)
        self.state = AppState.HIGHSCORE

    def _highscores_loop(self) -> None:
        """Show the high-score screen until SPACE is pressed.

        As with the level intro, redraw each frame and wait for SPACE to
        return to the main menu.
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
                elif (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_SPACE
                ):
                    waiting = False

            pygame.display.flip()
        self.state = AppState.INIT

    def _instructions_loop(self) -> None:
        """Show the instructions screen until SPACE is pressed.

        As with the level intro, redraw the screen and wait for SPACE to
        return to the main menu.
        """
        waiting: bool = True
        while waiting:
            self.clock.tick(_FPS)
            self._engine.window.blit(self._engine.background, (0, 0))
            self._engine._blit_instructions()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                elif (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_SPACE
                ):
                    waiting = False
            pygame.display.flip()

    @property
    def remaining_seconds(self) -> int:
        """Return remaining level time, rounded up to whole seconds.

        Clamp expired time to zero so the HUD never displays a negative
        countdown. Rounding up keeps a partially elapsed second visible.
        """
        remaining_ms = max(
            0,
            self.config.level_max_time * 1000 - self._level_timer_ms
        )
        return (remaining_ms + 999) // 1000

    def _game_loop(self) -> None:
        """Run the level until it is cleared, ended, or returned to the menu.

        Advance the level timer only during active play, update and draw each
        frame, then process player movement, pickups, ghost movement, and
        collisions. Death animations pause movement; time expiration or loss
        of all lives transitions the app to name entry.
        """
        self._engine._update_maze(self.maze)
        self._engine._put_maze(self.maze)
        self._engine._put_entities()
        self.state = AppState.RUN

        running = True
        while (
            running
            and not self._return_to_menu
            and not self._level_completed()
        ):
            dt: int = self.clock.tick(_FPS)

            if not self._pause and not self._death_in_progress:
                self._level_timer_ms += dt
                time_limit_ms = self.config.level_max_time * 1000

                if self._level_timer_ms >= time_limit_ms:
                    logger.info("Time limit reached - game over")
                    self.state = AppState.PLAYER_NAME
                    running = False
            self._engine._set_time(self.remaining_seconds)

            self._engine._blit_elements(dt, self.current_level)

            if self._death_in_progress:
                self._update_player_death(dt)
                if not self._death_in_progress and self.player.lives <= 0:
                    logger.info("GAME OVER")
                    self.state = AppState.PLAYER_NAME
                    running = False
            elif not self._pause:
                # Move Pac-Man.
                for _ in range(self.player.movement_ticks(dt)):
                    if self.list_key:
                        moved: bool = False
                        if len(self.list_key) == 2:
                            try:
                                self.player._move_in_direction(
                                    self.maze._bitmap, self.list_key[1])
                                self.list_key.pop(0)
                                moved = True
                            except HitWallError:
                                pass
                        if not moved:
                            try:
                                self.player._move_in_direction(
                                    self.maze._bitmap, self.list_key[0])
                            except HitWallError:
                                if len(self.list_key) == 2:
                                    self.list_key.pop(0)

                lives_before: int = self.player.lives

                super_pacgums_before: int = sum(
                    isinstance(pacgum, SuperPacGum) and pacgum.alive
                    for pacgum in self.pacgum
                )

                self.player.resolve_tile()

                super_pacgums_after: int = sum(
                    isinstance(pacgum, SuperPacGum) and pacgum.alive
                    for pacgum in self.pacgum
                )

                if super_pacgums_after < super_pacgums_before:
                    self._super_timer_ms = 0

                if self.player.lives < lives_before:
                    self.list_key.clear()
                    self._start_player_death()

                # Move the ghosts and resolve their collisions.
                if not self._death_in_progress:
                    for ghost in self.ghosts.values():
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

                # ==== SUPER PAC-GUM ====
                if Ghost.edible and not self._death_in_progress:
                    self._super_timer_ms += dt

                    warning_time_ms: int = 2_000
                    Ghost.show_white = (
                        self._super_timer_ms
                        >= _SUPER_PACGUM_DURATION_MS - warning_time_ms
                    )

                    if self._super_timer_ms >= _SUPER_PACGUM_DURATION_MS:
                        Ghost.edible = False
                        Ghost.show_white = False
                        self._super_timer_ms = 0

                if self.player.lives < lives_before:
                    self.list_key.clear()
                    if not self._death_in_progress:
                        self._start_player_death()

                if self.player.lives <= 0 and not self._death_in_progress:
                    self.state = AppState.PLAYER_NAME
                    running = False

            else:
                self._engine._blit_menu_pause(self._engine.menu_pause)

            if running:
                running = self._handle_events(get_keys(self))
            pygame.display.flip()
            self._engine.window.fill((0, 0, 0, 0))

    def _end_game(self) -> None:
        """Shut down Pygame."""
        pygame.quit()

    def _level_completed(self) -> bool:
        """Return True when no pac-gums remain alive in the level."""
        return all(not pacgum.alive for pacgum in self.pacgum)


def get_keys(app: App) -> Dict[int, Callable[[], object]]:
    """Return the keyboard actions for the current screen."""
    if app.state == AppState.INIT:
        menu: Menu = app._engine.menu_init
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
        keys: Dict[int, Callable[[], object]] = {}
        for char in "abcdefghijklmnopqrstuvwxyz0123456789":
            key = getattr(pygame, f"K_{char}")
            keys[key] = partial(app.player_name.build_name, char)
        keys[pygame.K_BACKSPACE] = app.player_name.delete_last
        keys[pygame.K_SPACE] = app._finish_player_name
        return keys

    if app.state in (
        AppState.NEWLEVEL,
        AppState.CONGRAT,
        AppState.GAMEOVER,
        AppState.HIGHSCORE,
    ):
        return {}

    raise ValueError(f"Unknown application state: {app.state}")
