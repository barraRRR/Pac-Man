import base64
import csv
import string
import sys
from pathlib import Path
import time


class HighScore:
    """Sistema de puntuaciones del juego.

    Valida registros con las reglas del subject, ofusca el archivo
    (XOR con contraseña + base64) y lo lee y lo escribe. El Top 10 y
    el registro de puntuaciones llegan en #47.
    """

    # Carpeta donde vive el archivo de puntuaciones, en la raíz.
    SCORES_FOLDER = "highscore"

    # Longitud máxima del nombre, tal cual la pide el subject.
    MAX_NAME_LENGTH = 10

    # Caracteres permitidos en el nombre: letras ASCII, dígitos y espacio.
    VALID_CHARACTERS = string.ascii_letters + string.digits + " "

    # Contraseña de ofuscación del archivo, acordada en equipo.
    PASSWORD = "jajajaja"

    scores: list[dict[str, str | int]] = []

    # Reintentos al guardar: intentos totales y segundos de espera
    # entre intento e intento.
    SAVE_ATTEMPTS = 3
    RETRY_SECONDS = 1

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

    @classmethod
    def _xor(cls, data: bytes) -> bytes:
        """Aplica (o deshace) el XOR con la contraseña como clave repetida.

        El XOR es su propio inverso: aplicarlo dos veces devuelve el
        original, así que un único método sirve para codificar y para
        decodificar.
        """
        key = cls.PASSWORD.encode("utf-8")
        return bytes(
            byte ^ key[index % len(key)]
            for index, byte in enumerate(data)
        )

    @classmethod
    def _encode(cls, text: str) -> str:
        """Ofusca un texto: UTF-8, XOR con la contraseña y base64."""
        encrypter: bytes = cls._xor(text.encode("utf-8"))
        return base64.b64encode(encrypter).decode("ascii")

    @classmethod
    def _decode(cls, encoded: str) -> str | None:
        """Deshace la ofuscación; devuelve None si el texto está dañado.

        None significa que el contenido no es base64 válido o que al
        quitar la ofuscación no se recupera texto UTF-8: el archivo ha
        sido manipulado o corrompido.
        """
        try:
            encrypted = base64.b64decode(
                encoded.encode("ascii"), validate=True
            )
            return cls._xor(encrypted).decode("utf-8")
        except ValueError:
            return None

    @classmethod
    def load(cls, filename: str) -> list[dict[str, str | int]]:
        """Carga el ranking desde el archivo de puntuaciones.

        El archivo lo escribe siempre save() con datos ya limpios y
        validados al registrarse, así que aquí no se revalida nada.
        Si el archivo no existe, el ranking empieza vacío. Si no se
        puede leer o decodificar, se avisa en inglés y empieza vacío:
        el archivo se regenerará en el próximo guardado.
        """

        patch: Path = Path(cls.SCORES_FOLDER) / filename
        if not patch.is_file():
            cls.scores = []
            return cls.scores
        try:
            text = cls._decode(patch.read_text(encoding="ascii"))
            if text is None:
                raise ValueError("File is corrupted or not base64.")
            rows: list[dict[str, str | int]] = []
            for row in csv.reader(text.splitlines()):
                if not row:
                    continue
                rows.append({"name": row[0], "score": int(row[1])})
        except (ValueError, IndexError, OSError):
            print(
                "Error: highscore file is damaged, "
                "starting with an empty ranking.",
                file=sys.stderr,
            )
            cls.scores = []
            return cls.scores
        cls.scores = rows
        return cls.scores

    @classmethod
    def save(cls, filename: str) -> bool:
        """Guarda el ranking en el archivo de puntuaciones.

        Construye el texto CSV con los registros en memoria y lo
        codifica. Si el disco falla (permisos, disco lleno...),
        reintenta unas cuantas veces con una cuenta atrás entre
        intentos, avisando en inglés por stderr; si agota los
        intentos, se rinde sin traceback y devuelve False: el
        ranking sobrevive en memoria y el próximo guardado volverá
        a intentarlo. Devuelve True si el archivo quedó escrito.
        """
        text = "".join(
            f"{record['name']},{record['score']}\n" for record in cls.scores)
        path = Path(cls.SCORES_FOLDER) / filename
        for attempt in range(1, cls.SAVE_ATTEMPTS + 1):
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(cls._encode(text), encoding="ascii")
                return True
            except OSError:
                if attempt == cls.SAVE_ATTEMPTS:
                    break
                print(
                    f"Error: could not save the highscore file "
                    f"(attempt {attempt} of {cls.SAVE_ATTEMPTS}).",
                    file=sys.stderr,
                )
                for count in range(cls.SAVE_ATTEMPTS, 0, -1):
                    print(f"Retrying in {count}...", file=sys.stderr)
                    time.sleep(cls.RETRY_SECONDS)
        print(
            "Error: total failure saving the highscore. "
            "The ranking survives in memory: play again and "
            "we will try again.",
            file=sys.stderr,
        )
        return False