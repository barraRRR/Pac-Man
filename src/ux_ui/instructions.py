

class Instructions:
    """Guarda el contenido de la pantalla de instrucciones."""

    _ENTRIES = {
        "ARROWS / WASD": "MOVE PAC-MAN",
        "SPACE": "PAUSE / CONFIRM",
        "UP / DOWN": "SELECT MENU OPTION",
    }

    @classmethod
    def get_entries(cls) -> tuple[tuple[str, str], ...]:
        """Devuelve las teclas y sus funciones en el orden de presentación."""
        return tuple(cls._ENTRIES.items())