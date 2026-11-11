"""Define regular pac-gums and the ones that activate scared mode."""

from src.utils.utils import Coord
from src.core.entity import Entity


PACGUM_COLOR = (255, 240, 200, 255)
SUPER_COLOR = (255, 240, 200, 255)


class PacGum(Entity):
    """An item that awards points when Pac-Man collects it."""

    def __init__(self, pos: Coord, points: int) -> None:
        """Create a pac-gum at ``pos`` with the specified score value."""
        super().__init__()
        self.pos.set_at(pos)
        self.color.set(PACGUM_COLOR)
        self.points: int = points


class SuperPacGum(PacGum):
    """A special pac-gum that lets Pac-Man eat ghosts temporarily."""

    def __init__(self, pos: Coord, points: int) -> None:
        """Create a super pac-gum at ``pos``."""
        super().__init__(pos, points)
        self.color.set(SUPER_COLOR)
