"""Modelos y validación de la configuración del juego."""

from typing import Any, Dict, List, Optional, Tuple, ClassVar
from pydantic import (
    BaseModel,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)
import json
import re
from src.utils.logger import logger


class Level(BaseModel):
    """Un nivel del juego: dimensiones del laberinto en celdas."""

    width: int = 15
    height: int = 15

    MIN_SIZE: ClassVar[int] = 15
    MAX_SIZE: ClassVar[int] = 35

    @field_validator("width", "height", mode="before")
    @classmethod
    def acotar(cls, valor: Any, info: ValidationInfo) -> int:
        """Acota el tamaño entre los límites configurados."""
        try:
            numero = int(valor)
        except (TypeError, ValueError):
            logger.error("Error: invalid %s '%s', using 15.",
                         info.field_name, valor)
            return 15
        acotado = max(cls.MIN_SIZE, min(cls.MAX_SIZE, numero))
        if acotado != numero:
            logger.error("Error: %s %s out of range, using %s.",
                         info.field_name, numero, acotado)
        return acotado


class Config(BaseModel):
    """Parámetros de configuración con valores por defecto y rangos válidos."""

    # Cada rango contiene el mínimo, el máximo y el valor por defecto.
    LIMITES: ClassVar[Dict[str, Tuple[Optional[int], Optional[int], int]]] = {
        "lives": (1, 9, 3),
        "pacgum": (0, None, 42),
        "points_per_pacgum": (0, None, 10),
        "points_per_super_pacgum": (0, None, 50),
        "points_per_ghost": (0, None, 200),
        "seed": (None, None, 42),
        "level_max_time": (1, None, 90),
    }

    # Archivo donde se guardan las puntuaciones en disco.
    highscore_filename: str = "highscore.csv"
    # Lista de niveles (mínimo 10).
    level: List[Level] = Field(default_factory=lambda: [
                               Level() for _ in range(10)])
    lives: int = Field(default=3)       # Vidas iniciales (mínimo 1, máximo 9).
    # Cantidad de bolitas normales en el mapa (mínimo 0).
    pacgum: int = Field(default=42)
    # Puntos por cada bolitas y fantasma (no negativos).
    points_per_pacgum: int = Field(default=10)
    points_per_super_pacgum: int = Field(default=50)
    points_per_ghost: int = Field(default=200)
    seed: int = 42
    # Tiempo máximo por nivel en segundos (mínimo 1).
    level_max_time: int = Field(default=90)

    @classmethod
    def _acoteo(
        cls,
        nombre: str,
        valor: Any,
        minimo: Any,
        maximo: Any,
        defecto: int,
    ) -> int:
        """Convierte el valor a entero y lo limita al rango."""
        try:
            numero = int(valor)
        except (TypeError, ValueError, OverflowError):
            logger.error("Error: invalid '%s' (%r), using %s.",
                         nombre, valor, defecto)
            return defecto
        acotado = numero
        if minimo is not None:
            acotado = max(minimo, acotado)
        if maximo is not None:
            acotado = min(maximo, acotado)
        if acotado != numero:
            logger.error("Error: '%s' %s out of range, using %s.",
                         nombre, numero, acotado)
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
                logger.error("Error: invalid highscore_filename (%r), "
                             "using highscore.csv.", nombre_archivo)
                datos["highscore_filename"] = "highscore.csv"

        # Se completan hasta diez niveles con el tamaño predeterminado.
        niveles = datos.get("level")
        if isinstance(niveles, list) and len(niveles) < 10:
            logger.error("Error: only %s levels found, filling up to 10.",
                         len(niveles))
            datos["level"] = niveles + [{} for _ in range(10 - len(niveles))]
        return datos

    @classmethod
    def json_parser(cls, config_file_path: str) -> "Config":
        """Lee un archivo JSON (con comentarios) y construye la Config."""
        try:
            with open(config_file_path, "r", encoding="utf-8") as file:
                config_raw: str = file.read()
        except OSError:
            logger.exception("No se pudo leer la configuración: %s",
                             config_file_path)
            raise

        # El patrón conserva cadenas y elimina comentarios JSON.
        pattern = r'("(?:\\.|[^"\\])*")|//.*|/\*[\s\S]*?\*/|#.*'

        def replacer(match: re.Match[str]) -> str:
            """Conserva cadenas JSON y elimina los fragmentos de comentario."""
            if match.group(1):
                return match.group(1)
            return ""

        config_clean: str = re.sub(pattern, replacer, config_raw)
        try:
            config_dict: Dict[str, Any] = json.loads(config_clean)
        except json.JSONDecodeError:
            logger.exception("La configuración no contiene JSON válido: %s",
                             config_file_path)
            raise

        return cls(**config_dict)
