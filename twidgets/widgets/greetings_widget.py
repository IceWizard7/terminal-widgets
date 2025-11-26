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
    if not widget.config.your_name:
        raise ConfigSpecificException(LogMessages([LogMessage(
            f'Configuration for your_name is missing / incorrect ("{widget.name}" widget)',
            LogLevels.ERROR.key)]))

    content = [
        f'Hello, {widget.config.your_name}!'
    ]

    draw_widget(widget, ui_state, base_config)
    add_widget_content(widget, content)


def draw_help(widget: Widget, ui_state: UIState, base_config: BaseConfig) -> None:
    draw_widget(widget, ui_state, base_config)

    add_widget_content(
        widget,
        [
            f'Help page ({widget.name} widget)',
            'Displays a greeting message.'
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
