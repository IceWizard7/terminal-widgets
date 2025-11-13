from __future__ import annotations  # allows forward references in type hints
from pathlib import Path
import yaml
import yaml.parser
from dotenv import load_dotenv  # type: ignore[import-not-found]
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
                       ['Widget', 'UIState', 'BaseConfig'], None] | typing.Callable[
        ['Widget', 'UIState', 'BaseConfig', dict[str, typing.Any]], None] | typing.Callable[
        ['Widget', 'UIState', 'BaseConfig', list[str]], None
    ]

    UpdateFunction = typing.Callable[['Widget', 'ConfigLoader'], dict[str, typing.Any] | list[str]]

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

    def draw(self, ui_state: UIState, base_config: BaseConfig, *args: typing.Any, **kwargs: typing.Any) -> None:
        if self.config.enabled:
            self._draw_func(self, ui_state, base_config, *args, **kwargs)

    def update(self, config_loader: ConfigLoader) -> dict[str, typing.Any] | list[str] | None:
        if self._update_func and self.config.enabled:
            return self._update_func(self, config_loader)
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


class StopException(Exception):
    """Raised to signal that the curses UI should stop"""
    def __init__(self, log_messages: LogMessages) -> None:
        self.log_messages: LogMessages = log_messages


class YAMLParseException(Exception):
    """Raised to signal that there was an error parsing a YAML file"""


class TerminalTooSmall(Exception):
    def __init__(self, height: int, width: int, min_height: int, min_width: int) -> None:
        """Raised to signal that the terminal is too small"""
        self.height = height
        self.width = width
        self.min_height = min_height
        self.min_width = min_width
        super().__init__(height, width)


class ConfigError(Exception):
    def __init__(self, error_details: str) -> None:
        self.error_details: str = error_details
        super().__init__(error_details)


class ConfigScanFoundError(Exception):
    def __init__(self, log_messages: LogMessages) -> None:
        self.log_messages: LogMessages = log_messages
        super().__init__(log_messages)


class ConfigFileNotFoundError(Exception):
    def __init__(self, error_details: str) -> None:
        self.error_details: str = error_details
        super().__init__(error_details)


class UnknownException(Exception):
    def __init__(self, log_messages: LogMessages, error_message: str) -> None:
        self.log_messages: LogMessages = log_messages
        self.error_message = error_message
        super().__init__(log_messages, error_message)


class LogMessages:
    def __init__(self, log_messages: list[str] | None = None) -> None:
        if log_messages is None:
            self.log_messages: list[str] = []
        else:
            self.log_messages: list[str] = log_messages

    def __add__(self, other: LogMessages) -> LogMessages:
        new_log: LogMessages = LogMessages()
        new_log.log_messages = self.log_messages + other.log_messages
        return new_log

    def __eq__(self, other: LogMessages) -> bool:
        return self.log_messages == other.log_messages

    def __ne__(self, other: LogMessages) -> bool:
        return self.log_messages != other.log_messages

    def add_log_message(self, message: str) -> None:
        self.log_messages.append(message)

    def print_log_messages(self, start: str, end: str) -> None:
        if self.log_messages:
            print(start, end='')
            for message in self.log_messages:
                print(message)
            print(end, end='')


class Config:
    def __init__(
            self,
            log_messages: LogMessages,
            name: str | None = None,
            title: str | None = None,
            enabled: bool | None = None,
            interval: int | float | None = None,
            height: int | None = None,
            width: int | None = None,
            y: int | None = None,
            x: int | None = None,
            **kwargs: typing.Any
    ) -> None:
        if name is None:
            log_messages.add_log_message(f'name missing value for unknown config')

        self.name = name

        if title is None:
            log_messages.add_log_message(f'Configuration for title is missing ("{name}" widget)')
        if enabled is None:
            log_messages.add_log_message(f'Configuration for enabled is missing ("{name}" widget)')
        if interval is None:
            log_messages.add_log_message(f'Configuration for interval is missing ("{name}" widget)')
        if height is None or not isinstance(height, int):
            log_messages.add_log_message(f'Configuration for height is missing / incorrect ("{name}" widget)')
        if width is None or not isinstance(width, int):
            log_messages.add_log_message(f'Configuration for width is missing / incorrect ("{name}" widget)')
        if y is None or not isinstance(y, int):
            log_messages.add_log_message(f'Configuration for y is missing / incorrect ("{name}" widget)')
        if x is None or not isinstance(x, int):
            log_messages.add_log_message(f'Configuration for x is missing / incorrect ("{name}" widget)')

        self.title = title
        self.enabled = enabled
        self.interval = interval
        if interval == 0:
            self.interval = None
        self.last_updated: int = 0
        self.dimensions: Dimensions = Dimensions(height=height, width=width, y=y, x=x)

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

    @staticmethod
    def add_rgb_color_from_dict(color: dict[str, typing.Any]) -> RGBColor:
        # make sure every value is an int (else -> error)
        return RGBColor(r=int(color['r']), g=int(color['g']), b=int(color['b']))


class BaseStandardFallBackConfig:
    def __init__(self) -> None:
        self.background_color: RGBColor = (
            RGBColor(r=31, g=29, b=67)
        )

        self.foreground_color: RGBColor = (
            RGBColor(r=227, g=236, b=252)
        )

        self.primary_color: RGBColor = (
            RGBColor(r=129, g=97, b=246)
        )

        self.secondary_color: RGBColor = (
            RGBColor(r=164, g=99, b=247)
        )

        self.loading_color: RGBColor = (
            RGBColor(r=215, g=135, b=0)
        )

        self.error_color: RGBColor = (
            RGBColor(r=255, g=0, b=0)
        )

        self.use_standard_terminal_background: bool = True

        self.quit_key: str = 'q'
        self.reload_key: str = 'r'
        self.help_key: str = 'h'


class BaseConfig:
    def __init__(
            self,
            log_messages: LogMessages,
            use_standard_terminal_background: bool | None = None,
            background_color: dict[str, typing.Any] | None = None,
            foreground_color: dict[str, typing.Any] | None = None,
            primary_color: dict[str, typing.Any] | None = None,
            secondary_color: dict[str, typing.Any] | None = None,
            loading_color: dict[str, typing.Any] | None = None,
            error_color: dict[str, typing.Any] | None = None,
            quit_key: str | None = None,
            reload_key: str | None = None,
            help_key: str | None = None,
            **kwargs: typing.Any
    ) -> None:
        base_standard_fallback_config: BaseStandardFallBackConfig = BaseStandardFallBackConfig()

        self.background_color: RGBColor = base_standard_fallback_config.background_color
        self.foreground_color: RGBColor = base_standard_fallback_config.foreground_color
        self.primary_color: RGBColor = base_standard_fallback_config.primary_color
        self.secondary_color: RGBColor = base_standard_fallback_config.secondary_color
        self.loading_color: RGBColor = base_standard_fallback_config.loading_color
        self.error_color: RGBColor = base_standard_fallback_config.error_color
        self.use_standard_terminal_background: bool = base_standard_fallback_config.use_standard_terminal_background
        self.quit_key: str = base_standard_fallback_config.quit_key
        self.reload_key: str = base_standard_fallback_config.reload_key
        self.help_key: str = base_standard_fallback_config.help_key

        if background_color is not None:
            try:
                self.background_color = RGBColor.add_rgb_color_from_dict(background_color)
            except KeyError as e:
                log_messages.add_log_message(f'background_color missing value for {e}')
            except ValueError as e:
                log_messages.add_log_message(f'background_color invalid value for {e}')
        else:
            log_messages.add_log_message(
                f'Configuration for background_color is missing (base.yaml,'
                f' falling back to standard config)'
            )

        if foreground_color is not None:
            try:
                self.foreground_color = RGBColor.add_rgb_color_from_dict(foreground_color)
            except KeyError as e:
                log_messages.add_log_message(f'foreground_color missing value for {e}')
            except ValueError as e:
                log_messages.add_log_message(f'foreground_color invalid value for {e}')
        else:
            log_messages.add_log_message(
                f'Configuration for foreground_color is missing (base.yaml,'
                f' falling back to standard config)'
            )

        if primary_color is not None:
            try:
                self.primary_color = RGBColor.add_rgb_color_from_dict(primary_color)
            except KeyError as e:
                log_messages.add_log_message(f'primary_color missing value for {e}')
            except ValueError as e:
                log_messages.add_log_message(f'error_color invalid value for {e}')
        else:
            log_messages.add_log_message(
                f'Configuration for primary_color is missing (base.yaml,'
                f' falling back to standard config)'
            )

        if secondary_color is not None:
            try:
                self.secondary_color = RGBColor.add_rgb_color_from_dict(secondary_color)
            except KeyError as e:
                log_messages.add_log_message(f'secondary_color missing value for {e}')
            except ValueError as e:
                log_messages.add_log_message(f'error_color invalid value for {e}')
        else:
            log_messages.add_log_message(
                f'Configuration for secondary_color is missing (base.yaml,'
                f' falling back to standard config)'
            )

        if loading_color is not None:
            try:
                self.loading_color = RGBColor.add_rgb_color_from_dict(loading_color)
            except KeyError as e:
                log_messages.add_log_message(f'loading_color missing value for {e}')
            except ValueError as e:
                log_messages.add_log_message(f'error_color invalid value for {e}')
        else:
            log_messages.add_log_message(
                f'Configuration for loading_color is missing (base.yaml,'
                f' falling back to standard config)'
            )

        if error_color is not None:
            try:
                self.error_color = RGBColor.add_rgb_color_from_dict(error_color)
            except KeyError as e:
                log_messages.add_log_message(f'error_color missing value for {e}')
            except ValueError as e:
                log_messages.add_log_message(f'error_color invalid value for {e}')
        else:
            log_messages.add_log_message(
                f'Configuration for error_color is missing (base.yaml,'
                f' falling back to standard config)'
            )

        self.base_colors: dict[int, tuple[int, RGBColor | int]] = {
            2: (1, self.foreground_color),
            15: (2, self.primary_color),
            13: (3, self.secondary_color),
            9: (4, self.loading_color),
            10: (5, self.error_color),
        }

        if use_standard_terminal_background is not None:
            if not isinstance(use_standard_terminal_background, bool):
                log_messages.add_log_message(f'use_standard_terminal_background not True or False')
            self.use_standard_terminal_background = use_standard_terminal_background
        else:
            log_messages.add_log_message(
                f'Configuration for use_standard_terminal_background is missing (base.yaml,'
                f' falling back to standard config)'
            )

        if self.use_standard_terminal_background:
            self.BACKGROUND_NUMBER: int = -1
        else:
            self.BACKGROUND_NUMBER = 1

        self.BACKGROUND_FOREGROUND_PAIR_NUMBER: int = 1
        self.PRIMARY_PAIR_NUMBER: int = 2
        self.SECONDARY_PAIR_NUMBER: int = 3
        self.LOADING_PAIR_NUMBER: int = 4
        self.ERROR_PAIR_NUMBER: int = 5

        if quit_key is not None:
            if len(quit_key) != 1:
                log_messages.add_log_message(f'quit_key value wrong length (not 1)')
            if not (quit_key.isalpha() or quit_key.isdigit()):
                log_messages.add_log_message(f'quit_key value not alphabetic or numeric')
            self.quit_key = quit_key
        else:
            log_messages.add_log_message(f'Configuration for quit_key is missing (base.yaml,'
                                         f' falling back to standard config)')

        if reload_key is not None:
            if len(reload_key) != 1:
                log_messages.add_log_message(f'reload_key value wrong length (not 1)')
            if not (reload_key.isalpha() or reload_key.isdigit()):
                log_messages.add_log_message(f'reload_key value not alphabetic or numeric')
            self.reload_key = reload_key
        else:
            log_messages.add_log_message(f'Configuration for reload_key is missing (base.yaml,'
                                         f' falling back to standard config)')

        if help_key is not None:
            if len(help_key) != 1:
                log_messages.add_log_message(f'help_key value wrong length (not 1)')
            if not (help_key.isalpha() or help_key.isdigit()):
                log_messages.add_log_message(f'help_key value not alphabetic or numeric')
            self.help_key = help_key
        else:
            log_messages.add_log_message(
                f'Configuration for help_key is missing (base.yaml,'
                f' falling back to standard config)'
            )

        for key, value in kwargs.items():
            log_messages.add_log_message(f'Configuration for key "{key}" is not expected (base.yaml)')


def draw_colored_border(win: typing.Any, color_pair: int) -> None:
    win.attron(curses.color_pair(color_pair))
    win.border()
    win.attroff(curses.color_pair(color_pair))


def draw_widget(
        widget: Widget,
        ui_state: UIState,
        base_config: BaseConfig,
        title: str | None = None,
        loading: bool = False,
        error: bool = False
) -> None:
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


def loading_screen(widgets: list[Widget], ui_state: UIState, base_config: BaseConfig) -> None:
    for widget in widgets:
        if not widget.config.enabled:
            continue
        draw_widget(widget, ui_state, base_config, loading=True)
        add_widget_content(widget, [' Loading... '])
        widget.win.refresh()
    return None


def display_error(widget: Widget, content: list[str], ui_state: UIState, base_config: BaseConfig) -> None:
    draw_widget(widget, ui_state, base_config, ' Error ', error=True)
    add_widget_content(widget, content)


def init_colors(base_config: BaseConfig) -> None:
    curses.start_color()
    if base_config.use_standard_terminal_background:
        curses.use_default_colors()
    if curses.can_change_color():
        if not base_config.use_standard_terminal_background:
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


def init_curses_setup(stdscr: typing.Any, base_config: BaseConfig) -> None:
    curses.mousemask(curses.ALL_MOUSE_EVENTS)
    curses.curs_set(0)
    curses.mouseinterval(0)
    stdscr.move(0, 0)
    curses.set_escdelay(25)
    init_colors(base_config)
    stdscr.bkgd(' ', curses.color_pair(1))  # Activate standard color
    stdscr.clear()
    stdscr.refresh()
    stdscr.timeout(100)


def cleanup_curses_setup(
        stop_event: threading.Event,
        reloader_thread: threading.Thread
) -> None:
    stop_event.set()
    reloader_thread.join(timeout=1)
    curses.endwin()


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

    def load_base_config(self, log_messages: LogMessages) -> BaseConfig:
        base_path = self.CONFIG_DIR / 'base.yaml'
        if not base_path.exists():
            raise ConfigFileNotFoundError(f'Base config "{base_path}" not found')
        try:
            pure_yaml: dict[str, typing.Any] = self.load_yaml(base_path)
        except yaml.parser.ParserError:
            raise YAMLParseException(f'Base config "{base_path}" not valid YAML')

        return BaseConfig(log_messages=log_messages, **pure_yaml)

    def load_widget_config(self, log_messages: LogMessages, widget_name: str) -> Config:
        path = self.WIDGETS_DIR / f'{widget_name}.yaml'
        if not path.exists():
            raise ConfigFileNotFoundError(f'Config for widget "{widget_name}" not found')
        try:
            pure_yaml: dict[str, typing.Any] = self.load_yaml(path)
        except yaml.parser.ParserError:
            raise YAMLParseException(f'Config for widget "{widget_name}" not valid YAML')

        return Config(log_messages=log_messages, **pure_yaml)


class ConfigScanner:
    def __init__(self, config_loader: ConfigLoader) -> None:
        self.config_loader = config_loader

    def scan_config(self, widget_names: list[str]) -> LogMessages | bool:
        """Scan config, either returns log messages or 'False' representing that no errors were found"""
        empty_log: LogMessages = LogMessages()
        final_log: LogMessages = LogMessages()

        current_log: LogMessages = LogMessages()
        try:
            self.config_loader.load_base_config(current_log)
            if current_log != empty_log:
                final_log += current_log
        except YAMLParseException as e:
            final_log += LogMessages([str(e)])

        for widget_name in widget_names:
            current_log: LogMessages = LogMessages()
            try:
                self.config_loader.load_widget_config(current_log, widget_name)
                if current_log != empty_log:
                    final_log += current_log
            except YAMLParseException as e:
                final_log += LogMessages([str(e)])

        if final_log != empty_log:
            return final_log
        return False
