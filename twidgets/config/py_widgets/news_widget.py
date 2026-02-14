import requests
import webbrowser
import feedparser  # type: ignore[import-untyped]
import typing
from twidgets.core.base import (
    Widget,
    WidgetContainer,
    Config,
    CursesWindowType,
    CursesKeys
)


def update(widget: Widget, widget_container: WidgetContainer) -> list[str]:
    feed_url: str | None = widget_container.config_loader.get_secret('NEWS_FEED_URL')
    feed_name: str | None = widget_container.config_loader.get_secret('NEWS_FEED_NAME')

    widget.internal_data['feed_entries'] = None

    if feed_url is None:
        return [
            'News data not available.',
            '',
            'Check your configuration.'
        ]

    if feed_name != '':
        widget.title = f'{widget.config.title} [{feed_name}]'

    content: list[str] = []

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

    feed_entries: list[feedparser.FeedParserDict] = feed.entries[:25]

    for i, entry in enumerate(feed_entries[:5]):  # Get top 5 articles
        content.append(f'{i+1}. {entry.title}')

    if not content:
        return [
            'News data not available.',
            '',
            'Check your internet connection and configuration.'
        ]

    widget.internal_data['feed_entries'] = feed_entries
    return content


def mouse_click_action(widget: Widget, _mx: int, my: int, _b_state: int, widget_container: WidgetContainer) -> None:
    if widget.help_mode:
        return

    feed_entries: list[feedparser.FeedParserDict] = typing.cast(
        list[feedparser.FeedParserDict], widget.internal_data.get('feed_entries')
    )
    if not feed_entries or widget_container.ui_state.highlighted != widget:
        widget.internal_data['selected_line'] = None
        return

    amount_rendered_articles: int = min(len(feed_entries), 5)  # 5 top articles are rendered at max

    # Click relative to widget border
    local_y: int = my - widget.dimensions.current_y - 1  # -1 for top border
    if 0 <= local_y < min(amount_rendered_articles, widget.dimensions.current_height - 2):
        # Compute which part of feed is currently visible
        abs_index: int = widget.internal_data.get('selected_line', 0) or 0
        start = max(abs_index - (widget.dimensions.current_height - 2)//2, 0)
        if start + (widget.dimensions.current_height - 2) > amount_rendered_articles:
            start = max(amount_rendered_articles - (widget.dimensions.current_height - 2), 0)

        # Absolute index of clicked line
        clicked_index = start + local_y
        if clicked_index >= amount_rendered_articles:
            clicked_index = amount_rendered_articles - 1

        widget.internal_data['selected_line'] = clicked_index
    else:
        widget.internal_data['selected_line'] = None


def keyboard_press_action(widget: Widget, key: int, _widget_container: WidgetContainer) -> None:
    if widget.help_mode:
        return

    feed_entries: list[feedparser.FeedParserDict] = typing.cast(
        list[feedparser.FeedParserDict], widget.internal_data.get('feed_entries')
    )
    if feed_entries is None:
        return

    amount_rendered_articles: int = min(len(feed_entries), 5)  # 5 top articles are rendered at max
    selected: int = widget.internal_data.get('selected_line', 0)

    if not isinstance(selected, int):
        selected = 0

    # Navigation
    if key == CursesKeys.UP:
        selected -= 1
    elif key == CursesKeys.DOWN:
        selected += 1

    # Wrap around
    if selected < 0:
        selected = amount_rendered_articles - 1

    if selected > (amount_rendered_articles - 1):  # If last entry disappears, wrap around to 0
        selected = 0

    widget.internal_data['selected_line'] = selected

    # Open link in browser
    if key in (CursesKeys.ENTER, 10, 13):
        webbrowser.open_new_tab(widget.internal_data['feed_entries'])


def draw(widget: Widget, widget_container: WidgetContainer, info: list[str]) -> None:
    widget_container.draw_widget(widget)
    widget.add_widget_content(info)


def draw_help(widget: Widget, widget_container: WidgetContainer) -> None:
    widget_container.draw_widget(widget)

    widget.add_widget_content(
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
        mouse_click_func=mouse_click_action,
        keyboard_func=keyboard_press_action,
        init_func=None,
        help_func=draw_help
    )

# TODO make this like TODO Widget
# TODO so enter -> website, and scrollable with arrow keys etc.
