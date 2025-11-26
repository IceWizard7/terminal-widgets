import requests
import feedparser  # type: ignore[import-untyped]
from twidgets.core.base import (
    Widget,
    Config,
    CursesWindowType,
    draw_widget,
    add_widget_content,
    ConfigLoader,
    UIState,
    BaseConfig
)


def update(_widget: Widget, _config_loader: ConfigLoader) -> list[str]:
    feed_url: str | None = _config_loader.get_secret('NEWS_FEED_URL')
    feed_name: str | None = _config_loader.get_secret('NEWS_FEED_NAME')

    if feed_url is None:
        return [
            'News data not available.',
            '',
            'Check your configuration.'
        ]

    if feed_name != '':
        _widget.title = f'{_widget.config.title} [{feed_name}]'

    content = []

    try:
        response = requests.get(feed_url, timeout=5)
        response.raise_for_status()  # Raises if status != 2xx

        # Parse from content (string)
        feed = feedparser.parse(response.text)

        if feed.bozo:
            # feedparser caught an internal parsing error
            return [
                'News data not available.',
                '',
                'Check your configuration.'
            ]
    except requests.exceptions.RequestException:
        return [
            'News data not available.',
            '',
            'Check your internet connection.'
        ]

    for i, entry in enumerate(feed.entries[:5]):  # Get top articles
        content.append(f'{i+1}. {entry.title}')

    if not content:
        return [
            'News data not available.',
            '',
            'Check your internet connection and configuration.'
        ]

    return content


def draw(widget: Widget, ui_state: UIState, base_config: BaseConfig, info: list[str]) -> None:
    draw_widget(widget, ui_state, base_config)
    add_widget_content(widget, info)


def draw_help(widget: Widget, ui_state: UIState, base_config: BaseConfig) -> None:
    draw_widget(widget, ui_state, base_config)

    add_widget_content(
        widget,
        [
            f'Help page ({widget.name} widget)',
            '',
            'Displays current news.'
        ]
    )


def build(stdscr: CursesWindowType, config: Config) -> Widget:
    return Widget(
        config.name, config.title, config, draw, config.interval, config.dimensions, stdscr,
        update_func=update,
        mouse_click_func=None,
        keyboard_func=None,
        init_func=None,
        help_func=draw_help
    )
