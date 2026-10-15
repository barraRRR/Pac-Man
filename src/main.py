from src.utils.class_config import Config
from src.core.app import App
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

    # Aquí hay try-excepts que pusiste Aitor, pero el flujo lo manejamos dentro de la clase? ya que el programa se sigue ejecutando aunque el file de config esté mal. Si el path es incorrecto podemos promptear para que el usuario decida si prefiere poner otra ruta o cargar valores por defecto.
    try:
        app = App(Config.json_parser(sys.argv[1]))
    except (OSError, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        return 1
    
    # ——— test suite ———
    # print(parser._config_clean) #Documento
    print(app.config.model_dump_json(indent=4)) #Objeto Config creado

    return app.run()





if __name__ == "__main__":
    sys.exit(main())
