from pydantic import BaseModel, Field
from typing import Any, Dict
import json
import re


class Config(BaseModel):
    """
    Definir qué parámetros aceptamos
    """
    highscore_filename: str
    level: int # Confirmar que es esto
    width: int
    height: int
    lives: int
    pacgum: int
    points_per_pacgum: int
    points_per_super_pacgum: int
    points_per_ghost: int
    seed: Any
    level_max_time: int


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

    def get(self) -> Config:
        """
        """
        # proteger con try-except en la llamada
        return Config(**self._config_dict)
