import time
from twidgets.core.base import (
    Widget,
    Config,
    CursesWindowType,
    draw_widget,
    add_widget_content,
    UIState,
    BaseConfig,
    ConfigSpecificException,
    LogMessages,
    LogMessage,
    LogLevels,
)


def draw(widget: Widget, ui_state: UIState, base_config: BaseConfig) -> None:
    if not widget.config.weekday_format:
        raise ConfigSpecificException(LogMessages([LogMessage(
            f'Configuration for weekday_format is missing / incorrect ("{widget.name}" widget)',
            LogLevels.ERROR.key)]))
    if not widget.config.date_format:
        raise ConfigSpecificException(LogMessages([LogMessage(
            f'Configuration for date_format is missing / incorrect ("{widget.name}" widget)',
            LogLevels.ERROR.key)]))
    if not widget.config.time_format:
        raise ConfigSpecificException(LogMessages([LogMessage(
            f'Configuration for time_format is missing / incorrect ("{widget.name}" widget)',
            LogLevels.ERROR.key)]))

    content = [
        time.strftime(widget.config.weekday_format),
        time.strftime(widget.config.date_format),
        time.strftime(widget.config.time_format),
    ]
    draw_widget(widget, ui_state, base_config)
    add_widget_content(widget, content)


def draw_help(widget: Widget, ui_state: UIState, base_config: BaseConfig) -> None:
    draw_widget(widget, ui_state, base_config)

    add_widget_content(
        widget,
        [
            f'Help page ({widget.name} widget)',
            'Displays the current date',
            'and time.',
        ]
    )


def build(stdscr: CursesWindowType, config: Config) -> Widget:
    return Widget(
        config.name, config.title, config, draw, config.interval, config.dimensions, stdscr,
        update_func=None,
        mouse_click_func=None,
        keyboard_func=None,
        init_func=None,
        help_func=draw_help
    )
