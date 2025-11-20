import typing
from core.base import Widget, Config, draw_widget, add_widget_content, UIState, BaseConfig


def draw(widget: Widget, ui_state: UIState, base_config: BaseConfig) -> None:
    content = [
        f'Hello, {widget.config.your_name}!' if widget.config.your_name else 'Invalid your_name',
    ]

    draw_widget(widget, ui_state, base_config)
    add_widget_content(widget, content)


def build(stdscr: typing.Any, config: Config) -> Widget:
    return Widget(
        config.name, config.title, config, draw, config.interval, config.dimensions, stdscr,
        update_func=None,
        mouse_click_func=None,
        keyboard_func=None
    )
