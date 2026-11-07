import base64
import csv
import string
import sys
from pathlib import Path
import time
from src.utils.title import Title
from src.utils.utils import make_interval_ticker


PLAYER_MAX_LEN_NAME = 10
PROMPT_INTERVAL = 300


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

    # Nombre ACTUAL del archivo de puntuaciones.
    filename: str = "highscore.csv"

    # Reintentos al guardar: intentos totales y segundos de espera
    # entre intento e intento.
    SAVE_ATTEMPTS = 3
    RETRY_SECONDS = 1

    security: bool = True

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
        """Convierte el CSV al formato de salida que pide security.

        True lo ofusca (UTF-8, XOR con la contraseña y base64); False
        lo devuelve tal cual, porque el archivo se queda en claro.
        """
        if not cls.security:
            return text

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
    def _is_encoded(cls, raw: str) -> bool:
        """Comprueba si el contenido del archivo está ofuscado.

        Se mira si el texto es base64 válido. Un CSV normal escrito
        por save() nunca lo es: lleva comas, y la coma no existe en
        el alfabeto base64.
        """
        try:
            base64.b64decode(raw.encode("ascii"), validate = True)
            return True
        except ValueError:
            return False

    @classmethod
    def load(cls) -> list[dict[str, str | int]]:
        """Carga el ranking desde el archivo de puntuaciones.

        Lee los dos formatos: si el contenido es base64 válido lo
        desofusca, y si no lo trata como CSV normal. Así security
        decide solo cómo se ESCRIBE: un archivo antiguo se sigue
        leyendo aunque el flag cambie. Si el archivo no existe, el
        ranking empieza vacío; si está dañado, se avisa en inglés
        y empieza vacío.
        """

        patch: Path = Path(cls.SCORES_FOLDER) / cls.filename
        if not patch.is_file():
            cls.scores = []
            return cls.scores
        try:
            raw: str = patch.read_text(encoding="ascii")

            # base64 válido = ofuscado; si no, CSV en claro.
            if cls._is_encoded(raw):
                text = cls._decode(raw)
                if text is None:
                    raise ValueError("File is corrupted or not base64.")
            else:
                text = raw
        
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
    def save(cls) -> bool:
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
        path = Path(cls.SCORES_FOLDER) / cls.filename
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

    @classmethod
    def register(cls, name: str, score: int) -> bool:
        """Registra una puntuación en el Top 10, si es que entra.

        Limpia el nombre y valida la puntuación; si algo falla, avisa
        en inglés por stderr y no toca nada. Con el ranking lleno,
        solo entra una puntuación estrictamente mayor que la última:
        un empate no desplaza a quien llegó antes. Si entra, se añade,
        se ordena de mayor a menor (la ordenación estable conserva el
        orden de llegada entre empates), se recorta a diez y se guarda
        el archivo.

        Devuelve True si el registro quedó dentro del Top 10 en
        memoria; si el disco falla, save() avisará por su cuenta.
        """
        clean_name = cls.clean_name(name)
        if not clean_name:
            print(
                "Error: player name cannot be empty.",
                file=sys.stderr,
            )
            return False

        if not cls.is_valid_score(score):
            print(
                "Error: score must be a non-negative integer.",
                file=sys.stderr,
            )
            return False

        if len(cls.scores) >= 10:
            lowest_score = int(cls.scores[-1]["score"])
            if score <= lowest_score:
                return False

        cls.scores.append({"name": clean_name, "score": score})
        cls.scores.sort(key=lambda record: int(record["score"]), reverse=True)
        cls.scores = cls.scores[:10]

        cls.save()
        return True


    @classmethod
    def top(cls) -> int:
        """Devuelve la mejor puntuación del ranking, o 0 si está vacío.

        El ranking siempre queda ordenado de mayor a menor, así que la
        primera fila es el récord que pinta el HUD del juego.
        """
        if not cls.scores:
            return 0
        return int(cls.scores[0]["score"])
            

class Score(Title):
    """
    Registra el score de la partida en curso
    """
    def __init__(self) -> None:
        self._points: int = 0
        super().__init__(text=str(self._points))

    def add(self, points) -> None:
        self._points += points
        self.sur = self._render(text=str(self._points))

    @property
    def points(self) -> int:
        return self._points

    def reset(self) -> None:
        """Vuelve el marcador a cero y refresca lo que se pinta en el HUD."""
        self._points = 0
        self.sur = self._render(text=str(self._points))


class PlayerName(Title):
    def __init__(self) -> None:
        super().__init__(text="")
        self._name = ""
        self.prompt = "|"
        self.timer = make_interval_ticker(PROMPT_INTERVAL)
        self.prompt_visible: bool = True
    
    def set_name(self, new: str) -> bool:
        if len(new) > PLAYER_MAX_LEN_NAME + 1:
            return False
    
        self._name = new
        self.text = new
        self.sur = self._render(text=new)
        return True
    
    def build_name(self, char: str) -> bool:
        return self.set_name(self._name + char)
    
    def delete_last(self) -> bool:
        return self.set_name(self._name[:-2])
    
    def get_name(self) -> str:
        return self._name

    def define_visible_prompt(self) -> None:
        self.prompt = "|" if self.prompt_visible else " "
    
    def get_prompt(self, dt: int) -> str:
        ticks = self.timer(dt)
        for _ in range(ticks):
            self.prompt_visible = not self.prompt_visible
            self.define_visible_prompt()
        return self._name + self.prompt







