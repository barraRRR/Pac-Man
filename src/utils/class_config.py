from typing import Any, Dict, List, Optional, Tuple, ClassVar
from pydantic import BaseModel, Field, ValidationError, ValidationInfo, field_validator, model_validator
import json
import re
import sys


class Level(BaseModel):
    """Un nivel del juego: dimensiones del laberinto en celdas."""
    width: int = 15
    height: int = 15

    @field_validator("width", "height", mode="before")
    @classmethod
    def acotar(cls, valor: Any, info: ValidationInfo) -> int:
        """Acota el tamaño entre 5 y 99; si no es un número, usa 15."""
        try:
            numero = int(valor)
        except (TypeError, ValueError):
            print(f"Error: invalid {info.field_name} '{valor}', using 15.",
                  file=sys.stderr)
            return 15
        acotado = max(5, min(99, numero))
        if acotado != numero:
            print(f"Error: {info.field_name} {numero} out of range, "
                  f"using {acotado}.", file=sys.stderr)
        return acotado
    

class Config(BaseModel):
    """Parámetros de configuración con valores por defecto y rangos válidos."""

    # Rangos de cada campo numérico: (mínimo, máximo, valor por defecto). None = sin límite.
    LIMITES: ClassVar[Dict[str, Tuple[Optional[int], Optional[int], int]]] = {
        "lives": (1, 9, 3),
        "pacgum": (0, None, 42),
        "points_per_pacgum": (0, None, 10),
        "points_per_super_pacgum": (0, None, 50),
        "points_per_ghost": (0, None, 200),
        "seed": (None, None, 42),
        "level_max_time": (1, None, 90),
    }

    highscore_filename: str = "highscore.csv"   # Archivo donde se guardan las puntuaciones en disco.
    level: List[Level] = Field(default_factory=lambda: [Level() for _ in range(10)])  # Lista de niveles (mínimo 10).
    lives: int = Field(default=3)       # Vidas iniciales (mínimo 1, máximo 9).
    pacgum: int = Field(default=42)       # Cantidad de bolitas normales en el mapa (mínimo 0).
    points_per_pacgum: int = Field(default=10)     # Puntos por cada bolitas y fantasma (no negativos).
    points_per_super_pacgum: int = Field(default=50)
    points_per_ghost: int = Field(default=200)
    seed: int = 42
    level_max_time: int = Field(default=90)       # Tiempo máximo por nivel en segundos (mínimo 1).

    @classmethod
    def _acoteo(cls, nombre: str, valor: Any, minimo: Any, maximo: Any, defecto: int) -> int:
        """Convierte a int y lo acota al rango; si no es número, usa el defecto."""
        try:
            numero = int(valor)
        except (TypeError, ValueError, OverflowError):
            print(f"Error: invalid '{nombre}' ({valor!r}), using {defecto}.",
                  file=sys.stderr)
            return defecto
        acotado = numero
        if minimo is not None:
            acotado = max(minimo, acotado)
        if maximo is not None:
            acotado = min(maximo, acotado)
        if acotado != numero:
            print(f"Error: '{nombre}' {numero} out of range, using {acotado}.",
                  file=sys.stderr)
        return acotado

    @model_validator(mode="before")
    @classmethod
    def acotar_rangos(cls, datos: Any) -> Any:
        """Acota los rangos válidos antes de que el modelo los valide."""
        if not isinstance(datos, dict):
            return datos
        # Trabajamos con una copia para no tocar el diccionario original
        datos = dict(datos)

        # Campos numéricos: se acotan al rango y se avisa si había que corregir
        for nombre, (minimo, maximo, defecto) in cls.LIMITES.items():
            if nombre in datos:
                datos[nombre] = cls._acoteo(nombre, datos[nombre],
                                            minimo, maximo, defecto)

        # Nombre del archivo de highscores: debe ser .csv y no solo números
        if "highscore_filename" in datos:
            nombre_archivo = datos["highscore_filename"]
            valido = (isinstance(nombre_archivo, str)
                      and nombre_archivo.endswith(".csv")
                      and len(nombre_archivo) > 4
                      and not nombre_archivo[:-4].isdigit())
            if not valido:
                print(f"Error: invalid highscore_filename "
                      f"({nombre_archivo!r}), using highscore.csv.",
                      file=sys.stderr)
                datos["highscore_filename"] = "highscore.csv"

        # El subject pide mínimo 10 niveles: los que falten se rellenan con 15x15
        niveles = datos.get("level")
        if isinstance(niveles, list) and len(niveles) < 10:
            print(f"Error: only {len(niveles)} levels found, "
                  f"filling up to 10.", file=sys.stderr)
            datos["level"] = niveles + [{} for _ in range(10 - len(niveles))]
        return datos

class JSONParser:
    """
    """
    def __init__(self, config_file_path: str) -> None:
        self._config_file_path: str = config_file_path

        with open(self._config_file_path, "r", encoding="utf-8") as file:
            self._config_raw: str = file.read()

        # Proteger read() con try-except (o hacerlo desde la llamada??
        self._config_clean: str = self.comment_remover(self._config_raw)
        self._config_dict: Dict[str, Any] = json.loads(self._config_clean)
        # Proteger json.loads() con try-except

        
    # TEAM NOTE: antes de procesar y parsear el json, le quitamos los comentarios para evitar un JSONError al cargarlo.
    @staticmethod
    def comment_remover(json_str: str) -> str:
        """
        Takes a json formt str and removes comments using regex.
        """
        # Este patrón lo vemos juntos mejor. Básicamente crea 4 grupos. El primero recoje todo lo válido y los otros son grupos que incluyen los comentarios
        pattern = r'("(?:\\.|[^"\\])*")|//.*|/\*[\s\S]*?\*/|#.*'

        # Creamos una función que recibe un objeto Match y comprobamos si hay coincidencia con el primer grupo de paréntesis
        def replacer(match: re.Match):
            if match.group(1):
                return match.group(1)
            return ""

        # Aquí re.sub() actúa como función de orden superior para ejectura replacer
        return re.sub(pattern, replacer, json_str)

    # He considerado crear este get que dejastes vacío, espero no fastidiar - jitowerr
    def get(self) -> Config:
        """Construye y devuelve el objeto Config a partir del JSON cargado.

        Si "level" falta, está vacío o no es una lista (por ejemplo el
        formato antiguo "level": 10), crea 10 niveles con el width y height
        de la raíz, o 15x15 si tampoco existen. Si aun así los niveles
        vienen mal formados, usa 10 niveles 15x15 y avisa por stderr.

        Returns:
            El Config validado, con los valores fuera de rango ya acotados.
        """
        """
        """
        # Si "level" no viene, viene vacío, o viene como un número (ej. 10),
        # lo convertimos a una lista de 10 niveles con los tamaños indicados
        # en la raíz, o con los por defecto si no hay ninguno.
        lvl = self._config_dict.get("level")
        if not isinstance(lvl, list) or not lvl:
            w = self._config_dict.get("width", 15)
            h = self._config_dict.get("height", 15)
            self._config_dict["level"] = [
                {"width": w, "height": h} for _ in range(10)
            ]

        try:
            return Config(**self._config_dict)
        except ValidationError:
            # Si algún nivel viene mal formado, lo dejamos con defectos seguros.
            print("Error: invalid level list, using default levels.",
                file=sys.stderr)
            self._config_dict["level"] = [{"width": 15, "height": 15} for _ in range(10)]
            return Config(**self._config_dict)

        
