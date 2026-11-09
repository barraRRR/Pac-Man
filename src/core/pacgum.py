"""Define las pacgums normales y las que activan el modo asustado."""

from src.utils.utils import Coord
from src.core.entity import Entity


PACGUM_COLOR = (255, 240, 200, 255)
SUPER_COLOR = (255, 240, 200, 255)


class PacGum(Entity):
    """Elemento que suma puntos cuando Pac-Man lo recoge."""

    def __init__(self, pos: Coord, points: int) -> None:
        """Crea una pacgum en ``pos`` con la puntuación indicada."""
        super().__init__()
        self.pos.set_at(pos)
        self.color.set(PACGUM_COLOR)
        self.points: int = points

class SuperPacGum(PacGum):
    """Pacgum especial que permite comer fantasmas temporalmente."""

    def __init__(self, pos: Coord, points: int) -> None:
        """Crea una super-pacgum en ``pos``."""
        super().__init__(pos, points)
        self.color.set(SUPER_COLOR)
