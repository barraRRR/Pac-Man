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


config.json