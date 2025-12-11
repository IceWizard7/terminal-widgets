import os
import typing

import twidgets.core.base as base
import twidgets.widgets as widgets_pkg


def main_curses(stdscr: base.CursesWindowType) -> None:
    # Always make relative paths work from the script’s directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Holds all widgets (Allows communication between scheduler thread & renderer, without exiting)
    widget_container: base.WidgetContainer = base.WidgetContainer(stdscr, widgets_pkg, test_env=False)

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

            # Refresh all widgets
            for widget in widget_container.return_widgets():
                try:
                    if widget_container.stop_event.is_set():
                        break

                    if not widget.updatable():
                        widget.draw(widget_container)
                        widget.noutrefresh()
                        continue

                    if widget.draw_data:
                        with widget.lock:
                            data_copy: typing.Any = widget.draw_data.copy()
                        if '__error__' in data_copy:
                            if isinstance(data_copy['__error__'], base.LogMessages):
                                for log_message in list(data_copy['__error__']):
                                    widget_container.display_error(widget, [str(log_message)])
                                    if log_message not in list(widget_container.log_messages):
                                        widget_container.log_messages.add_log_message(log_message)
                            else:
                                widget_container.display_error(widget, [widget.draw_data['__error__']])
                        else:
                            widget.draw(widget_container, data_copy)
                    # else: Data still loading
                except base.ConfigSpecificException as e:
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
                        new_log_message: base.LogMessage = base.LogMessage(
                            f'{str(e)} (widget "{widget.name}")',
                            base.LogLevels.ERROR.key
                        )

                        if new_log_message not in list(widget_container.log_messages):
                            widget_container.log_messages.add_log_message(new_log_message)
                        # If the widget failed, show the error inside the widget
                        widget_container.display_error(widget, [str(e)])

                widget.noutrefresh()

            # Refresh all warnings
            # Draw LAST, so they show on top
            for warning in widget_container.return_all_warnings():
                warning.draw(widget_container)
                if warning.win:
                    warning.win.noutrefresh()
            widget_container.update_screen()
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
            widget_container.cleanup_curses_setup()
            raise  # re-raise so wrapper(main_curses) exits and outer loop stops
        except Exception as e:
            # Clean up threads and re-raise so outer loop stops
            widget_container.cleanup_curses_setup()

            raise base.UnknownException(widget_container, e)


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
