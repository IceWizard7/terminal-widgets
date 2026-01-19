from __future__ import annotations  # Allows forward references in type hints
import enum
import pathlib
import yaml
import yaml.parser
import yaml.scanner
import dotenv
import os
import curses
import _curses
import typing
import collections
import threading
import time as time_module
import types
import importlib
import importlib.util
import sys
import traceback
import datetime


# region Widget & essentials

class Dimensions:
    def __init__(self, height: int, width: int, y: int, x: int, z_index: int) -> None:
        self.current_height: int = height
        self.current_width: int = width
        self.current_y: int = y
        self.current_x: int = x
        self.z_index: int = z_index

    def formatted(self) -> list[int]:
        return [self.current_height, self.current_width, self.current_y, self.current_x]

    def within_borders(self, min_height: int, min_width: int) -> bool:
        return (
                self.current_y >= 0 and
                self.current_x >= 0 and
                (self.current_y + self.current_height) < min_height and
                (self.current_x + self.current_width) < min_width
        )


class Widget:
    DrawFunction = typing.Callable[
        ['Widget', 'WidgetContainer'], None
    ]
    DrawFunctionWithDrawData = typing.Callable[
        ['Widget', 'WidgetContainer', list[str]], None
    ]
    HelpFunction = typing.Callable[
        ['Widget', 'WidgetContainer'], None
    ]
    UpdateFunction = typing.Callable[['Widget', 'WidgetContainer'], list[str]]
    MouseClickUpdateFunction = typing.Callable[['Widget', int, int, int, 'WidgetContainer'], None]
    KeyBoardUpdateFunction = typing.Callable[['Widget', int, 'WidgetContainer'], None]
    InitializeFunction = typing.Callable[['Widget', 'WidgetContainer'], None]

    def __init__(
            self,
            name: str | None,
            title: str,
            config: Config,
            draw_func: DrawFunction | DrawFunctionWithDrawData,
            interval: int | float | None,
            dimensions: Dimensions,
            stdscr: CursesWindowType,
            update_func: UpdateFunction | None = None,
            mouse_click_func: MouseClickUpdateFunction | None = None,
            keyboard_func: KeyBoardUpdateFunction | None = None,
            init_func: InitializeFunction | None = None,
            help_func: HelpFunction | None = None
    ) -> None:
        self.name = name
        self.title = title
        self.config = config
        self.interval = interval
        self._update_func = update_func
        self._mouse_click_func = mouse_click_func
        self._keyboard_func = keyboard_func
        self._draw_func = draw_func
        self._init_func = init_func
        self._help_func = help_func
        self.last_updated: int | float | None = 0
        self.dimensions = dimensions
        try:
            self.win: CursesWindowType | None = stdscr.subwin(*self.dimensions.formatted())
        except CursesError:
            self.win = None
        self.help_mode: bool = False
        self.draw_data: typing.Any = {}  # data used for drawing
        self.internal_data: typing.Any = {}  # internal data stored by widgets

        self.lock: threading.Lock = threading.Lock()

    def noutrefresh(self) -> None:
        if not self.win:
            return
        self.win.noutrefresh()

    def init(self, widget_container: WidgetContainer) -> None:
        if self._init_func and self.config.enabled:
            self._init_func(self, widget_container)

    def draw_function(self, widget_container: WidgetContainer, draw_data: typing.Any | None = None) -> None:
        if not self.config.enabled:
            return

        if self.help_mode and self._help_func:
            try:
                self._help_func(self, widget_container)
            except Exception:
                raise  # Re-Raise, catch in main.py
            return

        try:
            if draw_data is not None:
                typing.cast(Widget.DrawFunctionWithDrawData, self._draw_func)(self, widget_container, draw_data)
            else:
                typing.cast(Widget.DrawFunction, self._draw_func)(self, widget_container)
        except Exception:
            raise  # Re-Raise, catch in main.py

    def disable_help_mode(self) -> None:
        self.help_mode = False

    def enable_help_mode(self) -> None:
        self.help_mode = True

    def toggle_help_mode(self) -> None:
        if self.help_mode:
            self.disable_help_mode()
        else:
            self.enable_help_mode()

    def update(self, widget_container: WidgetContainer) -> list[str] | None:
        if self._update_func and self.config.enabled:
            return self._update_func(self, widget_container)
        return None

    def updatable(self) -> bool:
        if self._update_func and self.interval and self.config.enabled:
            return True
        return False

    def mouse_action(self, mx: int, my: int, b_state: int, widget_container: WidgetContainer) -> None:
        if self._mouse_click_func:
            self._mouse_click_func(self, mx, my, b_state, widget_container)

    def keyboard_action(self, key: int, widget_container: WidgetContainer) -> None:
        if self._keyboard_func:
            self._keyboard_func(self, key, widget_container)

    def reinit_window(self, widget_container: WidgetContainer) -> None:
        try:
            self.win = widget_container.stdscr.subwin(*self.dimensions.formatted())
        except CursesError:
            self.win = None

    def draw_colored_border(self, color_pair: int, test_env: bool) -> None:
        if not self.win:
            return

        if test_env:
            self.win.border()
        else:
            self.win.attron(curses.color_pair(color_pair))
            self.win.border()
            self.win.attroff(curses.color_pair(color_pair))

    @staticmethod
    def convert_color_number_to_curses_pair(color_number: int) -> int:
        return curses.color_pair(color_number)

    def safe_addstr(
            self,
            y: int,
            x: int,
            text: str,
            color_numbers: list[int] | None = None,
            curses_color_pairs: list[int] | None = None
    ) -> None:
        if not color_numbers:
            color_numbers = []

        if not curses_color_pairs:
            curses_color_pairs = []

        if not self.win:
            return

        max_y, max_x = self.win.getmaxyx()
        if y < 0 or y >= max_y:
            return
        safe_text = text[:max_x - x - 1]
        try:
            color_pairs: list[int] = [self.convert_color_number_to_curses_pair(color) for color in color_numbers]
            color: int = 0
            for color_pair in color_pairs + curses_color_pairs:
                color |= color_pair
            self.win.addstr(y, x, safe_text, color)
        except CursesError:
            pass

    def add_widget_content(self, content: list[str]) -> None:
        if not self.win:
            return

        for i, line in enumerate(content):
            if i < self.dimensions.current_height - 2:  # Keep inside border
                self.win.addstr(1 + i, 1, line[:self.dimensions.current_width - 2])

    def prompt_user_input(self, prompt: str) -> str:
        if not self.win:
            return ''

        win = self.win

        curses.curs_set(1)
        win.keypad(True)  # Enable special keys (arrow keys, backspace, etc.)

        may_y: int
        max_x: int

        max_y, max_x = win.getmaxyx()
        input_y: int = max_y - 2
        left_margin: int = 2
        right_margin: int = 2
        usable_width: int = max_x - (left_margin + right_margin)

        input_x: int = left_margin + len(prompt)
        max_input_len: int = max(0, usable_width - len(prompt) - 1)

        input_str: str = ''
        cursor_pos: int = 0

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
        except CursesError:
            return ''

        while True:
            ch = win.get_wch()

            if ch == '\n':  # ENTER
                break
            if ch == '\x1b' or ch == CursesKeys.ESCAPE:
                input_str = ''  # Return empty string
                break
            elif ch in ('\b', '\x7f', curses.KEY_BACKSPACE):  # BACKSPACE
                if cursor_pos > 0:
                    input_str = input_str[:cursor_pos - 1] + input_str[cursor_pos:]
                    cursor_pos -= 1
                    try:
                        redraw_input()
                    except CursesError:
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
                    except CursesError:
                        return ''
            elif isinstance(ch, int):  # Ignore other special keys
                continue
            elif isinstance(ch, str) and len(ch) == 1:  # Normal text input
                if len(input_str) < max_input_len:
                    input_str = input_str[:cursor_pos] + ch + input_str[cursor_pos:]
                    cursor_pos += 1
                    try:
                        redraw_input()
                    except CursesError:
                        return ''

        curses.curs_set(0)
        return input_str


class Config:
    def __init__(
            self,
            _test_env: bool,
            file_name: str,
            log_messages: LogMessages,
            name: str | None = None,
            title: str | None = None,
            enabled: bool | None = None,
            interval: int | float | None = None,
            height: int | None = None,
            width: int | None = None,
            y: int | None = None,
            x: int | None = None,
            z: int | None = None,
            **kwargs: typing.Any  # Used for extra arguments, e.g. 'time_format' in clock_widget
    ) -> None:
        fields: list[tuple[str, object, type | tuple[type, ...]]] = [
            ('name', name, str),
            ('title', title, str),
            ('enabled', enabled, bool),
            ('interval', interval, (int, float)),
            ('height', height, int),
            ('width', width, int),
            ('y', y, int),
            ('x', x, int),
            ('z', z, int),
        ]

        for field_name, value, expected_type in fields:
            if value is None or not isinstance(value, expected_type):
                log_messages.add_log_message(LogMessage(
                    f'Configuration for {field_name} is missing / incorrect ("{file_name}" widget)',
                    LogLevels.ERROR.key
                ))

        self.name: str = typing.cast(str, name)
        self.title: str = typing.cast(str, title)
        self.enabled: bool = typing.cast(bool, enabled)
        self.interval: int | float | None = interval
        if interval == 0:
            self.interval = None
        self.last_updated: int = 0
        self.dimensions: Dimensions = Dimensions(
            height=height, width=width, y=y, x=x, z_index=z  # type: ignore[arg-type]
        )

        for key, value in kwargs.items():
            if _test_env:
                if key.startswith('test_env_'):
                    setattr(self, key.removeprefix('test_env_'), value)
                    continue

                if f'test_env_{key}' in kwargs.keys():
                    continue

                setattr(self, key, value)
            else:
                if key.startswith('test_env_'):
                    continue
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
    def add_rgb_color_from_dict(color: dict[str, int]) -> RGBColor:
        # Make sure every value is an int (else raise an error)
        return RGBColor(r=int(color['r']), g=int(color['g']), b=int(color['b']))


# endregion Widget & essentials

# region WarningWidget

class FloatingWidget:
    def __init__(
            self,
            name: str,
            title: str,
            dimensions: Dimensions,
            description: list[str],
            stdscr: CursesWindowType
    ) -> None:
        self.name: str = name
        self.title: str = title
        self._dimensions: Dimensions = dimensions
        self._description: list[str] = description
        try:
            self.win: CursesWindowType | None = stdscr.subwin(*self._dimensions.formatted())
        except CursesError:
            self.win = None

    def noutrefresh(self) -> None:
        if self.win:
            self.win.noutrefresh()

    def reinit_window(self, widget_container: WidgetContainer) -> None:
        try:
            self.win = widget_container.stdscr.subwin(*self._dimensions.formatted())
        except CursesError:
            self.win = None

    def draw(self, widget_container: WidgetContainer) -> None:
        if not self.win:
            return

        self.erase_content()

        # Draw widget
        if self.win:
            title = self.title[:self._dimensions.current_width - 4]
            self.win.erase()  # Instead of clear(), prevents flickering

            # Add border
            self.win.attron(curses.color_pair(widget_container.base_config.ERROR_PAIR_NUMBER))
            self.win.border()
            self.win.attroff(curses.color_pair(widget_container.base_config.ERROR_PAIR_NUMBER))

            self.win.addstr(0, 2, f'{title}')

        # Add content
        if self.win:
            for i, line in enumerate(self._description):
                if i < self._dimensions.current_height - 2:  # Keep inside border
                    self.win.addstr(1 + i, 1, line[:self._dimensions.current_width - 2])

    def erase_content(self) -> None:
        if not self.win:
            return

        self.win.erase()


class WarningWidget(FloatingWidget):
    def __init__(
            self,
            name: str,
            title: str,
            warning_error: Exception,  # Instance, not a class
            description: list[str],
            dimensions: Dimensions,
            stdscr: CursesWindowType
    ) -> None:
        super().__init__(name, title, dimensions, description, stdscr)
        self.name: str = name
        self.warning_error: Exception = warning_error


# endregion WarningWidget

# region WidgetContainer & essentials

class WidgetContainer:
    def __init__(self, stdscr: CursesWindowType, test_env: bool) -> None:
        self.test_env: bool = test_env
        self.stdscr: CursesWindowType = stdscr
        self.ui_state: UIState = UIState()

        # Logs (Warnings, Errors)
        self.log_messages: LogMessages = LogMessages()

        # Directories
        self.ROOT_CONFIG_DIR: pathlib.Path = pathlib.Path.home() / '.config' / 'twidgets'
        self.ROOT_PER_WIDGET_CONFIG_DIR: pathlib.Path = self.ROOT_CONFIG_DIR / 'widgets'
        self.ROOT_PY_WIDGET_DIR: pathlib.Path = self.ROOT_CONFIG_DIR / 'py_widgets'
        self.SCRIPT_DIR: pathlib.Path = pathlib.Path(__file__).resolve().parent.parent  # Test ENV
        self.SCRIPT_DIR_PY_WIDGET_DIR: pathlib.Path = self.SCRIPT_DIR / 'config' / 'py_widgets'

        # Widget Loader (after directories are generated)
        self.widget_loader: WidgetLoader = WidgetLoader(self)

        # Define config loader (Only loads secrets)
        self.config_loader: ConfigLoader = ConfigLoader(self)
        self.config_loader.reload_secrets()  # Needed to reload secrets.env changes

        # Initiate base config
        self.base_config: BaseConfig = self.config_loader.load_base_config(self.log_messages)

        # Reloader Thread
        self.stop_event: threading.Event = threading.Event()
        self.reloader_thread: threading.Thread = threading.Thread(
            target=self.reload_widget_scheduler_function
        )
        if self.test_env:
            self.reloader_thread.daemon = True  # Make tests exit when they are all executed
        threading.excepthook = self.crash_on_thread_exception

        self._floating_widgets: list[FloatingWidget] = []
        self._all_widgets: list[Widget] = []
        self._widgets: list[Widget] = []

    def add_widget(self, widget: Widget) -> None:
        if not widget.config.enabled:
            return
        if widget not in self._all_widgets:
            self._all_widgets.append(widget)
        if widget not in self._widgets:
            if any(widget.name == _widget.name for _widget in self._widgets):
                # raise DebugException(f'Widget "{widget.name}" is already defined')
                return
            self._widgets.append(widget)

    def draw_widget(
            self,
            widget: Widget,
            title: str | None = None,
            loading: bool = False,
            error: bool = False
    ) -> None:
        if not widget.win:
            return

        if not title:
            title = widget.title[:widget.dimensions.current_width - 4]
        else:
            title = title[:widget.dimensions.current_width - 4]

        widget.win.erase()  # Instead of clear(), prevents flickering

        if widget == self.ui_state.highlighted:
            widget.draw_colored_border(self.base_config.PRIMARY_PAIR_NUMBER, self.test_env)
        elif loading:
            widget.draw_colored_border(self.base_config.LOADING_PAIR_NUMBER, self.test_env)
        elif error:
            widget.draw_colored_border(self.base_config.ERROR_PAIR_NUMBER, self.test_env)
        else:
            widget.win.border()
        widget.win.addstr(0, 2, f'{title}')

    @staticmethod
    def remove_widget_content(widget: Widget) -> None:
        if widget.win:
            widget.win.erase()

    def deactivate_widget(self, widget: Widget) -> None:
        if self.ui_state.highlighted == widget:
            self.ui_state.previously_highlighted = widget
            self.ui_state.highlighted = None
        self.remove_widget_content(widget)
        widget.disable_help_mode()
        widget.reinit_window(self)
        widget.noutrefresh()
        if widget in self._widgets:
            self._widgets.remove(widget)

    def reactivate_all_widgets(self) -> None:
        for widget in self._all_widgets:
            self.add_widget(widget)

    def reinit_all_widget_windows(self) -> None:
        for widget in self._widgets:
            widget.reinit_window(self)

    def reinit_all_floating_windows(self) -> None:
        for floating_widget in self._floating_widgets:
            floating_widget.reinit_window(self)
            if floating_widget.win:
                floating_widget.win.noutrefresh()

    def add_widget_list(self, widget_list: list[Widget]) -> None:
        for widget in widget_list:
            self.add_widget(widget)

    def return_widgets(self) -> list[Widget]:
        return self._widgets

    def return_widgets_ordered_by_z_index(self) -> dict[int, list[Widget]]:
        widgets_by_z_index: dict[int, list[Widget]] = {}
        for widget in self._widgets:
            z_index = widget.dimensions.z_index
            if z_index not in widgets_by_z_index.keys():
                widgets_by_z_index[z_index] = [widget]
            else:
                widgets_by_z_index[z_index].append(widget)
        return widgets_by_z_index

    def return_all_widgets(self) -> list[Widget]:
        return self._all_widgets

    def return_all_floating_windows(self) -> list[FloatingWidget]:
        return self._floating_widgets

    def get_max_height_width_all_widgets(self) -> tuple[int, int]:
        """Get max height, width for all widgets, not just activated widgets"""
        if not self.return_all_widgets():
            return 0, 0

        min_height: int = max(
            widget.dimensions.current_height + widget.dimensions.current_y for widget in self.return_all_widgets()
        )
        min_width: int = max(
            widget.dimensions.current_width + widget.dimensions.current_x for widget in self.return_all_widgets()
        )

        return min_height, min_width

    def get_max_height_width_widgets(self) -> tuple[int, int]:
        if not self.return_widgets():
            return 0, 0

        min_height: int = max(
            widget.dimensions.current_height + widget.dimensions.current_y for widget in self.return_widgets()
        )
        min_width: int = max(
            widget.dimensions.current_width + widget.dimensions.current_x for widget in self.return_widgets()
        )

        return min_height, min_width

    def add_floating_widget(self, floating_widget: FloatingWidget) -> None:
        self.remove_floating_widget_by_name_title(floating_widget.name, floating_widget.title)
        self._floating_widgets.append(floating_widget)

    def remove_floating_widget_by_name_title(self, name: str, title: str) -> None:
        remove_floating_widgets: list[FloatingWidget] = []

        for floating_widget in self._floating_widgets:
            if (
                    floating_widget.name == name and
                    floating_widget.title == title
            ):
                remove_floating_widgets.append(floating_widget)

        for floating_widget in remove_floating_widgets:
            self.remove_floating_widget(floating_widget)

    def remove_floating_widget(self, floating_widget: FloatingWidget) -> None:
        if floating_widget in self._floating_widgets:
            self._floating_widgets.remove(floating_widget)
            if floating_widget.win:
                floating_widget.win.erase()

    def discover_custom_widgets(self) -> list[str]:
        if self.test_env:
            return []
        return self.widget_loader.discover_custom_widgets()

    def scan_config(self) -> None:
        # Scan configs
        config_scanner: ConfigScanner = ConfigScanner(self.config_loader)
        config_scan_results: LogMessages | bool = config_scanner.scan_config(self.discover_custom_widgets())

        if config_scan_results is not True:
            raise ConfigScanFoundError(config_scan_results)  # type: ignore[arg-type]

    def build_widgets(self) -> dict[str, Widget]:
        # Import all widget modules
        custom_widget_modules: dict[str, types.ModuleType] = self.widget_loader.load_custom_widget_modules()

        try:
            widget_dict = self.widget_loader.build_widgets(self, custom_widget_modules)
            return widget_dict
        except Exception:
            raise

    def start_reloader_thread(self) -> None:
        self.reloader_thread.start()

    def init_curses_setup(self) -> None:
        curses.mousemask(curses.ALL_MOUSE_EVENTS)
        curses.curs_set(0)
        curses.mouseinterval(0)
        self.stdscr.move(0, 0)
        curses.set_escdelay(25)
        self.init_colors()
        self.stdscr.bkgd(' ', curses.color_pair(1))  # Activate standard color
        self.stdscr.clear()
        self.stdscr.refresh()
        self.stdscr.timeout(100)

    def loading_screen(self) -> None:
        widgets_by_z: dict[int, list[Widget]] = self.return_widgets_ordered_by_z_index()
        for widget in (
                w
                for z in sorted(widgets_by_z)
                for w in widgets_by_z[z]
        ):
            if not widget.win:
                continue
            self.draw_widget(widget, loading=True)
            widget.add_widget_content([' Loading... '])
            widget.win.refresh()
        return None

    def initialize_widgets(self) -> None:
        for widget in self.return_widgets():
            widget.init(self)
        return None

    def move_widgets_resize(
            self,
            min_height_current_layout: int,
            min_width_current_layout: int
    ) -> None:
        current_terminal_height: int
        current_terminal_width: int

        current_terminal_height, current_terminal_width = self.stdscr.getmaxyx()

        self.reactivate_all_widgets()  # Allows for making the terminal bigger

        for widget in self.return_all_widgets():
            if not widget.dimensions.within_borders(current_terminal_height, current_terminal_width):
                self.deactivate_widget(widget)

        self.reinit_all_widget_windows()  # Allows for making the terminal bigger
        self.reinit_all_floating_windows()  # Allows for making the terminal bigger
        if self.validate_terminal_too_small(min_height_current_layout, min_width_current_layout):
            self.display_error_message_screen_too_small(min_height_current_layout, min_width_current_layout)
        else:
            self.remove_floating_widget_by_name_title(
                'terminal_too_small',
                ' Terminal Too Small '
            )

    def handle_mouse_input(self, key: int) -> None:
        if key == CursesKeys.MOUSE:
            try:
                _me_id, mx, my, _mz, b_state = curses.getmouse()

                # Bitwise and, check if button 1 is pressed
                if b_state & CursesKeys.BUTTON1_PRESSED:
                    self.switch_windows(mx, my, b_state)
                    if self.ui_state.highlighted is not None:
                        self.ui_state.highlighted.mouse_action(mx, my, b_state, self)
            except CursesError:
                # Ignore invalid mouse events (like scroll in some terminals)
                return

    def handle_key_input(self, key: int, min_height_current_layout: int, min_width_current_layout: int) -> None:
        highlighted_widget: Widget | None = self.ui_state.highlighted

        if key == CursesKeys.ESCAPE:
            if highlighted_widget is not None:
                if self.base_config.reset_help_mode_after_escape:
                    highlighted_widget.disable_help_mode()
            self.ui_state.previously_highlighted = self.ui_state.highlighted
            self.ui_state.highlighted = None

        if key == curses.KEY_RESIZE:
            self.move_widgets_resize(min_height_current_layout, min_width_current_layout)
            return

        if highlighted_widget is None:
            if key == ord(self.base_config.quit_key):
                raise StopException(self.log_messages)
            elif key == ord(self.base_config.help_key):
                pass  # TODO: General help page
            elif key == ord(self.base_config.reload_key):  # Reload widgets & config
                raise RestartException
            return
        else:
            if key == ord(self.base_config.help_key):
                highlighted_widget.toggle_help_mode()

        highlighted_widget.keyboard_action(key, self)

    def switch_windows(self, mx: int, my: int, _b_state: int) -> None:
        if self.ui_state.highlighted:
            if self.base_config.reset_help_mode_after_escape:
                self.ui_state.highlighted.disable_help_mode()

        # Find which widget was clicked
        self.ui_state.previously_highlighted = self.ui_state.highlighted
        self.ui_state.highlighted = None

        widgets_by_z: dict[int, list[Widget]] = self.return_widgets_ordered_by_z_index()

        for widget in (
                w
                for z in sorted(widgets_by_z, reverse=True)  # Start at highest z-index
                for w in widgets_by_z[z]
        ):
            y1 = widget.dimensions.current_y
            y2 = y1 + widget.dimensions.current_height
            x1 = widget.dimensions.current_x
            x2 = x1 + widget.dimensions.current_width

            if y1 <= my <= y2 and x1 <= mx <= x2:
                self.ui_state.highlighted = widget
                break

    def validate_terminal_too_small(self, min_height: int, min_width: int) -> bool:
        height, width = self.stdscr.getmaxyx()

        if height < min_height or width < min_width:
            return True
        return False

    def display_error_message_screen_too_small(self, min_height: int, min_width: int) -> None:
        current_terminal_height, current_terminal_width = self.stdscr.getmaxyx()

        warning_message_height: int = 10
        warning_message_width: int = 50

        warning_message_y = (current_terminal_height - warning_message_height) // 2
        warning_message_x = (current_terminal_width - warning_message_width) // 2
        warning_message_z_index: int = 1000

        warning_error: TerminalTooSmall = TerminalTooSmall(
            current_terminal_height,
            current_terminal_width,
            min_height,
            min_width
        )

        warning_dimensions: Dimensions = Dimensions(
            warning_message_height,
            warning_message_width,
            warning_message_y,
            warning_message_x,
            warning_message_z_index
        )

        if not warning_dimensions.within_borders(current_terminal_height, current_terminal_width):
            raise warning_error

        warning: WarningWidget = WarningWidget(
            'terminal_too_small',
            ' Terminal Too Small ',
            warning_error,
            str(warning_error).split('\n'),
            warning_dimensions,
            self.stdscr
        )

        self.add_floating_widget(warning)

    def init_colors(self) -> None:
        if self.test_env:
            return  # Do not set up colours

        curses.start_color()
        if self.base_config.use_standard_terminal_background:
            curses.use_default_colors()

        can_change_color = curses.can_change_color()
        if can_change_color:
            if not self.base_config.use_standard_terminal_background:
                curses.init_color(
                    self.base_config.BACKGROUND_NUMBER,  # type: ignore[unused-ignore]
                    *self.base_config.background_color.rgb_to_0_1000()  # type: ignore[unused-ignore]
                )  # type: ignore[unused-ignore]
                # (PyCharm sees this as an error -> unused-ignore)

            for color_number, color in self.base_config.base_colors.items():
                curses.init_color(
                    color_number,  # type: ignore[unused-ignore]
                    *color[1].rgb_to_0_1000()  # type: ignore[union-attr]
                    # This will always be RGBColor, until the next part of the code is reached
                )  # type: ignore[unused-ignore]
                # (PyCharm sees this as an error -> unused-ignore)
        else:
            self.base_config.base_colors = {
                2: (1, curses.COLOR_WHITE),
                15: (2, curses.COLOR_BLUE),
                13: (3, curses.COLOR_CYAN),
                9: (4, curses.COLOR_YELLOW),
                10: (5, curses.COLOR_RED)
            }

        for color_number, color in self.base_config.base_colors.items():
            curses.init_pair(
                color[0],
                color_number,
                self.base_config.BACKGROUND_NUMBER
            )

        gradient_color: list[int] = [
            28, 34, 40, 46, 82, 118, 154, 172,
            196, 160, 127, 135, 141, 99, 63, 33, 27, 24
        ]

        for i, color in enumerate(gradient_color, start=6):  # type: ignore
            curses.init_pair(i, color, self.base_config.BACKGROUND_NUMBER)  # type: ignore[arg-type]

    def cleanup_curses_setup(self) -> None:
        self.stop_event.set()
        self.reloader_thread.join(timeout=1)
        try:
            curses.endwin()
        except CursesError:
            pass  # Ignore; Doesn't happen on Py3.13, but does on some versions of Py3.12

    def display_error(self, widget: Widget, content: list[str]) -> None:
        self.draw_widget(widget, ' Error ', error=True)
        widget.add_widget_content(content)

    def reload_widget_scheduler_function(self) -> None:
        while not self.stop_event.is_set():
            now = time_module.time()

            # Calculate reloadable widgets every time every widget has reloaded
            reloadable_widgets: list[Widget] = [w for w in self.return_widgets() if w.updatable()]
            # Update widgets if their interval has passed
            for widget in reloadable_widgets:
                if self.stop_event.is_set():  # Check on every iteration as well
                    break

                if widget.last_updated is None:
                    continue

                # See widget.updatable(), types are safe.
                if now - widget.last_updated >= widget.interval:  # type: ignore[operator]
                    try:
                        widget.draw_data = widget.update(self)
                        widget.last_updated = now
                    except ConfigSpecificException as e:
                        widget.draw_data = {'__error__': e.log_messages}
                    except Exception as e:
                        widget.draw_data = {'__error__': str(e)}

            # Small sleep to avoid busy loop, tuned to a small value
            time_module.sleep(0.06667)  # -> ~15 FPS

    @staticmethod
    def crash_on_thread_exception(args: typing.Any) -> None:
        print("Thread crashed:", args.exc_type.__name__, args.exc_value)
        traceback.print_tb(args.exc_traceback)
        sys.exit(1)

    @staticmethod
    def update_screen() -> None:
        curses.doupdate()


class BaseConfig:
    def __init__(
        self,
        log_messages: LogMessages,
        _test_env: bool,
        use_standard_terminal_background: bool | None = None,
        background_color: dict[str, int] | None = None,
        foreground_color: dict[str, int] | None = None,
        primary_color: dict[str, int] | None = None,
        secondary_color: dict[str, int] | None = None,
        loading_color: dict[str, int] | None = None,
        error_color: dict[str, int] | None = None,
        quit_key: str | None = None,
        reload_key: str | None = None,
        help_key: str | None = None,
        reset_help_mode_after_escape: bool | None = None,
        **kwargs: typing.Any
    ) -> None:

        base_cfg = BaseStandardFallBackConfig()

        # Load fallback colours
        self.background_color: RGBColor = base_cfg.background_color
        self.foreground_color: RGBColor = base_cfg.foreground_color
        self.primary_color: RGBColor = base_cfg.primary_color
        self.secondary_color: RGBColor = base_cfg.secondary_color
        self.loading_color: RGBColor = base_cfg.loading_color
        self.error_color: RGBColor = base_cfg.error_color

        self.use_standard_terminal_background: bool = base_cfg.use_standard_terminal_background
        self.quit_key: str = base_cfg.quit_key
        self.reload_key: str = base_cfg.reload_key
        self.help_key: str = base_cfg.help_key
        self.reset_help_mode_after_escape: bool = base_cfg.reset_help_mode_after_escape

        def apply_color(field_name: str, value: dict[str, int] | None) -> RGBColor:
            if value is None:
                log_messages.add_log_message(LogMessage(
                    f'Configuration for {field_name} is missing (base.yaml, falling back to standard config)',
                    LogLevels.WARNING.key,
                ))
                return getattr(self, field_name)  # type: ignore[no-any-return]

            try:
                return RGBColor.add_rgb_color_from_dict(value)
            except KeyError as e:
                log_messages.add_log_message(LogMessage(
                    f'Configuration for {field_name} is missing for {e}',
                    LogLevels.ERROR.key,
                ))
            except ValueError as e:
                log_messages.add_log_message(LogMessage(
                    f'Configuration for {field_name} is invalid for {e}',
                    LogLevels.ERROR.key,
                ))
            return getattr(self, field_name)  # type: ignore[no-any-return]

        # Apply all colours via loop
        color_inputs = {
            'background_color': background_color,
            'foreground_color': foreground_color,
            'primary_color': primary_color,
            'secondary_color': secondary_color,
            'loading_color': loading_color,
            'error_color': error_color,
        }

        for name, val in color_inputs.items():
            setattr(self, name, apply_color(name, val))

        # Mapping used later
        self.base_colors: dict[int, tuple[int, RGBColor] | tuple[int, int]] = {
            2: (1, self.foreground_color),
            15: (2, self.primary_color),
            13: (3, self.secondary_color),
            9: (4, self.loading_color),
            10: (5, self.error_color),
        }

        def apply_bool(field: str, value: bool | None) -> bool:
            if value is None:
                log_messages.add_log_message(LogMessage(
                    f'Configuration for {field} is missing (base.yaml, falling back to standard config)',
                    LogLevels.WARNING.key,
                ))
                return getattr(self, field)  # type: ignore[no-any-return]

            if not isinstance(value, bool):
                log_messages.add_log_message(LogMessage(
                    f'Configuration for {field} is invalid (not True / False)',
                    LogLevels.ERROR.key,
                ))
                return getattr(self, field)

            return value

        self.use_standard_terminal_background = apply_bool(
            'use_standard_terminal_background',
            use_standard_terminal_background
        )
        self.reset_help_mode_after_escape = apply_bool(
            'reset_help_mode_after_escape',
            reset_help_mode_after_escape
        )

        self.BACKGROUND_NUMBER: int = -1 if self.use_standard_terminal_background else 1
        if _test_env:
            self.BACKGROUND_NUMBER = -1

        self.BACKGROUND_FOREGROUND_PAIR_NUMBER: int = 1
        self.PRIMARY_PAIR_NUMBER: int = 2
        self.SECONDARY_PAIR_NUMBER: int = 3
        self.LOADING_PAIR_NUMBER: int = 4
        self.ERROR_PAIR_NUMBER: int = 5

        def apply_key(field: str, value: str | None) -> str:
            if value is None:
                log_messages.add_log_message(LogMessage(
                    f'Configuration for {field} is missing (base.yaml, falling back to standard config)',
                    LogLevels.WARNING.key,
                ))
                return getattr(self, field)  # type: ignore[no-any-return]

            if len(value) != 1:
                log_messages.add_log_message(LogMessage(
                    f'Configuration for {field} value wrong length (not 1)',
                    LogLevels.ERROR.key,
                ))
                return getattr(self, field)  # type: ignore[no-any-return]

            if not (value.isalpha() or value.isdigit()):
                log_messages.add_log_message(LogMessage(
                    f'Configuration for {field} value not alphabetic or numeric',
                    LogLevels.ERROR.key,
                ))
                return getattr(self, field)  # type: ignore[no-any-return]

            return value

        self.quit_key = apply_key('quit_key', quit_key)
        self.reload_key = apply_key('reload_key', reload_key)
        self.help_key = apply_key('help_key', help_key)

        # Unknown config keys
        for key in kwargs:
            log_messages.add_log_message(LogMessage(
                f'Configuration for key "{key}" is not expected (base.yaml)',
                LogLevels.WARNING.key,
            ))


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
        self.reset_help_mode_after_escape: bool = True


class UIState:
    def __init__(self) -> None:
        self.previously_highlighted: Widget | None = None
        self.highlighted: Widget | None = None


# endregion WidgetContainer & essentials

# region Custom Exceptions

class TWidgetException(Exception):
    """Superclass for all `twidgets`-specific errors, never gets raised directly"""
    def __init__(self, *args: typing.Any) -> None:
        super().__init__(args)


class RestartException(TWidgetException):
    """Raised to signal that the curses UI should restart"""


class StopException(TWidgetException):
    """Raised to signal that the curses UI should stop"""
    def __init__(self, log_messages: LogMessages) -> None:
        self.log_messages: LogMessages = log_messages


class YAMLParseException(TWidgetException):
    """Raised to signal that there was an error parsing a YAML file"""


class TerminalTooSmall(TWidgetException):
    def __init__(self, height: int, width: int, min_height: int, min_width: int) -> None:
        """Raised to signal that the terminal is too small"""
        self.height = height
        self.width = width
        self.min_height = min_height
        self.min_width = min_width
        super().__init__(height, width)

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return \
            f'\n' \
            f'⚠️ Terminal too small.\n' \
            f'Min. size: {self.min_width}x{self.min_height} (Width x Height)\n' \
            f'Current size: {self.width}x{self.height}\n' \
            f'Either decrease your font size,\n' \
            f'increase the size of the terminal,\n' \
            f'or remove widgets.\n'


class ConfigScanFoundError(TWidgetException):
    """Raised to signal that the ConfigScanner found an error"""
    def __init__(self, log_messages: LogMessages) -> None:
        self.log_messages: LogMessages = log_messages
        super().__init__(log_messages)


class ConfigFileNotFoundError(TWidgetException):
    """Raised to signal that a configuration (or base configuration) file was not found"""
    def __init__(self, error_details: str) -> None:
        self.error_details: str = error_details
        super().__init__(error_details)


class ConfigSpecificException(TWidgetException):
    """Raised to signal that something is wrong with a widget configuration"""
    def __init__(self, log_messages: LogMessages) -> None:
        self.log_messages: LogMessages = log_messages
        super().__init__(log_messages)


class WidgetSourceFileException(TWidgetException):
    """Raised to signal that the code for some widget python file is not correct"""
    def __init__(self, log_messages: LogMessages) -> None:
        self.log_messages: LogMessages = log_messages
        super().__init__(log_messages)


class UnknownException(TWidgetException):
    """Raised instead of Exception to keep log messages and the initial exception that caused UnknownException"""
    def __init__(self, widget_container: WidgetContainer, initial_exception: Exception) -> None:
        self.widget_container: WidgetContainer = widget_container
        self.initial_exception = initial_exception
        super().__init__(widget_container, initial_exception)


class DebugException(TWidgetException):
    """Raised to make debugging easier (not used in production)"""
    def __init__(self, error_message: str) -> None:
        self.error_message = error_message
        super().__init__(error_message)


# endregion Custom Exceptions

# region Logging

class LogLevels(enum.Enum):
    UNKNOWN = (0, '? Unknown')
    INFO = (1, 'ℹ️ Info')
    DEBUG = (2, '🐞 Debug')
    WARNING = (3, '⚠️ Warnings')
    ERROR = (4, '⚠️ Errors')  # Alternative Symbol: 🔴️

    @property
    def key(self) -> int:
        return self.value[0]

    @property
    def label(self) -> str:
        return self.value[1]

    @classmethod
    def from_key(cls, key: int) -> LogLevels:
        """Return the LogLevels member that matches the key"""
        for level in cls:
            if level.key == key:
                return level
        return LogLevels.UNKNOWN


class LogMessage:
    def __init__(self, message: str, level: int) -> None:
        self.log_time: datetime.datetime = datetime.datetime.now()
        self.message: str = message
        self.level: int = level

    def __str__(self) -> str:
        return f'{self.log_time.strftime("%H:%M:%S")}: {self.message}'

    def __repr__(self) -> str:
        return self.message

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LogMessage):
            return NotImplemented
        if self.message == other.message and self.level == other.level:
            return True
        return False

    def is_error(self) -> bool:
        if self.level == LogLevels.ERROR.key:
            return True
        return False


class LogMessages:
    def __init__(self, log_messages: list[LogMessage] | None = None) -> None:
        if log_messages is None:
            self.log_messages: list[LogMessage] = []
        else:
            self.log_messages = log_messages

    def __add__(self, other: LogMessages) -> LogMessages:
        new_log: LogMessages = LogMessages()
        new_log.log_messages = self.log_messages + other.log_messages
        return new_log

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LogMessages):
            return NotImplemented
        return self.log_messages == other.log_messages

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, LogMessages):
            return NotImplemented
        return self.log_messages != other.log_messages

    def __contains__(self, item: LogMessage) -> bool:
        for log_message in list(self.log_messages):
            if log_message == item:
                return True
        return False

    def __iter__(self) -> collections.abc.Iterator[LogMessage]:
        return iter(self.log_messages)

    def add_log_message(self, message: LogMessage) -> None:
        self.log_messages.append(message)

    def print_log_messages(self, heading: str) -> None:
        if not self.log_messages:
            return

        print(heading, end='')
        log_messages_by_level: dict[int, list[LogMessage]] = {}
        for message in self.log_messages:
            if message.level in log_messages_by_level.keys():
                log_messages_by_level[message.level].append(message)
            else:
                log_messages_by_level[message.level] = [message]

        for level in sorted(log_messages_by_level.keys()):
            if log_messages_by_level[level]:
                print(f'\n{LogLevels.from_key(level).label}:')
                for message in log_messages_by_level[level]:
                    print(message)

    def contains_error(self) -> bool:
        for message in self.log_messages:
            if message.is_error():
                return True
        return False

    def is_empty(self) -> bool:
        if self.log_messages:
            return False
        return True


# endregion Logging

# region Loaders & Scanners

class WidgetLoader:
    def __init__(self, widget_container: WidgetContainer) -> None:
        self._test_env = widget_container.test_env
        if self._test_env:
            self.PY_WIDGET_DIR = widget_container.SCRIPT_DIR_PY_WIDGET_DIR
        else:
            self.PY_WIDGET_DIR = widget_container.ROOT_PY_WIDGET_DIR

    def discover_custom_widgets(self) -> list[str]:
        """Discover user-defined widgets in ~/.config/twidgets/py_widgets/*_widget.py"""
        widget_names: list[str] = []
        if not self.PY_WIDGET_DIR.exists():
            return widget_names

        for file in self.PY_WIDGET_DIR.iterdir():
            if file.is_file() and file.name.endswith('_widget.py'):
                widget_name = file.stem.replace('_widget', '')
                widget_names.append(widget_name)

        return widget_names

    def load_custom_widget_modules(self) -> dict[str, types.ModuleType]:
        """Load custom widgets dynamically from files"""
        modules: dict[str, types.ModuleType] = {}
        if not self.PY_WIDGET_DIR.exists():
            return modules

        for file in self.PY_WIDGET_DIR.iterdir():
            widget_name = ''
            try:
                if file.is_file() and file.name.endswith('_widget.py'):
                    # widget_name = file.stem.replace('_widget', '')
                    widget_name = file.stem

                    spec = importlib.util.spec_from_file_location(widget_name, file)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[widget_name] = module
                        spec.loader.exec_module(module)
                        modules[widget_name] = module
            except Exception as e:
                raise WidgetSourceFileException(LogMessages(
                    [LogMessage(f'Error loading widget {widget_name}: {e}', LogLevels.ERROR.key)]
                ))

        return modules

    @staticmethod
    def build_widgets(widget_container: WidgetContainer, modules: dict[str, types.ModuleType]) -> dict[str, Widget]:
        widgets: dict[str, Widget] = {}
        for name, module in modules.items():
            widget_config: Config = widget_container.config_loader.load_widget_config(
                widget_container.log_messages, name
            )
            try:
                widgets[name] = module.build(widget_container.stdscr, widget_config)
            except Exception:
                raise WidgetSourceFileException(
                    LogMessages([LogMessage(
                        f'Code for `build` is missing / incorrect ("{name}" widget)', LogLevels.ERROR.key
                    )])
                )

        return widgets


class ConfigLoader:
    def __init__(self, widget_container: WidgetContainer) -> None:
        self.SCRIPT_DIR = widget_container.SCRIPT_DIR
        self.CONFIG_DIR = widget_container.ROOT_CONFIG_DIR
        self.PER_WIDGET_CONFIG_DIR = widget_container.ROOT_PER_WIDGET_CONFIG_DIR
        self._test_env = widget_container.test_env
        if self._test_env:
            dotenv.load_dotenv(self.SCRIPT_DIR / 'config' / f'secrets.env.example')
        else:
            dotenv.load_dotenv(self.CONFIG_DIR / 'secrets.env')

    def reload_secrets(self) -> None:
        if self._test_env:
            dotenv.load_dotenv(self.SCRIPT_DIR / 'config' / f'secrets.env.example')
        else:
            dotenv.load_dotenv(self.CONFIG_DIR / 'secrets.env', override=True)

    @staticmethod
    def get_secret(name: str, default: typing.Any = None) -> str | None:
        return os.getenv(name, default)

    @staticmethod
    def load_yaml(path: pathlib.Path) -> dict[typing.Any, typing.Any]:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except yaml.scanner.ScannerError:
            raise YAMLParseException(f'Config for path "{path}" not valid YAML')

    def load_base_config(self, log_messages: LogMessages) -> BaseConfig:
        base_path = self.CONFIG_DIR / 'base.yaml'
        if not base_path.exists():
            if self._test_env:
                # Fallback completely to BaseStandardFallbackConfig
                return BaseConfig(log_messages=log_messages, _test_env=self._test_env)
            else:
                raise ConfigFileNotFoundError(f'Base config "{base_path}" not found')
        try:
            pure_yaml: dict[typing.Any, typing.Any] = self.load_yaml(base_path)
        except yaml.parser.ParserError:
            raise YAMLParseException(f'Base config "{base_path}" not valid YAML')

        return BaseConfig(log_messages=log_messages, _test_env=self._test_env, **pure_yaml)

    def load_widget_config(self, log_messages: LogMessages, widget_name: str) -> Config:
        config_name: str = widget_name.replace('_widget', '')

        if self._test_env:
            path = self.SCRIPT_DIR / 'config' / 'widgets' / f'{config_name}.yaml'
            if not path.exists():
                raise ConfigFileNotFoundError(f'Config for widget "{config_name}" not found (test_env), {path}')
            try:
                pure_yaml: dict[typing.Any, typing.Any] = self.load_yaml(path)
            except yaml.parser.ParserError:
                raise YAMLParseException(f'Config for widget "{config_name}" not valid YAML')

            return Config(file_name=config_name, log_messages=log_messages, _test_env=self._test_env, **pure_yaml)

        path = self.PER_WIDGET_CONFIG_DIR / f'{config_name}.yaml'
        if not path.exists():
            raise ConfigFileNotFoundError(f'Config for widget "{config_name}" not found')
        try:
            pure_yaml = self.load_yaml(path)
        except yaml.parser.ParserError:
            raise YAMLParseException(f'Config for widget "{config_name}" not valid YAML')

        return Config(file_name=config_name, log_messages=log_messages, _test_env=self._test_env, **pure_yaml)


class ConfigScanner:
    def __init__(self, config_loader: ConfigLoader) -> None:
        self.config_loader: ConfigLoader = config_loader

    def scan_config(self, widget_names: list[str]) -> LogMessages | typing.Literal[True]:
        """Scan config, either returns log messages or 'True' representing that no errors were found"""
        final_log: LogMessages = LogMessages()

        current_log: LogMessages = LogMessages()
        try:
            self.config_loader.load_base_config(current_log)
            if current_log.contains_error():
                final_log += current_log
        except YAMLParseException as e:
            final_log += LogMessages([LogMessage(str(e), LogLevels.ERROR.key)])

        for widget_name in widget_names:
            config_name: str = widget_name.replace('_widget', '')
            current_log = LogMessages()
            try:
                self.config_loader.load_widget_config(current_log, config_name)
                if current_log.contains_error():
                    final_log += current_log
            except YAMLParseException as e:
                final_log += LogMessages([LogMessage(str(e), LogLevels.ERROR.key)])

        if final_log.contains_error():
            return final_log
        return True


# endregion Loaders & Scanners

# region Constants

CursesWindowType = _curses.window  # Type of stdscr, widget.win
CursesError = _curses.error


class CursesColors(enum.IntEnum):
    REVERSE = curses.A_REVERSE
    BOLD = curses.A_BOLD


class CursesKeys(enum.IntEnum):
    UP = curses.KEY_UP
    DOWN = curses.KEY_DOWN
    LEFT = curses.KEY_LEFT
    RIGHT = curses.KEY_RIGHT
    ENTER = curses.KEY_ENTER
    BACKSPACE = curses.KEY_BACKSPACE
    ESCAPE = 27
    MOUSE = curses.KEY_MOUSE
    BUTTON1_PRESSED = curses.BUTTON1_PRESSED

# endregion Constants


def curses_wrapper(func: typing.Callable[[CursesWindowType], None]) -> None:
    curses.wrapper(func)


def returnable_curses_wrapper(func: typing.Callable[[CursesWindowType], typing.Any]) -> typing.Any:
    result_container: dict[str, typing.Any] = {}

    def inner(stdscr: CursesWindowType) -> None:
        result_container['result'] = func(stdscr)

    curses_wrapper(inner)
    return result_container['result']
