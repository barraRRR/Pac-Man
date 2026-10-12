from src.utils.class_config import JSONParser, Config
import sys


def main() -> int:
    """Aquí comprobamos que nos hayan pasado el archivo de configuración."""
    if len(sys.argv) != 2:
        print(
            "Error: Expected exactly one config file.\n"
            "Usage: python3 pac-man.py <config.json>",
            file=sys.stderr,
        )
        return 1

    parser = JSONParser(sys.argv[1])
    config = parser.get()

    # ——— test suite ———
    print(parser._config_clean)
    return 0


if __name__ == "__main__":
    sys.exit(main())
