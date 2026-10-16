from enum import Enum
from src.utils.utils import Coord, Color


BLINKY_COLOR = (0, 0, 0, 0)
PINKY_COLOR = (0, 0, 0, 0)
INKY_COLOR = (0, 0, 0, 0)
CLYDE_COLOR = (0, 0, 0, 0)


class GState(Enum):
    """
    """
    NORMAL = "normal"
    HUNT = "hunt"
    FLEE = "flee"
    DEAD = "dead"
    PAUSE = "pause"


class Ghost:
    """
    """
    def __init__(self, name: str) -> None:
        self.name: str = ""
        self.state: GState = GState.PAUSE
        self.pos: Coord = Coord()


class Blinky(Ghost):
    """
    Blinky (Rojo): Conocido como Shadow ("Sombra"), es el más agresivo y persigue directamente a Pac-Man.
    """
    def __init__(self) -> None:
        super().__init__(name="Blinky")
        self.color: Color = Color(BLINKY_COLOR)


class Pinky(Ghost):
    """
    Pinky (Rosa): Conocida como Speedy ("Rápida"), intenta emboscar a Pac-Man posicionándose por delante de él.
    """
    def __init__(self) -> None:
        super().__init__(name="Pinky")
        self.color: Color = Color(PINKY_COLOR)


class Inky(Ghost):
    """
    Inky (Cian / Azul claro): Conocido como Bashful ("Tímido"), tiene un comportamiento impredecible que combina las posiciones de Blinky y Pac-Man.
    """
    def __init__(self) -> None:
        super().__init__(name="Inky")
        self.color: Color = Color(INKY_COLOR)


class Clyde(Ghost):
    """
    Clyde (Naranja): Conocido como Pokey ("Lento"), persigue a Pac-Man cuando está lejos, pero se aleja a su rincón cuando se acerca demasiado.
    """
    def __init__(self) -> None:
        super().__init__(name="Clyde")
        self.color: Color = Color(CLYDE_COLOR)

