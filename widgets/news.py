import typing
import requests
import feedparser  # type: ignore[import-untyped]
from .base import Widget, Config, draw_widget, add_widget_content
from utils.config_loader import get_secret


def update(_widget: Widget) -> list[str]:
    feed_url: str = get_secret('NEWS_FEED_URL')
    feed_name: str = get_secret('NEWS_FEED_NAME')

    if feed_name != '':
        _widget.title = f'{_widget.config.title} [{feed_name}]'

    content = []

    try:
        response = requests.get(feed_url, timeout=5)
        response.raise_for_status()  # Raises if status != 200

        # Parse from content (string)
        feed = feedparser.parse(response.text)
    except Exception:
        return [
            'News data not available.',
            'Check your internet connection.'
        ]

    for i, entry in enumerate(feed.entries[:5]):  # Get top articles
        content.append(f'{i+1}. {entry.title}')

    if not content:
        content = [
            'News data not available.',
            'Check your internet connection.'
        ]

    return content


def draw(widget: Widget, info: list[str]) -> None:
    draw_widget(widget)
    add_widget_content(widget, info)


def build(stdscr: typing.Any, config: Config) -> Widget:
    return Widget(
        config.name, config.title, config, draw, config.interval, config.dimensions, stdscr, update
    )
