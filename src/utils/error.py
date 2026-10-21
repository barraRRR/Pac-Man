class MovementError(Exception):
    pass


class HitWallError(MovementError):
    pass


class UnreachableTileError(MovementError):
    pass
