"""Define ghost movement logic and behavior."""

from src.utils.utils import Coord, Dir
from src.core.entity import Entity, State, ANI_SPEED
from src.utils.error import UnreachableTileError
import pygame
from src.utils.logger import logger
from pygame import Surface
from src.maze.bitmap import BitMap
from typing import List, Tuple, Set, Dict
from collections import deque
import random
from pathlib import Path


BLINKY_COLOR = (223, 0, 36, 255)
PINKY_COLOR = (255, 192, 203, 255)
INKY_COLOR = (46, 109, 180, 255)
CLYDE_COLOR = (238, 70, 36, 255)

# Lower values mean faster movement.
BLINKY_SPEED = 300
PINKY_SPEED = 500
INKY_SPEED = 500
CLYDE_SPEED = 500

# ASSETS PATHS
BLINKY_ANI_PATH = "assets/animations/ghosts/blinky"
PINKY_ANI_PATH = "assets/animations/ghosts/pinky"
INKY_ANI_PATH = "assets/animations/ghosts/inky"
CLYDE_ANI_PATH = "assets/animations/ghosts/clyde"

SCARED_GHOST = "assets/animations/ghosts/scared_ghost"


class Ghost(Entity):
    """Implement paths and states shared by all ghosts."""

    path_map: Dict[
        Tuple[Tuple[int, int], Tuple[int, int]],
        List[Coord]
    ] = {}
    edible: bool = False
    RESPAWN_DURATION_MS: int = 10_000
    RESPAWN_FLASH_DURATION_MS: int = 5_000

    _frames_scared: List[Surface] = []
    _frames_flashing: List[Surface] = []

    _scaled_scared_frames: Dict[Tuple[int, int],
                                Tuple[List[Surface], List[Surface]]] = {}
    show_white: bool = False

    def __init__(self, name: str, points: int) -> None:
        """Initialize a ghost with a name and capture score."""
        super().__init__()
        self.name: str = name
        self.ani_path: str = ""
        self._timer_ms: int = 0
        self._respawn_timer_ms: int = 0
        self.points: int = points
        self.current_corridor: List[Coord] = []
        self._ghost_spawns: List[Tuple[int, int]] = []
        self._flee_spawn: Coord | None = None
        self._flee_target: Coord | None = None
        self._scared_frame_timer_ms: int = 0
        self._scared_frame_index: int = 0

    def _move(
        self,
        target: Coord,
        dt: int,
        tile_size: int,
        bitmap: BitMap,
        directions: List[Dir] | None = None,
    ) -> None:
        """Define the movement specific to each ghost type."""
        raise NotImplementedError

    @classmethod
    def _load_scared_frames(cls) -> None:
        """Load the scared ghost frames once."""
        if cls._frames_scared:
            return

        frames: List[Surface] = []
        try:
            for png in sorted(Path(SCARED_GHOST).glob("*.png")):
                frames.append(pygame.image.load(str(png)).convert_alpha())
        except (OSError, pygame.error) as error:
            logger.exception("Could not load scared ghost frames from %s: %s",
                             SCARED_GHOST, error)
            raise RuntimeError(
                f"Could not load scared ghost frames from {SCARED_GHOST}"
            ) from error

        if not frames:
            logger.warning("No scared frames found in %s", SCARED_GHOST)
            return

        cls._frames_scared = frames[0::2]
        cls._frames_flashing = frames[1::2]

    def get_frame(self, dt: int) -> Surface:
        """Return the scared ghost frame scaled to the normal size."""
        if not self.edible or not self._frames_scared:
            return super().get_frame(dt)

        if self.delta is None:
            self.delta = Dir.RIGHT

        normal_frames = self._frames.get(self.delta)
        if not normal_frames:
            return super().get_frame(dt)

        frame_size = normal_frames[0].get_size()

        if frame_size not in Ghost._scaled_scared_frames:
            blue_frames = [
                pygame.transform.scale(frame, frame_size)
                for frame in Ghost._frames_scared
            ]
            white_frames = [
                pygame.transform.scale(frame, frame_size)
                for frame in Ghost._frames_flashing
            ]
            Ghost._scaled_scared_frames[frame_size] = (
                blue_frames,
                white_frames,
            )

        blue_frames, white_frames = Ghost._scaled_scared_frames[frame_size]
        frames = (
            white_frames
            if Ghost.show_white and white_frames
            else blue_frames
        )

        self._scared_frame_timer_ms += dt
        if self._scared_frame_timer_ms >= ANI_SPEED:
            self._scared_frame_timer_ms %= ANI_SPEED
            self._scared_frame_index = (
                self._scared_frame_index + 1
            ) % len(frames)

        return frames[self._scared_frame_index]

    def _find_path(
            self,
            start: Coord,
            target: Coord,
            bitmap: BitMap
    ) -> List[Coord]:
        """Find the shortest open-tile path with breadth-first search.

        Returns:
            Coordinates from ``start`` through ``target``, including both
            endpoints. Return an empty list if they are the same tile or no
            route exists.

        Cache successful paths by their start and target coordinates so
        repeated ghost decisions can reuse the search result.
        """
        if start == target:
            return []
        cache_key = (start.get(), target.get())
        if cache_key in self.path_map:
            return self.path_map[cache_key]

        queue: deque[Coord] = deque([start])
        visited: Set[Coord] = {start}
        parent_map: Dict[Coord, Coord] = {}
        found: bool = False

        while queue:
            curr_xy: Coord = queue.popleft()

            if curr_xy == target:
                found = True
                break

            for dir in [Dir.UP, Dir.RIGHT, Dir.DOWN, Dir.LEFT]:
                if not bitmap.grid[curr_xy.y][curr_xy.x] & dir.value:
                    new_xy = Coord(curr_xy.get())
                    new_xy.step(dir)

                    if new_xy not in visited:
                        visited.add(new_xy)
                        parent_map[new_xy] = curr_xy
                        queue.append(new_xy)

        path: List[Coord] = []
        if not found:
            return []
        current: Coord = target
        while current != start:
            path.append(Coord(current.get()))
            current = parent_map[current]
        path.append(Coord(start.get()))
        path.reverse()
        self.path_map[cache_key] = path
        return path

    def _update_delta(self, step: Coord) -> None:
        """Update the direction toward the next tile."""
        try:
            self.delta = self.pos._get_delta(step)
        except UnreachableTileError:
            pass

    def _get_corridor(self, path: List[Coord]) -> None:
        """Store the path's initial straight segment and set its direction.

        The segment begins at the ghost's current tile and stops before the
        first turn. This lets the ghost follow a corridor without recalculating
        its route at every tile.
        """
        self.current_corridor.clear()
        if len(path) < 2:
            return

        corridor_direction = self.pos._get_delta(path[1])
        self.delta = corridor_direction
        self.current_corridor.append(path[0])

        for previous, step in zip(path, path[1:]):
            step_direction = previous._get_delta(step)
            if step_direction != corridor_direction:
                break
            self.current_corridor.append(step)

    def _follow_corridor(self) -> None:
        """Move to the next tile in the current corridor."""
        self._set_position(self.current_corridor[1])
        self._update_delta(self.current_corridor[1])
        self.current_corridor.pop(0)

    def _die(self) -> None:
        """Return the ghost to its spawn position."""
        self.current_corridor.clear()
        self._set_position(self.spawn_pos)
        self.alive = True

    def _update_respawn(self, dt: int) -> None:
        """Wait 10 seconds, then reactivate the ghost in its corner."""
        if self.state != State.EATEN:
            self.state = State.EATEN
            self._respawn_timer_ms = 0

        self._respawn_timer_ms += dt

        if self._respawn_timer_ms >= self.RESPAWN_DURATION_MS:
            self._respawn_timer_ms = 0
            self.state = State.NORMAL
            self._die()

    def resolve_tile(self) -> None:
        """Check whether the ghost reaches the player on their tile."""
        if not self.alive:
            return
        from src.core.player import Player
        for ent in list(Entity.entity_map.get(self.pos.get(), [])):
            if isinstance(ent, Player) and not self.edible and ent.alive:
                ent._die()

    def _reset(self) -> None:
        """Reset the ghost and its timers."""
        self.alive = True
        self._timer_ms = 0
        self.current_corridor.clear()
        self._respawn_timer_ms = 0
        self.state = State.NORMAL
        self._flee_spawn = None
        self._flee_target = None

    def _get_quadrant(
        self,
        pos: Coord,
        bitmap: BitMap,
        opposite: bool = False
    ) -> int:
        """Return a tile's quadrant or its diagonally opposite quadrant."""
        middle_x: int = len(bitmap.grid[0]) // 2
        middle_y: int = len(bitmap.grid) // 2

        is_left: bool = pos.x < middle_x
        is_top: bool = pos.y < middle_y

        if is_top and is_left:
            quadrant: int = 1                # Top-left.
        elif is_top:
            quadrant = 2                     # Top-right.
        elif is_left:
            quadrant = 4                     # Bottom-left.
        else:
            quadrant = 3                     # Bottom-right.

        if opposite:
            # Map diagonals: 1 <-> 3 and 2 <-> 4.
            quadrant = quadrant + 2 if quadrant <= 2 else quadrant - 2

        return quadrant

    def _get_opposite_spawn(
        self,
        target: Coord,
        bitmap: BitMap,
        ghost_spawns: List[Tuple[int, int]]
    ) -> Coord | None:
        """Find a ghost spawn in the quadrant opposite Pac-Man."""
        target_quadrant: int = self._get_quadrant(
            target, bitmap, opposite=True)

        for spawn_x, spawn_y in ghost_spawns:
            spawn_quadrant: int = self._get_quadrant(
                Coord((spawn_x, spawn_y)), bitmap
            )
            if spawn_quadrant == target_quadrant:
                return Coord((spawn_x, spawn_y))

        return None

    def _get_nearby_cell(self, center: Coord, bitmap: BitMap) -> Coord | None:
        """Choose a random walkable tile one to three moves from ``center``.

        Expand through open neighboring tiles, without revisiting any tile.
        Return ``None`` if ``center`` has no reachable neighbor.
        """
        candidates: List[Coord] = []
        visited: Set[Coord] = {center}
        frontier: List[Coord] = [center]

        for _ in range(3):           # Three expansion rings.
            next_frontier: List[Coord] = []
            for cell in frontier:
                for dir in [Dir.UP, Dir.RIGHT, Dir.DOWN, Dir.LEFT]:
                    if bitmap.grid[cell.y][cell.x] & dir.value:
                        continue                           # Wall in that direction.
                    neighbour: Coord = Coord(cell.get())
                    neighbour.step(dir)
                    if neighbour in visited:
                        continue
                    visited.add(neighbour)
                    candidates.append(neighbour)
                    next_frontier.append(neighbour)
            frontier = next_frontier

        if not candidates:
            return None
        return random.choice(candidates)

    def _move_superpacgum(
        self,
        target: Coord,
        dt: int,
        bitmap: BitMap
    ) -> None:
        """Flee toward the spawn diagonally opposite Pac-Man.

        Re-evaluate the opposite quadrant on each movement tick and pathfind
        toward its ghost spawn. Once there, choose a nearby tile and move
        between it and the spawn until Pac-Man changes quadrants or scared
        mode ends.
        """

        self.current_corridor.clear()

        if not self._ghost_spawns:
            return

        ticks = self.movement_ticks(dt)
        if not ticks:
            return

        for _ in range(ticks):
            flee_spawn: Coord | None = self._get_opposite_spawn(
                target, bitmap, self._ghost_spawns)

            if flee_spawn is None:
                return

            if self._flee_spawn is None or self._flee_spawn != flee_spawn:
                self._flee_spawn = flee_spawn
                self._flee_target = Coord(flee_spawn.get())

            if self._flee_target is None:
                continue
            path: List[Coord] = self._find_path(
                start=self.pos,
                target=self._flee_target,
                bitmap=bitmap
            )
            if len(path) >= 2:
                self.delta = self.pos._get_delta(path[1])
                self._set_position(path[1])
                continue

            if self._flee_target == self._flee_spawn:
                nearby: Coord | None = self._get_nearby_cell(
                    self._flee_spawn, bitmap
                )
                if nearby is not None:
                    self._flee_target = nearby
            else:
                self._flee_target = Coord(self._flee_spawn.get())


class Blinky(Ghost):
    """Red ghost that directly chases Pac-Man."""

    def __init__(self, points: int) -> None:
        """Create Blinky with its color, speed, and animations."""
        super().__init__(name="Blinky", points=points)
        self.color.set(BLINKY_COLOR)
        self.speed: int = BLINKY_SPEED
        self.set_movement_interval(self.speed)

        self.ani_path: str = BLINKY_ANI_PATH

    def _move(
        self,
        target: Coord,
        dt: int,
        tile_size: int,
        bitmap: BitMap,
        directions: List[Dir] | None = None
    ) -> None:
        """Chase Pac-Man or flee while the super pac-gum is active."""
        if not self.alive:
            self._update_respawn(dt)
            return
        if self.edible:
            self._move_superpacgum(target, dt, bitmap)
            return
        for _ in range(self.movement_ticks(dt)):
            curr_target: Coord = target
            if len(self.current_corridor) >= 2:
                self._follow_corridor()

            else:
                self._get_corridor(
                    self._find_path(
                        start=self.pos,
                        target=curr_target,
                        bitmap=bitmap
                    )
                )
                if len(self.current_corridor) >= 2:
                    self._follow_corridor()


class Pinky(Ghost):
    """Pink ghost that tries to anticipate Pac-Man's path."""

    def __init__(self, points: int) -> None:
        """Create Pinky with its color, speed, and animations."""
        super().__init__(name="Pinky", points=points)
        self.color.set(PINKY_COLOR)
        self.speed: int = PINKY_SPEED
        self.ani_path: str = PINKY_ANI_PATH
        self.set_movement_interval(self.speed)

    def _move(
        self,
        target: Coord,
        dt: int,
        tile_size: int,
        bitmap: BitMap,
        directions: List[Dir] | None = None
    ) -> None:
        """Move Pinky: respawn, flee from the super pac-gum, or hunt with BFS."""
        if not self.alive:
            self._update_respawn(dt)
            return

        if self.edible:
            self._move_superpacgum(target, dt, bitmap)
            return

        for _ in range(self.movement_ticks(dt)):
            curr_target: Coord = self._predict_pinky_target(
                target, directions, bitmap
            )
            path: List[Coord] = self._find_path(
                start=self.pos,
                target=curr_target,
                bitmap=bitmap
            )
            if len(path) >= 2:
                self.delta = self.pos._get_delta(path[1])
                self._set_position(path[1])

    def _predict_pinky_target(
        self,
        target: Coord,
        directions: List[Dir] | None,
        bitmap: BitMap
    ) -> Coord:
        """Predict Pac-Man's position up to four tiles ahead.

        Follow the current queued direction and stop at a wall. If a second
        turn is queued, use it as soon as its direction is open. With no
        queued direction, return Pac-Man's current position.
        """
        # Use a copy so the prediction does not change the player's actual position.
        predicted: Coord = Coord(target.get())

        # If no data is available, chase the player directly.
        if not directions:
            return predicted

        current_direction: Dir = directions[0]
        pending_direction: Dir | None = (
            directions[1] if len(directions) == 2 else None
        )

        for _ in range(4):
            walls: int = bitmap.grid[predicted.y][predicted.x]

            # Try the second queued direction before continuing straight.
            if pending_direction is not None:
                if not walls & pending_direction.value:
                    current_direction = pending_direction
                    pending_direction = None

            # If movement in the chosen direction is blocked, stop here.
            if walls & current_direction.value:
                break

            predicted.step(current_direction)

        return predicted


class Inky(Ghost):
    """Cyan ghost that plans an ambush with Blinky."""

    def __init__(self, points: int) -> None:
        """Create Inky with its color, speed, and animations."""
        super().__init__(name="Inky", points=points)
        self.color.set(INKY_COLOR)
        self.speed: int = INKY_SPEED
        self.ani_path: str = INKY_ANI_PATH
        self.set_movement_interval(self.speed)

    def _move(
        self,
        target: Coord,
        dt: int,
        tile_size: int,
        bitmap: BitMap,
        directions: List[Dir] | None = None
    ) -> None:
        """Move Inky according to respawn, fleeing, or ambush behavior."""
        if not self.alive:
            self._update_respawn(dt)
            return

        if self.edible:
            self._move_superpacgum(target, dt, bitmap)
            return

        for _ in range(self.movement_ticks(dt)):
            curr_target: Coord = self._get_inky_target(
                target, directions, bitmap)
            path: List[Coord] = self._find_path(
                start=self.pos,
                target=curr_target,
                bitmap=bitmap
            )
            if len(path) < 2:
                path = self._find_path(
                    start=self.pos,
                    target=target,
                    bitmap=bitmap
                )
            if len(path) >= 2:
                self.delta = self.pos._get_delta(path[1])
                self._set_position(path[1])

    def _find_blinky(self) -> Coord | None:
        """Find Blinky and return a copy of its position."""
        for entities in Entity.entity_map.values():
            for ent in entities:
                if isinstance(ent, Blinky):
                    return Coord(ent.pos.get())
        return None

    def _get_pacman_ahead(
        self,
        target: Coord,
        directions: List[Dir] | None,
        bitmap: BitMap
    ) -> Coord | None:
        """Move up to two tiles or until a wall is reached."""
        if not directions:
            return None
        pac_ahead: Coord = Coord(target.get())
        current_direction: Dir = directions[0]
        for _ in range(2):
            if bitmap.grid[pac_ahead.y][pac_ahead.x] & current_direction.value:
                break
            pac_ahead.step(current_direction)
        return pac_ahead

    def _get_inky_target(
        self,
        target: Coord,
        directions: List[Dir] | None,
        bitmap: BitMap
    ) -> Coord:
        """Calculate the ambush point from Pac-Man's position and Blinky.

        Project Pac-Man up to two tiles along the current queued direction,
        then double the vector from Blinky to that projected position. If
        Blinky or a direction is unavailable, target Pac-Man directly.
        """
        blinky_pos: Coord | None = self._find_blinky()
        pac_ahead: Coord | None = self._get_pacman_ahead(
            target, directions, bitmap
        )

        # Without a partner or a known direction, skip the pincer and chase directly.
        if blinky_pos is None or pac_ahead is None:
            return target

        # Double the vector from Blinky to the target, starting at Blinky.
        vector: Coord = pac_ahead - blinky_pos
        return blinky_pos + vector + vector


class Clyde(Ghost):
    """Orange ghost that flees to its spawn when Pac-Man is nearby."""

    def __init__(self, points: int) -> None:
        """Create Clyde with its color, speed, and animations."""
        super().__init__(name="Clyde", points=points)
        self.color.set(CLYDE_COLOR)
        self.speed: int = CLYDE_SPEED
        self.ani_path: str = CLYDE_ANI_PATH
        self.set_movement_interval(self.speed)

    def _move(
        self,
        target: Coord,
        dt: int,
        tile_size: int,
        bitmap: BitMap,
        directions: List[Dir] | None = None
    ) -> None:
        """Chase Pac-Man unless the shortest route is fewer than eight tiles.

        When that distance threshold is met, head back to Clyde's spawn.
        Eaten ghosts use the shared respawn timer, while scared ghosts use the
        shared super-pac-gum fleeing behavior.
        """
        if not self.alive:
            self._update_respawn(dt)
            return

        if self.edible:
            self._move_superpacgum(target, dt, bitmap)
            return

        for _ in range(self.movement_ticks(dt)):

            path_to_target: List[Coord] = self._find_path(
                start=self.pos,
                target=target,
                bitmap=bitmap
            )
            curr_target: Coord = (
                self.spawn_pos if self.edible or
                len(path_to_target) < 8
                else target
            )
            if len(self.current_corridor) >= 2:
                self._follow_corridor()

            else:
                path_to_target = (
                    path_to_target if curr_target == target else
                    self._find_path(
                        start=self.pos,
                        target=curr_target,
                        bitmap=bitmap
                    )
                )
                self._get_corridor(path_to_target)
                if len(self.current_corridor) >= 2:
                    self._follow_corridor()
