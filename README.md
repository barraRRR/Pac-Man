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


## Configuración

El juego lee sus opciones desde un archivo JSON llamado `config.json`. El archivo admite comentarios: `#`, `//` y `/* ... */`.

La estructura exacta del archivo es una decisión del proyecto. Las claves del subject son sugerencias, pero el README debe explicar qué claves acepta el juego y cuáles son sus valores por defecto.
Try:
|
highscore_filename
highscore.csv
Nombre del archivo donde se guardarán las puntuaciones. Debe terminar en .csv.
level
10 niveles de 15 × 15
Lista de niveles. Cada nivel tiene su propio width y height.
width
15
Ancho usado para crear los niveles cuando no se proporciona una lista level.
height
15
Alto usado para crear los niveles cuando no se proporciona una lista level.
lives
3
Vidas iniciales; se limita al intervalo de 1 a 9.
pacgum
42
Cantidad de pacgums.
points_per_pacgum
10
Puntos obtenidos por cada pacgum normal.
points_per_super_pacgum
50
Puntos obtenidos por cada super-pacgum.
points_per_ghost
200
Puntos obtenidos por cada fantasma comestible.
seed
42
Semilla prevista para la generación de laberintos.
level_max_time
90
Tiempo máximo de cada nivel, en segundos.
Niveles
level es una lista de niveles, no un número. Cada elemento de la lista define el ancho y el alto de un nivel:

json
Copy
{
    "level": [
        {"width": 15, "height": 15},
        {"width": 17, "height": 17}
    ]
}
Try:
|
El juego requiere un mínimo de 10 niveles. Si se proporciona una lista con menos de 10, se completa hasta llegar a 10, usando niveles de 15 × 15 para los que faltan.

Si se proporciona level, los valores de width y height de la raíz no se usan. Si no se proporciona una lista level, se crean 10 niveles usando el width y el height de la raíz; si tampoco se indican, se usa el tamaño predeterminado de 15 × 15.

Valores inválidos y claves desconocidas
La configuración tiene valores por defecto para las claves que falten. Cuando se recibe un valor numérico fuera del intervalo establecido, se limita al valor más cercano permitido; por ejemplo, un lives de 45 se ajusta a 9. Si un valor no se puede convertir al tipo esperado, se usa el valor por defecto correspondiente y se muestra un mensaje de error claro.

Las claves desconocidas se ignoran. Los errores de configuración deben gestionarse sin mostrar un traceback.

Un archivo con sintaxis JSON rota —por ejemplo, un número escrito sin comillas y con letras— no es lo mismo que una clave con un valor inválido: no se puede construir la configuración porque el JSON no llega a cargarse. En ese caso se muestra un mensaje de error; actualmente no se debe afirmar que el juego continúa con los valores por defecto.

Generación de laberintos
El subject exige usar el paquete externo A-Maze-ing asignado al proyecto:

No se debe escribir un generador propio ni modificar el paquete.
El adaptador del proyecto debe ajustarse a la interfaz del paquete.
El parámetro PERFECT debe configurarse como False.
Si el generador falla, el error debe gestionarse limpiamente.
La integración del generador y el uso efectivo de la semilla deben documentarse cuando estén implementados y comprobados. No se afirma aquí que ya estén terminados.



## Extracción del mapa - paquete mazegenerator-00001.whl
Es el paquete A-Maze-ing que exige el subject como generador de laberintos. La versión que os han dado es la 2.1.0

Qué se puede y qué no se puede hacer con él;

SI   Usarlo tal cual - el subject dice explícitamente que no está permitido escribir un generador propio y que el paquete se usa sin modificar. Vuestro cargador debe adaptarse a la interfaz de A-Maze-ing, no al revés.
SI   perfect=False - el subject ordena poner perfect a False para que salgan pasillos compatibles con Pac-Man (sin callejones sin salida donde quedes atrapado). De hecho, el propio constructor ya lo trae por defecto a False, y el método _braid() es el que elimina los callejones.
SI   Semilla - seed se puede fijar (por defecto 0 = aleatorio). El subject dice: primer nivel con semilla fija (ej. 42), siguientes niveles aleatorios.           Esto confirma una teoría, tras realizar el config el otro día propuse crear el objeto como un iterador, no se si se podrá, pero en princpio según esto el primer mapa es el mismo y el resto aleatorio, es decir llamarlo con la semilla mas un número aleatorio y listo, elprimer nivel siempre es el mismo, pero el resto de niveles los mapas aleatorios, no se si decir que está bien o que está mal, proque realmente le quitas la gracia de él videojuego no??? el ranking de puntos compite con puntos ganados de la misma manera, una aleatoriedad puede favorecer o perjudicar a otro, no? nose, puede ser un buen pequeño debate jajaja
SI   Entrada/salida - entry_cell y exit_cell configurable. Por defecto entrada (0,0) y salida (-1,-1 que se convierte a la última celda).
SI   Camino más corto - el paquete te da shortest_path (un string con N/E/S/W) de la entrada a la salida. Eso te puede servir de referencia.
No modificar el paquete - es lo que dice el subject, y además en la revisión por pares se reinstala, así que si le tocas el código se os romperá.
No generar mapa a mano - todo el mapa (muros y pasillos) sale de este generador.

El patrón "42" - el generador inserta un patrón "42" oculto en el centro del laberinto (será un bloque de celdas valladas que os puede servir de pista/punto de referencia). Si el mapa es muy pequeño no cabe y lo avisa solo.








