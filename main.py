import curses
import time
import typing
import threading
import sys
import os

import core.base as base
import widgets.clock as clock
import widgets.greetings as greetings
import widgets.calendar as calendar
import widgets.neofetch as neofetch
import widgets.news as news
import widgets.weather as weather
import widgets.todo as todo
import widgets.mode as mode
import widgets.resources as resources
# Add more widgets here (1)


def switch_windows(
        ui_state: base.UIState,
        base_config: base.BaseConfig,
        mx: int,
        my: int,
        _b_state: int,
        widgets: dict[str, base.Widget]
) -> None:
    widget_list = list(widgets.values())
    mode_widget = widgets['mode']
    todo_widget = widgets['todo']

    # Find which widget was clicked
    ui_state.highlighted = None
    for widget in widget_list:
        y1 = widget.dimensions.y
        y2 = y1 + widget.dimensions.height
        x1 = widget.dimensions.x
        x2 = x1 + widget.dimensions.width
        if y1 <= my <= y2 and x1 <= mx <= x2:
            ui_state.highlighted = widget
            break
    mode_widget.draw(ui_state, base_config)
    mode_widget.direct_refresh()

    todo.mark_highlighted_line(todo_widget, my, ui_state)

    todo_widget.draw(ui_state, base_config)
    todo_widget.direct_refresh()


def handle_key_input(
        ui_state: base.UIState,
        base_config: base.BaseConfig,
        key: typing.Any,
        stop_event: threading.Event,
        widget_dict: dict[str, base.Widget],
) -> None:
    mode_widget: base.Widget = widget_dict['mode']
    todo_widget: base.Widget = widget_dict['todo']
    highlighted_widget: base.Widget | None = ui_state.highlighted

    if key == 27:  # ESC key
        ui_state.highlighted = None

        mode_widget.draw(ui_state, base_config)
        mode_widget.direct_refresh()

        todo.remove_highlighted_line(todo_widget)
        todo_widget.direct_refresh()
        return

    if highlighted_widget is None:
        if key == ord(base_config.quit_key):
            stop_event.set()
        elif key == ord(base_config.help_key):
            pass  # TODO: Help page? Even for each window?
        elif key == ord(base_config.reload_key):  # Reload widgets & config
            raise base.RestartException
        return

    if highlighted_widget == todo_widget:
        if 'todos' not in todo_widget.draw_data:
            return
        len_todos = len(todo_widget.draw_data['todos'])
        selected = todo_widget.draw_data.get('selected_line', 0)

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

        todo_widget.draw_data['selected_line'] = selected

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
                    todo.remove_todo(todo_widget, todo_widget.draw_data['selected_line'])

        todo_widget.draw(ui_state, base_config)
        todo_widget.direct_refresh()


def reload_widget_scheduler(
        config_loader: base.ConfigLoader,
        widget_dict: dict[str, base.Widget],
        stop_event: threading.Event
) -> None:
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
                continue

            if widget.last_updated is None:
                continue

            # See widget.updatable()
            if now - widget.last_updated >= widget.interval:  # type: ignore[operator]
                try:
                    widget.draw_data = widget.update(config_loader)
                    widget.last_updated = now
                except Exception as e:
                    widget.draw_data = {'__error__': str(e)}
        # Small sleep to avoid busy loop, tuned to a small value
        time.sleep(0.06667)  # -> ~15 FPS


def main_curses(stdscr: typing.Any) -> None:
    # Always make relative paths work from the script’s directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    config_loader: base.ConfigLoader = base.ConfigLoader()
    config_loader.reload_secrets()  # needed to reload secrets.env changes
    ui_state: base.UIState = base.UIState()
    base_config: base.BaseConfig = config_loader.load_base_config()

    base.init_curses_setup(stdscr, base_config)

    clock_widget: base.Widget = clock.build(stdscr, config_loader.load_widget_config('clock'))
    greetings_widget: base.Widget = greetings.build(stdscr, config_loader.load_widget_config('greetings'))
    calendar_widget: base.Widget = calendar.build(stdscr, config_loader.load_widget_config('calendar'))
    mode_widget: base.Widget = mode.build(stdscr, config_loader.load_widget_config('mode'))
    todo_widget: base.Widget = todo.build(stdscr, config_loader.load_widget_config('todo'))
    weather_widget: base.Widget = weather.build(stdscr, config_loader.load_widget_config('weather'))
    news_widget: base.Widget = news.build(stdscr, config_loader.load_widget_config('news'))
    neofetch_widget: base.Widget = neofetch.build(stdscr, config_loader.load_widget_config('neofetch'))
    resources_widget: base.Widget = resources.build(stdscr, config_loader.load_widget_config('resources'))
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
        'resources': resources_widget,
        'neofetch': neofetch_widget
        # Add more widgets here (3)
    }

    widget_list = list(widget_dict.values())

    min_height = max(widget.dimensions.height + widget.dimensions.y for widget in widget_list if widget.config.enabled)
    min_width = max(widget.dimensions.width + widget.dimensions.x for widget in widget_list if widget.config.enabled)
    base.validate_terminal_size(stdscr, min_height, min_width)

    base.loading_screen(widget_list, ui_state, base_config)

    stop_event = threading.Event()
    reloader_thread = threading.Thread(target=reload_widget_scheduler, args=(config_loader, widget_dict, stop_event))
    reloader_thread.daemon = True  # don't block exit if something goes wrong
    reloader_thread.start()

    # Load To-Do
    todo.load_todos(todo_widget)

    while True:
        try:
            min_height = max(
                widget.dimensions.height + widget.dimensions.y for widget in widget_list if widget.config.enabled)
            min_width = max(
                widget.dimensions.width + widget.dimensions.x for widget in widget_list if widget.config.enabled)
            base.validate_terminal_size(stdscr, min_height, min_width)

            key: typing.Any = stdscr.getch()  # Keypresses

            # Switch windows
            if key == curses.KEY_MOUSE:
                try:
                    _, mx, my, _, b_state = curses.getmouse()
                    if b_state & curses.BUTTON1_PRESSED:
                        switch_windows(ui_state, base_config, mx, my, b_state, widget_dict)
                except curses.error:
                    # Ignore invalid mouse events (like scroll in some terminals)
                    continue

            handle_key_input(ui_state, base_config, key, stop_event, widget_dict)

            if stop_event.is_set():
                break

            # Refresh all widgets
            for widget in widget_list:
                if stop_event.is_set():
                    break

                if widget == mode_widget:
                    widget.draw(ui_state, base_config)
                    widget.direct_refresh()
                    continue

                if widget == todo_widget:
                    widget.draw(ui_state, base_config)
                    widget.direct_refresh()
                    continue

                if widget.draw_data:
                    with widget.lock:
                        data_copy = widget.draw_data.copy()
                    if '__error__' in data_copy:
                        base.display_error(widget, [widget.draw_data['__error__']], ui_state, base_config)
                    else:
                        widget.draw(ui_state, base_config, data_copy)
                elif not widget.updatable():
                    widget.draw(ui_state, base_config)
                else:
                    pass  # Data still loading

                widget.noutrefresh()
            curses.doupdate()
        except (base.RestartException, base.TerminalTooSmall, base.ConfigError, base.ConfigFileNotFoundError):
            # Clean up threads and re-raise so outer loop stops
            stop_event.set()
            reloader_thread.join(timeout=1)
            raise  # re-raise so wrapper(main_curses) exits and outer loop stops
        except Exception as e:
            stop_event.set()
            reloader_thread.join(timeout=1)
            try:
                min_height = max(
                    widget.dimensions.height + widget.dimensions.y for widget in widget_list if widget.config.enabled)
                min_width = max(
                    widget.dimensions.width + widget.dimensions.x for widget in widget_list if widget.config.enabled)
                base.validate_terminal_size(stdscr, min_height, min_width)
            except Exception:
                raise  # if the terminal size just changed, raise that. needed if e.g. split windows
            raise base.UnknownException(f'Error: {e}')


def main_entry_point() -> None:
    while True:
        try:
            curses.wrapper(main_curses)
        except base.RestartException:
            # wrapper() has already cleaned up curses at this point
            sys.stdout.write('\033[2J\033[3J\033[H')  # clear screen, scrollback, and move cursor home
            sys.stdout.flush()
            continue  # Restart main
        except base.ConfigError as e:
            print(f'⚠️ Config Error: {e}')
            break
        except base.ConfigFileNotFoundError as e:
            print(f'⚠️ Config File Not Found Error: {e}')
            break
        except KeyboardInterrupt:
            pass
        except base.TerminalTooSmall as e:
            print(
                f'',
                f'⚠️ Terminal too small. Minimum size: {e.min_width}x{e.min_height}',
                f'(Width x Height)',
                f'Current size: {e.width}x{e.height}',
                f'Either decrease your font size, increase the size of the terminal, or remove widgets.',
                f'',
                sep='\n'
            )
            break
        except base.UnknownException as e:
            print(f'Unknown error\n{e.error_message}\n\n')
            raise
        break  # Exit if the end of the loop is reached (User exit)


if __name__ == '__main__':
    main_entry_point()


# TODO: Add examples / images
# TODO: Autodetect system OS?

# TODO: When config has flaws, this should not only say 1 problem but rather all...
# TODO: Any more terminal too small changes or sth?? Or config file change??

# Ideas:
# - quote of the day, etc.
