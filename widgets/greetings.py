import typing
from core.base import Widget, Config, draw_widget, add_widget_content


def draw(widget: Widget) -> None:
    draw_widget(widget)
    add_widget_content(widget, ['Hello, Ice!'])


def build(stdscr: typing.Any, config: Config) -> Widget:
    return Widget(
        config.name, config.title, config, draw, config.interval, config.dimensions, stdscr
    )
