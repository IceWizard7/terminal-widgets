import time
import typing
from .base import Widget, draw_widget, add_widget_content, Config


def draw(widget: Widget) -> None:
    content = [
        time.strftime('%A'),
        time.strftime('%d.%m.%Y'),
        time.strftime('%H:%M:%S')
    ]
    draw_widget(widget)
    add_widget_content(widget, content)


def build(stdscr: typing.Any, config: Config) -> Widget:
    return Widget(
        config.name, config.title, config, draw, config.interval, config.dimensions, stdscr
    )
