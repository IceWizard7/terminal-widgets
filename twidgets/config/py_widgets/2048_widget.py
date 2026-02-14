import random
import math
from twidgets.core.base import (
    Widget,
    WidgetContainer,
    Config,
    CursesWindowType,
    CursesKeys
)


class Cell:
    colors = [i for i in range(1, 18)]

    def __init__(self, number: int):
        self.number: int = number

    def get_color(self) -> int:
        power = int(math.log2(self.number))
        return self.colors[power % len(self.colors)] * 2

    def __str__(self) -> str:
        return str(self.number)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Cell):
            return NotImplemented
        return self.number == other.number

    @classmethod
    def random_value(cls) -> Cell:
        random_value: int = random.choices([2, 4], weights=[90, 10])[0]
        return Cell(random_value)


class Board:
    def __init__(self) -> None:
        self.width: int = 4
        self.height: int = 4

        self.cells: list[list[Cell | None]] = [
            [
                None for _ in range(self.width)
            ] for _ in range(self.height)
        ]

    def _get_free_positions(self) -> list[tuple[int, int]]:
        free_positions: list[tuple[int, int]] = [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if self.cells[y][x] is None
        ]
        return free_positions

    def spawn_random_tile(self) -> None:
        free_positions: list[tuple[int, int]] = self._get_free_positions()
        if not free_positions:
            return
        random_position: tuple[int, int] = random.choice(free_positions)
        random_cell: Cell = Cell.random_value()
        self._set_cell_at_position(random_position, random_cell)

    def _set_cell_at_position(self, position: tuple[int, int], cell: Cell) -> None:
        x: int = position[0]
        y: int = position[1]
        self.cells[y][x] = cell

    # After calling this, you are always moving "to the left"
    def _get_lines(self, direction: int) -> list[list[Cell | None]]:
        lines: list[list[Cell | None]] = []

        if direction == CursesKeys.LEFT:
            for y in range(self.height):
                lines.append(self.cells[y][:])  # [:] creates a shallow copy of that list

        elif direction == CursesKeys.RIGHT:
            for y in range(self.height):
                lines.append(list(reversed(self.cells[y])))

        elif direction == CursesKeys.UP:
            for x in range(self.width):
                lines.append([self.cells[y][x] for y in range(self.height)])

        elif direction == CursesKeys.DOWN:
            for x in range(self.width):
                lines.append([self.cells[y][x] for y in reversed(range(self.height))])

        return lines

    # Write lines back to the board (given lines will always be in the "moving left" perspective)
    def _set_lines(self, direction: int, lines: list[list[Cell | None]]) -> None:
        if direction == CursesKeys.LEFT:
            for y in range(self.height):
                self.cells[y] = lines[y]

        elif direction == CursesKeys.RIGHT:
            for y in range(self.height):
                self.cells[y] = list(reversed(lines[y]))

        elif direction == CursesKeys.UP:
            for x in range(self.width):
                for y in range(self.height):
                    self.cells[y][x] = lines[x][y]

        elif direction == CursesKeys.DOWN:
            for x in range(self.width):
                for y, val in enumerate(reversed(lines[x])):
                    self.cells[y][x] = val

    # Move into empty cells
    def _compress(self, direction: int) -> None:
        lines = self._get_lines(direction)
        new_lines: list[list[Cell | None]] = []

        for line in lines:
            non_empty = [cell for cell in line if cell is not None]
            new_line = non_empty + [None] * (self.width - len(non_empty))
            new_lines.append(new_line)

        self._set_lines(direction, new_lines)

    # Merge adjacent equal cells into each other
    def _merge(self, direction: int) -> None:
        lines = self._get_lines(direction)

        for line in lines:
            for i in range(len(line) - 1):
                current: Cell | None = line[i]
                next_cell: Cell | None = line[i + 1]

                if current is not None and current == next_cell:
                    current = Cell(current.number * 2)
                    line[i + 1] = None

        self._set_lines(direction, lines)

    def move(self, direction: int) -> None:
        if direction not in [CursesKeys.UP, CursesKeys.RIGHT, CursesKeys.DOWN, CursesKeys.LEFT]:
            return

        self._compress(direction)
        self._merge(direction)
        self._compress(direction)
        self.spawn_random_tile()

    def is_full(self) -> bool:
        return not self._get_free_positions()

    def init_board(self) -> None:
        self.spawn_random_tile()
        self.spawn_random_tile()

    def reset_board(self) -> None:
        self.cells = [
            [
                None for _ in range(self.width)
            ] for _ in range(self.height)
        ]
        self.init_board()


def keyboard_press_action(widget: Widget, key: int, _widget_container: WidgetContainer) -> None:
    if widget.help_mode:
        return

    board: Board = widget.internal_data['game_board']

    if key == ord('r'):
        board.reset_board()
        return

    if not board.is_full():
        board.move(key)
    return


def init(widget: Widget, _widget_container: WidgetContainer) -> None:
    board: Board = Board()
    board.init_board()
    widget.internal_data['game_board'] = board


def draw(widget: Widget, widget_container: WidgetContainer) -> None:
    widget_container.draw_widget(widget, widget.title)

    board: Board = widget.internal_data['game_board']

    max_width: int = widget.dimensions.current_width - 2

    for zero_based, row in enumerate(board.cells):
        row_num: int = zero_based + 1
        char_num: int = 1
        widget.safe_addstr(row_num, char_num, '|'[:max_width])
        char_num += 1
        for cell in row:
            if cell:
                widget.safe_addstr(
                    row_num, char_num, f' {str(cell).ljust(4)}',
                    [cell.get_color()]
                )
            else:
                widget.safe_addstr(row_num, char_num, '     ')
            widget.safe_addstr(row_num, 5 + char_num, ' |')
            char_num += 7

    if board.is_full():
        widget.safe_addstr(
            2 + len(board.cells), 1, 'You lost! Press \'r\' to restart!'[:widget.dimensions.current_width - 2]
        )


def draw_help(widget: Widget, widget_container: WidgetContainer) -> None:
    widget_container.draw_widget(widget)

    widget.add_widget_content(
        [
            f'Help page ({widget.name} widget)',
            '',
            'Keybinds: ',
            'Arrow keys - Move tiles',
            'r - Reset board',
            '',
            'Play 2048.'
        ]
    )


def build(stdscr: CursesWindowType, config: Config) -> Widget:
    return Widget(
        config.name, config.title, config, draw, config.interval, config.dimensions, stdscr,
        update_func=None,
        mouse_click_func=None,
        keyboard_func=keyboard_press_action,
        init_func=init,
        help_func=draw_help
    )
