<div align="center">

[![pacman](https://ascii.rest/banner/pacman.svg?color=f97316&speed=fast&font=tall&shadow=rounded)](https://ascii.rest/banner/)

</div>


```
.
├── Attract Mode & HUD Assets.png
├── ghosts
│   ├── blinky_down.gif
│   ├── blinky_intermission_3.gif
│   ├── blinky_left.gif
│   ├── blinky_right.gif
│   ├── blinky_up.gif
│   ├── clyde_down.gif
│   ├── clyde_left.gif
│   ├── clyde_right.gif
│   ├── clyde_up.gif
│   ├── inky_down.gif
│   ├── inky_left.gif
│   ├── inky_right.gif
│   ├── inky_up.gif
│   ├── izike_flashing_scared_ghost.gif
│   ├── izike_scared_ghost.gif
│   ├── pinky_down.gif
│   ├── pinky_left.gif
│   ├── pinky_right.gif
│   └── pinky_up.gif
├── player
│   ├── pac-man_death_animation.gif
│   ├── pac-man_down.gif
│   ├── pac-man_intermission_#1.gif
│   ├── pac-man_left.gif
│   ├── pac-man_right.gif
│   └── pac-man_up.gif
├── seleccion fantasma y pops de pollo , su posicion de inicio.png
└── visualization.png
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




## Puntuaciones (Highscore)

La gestión de puntuaciones vive en `src/score/highscore.py`, en la clase `HighScore`. Todos sus métodos son métodos de clase: no se crea ningún objeto, se llama a las funciones directamente (`HighScore.load()`, `HighScore.save()`...).

El ranking se guarda en el atributo de clase `HighScore.scores`: una lista de registros, donde cada registro es un diccionario con `name` y `score`. Esa lista en memoria es el ranking de verdad; el archivo es su copia de respaldo.

### El archivo de puntuaciones

- Vive en la carpeta `highscore/`, en la raíz del proyecto. El nombre de la carpeta es fijo en el código y se crea solo la primera vez que se guarda.
- El nombre del archivo vendrá de `config.json` (clave `highscore_filename`, que debe acabar en `.csv`). Config ya lee y valida esa clave; cuando conectemos esta clase con el juego, App se la asignará a `HighScore.filename` al arrancar.
- El formato interno es CSV: una fila por jugador, con `nombre,puntuación`, ordenado de mayor a menor y con solo el Top 10.

El CSV "de verdad", después de descodificar, se ve así:

```text
Luna,100
Marta,70
Aitor,40
```

Pero ese contenido nunca se guarda en claro: antes pasa por la ofuscación. Si abres el archivo con un editor verás una línea de letras y números sin sentido:

```text
Kw8LTVhUWmsoBAtNW1RaazoACQwLD0ZQWlFg
```

### Cómo se codifica y se descodifica

Para guardar, el texto del CSV pasa por tres pasos:

1. Se convierte a bytes (UTF-8).
2. Se aplica XOR con una contraseña fija, guardada como constante dentro de la propia clase. La contraseña se repite como clave hasta cubrir todo el texto: cada byte se mezcla con el byte de la clave que le toca.
3. El resultado son bytes que no se pueden escribir bien en un archivo de texto, así que se convierten a base64, que sí es texto normal. Eso es lo que se escribe.

Para leer, se hace lo mismo al revés: base64 a bytes, XOR otra vez, y de ahí sale el texto del CSV.

El truco es que XOR es su propio inverso: aplicarlo dos veces devuelve el original. Por eso un único método (`_xor`) sirve para codificar y descodificar, con `_encode` y `_decode` como envoltorios.

Si el archivo no es base64 válido, o al deshacer no se recupera texto UTF-8, `_decode` devuelve `None`: el archivo está dañado. Esto no es un cifrado fuerte, ni pretende serlo: es una protección ligera para que nadie edite el ranking a mano con el bloc de notas.

### Las 3 funciones

| Función | Recibe | Devuelve | Qué hace |
|---|---|---|---|
| `HighScore.load()` | Nada | La lista de registros (y la deja en `HighScore.scores`) | Lee el archivo, lo descodifica y rellena el ranking |
| `HighScore.save()` | Nada | `True` si el archivo quedó escrito; `False` si falló todo | Vuelca `HighScore.scores` al archivo |
| `HighScore.register(name, score)` | Un nombre y una puntuación | `True` si la puntuación entró en el Top 10; `False` si no | Limpia, valida, ordena, recorta a 10 y guarda |

#### `HighScore.load()`

- Si el archivo no existe, el ranking empieza vacío y sin ningún aviso: es lo normal la primera vez que se juega.
- Si el archivo está dañado, se escribe un aviso en inglés por stderr y el ranking empieza vacío, sin traceback. El archivo se regenerará en el próximo guardado.
- No revalida lo que lee: confía en el archivo porque el único escritor es `save()`, que guarda datos ya limpios y validados.

#### `HighScore.save()`

- Vuelca a disco lo que hay en memoria en ese momento.
- Si el disco falla (permisos, disco lleno...), lo intenta hasta 3 veces, con una cuenta atrás de 3, 2, 1 segundos entre intento e intento, avisando en inglés por stderr.
- Si agota los intentos, avisa del fallo total y devuelve `False`, sin traceback: el ranking sobrevive en memoria y el próximo guardado volverá a intentarlo.

#### `HighScore.register(name, score)`

Es el orquestador: hace todo, en este orden.

1. Limpia el nombre con las reglas de abajo. Si tras limpiar queda vacío, avisa y devuelve `False`.
2. Valida la puntuación con las reglas de abajo. Si no es válida, avisa y devuelve `False`.
3. Si el Top 10 está lleno, solo entra una puntuación estrictamente mayor que la última. Un empate no desplaza a quien llegó antes, y una puntuación menor se descarta sin tocar nada.
4. Añade el registro, ordena el ranking de mayor a menor y lo recorta a 10.
5. Llama a `save()` y devuelve `True` si el registro quedó dentro del Top 10 en memoria.

Dos detalles del ordenado: es estable, así que si dos registros empatan se conserva el orden de llegada y el nuevo se queda por detrás del anterior. Y los nombres pueden repetirse: no se quitan duplicados, porque pueden ser jugadores distintos con las mismas iniciales.

### Reglas del nombre y de la puntuación

**El nombre:**

- Máximo 10 caracteres; si tiene más, se recorta con un aviso.
- Caracteres permitidos: letras, dígitos y espacio. Cualquier otro carácter se elimina.
- Los espacios del final se quitan; los del principio se conservan, así se acordó.
- Si tras limpiar no queda nada, el registro se rechaza.

**La puntuación:**

- Un número entero mayor o igual que 0.
- `True` y `False` no valen: Python los trata como enteros y se descartan a mano.

### Nada de tracebacks

El subject lo prohíbe, y aquí se cumple: cualquier situación rara (archivo que no existe, archivo dañado, disco que falla) termina en un aviso en inglés por stderr y el juego sigue funcionando. Un fallo de disco jamás destruye el ranking en memoria.

### Conexión con el juego (pendiente)

La clase ya está terminada y probada, pero App todavía no la usa. La conexión, cuando llegue con la mecánica del juego, tiene tres puntos:

1. **Al arrancar:** `HighScore.filename = config.highscore_filename` (la clave ya existe en `config.json` y Config la valida).
2. **Una vez al inicio:** `HighScore.load()` para tener el ranking en memoria.
3. **Al terminar la partida** (momento 4, `_end_game`, que ya reserva ese paso): `HighScore.register(nombre, score)`.

Mientras tanto, la clase se puede usar de forma aislada:

```python
from src.score.highscore import HighScore

HighScore.register("Aitor", 846)   # limpia, valida, ordena y guarda
ranking = HighScore.load()          # lee el archivo y lo descodifica
```

Movimiento del jugador
El movimiento de Pac-Man se coordina desde App. _handle_events() recoge las teclas pulsadas y traduce las flechas de Pygame a las direcciones del juego (UP, RIGHT, DOWN y LEFT). En lugar de mover al jugador directamente al recibir cada evento, guarda las direcciones en list_key, un búfer de hasta dos posiciones:

La posición 0 conserva la dirección actual.
La posición 1 guarda el siguiente giro solicitado.
Si el búfer ya está lleno, una nueva tecla sustituye la dirección pendiente.
Así, Pac-Man puede continuar avanzando aunque el jugador no mantenga pulsada la tecla. El bucle de juego acumula el tiempo transcurrido entre fotogramas (dt) y, al alcanzar el intervalo de movimiento, intenta avanzar una casilla. La velocidad se controla con _MOVEMENT_INTERVAL, por separado de la frecuencia de dibujo del juego.

El bucle también comprueba la dirección pendiente. Si esa dirección no está bloqueada por una pared, Pac-Man gira y la pendiente pasa a ser la dirección actual. Si todavía no puede girar, continúa por su dirección actual. El movimiento se realiza mediante Entity._move(), que consulta el mapa y avanza la posición; si encuentra una pared, señaliza el bloqueo con HitWallError.

Finalmente, el jugador se dibuja después de actualizar su posición, de modo que cada fotograma muestra el estado más reciente.

Estado: el movimiento continuo y los giros anticipados ya funcionan en las pruebas realizadas. La velocidad se ajusta mediante _MOVEMENT_INTERVAL; si has aplicado el valor de 150 ms, Pac-Man tiene un intervalo menor que el de Blinky (200 ms) y, por tanto, puede avanzar más rápido. Queda verificar el giro de 180° y probar distintas situaciones del laberinto antes de dar por cerrada toda la lógica de movimiento.






============pausa==============1. Qué dice el subject sobre la pausa
La sección relevante, textual:

Pause Menu

Resume the game - Allows the player to return to the ongoing game.
Return to the main menu - Allows the player to exit the current game and go back to the main menu.
Y sobre teclas, esto es todo lo que hay:

"Can move in 4 directions (up, down, left, right) using arrow keys or WASD (depending on your keyboard)."

"Push SPACE to play" (pie de la imagen de ejemplo del menú principal)

El subject NO fija ninguna tecla de pausa. No aparece la palabra en todo el documento salvo en el título de esa sección. Lo que sí hace es: exigir que el menú de pausa tenga exactamente esas 2 opciones


Issue #69 — Plan de trabajo: menú de pausa
Propósito: al pulsar ESPACIO durante la partida, detener temporalmente el juego y mostrar una pantalla de pausa con el logo habitual arriba, la partida congelada detrás de un velo gris o blanco, el título PAUSE y estas dos opciones:

Resume the game
Return to the main menu



Como funciona la pausa:

App controla el estado del juego con _pause; GraphicEngine se ocupa de dibujar.
Durante la partida, ESPACIO abre la pausa. Mientras está pausada, ↑/↓ cambian la opción y ESPACIO confirma.
MenuPause reutiliza la clase Menu y ofrece Resume y Main Menu.
Resume pone _pause a False.
Main Menu pone _pause a False y activa _return_to_menu. El bucle de juego termina al ver esa señal, y run() vuelve a mostrar el menú de inicio.
Ya probaste que al elegir Main Menu se vuelve al menú inicial. Queda probar el ciclo completo y revisar qué estado debe reiniciarse al empezar otra partida, además de comprobar ESC/X y documentar las teclas.


## feat(#69): menú de pausa completo y mejoras visuales de menús

### Qué añade
- **Pausa durante la partida**: SPACE pausa y reanuda. El juego se congela
  del todo (player, fantasmas y timers quedan como están) y se muestran las
  opciones sobre la escena congelada.
- **MenuPause** (hereda de Menu, como MenuInit) con dos opciones: RESUME y
  MAIN MENU. ItemType ampliado de forma aditiva.
- **Volver al menú inicial**: al elegir MAIN MENU se descongela la pausa y se
  activa la señal `_return_to_menu`; `run()` tiene un bucle exterior que
  rompe el ciclo de niveles y vuelve al menú de inicio sin reiniciar el
  programa. Probado el ciclo completo: partida → pausa → main menu → nueva
  partida (sin arrastrar score, vidas ni teclas pendientes).
- **Confirmación unificada con SPACE** en todos los menús: `_menu_loop`
  cambia K_RETURN por K_SPACE, coherente con la pausa y con el subject
  ("Push SPACE to play").

### Mejoras visuales de los menús
- **Fuente del proyecto** `assets/font/font_emulogic.ttf` en las opciones de
  pausa: `Item._render_item` y `Menu._render_item_list` aceptan ahora
  `font_path` y `size_font` opcionales; sin argumentos siguen usando la
  fuente del sistema, así START/QUIT no cambian por defecto.
- **Opciones centradas**: el blit usaba el centro de la ventana como esquina
  del texto; ahora se resta la mitad del ancho de cada `item.sur` (arreglado
  en `_blit_menu_init` y `_blit_menu_pause`).
- **Separación entre opciones** subida a 60 px (`_ITEM_LINE_SPACING`).
- **Panel opaco** detrás de las opciones de pausa: superficie del color del
  fondo (`_BACKGROUND_COLOR`) medida a partir del ancho de la opción más
  larga, pintada antes que los textos. Sin transparencia (solo
  Surface/fill/blit, sin SRCALPHA).

### Archivos tocados
- `src/ux_ui/menu.py` — fuente y tamaño opcionales en Item/Menu, MenuPause.
- `src/core/engine.py` — centrado, panel de pausa, spacing.
- `src/core/app.py` — pausa, confirmación, return-to-menu, SPACE en menús.

### Para comentar con el equipo
- El spacing a 60 px es global: también separa START/QUIT en el menú inicial.
- El centrado toca `_blit_menu_init` (código compartido).
- Pendiente documentar las teclas elegidas en Instructions.


Trabajo que hemos hecho en esta conversación
Intro entre niveles
Se muestra LEVEL <n> y Push SPACE to play sobre una banda de ancho completo.
Espera a que se pulse SPACE antes de empezar a jugar.
La llamada desde run() debe ser a self._level_intro(number) y solo mostrarse cuando number > 1.
Opciones del menú principal
Añadimos las cuatro opciones del subject: START GAME, VIEW HIGHSCORES, INSTRUCTIONS y EXIT.
Propusimos cambiar el despacho de run() para que solo START inicie la partida.
Importante: en la última versión comentada aquí, las ramas de Highscores e Instructions todavía tenían pass. Eso evita que lancen la partida, pero sus pantallas no están hechas todavía.
Bug #80
Reiniciar las direcciones pendientes al empezar un nivel, limpiando list_key.



Issue #88: pantalla de instrucciones con placas de teclas

- Nuevo Instructions en src/ux_ui/instructions.py: guarda el contenido
  (tecla -> funcion) y renderiza de una vez placas de teclas, textos y
  pista de salida, igual que los menus renderizan sus items.
- Engine: self.instructions en __init__ y _blit_instructions() que pega
  fondo, logo, filas placa+texto centradas y la pista "Push SPACE to go
  back"; constantes _INSTR_* de colocacion.
- App: _instructions_loop() (misma estructura que _level_intro, espera
  SPACE) y rama ItemType.INSTRUCTIONS conectada en run().
- Ajuste: _MOVEMENT_INTERVAL 150 -> 200, mas margen de reaccion en
  pasillos estrechos.
















































