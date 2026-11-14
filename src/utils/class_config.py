"""Models and validation for the game configuration."""

from typing import Any, Dict, List, Optional, Tuple, ClassVar
from pydantic import (
    BaseModel,
    ValidationError,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)
import json
import re
from src.utils.logger import logger


class Level(BaseModel):
    """A game level defined by the maze dimensions in tiles."""

    width: int = 15
    height: int = 15

    MIN_SIZE: ClassVar[int] = 15
    MAX_SIZE: ClassVar[int] = 35

    @field_validator("width", "height", mode="before")
    @classmethod
    def acotar(cls, valor: Any, info: ValidationInfo) -> int:
        """Clamp the size to the configured limits."""
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
    """Configuration parameters with default values and valid ranges."""

    # Each range contains the minimum, maximum, and default value.
    LIMITES: ClassVar[Dict[str, Tuple[Optional[int], Optional[int], int]]] = {
        "lives": (1, 9, 3),
        "pacgum": (0, None, 42),
        "points_per_pacgum": (0, None, 10),
        "points_per_super_pacgum": (0, None, 50),
        "points_per_ghost": (0, None, 200),
        "seed": (None, None, 42),
        "level_max_time": (1, None, 90),
    }

    # File used to store scores on disk.
    highscore_filename: str = "highscore.csv"
    # Level list (minimum of 10).
    level: List[Level] = Field(default_factory=lambda: [
                               Level() for _ in range(10)])
    lives: int = Field(default=3)       # Starting lives: 1 to 9.
    # Number of regular pac-gums in the maze (minimum 0).
    pacgum: int = Field(default=42)
    # Points per regular pac-gum, super pac-gum, and ghost (non-negative).
    points_per_pacgum: int = Field(default=10)
    points_per_super_pacgum: int = Field(default=50)
    points_per_ghost: int = Field(default=200)
    seed: int = 42
    # Maximum level duration in seconds (minimum 1).
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
        """Convert the value to an integer and clamp it to the range."""
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
        """Clamp values to valid ranges before model validation."""
        if not isinstance(datos, dict):
            return datos
        # Work on a copy to avoid modifying the original dictionary.
        datos = dict(datos)

        # Clamp numeric fields and log a warning if a value changes.
        for nombre, (minimo, maximo, defecto) in cls.LIMITES.items():
            if nombre in datos:
                datos[nombre] = cls._acoteo(nombre, datos[nombre],
                                            minimo, maximo, defecto)

        # The high-score filename must end in .csv and cannot be only digits.
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

        # Fill the list to ten levels using the default dimensions.
        niveles = datos.get("level")
        if isinstance(niveles, list) and len(niveles) < 10:
            logger.error("Error: only %s levels found, filling up to 10.",
                         len(niveles))
            datos["level"] = niveles + [{} for _ in range(10 - len(niveles))]
        return datos

    @classmethod
    def json_parser(cls, config_file_path: str) -> "Config":
        """Read a JSON file (with comments) and build a Config.

        Any problem with the file falls back to default values: the game
        keeps running and the reason is logged.
        """
        try:
            with open(config_file_path, "r", encoding="utf-8") as file:
                config_raw: str = file.read()
        except (OSError, UnicodeDecodeError) as error:
            logger.error("Could not read the configuration file %s (%s), "
                         "using default values.", config_file_path, error)
            return cls()

        # Preserve strings while removing JSON-style comments.
        pattern = r'("(?:\\.|[^"\\])*")|//.*|/\*[\s\S]*?\*/|#.*'

        def replacer(match: re.Match[str]) -> str:
            """Preserve JSON strings and remove comment fragments."""
            if match.group(1):
                return match.group(1)
            return ""

        config_clean: str = re.sub(pattern, replacer, config_raw)
        try:
            config_dict: Any = json.loads(config_clean)
        except json.JSONDecodeError as error:
            logger.error("The configuration %s is not valid JSON (%s), "
                         "using default values.", config_file_path, error)
            return cls()

        if not isinstance(config_dict, dict):
            logger.error("The configuration %s must be a JSON object, "
                         "using default values.", config_file_path)
            return cls()

        try:
            return cls(**config_dict)
        except ValidationError as error:
            bad_keys = {str(e["loc"][0]) for e in error.errors() if e["loc"]}
            logger.error("Invalid configuration values %s, using defaults "
                         "for them.", sorted(bad_keys))
            clean = {k: v for k, v in config_dict.items()
                     if k not in bad_keys}
            try:
                return cls(**clean)
            except ValidationError:
                return cls()
