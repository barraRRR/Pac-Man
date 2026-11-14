import io
import logging
from typing import Iterator

import pytest

from src.utils.logger import logger


@pytest.fixture
def logs() -> Iterator[io.StringIO]:
    """Capture the game logger output, which does not propagate to caplog."""
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger.addHandler(handler)
    try:
        yield stream
    finally:
        logger.removeHandler(handler)
