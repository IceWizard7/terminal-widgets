import typing
from core.base import Widget, Config, draw_widget, add_widget_content, UIState, BaseConfig


def draw(widget: Widget, ui_state: UIState, base_config: BaseConfig) -> None:
    mode: str = 'None'
    if ui_state.highlighted:
        mode = str(ui_state.highlighted.name)

    draw_widget(widget, ui_state, base_config)
    add_widget_content(widget, [mode])


def build(stdscr: typing.Any, config: Config) -> Widget:
    return Widget(
        config.name, config.title, config, draw, config.interval, config.dimensions, stdscr,
        update_func=None,
        switch_window_update_func=None
    )
