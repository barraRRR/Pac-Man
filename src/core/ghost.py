from enum import Enum
from src.utils.utils import Coord, Color
from src.core.entity import Entity, State


BLINKY_COLOR = (223, 0, 36, 255)
PINKY_COLOR = (255, 192, 203, 255)
INKY_COLOR = (46, 109, 180, 255)
CLYDE_COLOR = (238, 70, 36, 255)


class Ghost(Entity):
    """
    """
    def __init__(self, name: str) -> None:
        super().__init__()
        self.name: str = name


class Blinky(Ghost):
    """
    Blinky (Rojo): Conocido como Shadow ("Sombra"), es el más agresivo y persigue directamente a Pac-Man.
    """
    def __init__(self) -> None:
        super().__init__(name="Blinky")
        self.color.set(BLINKY_COLOR)


class Pinky(Ghost):
    """
    Pinky (Rosa): Conocida como Speedy ("Rápida"), intenta emboscar a Pac-Man posicionándose por delante de él.
    """
    def __init__(self) -> None:
        super().__init__(name="Pinky")
        self.color.set(PINKY_COLOR)


class Inky(Ghost):
    """
    Inky (Cian / Azul claro): Conocido como Bashful ("Tímido"), tiene un comportamiento impredecible que combina las posiciones de Blinky y Pac-Man.
    """
    def __init__(self) -> None:
        super().__init__(name="Inky")
        self.color.set(INKY_COLOR)


class Clyde(Ghost):
    """
    Clyde (Naranja): Conocido como Pokey ("Lento"), persigue a Pac-Man cuando está lejos, pero se aleja a su rincón cuando se acerca demasiado.
    """
    def __init__(self) -> None:
        super().__init__(name="Clyde")
        self.color.set(CLYDE_COLOR)

