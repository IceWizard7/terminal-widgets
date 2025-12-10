import typing
import unittest
from twidgets.core.base import WidgetContainer, returnable_curses_wrapper, CursesWindowType
import twidgets.core.base as base
import twidgets.widgets as widgets_pkg
import os
import time as time_module

os.environ['LINES'] = '100'
os.environ['COLUMNS'] = '200'


class TestWidgetContainer(unittest.TestCase):
    def test_whole_screen(self) -> None:
        def main_curses(stdscr: CursesWindowType) -> list[str]:
            widget_container: WidgetContainer = WidgetContainer(stdscr, widgets_pkg, test_env=True)
            widget_container.scan_config()
            widget_container.init_curses_setup()
            widget_container.add_widget_list(list(widget_container.build_widgets().values()))
            widget_container.loading_screen()
            widget_container.initialize_widgets()
            widget_container.start_reloader_thread()

            # Give the reloader thread 0.5 seconds to load every widget
            time_module.sleep(0.01)
            # (Re-)Draw every widget

            done: bool = False

            while not done:
                done = True

                for widget in widget_container.return_widgets():
                    try:
                        if not widget.updatable():
                            widget.draw(widget_container)
                            widget.noutrefresh()
                            continue

                        if widget.draw_data:
                            with widget.lock:
                                data_copy: typing.Any = widget.draw_data.copy()
                            # if '__error__' not in data_copy:
                            widget.draw(widget_container, data_copy)
                        else:
                            # Data still loading
                            done = False
                    except base.ConfigSpecificException:
                        # TODO: We need to assume some kind of base config for the unit testing, load from repo
                        pass

                    widget.noutrefresh()
                time_module.sleep(0.01)
            widget_container.update_screen()

            screenshot: list[str] = []
            height, width = stdscr.getmaxyx()
            for y in range(height):
                _line: str = stdscr.instr(y, 0, width).decode('utf-8')
                screenshot.append(_line)

            return screenshot

        result: list[str] = returnable_curses_wrapper(main_curses)
        print('\n\n')
        for line in result:
            if any(char != ' ' for char in str(line)):
                print(line)
        print('\n')


# TODO: Can I integrate this? Does github workflow use a terminal...?!

# python -m tests.test_whole_screen
# python tests/run_tests.py
