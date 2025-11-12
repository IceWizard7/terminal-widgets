import typing
from core.base import Widget, Config, draw_widget, add_widget_content, UIState, BaseConfig


def draw(widget: Widget, ui_state: UIState, base_config: BaseConfig) -> None:
    draw_widget(widget, ui_state, base_config)
    add_widget_content(widget, [f'Hello, {widget.config.your_name}!'])


def build(stdscr: typing.Any, config: Config) -> Widget:
    return Widget(
        config.name, config.title, config, draw, config.interval, config.dimensions, stdscr
    )
