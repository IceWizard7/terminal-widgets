import requests
import webbrowser
import feedparser  # type: ignore[import-untyped]
import typing
from twidgets.core.base import (
    Widget,
    WidgetContainer,
    Config,
    CursesWindowType,
    CursesKeys,
    CursesColors, DebugException
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

    feed_entries: list[feedparser.FeedParserDict] = feed.entries[:50]  # 50 internal maximum

    if not feed_entries:
        return [
            'News data not available.',
            '',
            'Check your internet connection and configuration.'
        ]

    widget.internal_data['feed_entries'] = feed_entries
    return ['Success']


def mouse_click_action(widget: Widget, _mx: int, my: int, _b_state: int, widget_container: WidgetContainer) -> None:
    if widget.help_mode:
        return

    feed_entries: list[feedparser.FeedParserDict] = typing.cast(
        list[feedparser.FeedParserDict], widget.internal_data.get('feed_entries')
    )
    if not feed_entries or widget_container.ui_state.highlighted != widget:
        widget.internal_data['selected_line'] = None
        return

    amount_rendered_articles: int = len(feed_entries)

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

    amount_rendered_articles: int = len(feed_entries)
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
        if selected <= len(feed_entries) - 1:
            target_entry: feedparser.FeedParserDict = feed_entries[selected]
            webbrowser.open_new_tab(target_entry.link)


def render_feed(
        feed_entries: list[feedparser.FeedParserDict], highlighted_line: int | None, max_render: int
) -> tuple[list[str], int | None]:
    # Everything fits, no slicing needed
    if len(feed_entries) <= max_render:
        return [
            f'{i+1}. {entry.title}' for i, entry in enumerate(feed_entries)
        ], highlighted_line

    if highlighted_line is None:
        # No highlight -> show first items
        start = 0
    else:
        radius = max_render // 2
        # Compute slice around highlighted line
        start = max(highlighted_line - radius, 0)

        # Make sure we don't go past the list
        if start + max_render > len(feed_entries):
            start = max(len(feed_entries) - max_render, 0)

    end: int = start + max_render
    visible_feed: list[str] = [
        f'{start+i+1}. {entry.title}' for i, entry in enumerate(feed_entries[start:end])
    ]

    if highlighted_line is None:
        rel_index: int | None = None
    else:
        rel_index = highlighted_line - start

    # Ellipsis if needed
    if end < len(feed_entries):
        visible_feed.append('...')
        if rel_index is not None and rel_index >= max_render:
            rel_index = max_render - 1  # highlight the last visible line

    return visible_feed, rel_index


def draw(widget: Widget, widget_container: WidgetContainer, info: list[str]) -> None:
    widget_container.draw_widget(widget)

    if info and info != ['Success']:  # Display error if something went wrong
        widget.add_widget_content(info)
        return

    if widget_container.ui_state.highlighted != widget:
        widget.internal_data['selected_line'] = None

    feed_entries, rel_index = render_feed(
        widget.internal_data.get('feed_entries', []),
        widget.internal_data.get('selected_line'),
        widget.config.max_rendering if widget.config.max_rendering else 5
    )

    for i, entry in enumerate(feed_entries):
        if rel_index is not None and i == rel_index:
            widget.safe_addstr(
                1 + i, 1, entry[:widget.dimensions.current_width - 2],
                [widget_container.base_config.SECONDARY_PAIR_NUMBER], [CursesColors.REVERSE])
        else:
            widget.safe_addstr(1 + i, 1, entry[:widget.dimensions.current_width - 2])


def draw_help(widget: Widget, widget_container: WidgetContainer) -> None:
    widget_container.draw_widget(widget)

    widget.add_widget_content(
        [
            f'Help page ({widget.name} widget)',
            '',
            'Keybinds: ',
            'Enter - Open link in web browser',
            'Arrow Keys - Navigation',
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
