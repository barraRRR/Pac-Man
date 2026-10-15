from mazegenerator import MazeGenerator
from collections import deque
import random


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
        best_dist: int | None = None

        for y in range(height_map):
            for x in range(width):
                if self._grid[y][x] == 15: #El 15 SOn los bloques del 42
                    continue
                dist = (x - center_x) ** 2 + (y - center_y) ** 2
                if best_dist is None or dist < best_dist:
                    best = (x, y)
                    best_dist = dist
        if best is None:
            raise ValueError("Maze has no walkable cells.")
        # print(best)
        return best

    # def ghost_corners(self) -> list[tuple[int, int]]:
    #     """Devuelve las cuatro esquinas del laberinto como (x, y).

    #     El orden es: arriba-izquierda, arriba-derecha,
    #     abajo-izquierda y abajo-derecha.
    #     """
    #     height = len(self._grid)
    #     width = len(self._grid[0])

    #     return [
    #         (0, 0),
    #         (width - 1, 0),
    #         (0, height - 1),
    #         (width - 1, height - 1),
    #     ]

    def select_ghost_spawns(self, start: tuple[int, int]) -> list[tuple[int, int]]:
        """Elige al azar una casilla alcanzable de cada zona de esquina.

        El orden es el mismo que corner_zone_cells: arriba-izquierda,
        arriba-derecha, abajo-izquierda y abajo-derecha.

        Args:
            start: posición del comecocos, (x, y), desde la que se
                comprueba la accesibilidad.
        """
        zones = self.corner_zone_cells()
        reachability = self.corner_zone_reachability(start)

        ghost_spawns: list[tuple[int, int]] = []

        for zone, flags in zip(zones, reachability):
            # Nos quedamos solo con las casillas con camino hasta el comecocos.
            candidates = [
                cell
                for cell, is_reachable in zip(zone, flags)
                if is_reachable
            ]

            if not candidates:
                raise ValueError("No reachable cell in a ghost corner zone.")

            ghost_spawns.append(random.choice(candidates))

        return ghost_spawns

    def reachable_cells(self, start: tuple[int, int]) -> set[tuple[int, int]]:
        """Devuelve las celdas con camino desde start, en coordenadas (x, y)."""
        if not self._grid:
            raise ValueError("Maze has not been generated.")

        height = len(self._grid)
        width = len(self._grid[0])
        start_x, start_y = start

        if not (0 <= start_x < width and 0 <= start_y < height):
            raise ValueError("Starting position is outside the maze.")

        # Celdas descubiertas, para no recorrer una celda más de una vez.
        visited = {start}

        # Celdas descubiertas que todavía tenemos que revisar.
        pending = deque([start])

        # (dx, dy, pared de salida, pared opuesta de la celda vecina)
        directions = (
            (0, -1, 1, 4),   # Arriba: N=1 y S=4
            (1, 0, 2, 8),    # Derecha: E=2 y W=8
            (0, 1, 4, 1),    # Abajo: S=4 y N=1
            (-1, 0, 8, 2),  # Izquierda: W=8 y E=2
        )

        while pending:
            x, y = pending.popleft()
            current_cell = self._grid[y][x]

            for dx, dy, wall, opposite_wall in directions:
                next_x = x + dx
                next_y = y + dy

                # Ignoramos vecinos que quedan fuera de la cuadrícula.
                if not (0 <= next_x < width and 0 <= next_y < height):
                    continue

                next_position = (next_x, next_y)

                # No repetimos celdas que ya descubrimos.
                if next_position in visited:
                    continue

                next_cell = self._grid[next_y][next_x]

                # Solo se puede pasar si no hay pared en ninguno de los dos lados.
                if current_cell & wall or next_cell & opposite_wall:
                    continue

                visited.add(next_position)
                pending.append(next_position)

        return visited

    def corner_zone_cells(self) -> list[list[tuple[int, int]]]:
        """Devuelve las casillas de las zonas de esquina en orden fijo.

        El orden de las zonas es: arriba-izquierda, arriba-derecha,
        abajo-izquierda y abajo-derecha. Dentro de cada zona, las casillas
        se recorren por filas, de izquierda a derecha.
        """
        if not self.grid:
            raise ValueError("Maze has not been generated.")

        height = len(self.grid)
        width = len(self.grid[0])

        zone_width = max(1, width // 5)
        zone_height = max(1, height // 5)

        top_left = [
            (x, y)
            for y in range(zone_height)
            for x in range(zone_width)
        ]

        top_right = [
            (x, y)
            for y in range(zone_height)
            for x in range(width - zone_width, width)
        ]

        bottom_left = [
            (x, y)
            for y in range(height - zone_height, height)
            for x in range(zone_width)
        ]

        bottom_right = [
            (x, y)
            for y in range(height - zone_height, height)
            for x in range(width - zone_width, width)
        ]

        return [top_left, top_right, bottom_left, bottom_right]


    def corner_zone_reachability(
        self,
        start: tuple[int, int],
    ) -> list[list[bool]]:
        """Indica qué casillas de cada zona son alcanzables desde start."""
        zones = self.corner_zone_cells()
        reachable = self.reachable_cells(start)

        return [
            [cell in reachable for cell in zone]
            for zone in zones
        ]

    def select_super_pacgum_spawns(
        self,
        start: tuple[int, int],
        ghost_spawns: list[tuple[int, int]],
    ) -> list[tuple[int, int]]:
        """Elige una super-pacgum alcanzable por cada zona de esquina."""
        zones = self.corner_zone_cells()
        reachability = self.corner_zone_reachability(start)
        ghost_positions = set(ghost_spawns)

        super_pacgum_spawns: list[tuple[int, int]] = []

        for zone, flags in zip(zones, reachability):
            candidates = [
                cell
                for cell, is_reachable in zip(zone, flags)
                if is_reachable and cell not in ghost_positions
            ]

            if not candidates:
                raise ValueError(
                    "No available reachable cell for a super-pacgum."
                )

            super_pacgum_spawns.append(random.choice(candidates))

        return super_pacgum_spawns

    









