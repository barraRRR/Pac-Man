"""Configure game logging to the console and a file."""

import logging
import sys
from pathlib import Path


_LOGGER_NAME = "pac_man"
_LOG_FILE = Path(__file__).resolve().parents[2] / "temp" / "log.txt"


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Return a logger that writes to the console and ``repo/temp/log.txt``.
    """
    logger = logging.getLogger(name or _LOGGER_NAME)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    try:
        _LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
    except OSError as error:
        console_handler.handle(
            logging.LogRecord(
                logger.name,
                logging.ERROR,
                __file__,
                0,
                "No se pudo abrir el archivo de logs %s: %s",
                (_LOG_FILE, error),
                None,
            )
        )
    else:
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


logger = get_logger()
