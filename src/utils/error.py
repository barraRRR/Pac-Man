"""Maze-specific movement exceptions."""


class MovementError(Exception):
    """Base error for invalid movement."""


class HitWallError(MovementError):
    """Indicate that an entity tried to move into a wall."""


class UnreachableTileError(MovementError):
    """Indicate that a neighboring tile cannot be reached."""
