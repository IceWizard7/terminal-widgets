from __future__ import annotations  # allows forward references in type hints
import curses
import typing
import threading

from widgets.config import (
    PRIMARY_COLOR_NUMBER, LOADING_COLOR_NUMBER, ERROR_COLOR_NUMBER,
    CUSTOM_BACKGROUND_VALUE, BASE_PAIR_NUMBER, BASE_FOREGROUND,
    MINIMUM_HEIGHT, MINIMUM_WIDTH, CUSTOM_BACKGROUND_NUMBER
)


class Dimensions:
    def __init__(self, height: int, width: int, y: int, x: int) -> None:
        self.height: int = height
        self.width: int = width
        self.y: int = y
        self.x: int = x

    def formatted(self) -> list[int]:
        return [self.height, self.width, self.y, self.x]


class Widget:
    DrawFunction = typing.Callable[['Widget'], None] | typing.Callable[['Widget', dict[str, typing.Any]], None] | typing.Callable[['Widget', list[str]], None]
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
        self.data: typing.Any = {}

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
    def __init__(self, height: int, width: int) -> None:
        self.height = height
        self.width = width
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

        for key, value in kwargs.items():
            setattr(self, key, value)

    def __getattr__(self, name: str) -> typing.Any:  # only gets called if key is not found
        return None  # signal to code editor that any key may exist


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
        draw_colored_border(widget.win, PRIMARY_COLOR_NUMBER)
    elif loading:
        draw_colored_border(widget.win, LOADING_COLOR_NUMBER)
    elif error:
        draw_colored_border(widget.win, ERROR_COLOR_NUMBER)
    else:
        widget.win.border()
    widget.win.addstr(0, 2, f'{title}')


def add_widget_content(widget: Widget, content: list[str]) -> None:
    for i, line in enumerate(content):
        if i < widget.dimensions.height - 2:  # Keep inside border
            widget.win.addstr(1 + i, 1, line[:widget.dimensions.width - 2])


def safe_addstr(widget: Widget, y: int, x: int, text: str, color: int = 0):
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


def init_colors(custom_background_number: int) -> None:
    curses.start_color()
    if curses.can_change_color():
        curses.init_color(
            custom_background_number,
            *CUSTOM_BACKGROUND_VALUE,  # type: ignore[call-arg, unused-ignore]
        )  # type: ignore[call-arg, unused-ignore]
    else:
        custom_background_number = curses.COLOR_BLACK

    curses.init_pair(BASE_PAIR_NUMBER, BASE_FOREGROUND, custom_background_number)

    gradient_color: list[int] = [
        28, 34, 40, 46, 82, 118, 154, 172,  # colors 2-9
        196, 160, 127, 135, 141, 99, 63, 33, 27  # colors 10-18
    ]

    # Base color
    curses.init_pair(1, BASE_FOREGROUND, custom_background_number)

    for i, color in enumerate(gradient_color, start=2):
        curses.init_pair(i, color, custom_background_number)  # foreground=color, background=black


def init_curses_setup(stdscr: typing.Any) -> None:
    curses.mousemask(curses.ALL_MOUSE_EVENTS)
    curses.curs_set(0)
    curses.mouseinterval(0)
    stdscr.move(0, 0)
    curses.set_escdelay(25)
    init_colors(CUSTOM_BACKGROUND_NUMBER)
    stdscr.bkgd(' ', curses.color_pair(1))  # Activate standard color
    stdscr.clear()
    stdscr.refresh()
    stdscr.timeout(100)


def validate_terminal_size(stdscr: typing.Any) -> None:
    height, width = stdscr.getmaxyx()

    if height < MINIMUM_HEIGHT or width < MINIMUM_WIDTH:
        raise TerminalTooSmall(height, width)


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

    input_str = ""
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

        if ch == "\n":  # ENTER
            break
        elif ch in ("\b", "\x7f", curses.KEY_BACKSPACE):  # BACKSPACE
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


ui_state: UIState = UIState()
