from __future__ import annotations  # allows forward references in type hints
from pathlib import Path
import yaml
from dotenv import load_dotenv
import os
import curses
import typing
import threading


class Dimensions:
    def __init__(self, height: int, width: int, y: int, x: int) -> None:
        self.height: int = height
        self.width: int = width
        self.y: int = y
        self.x: int = x

    def formatted(self) -> list[int]:
        return [self.height, self.width, self.y, self.x]


class Widget:
    DrawFunction = typing.Callable[
                       ['Widget'], None] | typing.Callable[
        ['Widget', dict[str, typing.Any]], None] | typing.Callable[
        ['Widget', list[str]], None
    ]

    UpdateFunction = typing.Callable[['Widget'], dict[str, typing.Any] | list[str]]

    def __init__(
            self,
            name: str,
            title: str,
            config: Config,
            draw_func: DrawFunction,
            interval: int | float | None,
            dimensions: Dimensions,
            stdscr: typing.Any,
            update_func: UpdateFunction | None = None,
    ) -> None:
        self.name = name
        self.title = title
        self.config = config
        self.interval = interval
        self._update_func = update_func
        self._draw_func = draw_func
        self.last_updated: int | float | None = 0
        self.dimensions = dimensions
        try:
            self.win: typing.Any = stdscr.subwin(*self.dimensions.formatted())
        except curses.error:
            self.win = None
        self.draw_data: typing.Any = {}  # data used for drawing
        self.internal_data: typing.Any = {}  # internal data stored by widgets

        self.lock: threading.Lock = threading.Lock()

    def direct_refresh(self) -> None:
        self.win.refresh()

    def noutrefresh(self) -> None:
        self.win.noutrefresh()

    def draw(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        if self.config.enable:
            self._draw_func(self, *args, **kwargs)

    def update(self) -> dict[str, typing.Any] | list[str] | None:
        if self._update_func and self.config.enable:
            return self._update_func(self)
        return None

    def updatable(self) -> bool:
        if self._update_func and self.interval:
            return True
        return False

    def reinit_window(self, stdscr: typing.Any) -> None:
        self.win = stdscr.subwin(*self.dimensions.formatted())


class UIState:
    def __init__(self) -> None:
        self.highlighted: Widget | None = None


class RestartException(Exception):
    """Raised to signal that the curses UI should restart"""


class TerminalTooSmall(Exception):
    def __init__(self, height: int, width: int, min_height: int, min_width: int) -> None:
        self.height = height
        self.width = width
        self.min_height = min_height
        self.min_width = min_width
        super().__init__(height, width)  # Raised to signal that the terminal is too small


class UnknownException(Exception):
    def __init__(self, error_message: str) -> None:
        self.error_message = error_message
        super().__init__(error_message)


class Config:
    def __init__(
            self,
            name: str,
            title: str,
            enable: bool,
            interval: int | float | None,
            height: int,
            width: int,
            y: int,
            x: int,
            save_path: str | None = None,
            **kwargs: typing.Any
    ) -> None:
        self.name = name
        self.title = title
        self.enable = enable
        self.interval = interval
        if interval == 0:
            self.interval = None
        self.last_updated: int = 0
        self.dimensions: Dimensions = Dimensions(height=height, width=width, y=y, x=x)

        if save_path is not None:
            self.save_path = save_path

        for key, value in kwargs.items():
            setattr(self, key, value)

    def __getattr__(self, name: str) -> typing.Any:  # only gets called if key is not found
        return None  # signal to code editor that any key may exist


class RGBColor:
    def __init__(self, r: int, g: int, b: int) -> None:
        self.r = r
        self.g = g
        self.b = b

    def rgb_to_0_1000(self) -> tuple[int, int, int]:
        return (
            round(self.r * 1000 / 255),
            round(self.g * 1000 / 255),
            round(self.b * 1000 / 255),
        )


class BaseConfig:
    def __init__(
            self,
            background_color: dict[str, typing.Any],
            foreground_color: dict[str, typing.Any],
            primary_color: dict[str, typing.Any],
            secondary_color: dict[str, typing.Any],
            loading_color: dict[str, typing.Any],
            error_color: dict[str, typing.Any],
            quit_key: str,
            reload_key: str,
            help_key: str
    ) -> None:
        self.background_color: RGBColor = (
            RGBColor(r=background_color['r'], g=background_color['g'], b=background_color['b'])
        )

        self.foreground_color: RGBColor = (
            RGBColor(r=foreground_color['r'], g=foreground_color['g'], b=foreground_color['b'])
        )

        self.primary_color: RGBColor = (
            RGBColor(r=primary_color['r'], g=primary_color['g'], b=primary_color['b'])
        )

        self.secondary_color: RGBColor = (
            RGBColor(r=secondary_color['r'], g=secondary_color['g'], b=secondary_color['b'])
        )

        self.loading_color: RGBColor = (
            RGBColor(r=loading_color['r'], g=loading_color['g'], b=loading_color['b'])
        )

        self.error_color: RGBColor = (
            RGBColor(r=error_color['r'], g=error_color['g'], b=error_color['b'])
        )

        self.base_colors: dict[int, tuple[int, RGBColor | int]] = {
            2: (1, self.foreground_color),
            15: (2, self.primary_color),
            13: (3, self.secondary_color),
            9: (4, self.loading_color),
            10: (5, self.error_color),
        }

        self.BACKGROUND_NUMBER: int = 1

        self.BACKGROUND_FOREGROUND_PAIR_NUMBER: int = 1
        self.PRIMARY_PAIR_NUMBER: int = 2
        self.SECONDARY_PAIR_NUMBER: int = 3
        self.LOADING_PAIR_NUMBER: int = 4
        self.ERROR_PAIR_NUMBER: int = 5

        self.quit_key = quit_key
        self.reload_key = reload_key
        self.help_key = help_key


def draw_colored_border(win: typing.Any, color_pair: int) -> None:
    win.attron(curses.color_pair(color_pair))
    win.border()
    win.attroff(curses.color_pair(color_pair))


def draw_widget(widget: Widget, title: str | None = None, loading: bool = False, error: bool = False) -> None:
    if not title:
        title = widget.title[:widget.dimensions.width - 4]
    else:
        title = title[:widget.dimensions.width - 4]
    widget.win.erase()  # Instead of clear(), prevents flickering
    if widget == ui_state.highlighted:
        draw_colored_border(widget.win, base_config.PRIMARY_PAIR_NUMBER)
    elif loading:
        draw_colored_border(widget.win, base_config.LOADING_PAIR_NUMBER)
    elif error:
        draw_colored_border(widget.win, base_config.ERROR_PAIR_NUMBER)
    else:
        widget.win.border()
    widget.win.addstr(0, 2, f'{title}')


def add_widget_content(widget: Widget, content: list[str]) -> None:
    for i, line in enumerate(content):
        if i < widget.dimensions.height - 2:  # Keep inside border
            widget.win.addstr(1 + i, 1, line[:widget.dimensions.width - 2])


def safe_addstr(widget: Widget, y: int, x: int, text: str, color: int = 0) -> None:
    max_y, max_x = widget.win.getmaxyx()
    if y < 0 or y >= max_y:
        return
    safe_text = text[:max_x - x - 1]
    try:
        widget.win.addstr(y, x, safe_text, color)
    except curses.error:
        pass


def loading_screen(widgets: list[Widget]) -> None:
    for widget in widgets:
        if not widget.config.enable:
            continue
        draw_widget(widget, loading=True)
        add_widget_content(widget, [' Loading... '])
        widget.win.refresh()
    return None


def display_error(widget: Widget, content: list[str]) -> None:
    draw_widget(widget, ' Error ', error=True)
    add_widget_content(widget, content)


def init_colors() -> None:
    curses.start_color()
    if curses.can_change_color():
        curses.init_color(
            base_config.BACKGROUND_NUMBER,  # type: ignore[call-arg, unused-ignore]
            *base_config.background_color.rgb_to_0_1000()  # type: ignore[call-arg, unused-ignore]
        )

        for color_number, color in base_config.base_colors.items():
            curses.init_color(
                color_number,  # type: ignore[call-arg, unused-ignore]
                *color[1].rgb_to_0_1000()  # type: ignore[union-attr]
            )
    else:
        base_config.base_colors = {
            2: (1, curses.COLOR_WHITE),
            15: (2, curses.COLOR_BLUE),
            13: (3, curses.COLOR_CYAN),
            9: (4, curses.COLOR_YELLOW),
            10: (5, curses.COLOR_RED)
        }

    for color_number, color in base_config.base_colors.items():
        curses.init_pair(
            color[0],
            color_number,
            base_config.BACKGROUND_NUMBER
        )

    gradient_color: list[int] = [
        28, 34, 40, 46, 82, 118, 154, 172,
        196, 160, 127, 135, 141, 99, 63, 33, 27, 24
    ]

    for i, color in enumerate(gradient_color, start=6):  # type: ignore
        curses.init_pair(i, color, base_config.BACKGROUND_NUMBER)  # type: ignore[arg-type]


def init_curses_setup(stdscr: typing.Any) -> None:
    curses.mousemask(curses.ALL_MOUSE_EVENTS)
    curses.curs_set(0)
    curses.mouseinterval(0)
    stdscr.move(0, 0)
    curses.set_escdelay(25)
    init_colors()
    stdscr.bkgd(' ', curses.color_pair(1))  # Activate standard color
    stdscr.clear()
    stdscr.refresh()
    stdscr.timeout(100)


def validate_terminal_size(stdscr: typing.Any, min_height: int, min_width: int) -> None:
    height, width = stdscr.getmaxyx()

    if height < min_height or width < min_width:
        raise TerminalTooSmall(height, width, min_height, min_width)


def prompt_user_input(widget: Widget, prompt: str) -> str:
    if not widget.win:
        return ''

    win = widget.win

    curses.curs_set(1)
    win.keypad(True)  # Enable special keys (arrow keys, backspace, etc.)

    max_y, max_x = win.getmaxyx()
    input_y = max_y - 2
    left_margin = 2
    right_margin = 2
    usable_width = max_x - (left_margin + right_margin)

    input_x = left_margin + len(prompt)
    max_input_len = max(0, usable_width - len(prompt) - 1)

    input_str = ''
    cursor_pos = 0

    def redraw_input() -> None:
        win.move(input_y, left_margin)
        # Clear only the safe inner region (never touch border)
        win.addstr(' ' * usable_width)
        win.move(input_y, left_margin)
        win.addstr(prompt)
        visible_text = input_str[:max_input_len]
        win.addstr(visible_text)
        win.move(input_y, input_x + cursor_pos)
        win.refresh()

    try:
        redraw_input()
    except curses.error:
        return ''

    while True:
        ch = win.get_wch()

        if ch == '\n':  # ENTER
            break
        elif ch in ('\b', '\x7f', curses.KEY_BACKSPACE):  # BACKSPACE
            if cursor_pos > 0:
                input_str = input_str[:cursor_pos - 1] + input_str[cursor_pos:]
                cursor_pos -= 1
                try:
                    redraw_input()
                except curses.error:
                    return ''
        elif ch == curses.KEY_LEFT:  # LEFT
            if cursor_pos > 0:
                cursor_pos -= 1
                win.move(input_y, input_x + cursor_pos)
                win.refresh()
        elif ch == curses.KEY_RIGHT:  # RIGHT
            if cursor_pos < len(input_str):
                cursor_pos += 1
                win.move(input_y, input_x + cursor_pos)
                win.refresh()
        elif ch == curses.KEY_DC:  # DELETE
            if cursor_pos < len(input_str):
                input_str = input_str[:cursor_pos] + input_str[cursor_pos + 1:]
                try:
                    redraw_input()
                except curses.error:
                    return ''
        elif isinstance(ch, int):  # Ignore other special keys
            continue
        elif isinstance(ch, str) and len(ch) == 1:  # Normal text input
            if len(input_str) < max_input_len:
                input_str = input_str[:cursor_pos] + ch + input_str[cursor_pos:]
                cursor_pos += 1
                try:
                    redraw_input()
                except curses.error:
                    return ''

    curses.curs_set(0)
    return input_str


class ConfigLoader:
    def __init__(self) -> None:
        self.BASE_DIR = Path(__file__).resolve().parent.parent
        self.CONFIG_DIR = self.BASE_DIR / 'config'
        self.WIDGETS_DIR = self.CONFIG_DIR / 'widgets'
        load_dotenv(self.CONFIG_DIR / 'secrets.env')

    def reload_secrets(self) -> None:
        load_dotenv(self.CONFIG_DIR / 'secrets.env', override=True)

    @staticmethod
    def get_secret(name: str, default: typing.Any | None = None) -> str | None:
        return os.getenv(name, default)

    @staticmethod
    def load_yaml(path: Path) -> dict[str, typing.Any]:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}

    def load_base_config(self) -> BaseConfig:
        base_path = self.CONFIG_DIR / 'base.yaml'
        if not base_path.exists():
            raise FileNotFoundError(f'Base config "{base_path}" not found.')
        pure_yaml: dict[str, typing.Any] = self.load_yaml(base_path)

        return BaseConfig(**pure_yaml)

    def load_widget_config(self, widget_name: str) -> Config:
        path = self.WIDGETS_DIR / f'{widget_name}.yaml'
        if not path.exists():
            raise FileNotFoundError(f'Config for widget "{widget_name}" not found.')
        pure_yaml: dict[str, typing.Any] = self.load_yaml(path)

        return Config(**pure_yaml)


config_loader = ConfigLoader()
ui_state: UIState = UIState()
base_config: BaseConfig = config_loader.load_base_config()
