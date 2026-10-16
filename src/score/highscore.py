


class HighScore:
    """Sistema de puntuaciones del juego.

    De momento solo valida un registro (nombre y puntuación) con las reglas
    del subject. La lectura/escritura del CSV y el Top 10 llegan después.
    """
    MAX_NAME_LENGTH = 10

    @classmethod
    def normalize_name(cls, name: str) -> str:
        """Deja el nombre listo para validar y guardar.

        Reglas acordadas:
        - Un tabulador de verdad son 4 espacios.
        - Un salto de línea de verdad se elimina.
        - El texto literal "\\n", "\\t", "\\\\" o comillas no se toca aquí:
          son caracteres normales y los decidirá la validación.
        - Si tras limpiar no queda nada, se devuelve "": sin nombre.
        """






























