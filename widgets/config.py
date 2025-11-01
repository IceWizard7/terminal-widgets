import curses


BASE_FOREGROUND: int = curses.COLOR_WHITE
CUSTOM_BACKGROUND_VALUE: tuple[int, int, int] = (121, 114, 263)  # Range 0-1000
CUSTOM_BACKGROUND_NUMBER: int = 20
BASE_PAIR_NUMBER: int = 1

PRIMARY_COLOR_NUMBER: int = 15
SECONDARY_COLOR_NUMBER: int = 13
LOADING_COLOR_NUMBER: int = 9
ERROR_COLOR_NUMBER: int = 10

TODO_SAVE_PATH: str = 'widgets/save_file.txt'
MAX_TODOS_RENDERING: int = 7

# Possibly automate this:
MINIMUM_HEIGHT: int = 30  # max(height + y)
MINIMUM_WIDTH: int = 172  # max(width + x)
