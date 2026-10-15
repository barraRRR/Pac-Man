from src.utils.class_config import Config
from src.core.engine import Engine


class App:
    """
    """
    def __init__(self, config: Config) -> None:
        self.config = config
        self.engine = Engine()
