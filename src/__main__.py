"""Allow launching the game with ``python -m src``."""

import sys
from src.main import main


if __name__ == "__main__":
    sys.exit(main())
