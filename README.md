<div align="center">

[![pacman](https://ascii.rest/banner/pacman.svg?color=f97316&speed=fast&font=tall&shadow=rounded)](https://ascii.rest/banner/)

</div>


```
pacman/
├── assets/                  # Sprites, mapas, sonidos
├── src/                     # Código fuente directo
│   ├── __init__.py
│   ├── __main__.py          # Opcional: para `python3 -m src config.json`
│   ├── main.py              # Función main() principal
│   ├── core/                # Engine, game loop, estados
│   │   ├── engine.py
│   │   └── states.py
│   ├── entities/            # Pacman, fantasmas, pellets
│   │   ├── player.py
│   │   └── ghost.py
│   ├── map/                 # Carga de mapas y grid
│   └── utils/               # Rutas, config.json parser
├── tests/                   # Batería de tests con pytest
├── pac-man.py               # Script lanzador raíz
├── config.json              # Config file
├── Makefile
└── requirements.txt
```


#config.json

¿Alguna clave del config es obligatoria?
    El subject lo deja claro: "The exact structure is up to you" (la estructura exacta depende de ti) y las claves son sugeridas ("Suggested keys (names are indicative)").
    Pero hay tres condiciones que sí son obligatorias:
        Que sean claras y las documentéis en el README.
        Que tengáis valores por defecto robustos (si falta una clave, el juego usa su valor por defecto y sigue).
        Que cualquier valor inválido o falta se acote a un valor seguro, se avise y continúe (sin traceback).

Las claves que sugiere el subject
    highscore_filename	(indicativo del nombre del archivo de récords)
    level	array de múltiples niveles
    width, height	por cada nivel
    lives	3
    pacgum	42
    points_per_pacgum	10
    points_per_super_pacgum	50
    points_per_ghost	200
    seed	42
    level_max_time	90

    El subject sugiere que level sea un array de niveles, no un único int.
        "levels": [
            {"width": 15, "height": 15},
            {"width": 17, "height": 17},
            etc...
        ]
    Y que width y height sean por cada nivel.
    Si hay escritos 10 niveles serás ganador al llegar a lso 10 niveles, el fin del juego
    Si se han puesto 10 niveles y solo se han escrito 3, dos opciones o modificar el total de niveles a 3 o complementar hasta 10 cogiendo el ancho y alto de config o default
    Si existe niveles, ancho y alto aunque estén rellenados se obvian. Si no existe niveles, se tiene en cuenta, si no se rellena ninguno de los dos, coge losd efault

    Semilla y Niveles entran en juego, es decir, el amazing habrá que iterarlo como un generador, "yield" imagino, para intentar mantener la semilla y que el mapa sea los mismos, si semilla no existe o es None, entonces es aleatorio


El generador de laberintos (A-Maze-ing)

El subject dice textualmente:
    "Maze generation based on an external 'A-Maze-ing' package (not yours!)".
    "You must not write your own generator."
    "You must use their package as-is, without modifying it."
    "Your loader must adapt to their interface, not the opposite."
    "The parameter PERFECT will be set to False to produce Pac-Man-compatible corridors (see A-Maze-ing subject)."
    "If the generator fails, you must handle the error cleanly."
    PERFECT = False