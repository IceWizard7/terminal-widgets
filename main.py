import curses
import threading
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


def main_curses(stdscr: base.CursesWindowType) -> None:
    # Always make relative paths work from the script’s directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Logs (e.g. Warnings)
    log_messages: base.LogMessages = base.LogMessages()

    # Config loader (Doesn't load anything yet)
    config_loader: base.ConfigLoader = base.ConfigLoader()
    config_loader.reload_secrets()  # needed to reload secrets.env changes

    # Scan configs
    config_scanner: base.ConfigScanner = base.ConfigScanner(config_loader)
    config_scan_results: base.LogMessages | bool = config_scanner.scan_config([
        'clock', 'greetings', 'calendar', 'mode', 'todo', 'weather', 'news', 'neofetch', 'resources'
    ])
    # Add more widgets here (2)

    if config_scan_results is not True:
        raise base.ConfigScanFoundError(config_scan_results)  # type: ignore[arg-type]

    # Initiate base config
    base_config: base.BaseConfig = config_loader.load_base_config(log_messages)

    # Initiate base UI State
    ui_state: base.UIState = base.UIState()

    # Initiate setup
    base.init_curses_setup(stdscr, base_config)

    try:
        clock_widget: base.Widget = clock.build(
            stdscr, config_loader.load_widget_config(log_messages, 'clock')
        )
        greetings_widget: base.Widget = greetings.build(
            stdscr, config_loader.load_widget_config(log_messages, 'greetings')
        )
        calendar_widget: base.Widget = calendar.build(
            stdscr, config_loader.load_widget_config(log_messages, 'calendar')
        )
        mode_widget: base.Widget = mode.build(
            stdscr, config_loader.load_widget_config(log_messages, 'mode')
        )
        todo_widget: base.Widget = todo.build(
            stdscr, config_loader.load_widget_config(log_messages, 'todo')
        )
        weather_widget: base.Widget = weather.build(
            stdscr, config_loader.load_widget_config(log_messages, 'weather')
        )
        news_widget: base.Widget = news.build(
            stdscr, config_loader.load_widget_config(log_messages, 'news')
        )
        neofetch_widget: base.Widget = neofetch.build(
            stdscr, config_loader.load_widget_config(log_messages, 'neofetch')
        )
        resources_widget: base.Widget = resources.build(
            stdscr, config_loader.load_widget_config(log_messages, 'resources')
        )
        # Add more widgets here (3)
    except Exception as e:
        raise base.UnknownException(log_messages, str(e))

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
        # Add more widgets here (4)
    }

    widget_list = list(widget_dict.values())

    min_height = max(widget.dimensions.height + widget.dimensions.y for widget in widget_list if widget.config.enabled)
    min_width = max(widget.dimensions.width + widget.dimensions.x for widget in widget_list if widget.config.enabled)
    base.validate_terminal_size(stdscr, min_height, min_width)

    base.loading_screen(widget_list, ui_state, base_config)

    stop_event: threading.Event = threading.Event()
    reloader_thread: threading.Thread = threading.Thread(
        target=base.reload_widget_scheduler,
        args=(
            config_loader,
            widget_dict,
            stop_event
        )
    )
    reloader_thread.daemon = True  # don't block exit if something goes wrong
    reloader_thread.start()

    # Load To-Dos (initially, will get reloaded every mouse / keyboard action)
    todo.load_todos(todo_widget)

    while True:
        try:
            min_height = max(
                widget.dimensions.height + widget.dimensions.y for widget in widget_list if widget.config.enabled)
            min_width = max(
                widget.dimensions.width + widget.dimensions.x for widget in widget_list if widget.config.enabled)
            base.validate_terminal_size(stdscr, min_height, min_width)

            key: int = stdscr.getch()  # Keypresses

            base.handle_mouse_input(ui_state, base_config, key, log_messages, widget_dict)

            base.handle_key_input(ui_state, base_config, key, log_messages, widget_dict)

            if stop_event.is_set():
                break

            # Refresh all widgets
            for widget in widget_list:
                if stop_event.is_set():
                    break

                if not widget.updatable():
                    widget.draw(ui_state, base_config)
                    widget.noutrefresh()
                    continue

                if widget.draw_data:
                    with widget.lock:
                        data_copy = widget.draw_data.copy()
                    if '__error__' in data_copy:
                        base.display_error(widget, [widget.draw_data['__error__']], ui_state, base_config)
                    else:
                        widget.draw(ui_state, base_config, data_copy)
                # else: Data still loading

                widget.noutrefresh()
            curses.doupdate()
        except (
                base.TerminalTooSmall,
                base.ConfigFileNotFoundError,
                base.StopException,
                base.RestartException,
                base.ConfigScanFoundError
        ):
            # Clean up threads and re-raise so outer loop stops
            base.cleanup_curses_setup(stop_event, reloader_thread)
            raise  # re-raise so wrapper(main_curses) exits and outer loop stops
        except Exception as e:
            # Clean up threads and re-raise so outer loop stops
            base.cleanup_curses_setup(stop_event, reloader_thread)
            try:
                min_height = max(
                    widget.dimensions.height + widget.dimensions.y for widget in widget_list if widget.config.enabled)
                min_width = max(
                    widget.dimensions.width + widget.dimensions.x for widget in widget_list if widget.config.enabled)
                base.validate_terminal_size(stdscr, min_height, min_width)
            except base.TerminalTooSmall:
                raise  # E.g. the terminal size just changed (split windows, ...)
            raise base.UnknownException(log_messages, str(e))


def main_entry_point() -> None:
    while True:
        try:
            curses.wrapper(main_curses)
        except base.RestartException:
            # wrapper() has already cleaned up curses at this point
            continue  # Restart main
        except base.ConfigScanFoundError as e:
            e.log_messages.print_log_messages(heading='Config errors & warnings (found by ConfigScanner):\n')
            break
        except base.ConfigFileNotFoundError as e:
            print(f'⚠️ Config File Not Found Error: {e}')
            break
        except base.ConfigSpecificException as e:
            e.log_messages.print_log_messages(heading='Config errors & warnings (found at runtime):\n')
            break
        except base.StopException as e:
            e.log_messages.print_log_messages(heading='Config errors & warnings (found by ConfigScanner):\n')
            break
        except KeyboardInterrupt:
            break
        except base.TerminalTooSmall as e:
            print(e)
        except base.UnknownException as e:
            if not e.log_messages.is_empty():
                e.log_messages.print_log_messages(heading='Config errors & warnings:\n')
                print('-> which results in:\n')
            print(
                f'⚠️ Unknown errors:\n'
                f'{e.error_message}\n'
            )
            break
            # raise
        break  # Exit if the end of the loop is reached (User exit)


if __name__ == '__main__':
    main_entry_point()


# TODO: Autodetect system OS?

# Ideas:
# - quote of the day, etc.
