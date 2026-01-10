import datetime
import calendar
from twidgets.core.base import (
    Widget,
    WidgetContainer,
    Config,
    CursesWindowType,
    CursesColors
)


def draw(widget: Widget, widget_container: WidgetContainer) -> None:
    widget_container.draw_widget(widget)

    today = datetime.date.today()
    year, month, day = today.year, today.month, today.day

    # Month header
    month_name = today.strftime('%B %Y')
    widget.safe_addstr(1, 2, month_name)

    # Weekday headers
    weekdays = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
    widget.safe_addstr(2, 2, ' '.join(weekdays))

    # Calendar days
    cal = calendar.Calendar(firstweekday=0)  # Monday first
    row = 3
    col = 2
    for i, week in enumerate(cal.monthdayscalendar(year, month)):
        for d in week:
            if d == 0:
                widget.safe_addstr(row, col, ' ')
            elif d == day:
                widget.safe_addstr(
                    row, col, f'{d:02}', [widget_container.base_config.PRIMARY_PAIR_NUMBER], [CursesColors.BOLD]
                )
            else:
                widget.safe_addstr(row, col, f'{d:02}')
            col += 3
        col = 2
        row += 1


def draw_help(widget: Widget, widget_container: WidgetContainer) -> None:
    widget_container.draw_widget(widget)

    widget.add_widget_content(
        [
            'Help page ',
            f'({widget.name} widget)',
            '',
            'Displays a calendar.'
        ]
    )


def build(stdscr: CursesWindowType, config: Config) -> Widget:
    return Widget(
        config.name, config.title, config, draw, config.interval, config.dimensions, stdscr,
        update_func=None,
        mouse_click_func=None,
        keyboard_func=None,
        init_func=None,
        help_func=draw_help
    )
