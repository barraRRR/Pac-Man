<div align="center">

[![pacman](https://ascii.rest/banner/pacman.svg?color=f97316&speed=fast&font=tall&shadow=rounded)](https://ascii.rest/banner/)

</div>


```
.
├── Makefile
├── README.md
├── assets
│   ├── seleccion fantasma y pops de pollo , su posicion de inicio.png
│   ├── visualization.png
│   └── visualization.png:Zone.Identifier
├── config.json
├── en.subject.pdf
├── pac-man.py
├── pyproject.toml
├── scripts
├── src
│   ├── __init__.py
│   ├── __main__.py
│   ├── core
│   │   └── app.py
│   ├── main.py
│   └── utils
│       ├── class_config.py
│       └── class_maze.py
├── tests
├── uv.lock
├── visualization.png:Zone.Identifier
└── wheels
    ├── mazegenerator-2.1.0-py3-none-any - copia
    │   ├── mazegenerator
    │   │   ├── __init__.py
    │   │   └── mazegenerator.py
    │   └── mazegenerator-2.1.0.dist-info
    │       ├── METADATA
    │       ├── RECORD
    │       ├── WHEEL
    │       └── top_level.txt
    └── mazegenerator-2.1.0-py3-none-any.whl
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





15/10/2026
# Generación del laberinto y colocación de entidades

> Anotaciones del proyecto — 15/10/2026

## Cómo se conectan `main`, `App` y `Maze`

La idea es que cada parte tenga una responsabilidad clara:

| Clase o función | Qué hace en esta parte del proyecto |
|---|---|
| `main()` | Carga la configuración, crea `App` y devuelve el resultado de `app.run()`. No genera ni manipula mapas. |
| `App` | Recorre los niveles definidos en la configuración y organiza la preparación de cada uno. También guarda las posiciones iniciales de las entidades. |
| `Maze` | Hace de adaptador del paquete `mazegenerator`: genera el mapa y ofrece operaciones para calcular posiciones y comprobar qué celdas son alcanzables. |

`Maze` es la única clase del proyecto que importa `mazegenerator`. `App` decide cuándo toca preparar el mapa y le pasa a `Maze` el número, el ancho y el alto del nivel.

El flujo, simplificado, es este:

```python
app = App(config)
app.run()

# App prepara los niveles en orden
for number, level in enumerate(self.config.level, start=1):
    self._start_level(number, level)

# Maze elige la semilla y crea el generador
seed = self._seed if number == 1 else 0
generator = MazeGenerator(
    size=(width, height),
    perfect=False,
    seed=seed,
)
```

Este ejemplo muestra la idea general; no es una copia literal de cada línea del proyecto.

## Generación de niveles y semilla

`App._start_level()` llama a `Maze.generate_level()` con el número y las dimensiones del nivel. `Maze` crea un `MazeGenerator` nuevo y guarda la cuadrícula generada en `self._grid`.

Para el primer nivel se utiliza la semilla recibida desde la configuración. Para los siguientes se pasa `0`, que el paquete utiliza para generar un mapa aleatorio. Así, el código solicita que el primer nivel use una semilla fija y que los demás se generen aleatoriamente. Eso no significa que todos los mapas posteriores tengan que ser distintos entre sí: podría haber coincidencias.

El parámetro `perfect=False` se pasa al generador. El resto de la lógica de este proyecto trabaja sobre el mapa que devuelve el paquete; aquí no se construye un generador propio.

## Dónde empieza Pac-Man

Después de generar el mapa, `App._start_level()` llama a `center_comecocos()` para elegir la posición inicial de Pac-Man.

El método busca la celda distinta de `15` que esté más cerca del centro de la cuadrícula. El valor `15` representa una celda cerrada en las cuatro direcciones y se evita para que Pac-Man no empiece dentro de uno de esos bloques.

La cuadrícula se consulta como `grid[y][x]`: primero la fila (`y`) y luego la columna (`x`). Las posiciones que guardamos, en cambio, se expresan como `(x, y)`. Es importante no intercambiar esos dos órdenes.

## Zonas de las esquinas

Para colocar fantasmas y super-pacgums, `corner_zone_cells()` divide las esquinas del mapa en cuatro zonas. El orden siempre es:

1. Arriba a la izquierda.
2. Arriba a la derecha.
3. Abajo a la izquierda.
4. Abajo a la derecha.

El ancho de cada zona se calcula como una quinta parte del ancho del mapa, y su alto como una quinta parte de la altura. Se descartan las fracciones y se asegura un mínimo de una celda en cada dimensión.

| Tamaño del mapa | Tamaño de cada zona | Celdas por zona |
|---|---:|---:|
| 10 × 10 | 2 × 2 | 4 |
| 15 × 15 | 3 × 3 | 9 |
| 21 × 15 | 4 × 3 | 12 |
| 25 × 21 | 5 × 4 | 20 |

Las zonas se hacen mayores a medida que crece el mapa, para que haya más casillas posibles donde elegir las posiciones.

## Cómo se comprueba si una celda es alcanzable: BFS

`reachable_cells(start)` calcula qué celdas se pueden alcanzar desde una posición inicial. Para ello usa una búsqueda en anchura, conocida como BFS (*Breadth-First Search*).

La búsqueda empieza en `start` y va visitando las celdas vecinas a las que se puede llegar. Utiliza:

- Una `deque` como cola FIFO: las celdas descubiertas se añaden al final y se procesa primero la que lleva más tiempo esperando.
- Un conjunto `visited`: guarda las celdas ya descubiertas, para no procesarlas varias veces.
- Las paredes codificadas como bits: norte `1`, este `2`, sur `4` y oeste `8`.

Para moverse a una celda vecina, el método comprueba las dos caras que comparten las celdas: que no haya pared en la dirección de salida de la celda actual ni en la dirección opuesta de la celda vecina. Por ejemplo, para moverse al este, comprueba la pared este de la celda actual y la pared oeste de la siguiente.

Una celda con valor `15` tiene activados los cuatro bits de pared. Por eso no se puede entrar en ella desde una celda vecina siguiendo las reglas del BFS.

El método devuelve un conjunto de coordenadas `(x, y)` alcanzables. No guarda distancias ni números de oleada. Los números que aparecen en el dibujo explicativo muestran el orden aproximado en que se van descubriendo las celdas; no son un resultado que el método almacene.

## Elección de posiciones para fantasmas, super-pacgums y pacgums

App._start_level() calcula una vez las celdas alcanzables desde la posición inicial de Pac-Man y reutiliza ese resultado en las selecciones del nivel.

select_ghost_spawns(reachable) elige una celda alcanzable de cada zona de esquina para colocar los cuatro fantasmas.

select_super_pacgum_spawns(reachable, ghost_spawns) elige una celda alcanzable de cada zona de esquina para las cuatro super-pacgums. Descarta las posiciones ocupadas por los fantasmas.

select_pacgum_spawns(reachable, pacman_start, ghost_spawns, super_pacgum_spawns, requested) elige las posiciones de las pacgums normales. Solo selecciona celdas alcanzables y libres; excluye la posición de Pac-Man, las de los fantasmas y las de las super-pacgums. Las posiciones se eligen al azar y no se repiten.

## Qué pasa si no caben todas las pacgums
La cantidad solicitada se configura con pacgum. Su mínimo es 0 y no tiene un máximo fijo en la configuración, porque la cantidad que cabe depende del mapa generado.

Para calcular las posiciones posibles, el método parte de las celdas alcanzables y quita las que ya están ocupadas. Así no se basa únicamente en width × height: también tiene en cuenta las celdas no alcanzables y las posiciones de las demás entidades.

Si se solicitan más pacgums de las que caben, el programa coloca todas las que puede y escribe un mensaje de error en inglés en stderr. No se detiene ni reduce la cantidad sin avisar. El aviso lo emite Maze.select_pacgum_spawns(), que también realiza la selección.

## El BFS se calcula una vez por nivel
App._start_level() llama una vez a reachable_cells(self.pacman_start) y guarda el resultado en reachable. Después pasa ese conjunto a los métodos que necesitan comprobar qué celdas son alcanzables.

Así se evita repetir el recorrido BFS al seleccionar fantasmas, super-pacgums y pacgums normales.