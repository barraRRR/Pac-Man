from src.utils.class_config import JSONParser, Config
import json
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
    try:
        parser = JSONParser(sys.argv[1])
        config = parser.get()
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        return 1
    
    # ——— test suite ———
    print(parser._config_clean)
    return 0


if __name__ == "__main__":
    sys.exit(main())
