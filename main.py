import curses
import time
import typing
import threading
import sys

import widgets.base as base
import widgets.clock as clock
import widgets.greetings as greetings
import widgets.calendar as calendar
import widgets.neofetch as neofetch
import widgets.news as news
import widgets.weather as weather
import widgets.todo as todo
import widgets.mode as mode
# Add more widgets here (1)

from widgets.config import MINIMUM_WIDTH, MINIMUM_HEIGHT
from utils.config_loader import load_widget_config


def switch_windows(
        mx: int,
        my: int,
        _b_state: int,
        widgets: dict[str, base.Widget]
) -> None:
    widget_list = list(widgets.values())
    mode_widget = widgets['mode']
    todo_widget = widgets['todo']

    # Find which widget was clicked
    base.ui_state.highlighted = None
    for widget in widget_list:
        y1 = widget.dimensions.y
        y2 = y1 + widget.dimensions.height
        x1 = widget.dimensions.x
        x2 = x1 + widget.dimensions.width
        if y1 <= my <= y2 and x1 <= mx <= x2:
            base.ui_state.highlighted = widget
            break
    mode_widget.draw()
    mode_widget.direct_refresh()

    todo.mark_highlighted_line(todo_widget, my)

    todo_widget.draw()
    todo_widget.direct_refresh()


def handle_key_input(
        key: typing.Any,
        widget_list: list[base.Widget],
        stop_event: threading.Event,
        widget_dict: dict[str, base.Widget]
) -> None:
    mode_widget: base.Widget = widget_dict['mode']
    todo_widget: base.Widget = widget_dict['todo']
    highlighted_widget: base.Widget | None = base.ui_state.highlighted

    if key == 27:  # ESC key
        base.ui_state.highlighted = None

        mode_widget.draw()
        mode_widget.direct_refresh()

        todo.remove_highlighted_line(todo_widget)
        todo_widget.direct_refresh()
        return

    if highlighted_widget is None:
        if key == ord('q'):
            stop_event.set()
        elif key == ord('h'):
            pass  # TODO: Help page? Even for each window?
        elif key == ord('r'):  # Reload widgets & config
            base.loading_screen(widget_list)
            raise base.RestartException
        return

    if highlighted_widget == todo_widget:
        if 'todos' not in todo_widget.data:
            return
        len_todos = len(todo_widget.data['todos'])
        selected = todo_widget.data.get('selected_line', 0)

        if not isinstance(selected, int):
            selected = 0

        # Navigation
        if key == curses.KEY_UP:
            selected -= 1
        elif key == curses.KEY_DOWN:
            selected += 1

        # Wrap around
        if selected < 0:
            selected = len_todos - 1

        if selected > (len_todos - 1):  # If you delete the last to-do, this will wrap around to 0
            selected = 0

        todo_widget.data['selected_line'] = selected

        # Add new to_do
        if key in (curses.KEY_ENTER, 10, 13):
            new_todo = base.prompt_user_input(todo_widget, 'New To-Do: ')
            if new_todo.strip():
                todo.add_todo(todo_widget, new_todo.strip())

        # Delete to_do
        elif key in (curses.KEY_BACKSPACE, 127, 8):  # Backspace
            if len_todos > 0:
                confirm = base.prompt_user_input(todo_widget, 'Confirm deletion (y): ')
                if confirm.lower().strip() in ['y']:
                    todo.remove_todo(todo_widget, todo_widget.data['selected_line'])

        todo_widget.draw()
        todo_widget.direct_refresh()


def reload_widget_scheduler(widget_dict: dict[str, base.Widget], stop_event: threading.Event) -> None:
    widget_list = list(widget_dict.values())
    reloadable_widgets = [w for w in widget_list if w.updatable()]

    todo_widget = widget_dict['todo']

    while not stop_event.is_set():
        now = time.time()
        # Update widgets if their interval has passed
        for widget in reloadable_widgets + [todo_widget]:
            if stop_event.is_set():  # Check on every iteration as well
                break
            if widget == todo_widget:
                todo.load_todos(widget)
                todo_widget.data['updating'] = False
                continue

            if widget.last_updated is None:
                continue

            # See widget.updatable()
            if now - widget.last_updated >= widget.interval:  # type: ignore[operator]
                try:
                    widget.data = widget.update()
                    widget.last_updated = now
                except Exception as e:
                    widget.data = {"__error__": str(e)}
        # Small sleep to avoid busy loop, tuned to a small value
        time.sleep(0.06667)  # -> 15 FPS


def main_curses(stdscr: typing.Any) -> None:
    base.init_curses_setup(stdscr)
    base.validate_terminal_size(stdscr)

    clock_widget: base.Widget = clock.build(stdscr, load_widget_config('clock'))
    greetings_widget: base.Widget = greetings.build(stdscr, load_widget_config('greetings'))
    calendar_widget: base.Widget = calendar.build(stdscr, load_widget_config('calendar'))
    mode_widget: base.Widget = mode.build(stdscr, load_widget_config('mode'))
    todo_widget: base.Widget = todo.build(stdscr, load_widget_config('todo'))
    weather_widget: base.Widget = weather.build(stdscr, load_widget_config('weather'))
    news_widget: base.Widget = news.build(stdscr, load_widget_config('news'))
    neofetch_widget: base.Widget = neofetch.build(stdscr, load_widget_config('neofetch'))
    # Add more widgets here (2)

    # Loading order is defined here
    widget_dict: dict[str, base.Widget] = {
        'clock': clock_widget,
        'greeting': greetings_widget,
        'calendar': calendar_widget,
        'mode': mode_widget,
        'todo': todo_widget,
        'weather': weather_widget,
        'news': news_widget,
        'neofetch': neofetch_widget
        # Add more widgets here (3)
    }

    widget_list = list(widget_dict.values())

    base.loading_screen(widget_list)

    stop_event = threading.Event()
    reloader_thread = threading.Thread(target=reload_widget_scheduler, args=(widget_dict, stop_event))
    reloader_thread.daemon = True  # don't block exit if something goes wrong
    reloader_thread.start()

    # Load To-Do
    todo.load_todos(todo_widget)

    while True:
        try:
            base.validate_terminal_size(stdscr)
            key: typing.Any = stdscr.getch()  # Keypresses

            # Switch windows
            if key == curses.KEY_MOUSE:
                try:
                    _, mx, my, _, b_state = curses.getmouse()
                    if b_state & curses.BUTTON1_PRESSED:
                        switch_windows(mx, my, b_state, widget_dict)
                except curses.error:
                    # Ignore invalid mouse events (like scroll in some terminals)
                    continue

            handle_key_input(key, widget_list, stop_event, widget_dict)

            if stop_event.is_set():
                break

            # Refresh all widgets
            for widget in widget_list:
                if stop_event.is_set():
                    break

                if widget == mode_widget:
                    widget.draw()
                    widget.direct_refresh()
                    continue
                if widget == todo_widget:
                    if 'updating' in widget.data:
                        if todo_widget.data['updating']:
                            continue  # Currently reloading
                    widget.draw()
                    widget.direct_refresh()
                    continue

                if widget.data:
                    with widget.lock:
                        data_copy = widget.data.copy()
                    if '__error__' in data_copy:
                        base.display_error(widget, [widget.data['__error__']])
                    else:
                        widget.draw(data_copy)
                elif not widget.updatable():
                    widget.draw()
                else:
                    pass  # Data still loading

                widget.noutrefresh()
            curses.doupdate()
        except (base.RestartException, base.TerminalTooSmall):
            # Clean up threads and re-raise so outer loop restarts
            stop_event.set()
            reloader_thread.join(timeout=1)
            raise  # re-raise so wrapper(main) exits and outer loop restarts
        except Exception as e:
            stop_event.set()
            reloader_thread.join(timeout=1)
            raise base.UnknownException(f'Error: {e}')


def main_entry_point() -> None:
    while True:
        try:
            curses.wrapper(main_curses)
        except base.RestartException:
            # wrapper() has already cleaned up curses at this point
            sys.stdout.write("\033[2J\033[3J\033[H")  # clear screen, scrollback, and move cursor home
            sys.stdout.flush()
            continue  # Restart main
        except KeyboardInterrupt:
            pass
        except base.TerminalTooSmall as e:
            print(
                f'\n'
                f'Terminal too small. Minimum size: {MINIMUM_WIDTH}x{MINIMUM_HEIGHT} (Width x Height)\n'
                f'Current size: {e.width}x{e.height}.\n'
                f'Either decrease your font size, increase the size of the terminal, or remove widgets.\n'
                f'\n'
            )
            break
        except base.UnknownException as error:
            print(f'Unknown error\n{error.error_message}')
            break
        break  # Exit if the end of the loop is reached (User exit)


if __name__ == '__main__':
    main_entry_point()


# TODO: Add repo name
#
# TODO: Neofetch widget add support for other devices
# TODO: Add stuff to base.yaml
#
# TODO: If I ever release this, make sure to not reveal my API keys, location, etc.
