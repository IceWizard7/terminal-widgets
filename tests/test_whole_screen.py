import typing
import unittest
from twidgets.core.base import WidgetContainer, returnable_curses_wrapper, CursesWindowType
import os
import time as time_module

os.environ['LINES'] = '30'
os.environ['COLUMNS'] = '172'


class TestWholeScreen(unittest.TestCase):
    def test_whole_screen(self) -> None:
        def main_curses(stdscr: CursesWindowType) -> list[str]:
            widget_container: WidgetContainer = WidgetContainer(stdscr, test_env=True)
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
                    if not widget.updatable():
                        widget.draw_function(widget_container)
                        widget.noutrefresh()
                        continue

                    if widget.draw_data:
                        with widget.lock:
                            data_copy: typing.Any = widget.draw_data.copy()
                        # if '__error__' not in data_copy:
                        widget.draw_function(widget_container, data_copy)
                    else:
                        # Data still loading
                        done = False

                    widget.noutrefresh()
                time_module.sleep(0.01)
            widget_container.update_screen()

            screenshot: list[str] = []

            height: int
            width: int
            height, width = stdscr.getmaxyx()
            for y in range(height):
                y_line: str = stdscr.instr(y, 0, width).decode('utf-8')
                screenshot.append(y_line)

            return screenshot

        result: list[str] = returnable_curses_wrapper(main_curses)
        with open('tests/test_screen_expected_result.txt', 'r') as file:
            expected_result: list[str] = file.readlines()
        ignored_character: str = '*'  # Char (in test_screen_expected_result.txt) that means Any

        if len(result) != len(expected_result):
            raise AssertionError(
                f'Length of screenshot {len(result)} != {len(expected_result)} (expected {len(expected_result)})'
            )

        line: str
        expected_line: str
        print('\n\nResult:\n\n')
        for line in result:
            print(line)

        for line_count, (line, expected_line) in enumerate(zip(result, expected_result)):
            for char_count, chars in enumerate(zip(line, expected_line)):
                char: str = chars[0]
                expected_char: str = chars[1]
                # print(f'Checking "{char}" == "{expected_char}"')
                if expected_char == ignored_character:
                    continue
                if char == expected_char:
                    continue
                raise AssertionError(
                    f'"{char}" != "{expected_char}"'
                    f' (expected "{expected_char}"), Line {line_count + 1}, Char {char_count + 1}'
                )

        self.assertEqual(True, True)
