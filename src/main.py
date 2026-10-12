from src.utils.class_config import JSONParser, Config
import sys


def main() -> None:
    """
    """
    if len(sys.argv) != 2:
        ... # definir error

    parser = JSONParser(sys.argv[1])
    config = parser.get()


    # ——— test suite ———
    print(parser._config_clean)


if __name__ == "__main__":
    sys.exit(main())
