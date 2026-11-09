"""Excepciones de movimiento propias del laberinto."""


class MovementError(Exception):
    """Error base para movimientos no válidos."""


class HitWallError(MovementError):
    """Señala que una entidad intentó avanzar contra una pared."""


class UnreachableTileError(MovementError):
    """Señala que no se puede alcanzar una casilla vecina."""
