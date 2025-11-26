from twidgets.core.base import (
    Widget,
    Config,
    CursesWindowType,
    draw_widget,
    add_widget_content,
    UIState,
    BaseConfig
)


def draw(widget: Widget, ui_state: UIState, base_config: BaseConfig) -> None:
    mode: str = 'none'
    if ui_state.highlighted:
        mode = str(ui_state.highlighted.name)

    draw_widget(widget, ui_state, base_config)
    add_widget_content(widget, [mode])


def draw_help(widget: Widget, ui_state: UIState, base_config: BaseConfig) -> None:
    draw_widget(widget, ui_state, base_config)

    add_widget_content(
        widget,
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
