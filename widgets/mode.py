import typing
from core.base import Widget, Config, draw_widget, add_widget_content, ui_state


def draw(widget: Widget) -> None:
    mode: str = 'None'
    if ui_state.highlighted:
        # mode = str(ui_state.highlighted.title)[1:-1]
        mode = str(ui_state.highlighted.name)

    draw_widget(widget)
    add_widget_content(widget, [mode])


def build(stdscr: typing.Any, config: Config) -> Widget:
    return Widget(
        config.name, config.title, config, draw, config.interval, config.dimensions, stdscr
    )
