import threading
import os
import types
import typing

import twidgets.core.base as base
import twidgets.widgets as widgets_pkg


def main_curses(stdscr: base.CursesWindowType) -> None:
    # Always make relative paths work from the script’s directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Logs (Warnings, Errors)
    log_messages: base.LogMessages = base.LogMessages()

    # Config loader (Doesn't load anything yet)
    config_loader: base.ConfigLoader = base.ConfigLoader()
    config_loader.reload_secrets()  # needed to reload secrets.env changes

    # Widget Loader
    widget_loader: base.WidgetLoader = base.WidgetLoader()

    builtin_widget_names: list[str] = widget_loader.discover_builtin_widgets(widgets_pkg)
    custom_widget_names: list[str] = widget_loader.discover_custom_widgets()

    # Scan configs
    config_scanner: base.ConfigScanner = base.ConfigScanner(config_loader)
    config_scan_results: base.LogMessages | bool = config_scanner.scan_config(
        builtin_widget_names + custom_widget_names
    )

    if config_scan_results is not True:
        raise base.ConfigScanFoundError(config_scan_results)  # type: ignore[arg-type]

    # Initiate base config
    base_config: base.BaseConfig = config_loader.load_base_config(log_messages)

    # Initiate base UI State
    ui_state: base.UIState = base.UIState()

    # Initiate setup
    base.init_curses_setup(stdscr, base_config)

    # Import all widget modules
    builtin_widget_modules: dict[str, types.ModuleType] = widget_loader.load_builtin_widget_modules(
        builtin_widget_names
    )
    custom_widget_modules: dict[str, types.ModuleType] = widget_loader.load_custom_widget_modules()

    try:
        widget_dict = widget_loader.build_widgets(
            stdscr, config_loader, log_messages,
            builtin_widget_modules | custom_widget_modules
        )
    except base.WidgetSourceFileException:
        raise
    except Exception as e:
        raise base.UnknownException(log_messages, str(e))

    widget_list: list[base.Widget] = list(widget_dict.values())
    enabled_widget_list: list[base.Widget] = [widget for widget in widget_list if widget.config.enabled]

    min_height = max(widget.dimensions.current_height + widget.dimensions.current_y for widget in enabled_widget_list)
    min_width = max(widget.dimensions.current_width + widget.dimensions.current_x for widget in enabled_widget_list)
    base.validate_terminal_size(stdscr, min_height, min_width)
    # base.move_widgets_terminal_too_small(stdscr, enabled_widget_list, min_height, min_width)

    base.loading_screen(enabled_widget_list, ui_state, base_config)
    base.initialize_widgets(enabled_widget_list, ui_state, base_config)

    stop_event: threading.Event = threading.Event()
    reloader_thread: threading.Thread = threading.Thread(
        target=base.reload_widget_scheduler,
        args=(
            config_loader,
            enabled_widget_list,
            stop_event
        )
    )
    reloader_thread.daemon = True  # don't block exit if something goes wrong
    reloader_thread.start()

    while True:
        try:
            min_height = max(
                widget.dimensions.base_height + widget.dimensions.base_y for widget in enabled_widget_list)
            min_width = max(
                widget.dimensions.base_width + widget.dimensions.base_x for widget in enabled_widget_list)
            base.validate_terminal_size(stdscr, min_height, min_width)

            key: int = stdscr.getch()  # Keypresses

            base.handle_mouse_input(ui_state, base_config, key, log_messages, enabled_widget_list)

            base.handle_key_input(
                stdscr, ui_state, base_config, key, log_messages, enabled_widget_list, min_height, min_width
            )

            if stop_event.is_set():
                break

            # Refresh all widgets
            for widget in enabled_widget_list:
                try:
                    if stop_event.is_set():
                        break

                    if not widget.updatable():
                        widget.draw(ui_state, base_config)
                        widget.noutrefresh()
                        continue

                    if widget.draw_data:
                        with widget.lock:
                            data_copy: typing.Any = widget.draw_data.copy()
                        if '__error__' in data_copy:
                            if isinstance(data_copy['__error__'], base.LogMessages):
                                for log_message in list(data_copy['__error__']):
                                    base.display_error(widget, [str(log_message)], ui_state, base_config)
                                    if log_message not in list(log_messages):
                                        log_messages.add_log_message(log_message)
                            else:
                                base.display_error(widget, [widget.draw_data['__error__']], ui_state, base_config)
                        else:
                            widget.draw(ui_state, base_config, data_copy)
                    # else: Data still loading
                except base.ConfigSpecificException as e:
                    for log_message in list(e.log_messages):
                        base.display_error(widget, [str(log_message)], ui_state, base_config)
                        if log_message not in list(log_messages):
                            log_messages.add_log_message(log_message)
                except Exception as e:
                    if hasattr(e, 'log_messages'):
                        for log_message in list(e.log_messages):
                            base.display_error(widget, [str(log_message)], ui_state, base_config)
                            if log_message not in list(log_messages):
                                log_messages.add_log_message(log_message)
                    else:
                        new_log_message: base.LogMessage = base.LogMessage(
                            f'{str(e)} (widget "{widget.name}")',
                            base.LogLevels.ERROR.key
                        )

                        if new_log_message not in list(log_messages):
                            log_messages.add_log_message(new_log_message)
                        # If the widget failed, show the error inside the widget
                        base.display_error(widget, [str(e)], ui_state, base_config)

                widget.noutrefresh()
            base.update_screen()
        except (
                base.RestartException,
                base.ConfigScanFoundError,
                base.ConfigFileNotFoundError,
                base.ConfigSpecificException,
                base.StopException,
                base.TerminalTooSmall,
                base.WidgetSourceFileException
        ):
            # Clean up threads and re-raise so outer loop stops
            try:
                base.cleanup_curses_setup(stop_event, reloader_thread)
            except base.CursesError:
                return  # Ignore; Doesn't happen on Py3.13, but does on Py3.12
            raise  # re-raise so wrapper(main_curses) exits and outer loop stops
        except Exception as e:
            # Clean up threads and re-raise so outer loop stops
            # This also catches base.WidgetWinNotInitializedException
            try:
                base.cleanup_curses_setup(stop_event, reloader_thread)
            except base.CursesError:
                return  # Ignore; Doesn't happen on Py3.13, but does on Py3.12
            try:
                min_height = max(
                    widget.dimensions.current_height + widget.dimensions.current_y for widget in enabled_widget_list)
                min_width = max(
                    widget.dimensions.current_width + widget.dimensions.current_x for widget in enabled_widget_list)
                base.validate_terminal_size(stdscr, min_height, min_width)
            except base.TerminalTooSmall:
                raise  # E.g. the terminal size just changed (split windows, ...)
            raise base.UnknownException(log_messages, str(e))


def main_entry_point() -> None:
    while True:
        try:
            base.curses_wrapper(main_curses)
        except base.RestartException:
            # wrapper() has already cleaned up curses at this point
            continue  # Restart main
        except base.ConfigScanFoundError as e:
            e.log_messages.print_log_messages(heading='Config errors & warnings (found by ConfigScanner):\n')
            break
        except base.ConfigFileNotFoundError as e:
            print(f'⚠️ Config File Not Found Error: {e}')
            print(f'\nPerhaps you haven\'t initialized the configuration. Please run: twidgets init')
            break
        except base.ConfigSpecificException as e:
            e.log_messages.print_log_messages(heading='Config errors & warnings (found at runtime):\n')
            break
        except base.StopException as e:
            e.log_messages.print_log_messages(heading='Config errors & warnings:\n')
            break
        except KeyboardInterrupt:
            break
        except base.TerminalTooSmall as e:
            print(e)
        except base.WidgetSourceFileException as e:
            e.log_messages.print_log_messages(heading='WidgetSource errors & warnings (found at runtime):\n')
            # raise
        except base.CursesError:
            break  # Ignore; Doesn't happen on Py3.13, but does on Py3.12
        except base.UnknownException as e:
            if not e.log_messages.is_empty():
                e.log_messages.print_log_messages(heading='Config errors & warnings:\n')
                print('-> which results in:\n')
            print(
                f'⚠️ Unknown errors:\n'
                f'{e.error_message}\n'
            )
            raise
        break  # Exit if the end of the loop is reached (User exit)


if __name__ == '__main__':
    main_entry_point()


# TODO: Autodetect system OS?

# Ideas:
# - quote of the day, etc.

# TODO: Do what FRoith said, so like flex widgets and stuff. Idea:
# Get all widgets that need to be moved when terminal is too small, just a for, and then add like width + x or sth.
# Then see which widgets can stay. (Not those who need to move)
# Then go through these widgets that stay, and every widget that has to move, which has a higher Y
# (or Y + height, idk yet)
# Moves UNDER that widget.
# For that to work, start looping from the TOP MOST widget
