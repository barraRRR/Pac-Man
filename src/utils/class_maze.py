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








