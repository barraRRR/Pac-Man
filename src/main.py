"""Carga la configuración y arranca la aplicación."""

from src.utils.class_config import Config
from src.core.app import App
from src.utils.logger import logger
import json
import pygame
import sys


def main() -> int:
    """Aquí comprobamos que nos hayan pasado el archivo de configuración."""
    if len(sys.argv) != 2:
        logger.error(
            "Error: Expected exactly one config file.\n"
            "Usage: python3 pac-man.py <config.json>"
        )
        return 1

    try:
        app = App(Config.json_parser(sys.argv[1]))
        return app.run()
    except (OSError, FileNotFoundError, json.JSONDecodeError) as error:
        logger.exception("Error loading or initializing application: %s",
                         error)
        return 1
    except Exception:
        logger.exception("Unhandled application error")
        return 1
    except KeyboardInterrupt:
        logger.error("Forced exit")
        return 1
    finally:
        logger.info("Quiting game. See you soon!")
        pygame.quit()


if __name__ == "__main__":
    sys.exit(main())
