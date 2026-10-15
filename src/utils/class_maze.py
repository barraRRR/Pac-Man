from mazegenerator import MazeGenerator


class Maze:
    """Adaptador del laberinto: envuelve el paquete mazegenerator.

    Es la única clase del proyecto que conoce el paquete externo.
    App decide cuándo generar cada nivel; Maze sabe cómo hacerlo.
    """

    def __init__(self, seed: int):
        """Guarda la semilla base y deja el estado vacío.

        Args:
            seed: semilla de la configuración, usada solo para el nivel 1.
        """
        self._seed = seed                  # Semilla base (solo nivel 1).
        self._grid: list = []              # Grid [fila][columna] del nivel actual ([] = sin nivel).


    def generate_level(self, number:int, width: int, height:int) -> None:
        """Genera el mapa de un nivel y guarda sus cuadrícula.

        Args:
            number: número del nivel (1 en adelante).
            width: ancho del nivel en celdas.
            height: alto del nivel en celdas.
        """
        semilla = self._seed if number == 1 else 0

        # Crear el generador ES generar el mapa (su __init__ ya llama a generate()).
        generator_map = MazeGenerator(size=(width, height), perfect=False, seed=semilla)

        self._grid = generator_map.maze #Lee el mapa ya creado contiene Una lista de listas de enteros (list[list[int]]
        # print(self._grid)
        # print('\n')
        # for row in self._grid:
        #     print(row)

    @property
    def grid(self) -> list[list[int]]:
        """Devuelve la cuadrícula del nivel actual (solo lectura)."""
        return self._grid


    def center_comecocos(self) -> tuple[int, int]:
        """
        Devuelve la celda transitable más cercana al centro, como (x, y).

        Recorre la cuadrícula y elige, entre las celdas que no son un
        bloque sólido (15), la que menos distancia tiene al centro.
        """
        height_map = len(self.grid)
        width = len(self._grid[0])
        center_x = width // 2
        center_y = height_map // 2

        best: tuple[int, int] | None = None
        best_best: int | None = None

        for y in range(height_map):
            for x in range(width):
                if self._grid[y][x] == 15: #El 15 SOn los bloques del 42
                    continue
                dist = (x - center_x) ** 2 + (y - center_y) ** 2
                if best_best is None or dist < best_best:
                    best = (x, y)
                    best_best = dist
        if best is None:
            raise ValueError("Maze has no walkable cells.")
        # print(best)
        return best


