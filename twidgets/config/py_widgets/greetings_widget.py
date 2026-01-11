from twidgets.core.base import (
    Widget,
    WidgetContainer,
    Config,
    CursesWindowType,
    ConfigSpecificException,
    LogMessages,
    LogMessage,
    LogLevels,
)


def draw(widget: Widget, widget_container: WidgetContainer) -> None:
    if not widget.config.your_name:
        raise ConfigSpecificException(LogMessages([LogMessage(
            f'Configuration for your_name is missing / incorrect ("{widget.name}" widget)',
            LogLevels.ERROR.key)]))

    content = [
        f'Hello, {widget.config.your_name}!'
    ]

    widget_container.draw_widget(widget)
    widget.add_widget_content(content)


def draw_help(widget: Widget, widget_container: WidgetContainer) -> None:
    widget_container.draw_widget(widget)

    widget.add_widget_content(
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
