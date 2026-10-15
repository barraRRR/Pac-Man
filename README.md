<div align="center">

[![pacman](https://ascii.rest/banner/pacman.svg?color=f97316&speed=fast&font=tall&shadow=rounded)](https://ascii.rest/banner/)

</div>


```
.
├── .gitignore                         # Files and folders that Git should ignore
├── Makefile                           # Shortcuts for installing, running, debugging and checking the project
├── README.md                          # Project overview, setup instructions and documentation
├── assets/
│   └── .gitkeep                       # Keeps this currently empty directory in Git
├── config.json                        # Default game configuration
├── en.subject.pdf                     # Project requirements and evaluation subject
├── pac-man.py                         # Root script used to launch the game
├── pyproject.toml                     # Project metadata and Python dependencies
├── scripts/
│   └── .gitkeep                       # Keeps this currently empty directory in Git
├── src/
│   ├── __init__.py                    # Marks src as a Python package
│   ├── __main__.py                    # Allows the application to be launched as a Python module
│   ├── core/
│   │   └── app.py                     # App class, which currently stores the game configuration
│   ├── main.py                        # Checks command-line arguments and starts the application
│   └── utils/
│       └── class_config.py            # Level and Config classes, including configuration loading and validation
├── tests/
│   └── .gitkeep                       # Keeps this currently empty directory in Git
├── uv.lock                            # Locked dependency versions for reproducible installations
└── wheels/
    └── mazegenerator-2.1.0-py3-none-any.whl  # Assigned A-Maze-ing package wheel
```
tree -I '.venv|.git'

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






# 15/10/2026 — Integración del generador: cómo se hilan Config, App y Maze

Hoy hemos cerrado el circuito completo: la configuración llega al generador
y los 10 niveles se generan de verdad por `make run`.

- `main()` solo construye `App` con la configuración y llama a `app.run()`. No sabe nada de mapas.
- `App` es la mecánica del juego: decide **cuándo** se genera cada nivel y en qué orden ocurren
  los momentos (preparar nivel, spawn de entidades, game loop, fin de partida).
- `Maze` es el adaptador: sabe **cómo** generar. Sigue siendo la única clase del proyecto que
  importa `mazegenerator`.

La cadena queda así:

```python
# main.py
app = App(config)
app.run()

# app.py — App recorre los niveles y pasa el número real de cada uno
for number, level in enumerate(self.config.level, start=1):
    self._start_level(number, level)          # -> self.maze.generate_level(...)

# class_maze.py — Maze traduce el número de nivel a semilla
semilla = self._seed if number == 1 else 0
generator_map = MazeGenerator(size=(width, height), perfect=False, seed=semilla)
```

App no sabe qué significa 0: la regla de la semilla vive solo en Maze, única fuente de verdad.


La semilla: nivel 1 fijo, resto aleatorio
Config.seed (42) se guarda como semilla base y solo se usa para el nivel 1. Del 2 en adelante se
genera con seed=0, que en el paquete significa aleatorio. Así el primer nivel es siempre el mismo
y el resto cambian en cada partida.

Comprobación hecha
Dos ejecuciones seguidas de make run, comparadas a mano: el nivel 1 sale idéntico entre
ejecuciones (misma semilla → mismo mapa) y los niveles 2-10 salen distintos entre ejecuciones y
dentro de una misma ejecución.







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

## *************ATENCIÓN*******************
Verificado contra el código fuente del .whl (lo acabo de desempaquetar y leer). Tres confirmaciones que afectan directo a maze.py:

    - El constructor genera el mapa solo: en __init__ hace self.generate(self._seed). Por eso no hay que llamar a ningún método tras crear el objeto: crear el MazeGenerator es generar el nivel.

    - maze_entry/maze_exit devuelven (x, y) = (columna, fila): el código hace return self._entryx, self._entryy, y el grid se indexa como maze[y][x]. O sea, el README de nuevo miente (dice (row, col)). Para coger la entrada sería grid[entry[1]][entry[0]]. Trampa apuntada.

    - Semilla: random.seed(seed) if seed > 0 else random.seed() — con semilla > 0 el mapa es reproducible; con 0 (o negativa), aleatorio total. Tu seed: 88 del config funcionará tal cual.






