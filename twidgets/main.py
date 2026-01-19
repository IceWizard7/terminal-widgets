import os
import typing
from twidgets.core.base import (
    # Essentials
    Widget,
    WidgetContainer,
    CursesWindowType,

    # Logging
    LogMessages,
    LogMessage,
    LogLevels,

    # Exceptions
    RestartException,
    ConfigScanFoundError,
    ConfigFileNotFoundError,
    ConfigSpecificException,
    StopException,
    TerminalTooSmall,
    WidgetSourceFileException,
    CursesError,
    UnknownException,

    # Wrapper (starting twidgets)
    curses_wrapper, DebugException
)


def main_curses(stdscr: CursesWindowType) -> None:
    # Always make relative paths work from the script’s directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Holds all widgets (Allows communication between scheduler thread & renderer, without exiting)
    widget_container: WidgetContainer = WidgetContainer(stdscr, test_env=False)

    # Scan configs
    widget_container.scan_config()

    # Initiate setup
    widget_container.init_curses_setup()

    # Build widgets
    widget_container.add_widget_list(list(widget_container.build_widgets().values()))

    min_height: int
    min_width: int
    min_height, min_width = widget_container.get_max_height_width_all_widgets()

    widget_container.loading_screen()
    widget_container.initialize_widgets()
    widget_container.move_widgets_resize(min_height, min_width)
    widget_container.start_reloader_thread()

    while True:
        try:
            min_height, min_width = widget_container.get_max_height_width_all_widgets()

            key: int = widget_container.stdscr.getch()  # Keypresses

            widget_container.handle_mouse_input(key)

            widget_container.handle_key_input(key, min_height, min_width)

            if widget_container.stop_event.is_set():
                break

            widgets_by_z: dict[int, list[Widget]] = widget_container.return_widgets_ordered_by_z_index()

            # Main drawing loop (refresh all widgets)
            for widget in (
                    w
                    for z in sorted(widgets_by_z)
                    for w in widgets_by_z[z]
            ):
                try:
                    if widget_container.stop_event.is_set():
                        break

                    if not widget.updatable():
                        widget.draw_function(widget_container)
                        widget.noutrefresh()
                        continue

                    if widget.draw_data:
                        with widget.lock:
                            data_copy: typing.Any = widget.draw_data.copy()
                        if '__error__' in data_copy:
                            if isinstance(data_copy['__error__'], LogMessages):
                                for log_message in list(data_copy['__error__']):
                                    widget_container.display_error(widget, [str(log_message)])
                                    if log_message not in list(widget_container.log_messages):
                                        widget_container.log_messages.add_log_message(log_message)
                            else:
                                widget_container.display_error(widget, [widget.draw_data['__error__']])
                        else:
                            widget.draw_function(widget_container, data_copy)
                    # else: Data still loading
                except ConfigSpecificException as e:
                    for log_message in list(e.log_messages):
                        widget_container.display_error(widget, [str(log_message)])
                        if log_message not in list(widget_container.log_messages):
                            widget_container.log_messages.add_log_message(log_message)
                except Exception as e:
                    if hasattr(e, 'log_messages'):
                        for log_message in list(e.log_messages):
                            widget_container.display_error(widget, [str(log_message)])
                            if log_message not in list(widget_container.log_messages):
                                widget_container.log_messages.add_log_message(log_message)
                    else:
                        new_log_message: LogMessage = LogMessage(
                            f'{str(e)} (widget "{widget.name}")', LogLevels.ERROR.key
                        )

                        if new_log_message not in list(widget_container.log_messages):
                            widget_container.log_messages.add_log_message(new_log_message)
                        # If the widget failed, show the error inside the widget
                        widget_container.display_error(widget, [str(e)])

                widget.noutrefresh()

            # Refresh all floating widgets
            # Draw last, so they show on top
            for floating_widget in widget_container.return_all_floating_windows():
                floating_widget.draw(widget_container)
                floating_widget.noutrefresh()
            widget_container.update_screen()
        except (
                RestartException,
                ConfigScanFoundError,
                ConfigFileNotFoundError,
                ConfigSpecificException,
                StopException,
                TerminalTooSmall,
                WidgetSourceFileException
        ):
            # Clean up threads and re-raise so outer loop stops
            widget_container.cleanup_curses_setup()
            raise  # re-raise so wrapper(main_curses) exits and outer loop stops
        except Exception as e:
            # Clean up threads and re-raise so outer loop stops
            widget_container.cleanup_curses_setup()

            raise UnknownException(widget_container, e)


def main_entry_point() -> None:
    while True:
        try:
            curses_wrapper(main_curses)
        except RestartException:
            # wrapper() has already cleaned up curses at this point
            continue  # Restart main
        except ConfigScanFoundError as e:
            e.log_messages.print_log_messages(heading='Config errors & warnings (found by ConfigScanner):\n')
            break
        except ConfigFileNotFoundError as e:
            print(f'⚠️ Config File Not Found Error: {e}')
            print(f'\nPerhaps you haven\'t initialized the configuration. Please run: twidgets init')
            break
        except ConfigSpecificException as e:
            e.log_messages.print_log_messages(heading='Config errors & warnings (found at runtime):\n')
            break
        except StopException as e:
            e.log_messages.print_log_messages(heading='Config errors & warnings:\n')
            break
        except KeyboardInterrupt:
            break
        except TerminalTooSmall as e:
            print(e)
        except WidgetSourceFileException as e:
            e.log_messages.print_log_messages(heading='WidgetSource errors & warnings (found at runtime):\n')
            # raise
        except CursesError:
            break  # Ignore; Doesn't happen on Py3.13, but does on Py3.12
        except UnknownException as e:
            if not e.widget_container.log_messages.is_empty():
                e.widget_container.log_messages.print_log_messages(heading='Config errors & warnings:\n')
                print(f'')
            print(
                f'⚠️ Unknown errors:\n'
                f'{str(e)}\n'
            )
            raise e.initial_exception
        break  # Exit if the end of the loop is reached (User exit)


if __name__ == '__main__':
    main_entry_point()


# Ideas:
# - Quote of the day, ... of the day
