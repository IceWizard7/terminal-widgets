from twidgets.core.base import (
    Widget,
    WidgetContainer,
    Config,
    CursesWindowType
)


def draw(widget: Widget, widget_container: WidgetContainer) -> None:
    mode: str = 'none'
    if widget_container.ui_state.highlighted:
        mode = str(widget_container.ui_state.highlighted.name)

    widget_container.draw_widget(widget)
    widget.add_widget_content([mode])


def draw_help(widget: Widget, widget_container: WidgetContainer) -> None:
    widget_container.draw_widget(widget)

    widget.add_widget_content(
        [
            f'Help page ({widget.name} widget)',
            'Displays selected widget.'
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
