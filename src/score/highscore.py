import string
import sys


class HighScore:
    """Sistema de puntuaciones del juego.

    De momento solo valida un registro (nombre y puntuación) con las reglas
    del subject. La lectura/escritura del CSV y el Top 10 llegan después.
    """

    # Longitud máxima del nombre, tal cual la pide el subject.
    MAX_NAME_LENGTH = 10

    # Caracteres permitidos en el nombre: letras ASCII, dígitos y espacio.
    VALID_CHARACTERS = string.ascii_letters + string.digits + " "

    @classmethod
    def clean_name(cls, name: str) -> str:
        """Deja el nombre listo para guardar, aplicando las reglas acordadas.

        Quita los caracteres que el subject no permite: la barra de un
        "\\n" escrito a mano desaparece y la letra se queda ("\\t" entra,
        "t" sale). Solo se quitan los espacios del final; los del
        principio se conservan, así se ha acordado. Si el nombre limpio
        supera el máximo, se recorta con un aviso en inglés por stderr.
        Si tras limpiar no queda nada, devuelve "": jugador sin nombre.
        """
        characters: list[str] = []
        for char in name:
            if char in cls.VALID_CHARACTERS:
                characters.append(char)
            else:
                characters.append('')

        clean_name = "".join(characters).rstrip()

        if len(clean_name) > cls.MAX_NAME_LENGTH:
            clean_name = clean_name[:cls.MAX_NAME_LENGTH]
            print(
                "Error: name is longer than "
                f"{cls.MAX_NAME_LENGTH} characters, "
                f'keeping "{clean_name}".',
                file=sys.stderr,
            )
        return clean_name

    @classmethod
    def is_valid_score(cls, score: object) -> bool:
        """Comprueba que la puntuación sea un entero no negativo.

        Devuelve solo la respuesta sí/no: el aviso en inglés y el "saltarse
        esta puntuación" los decidirá quien llame (en #45, al cargar filas
        del CSV), igual que pasa con el nombre.
        """
        if isinstance(score, bool):
            return False
        if isinstance(score, int) and score >= 0:
            return True
        return False
