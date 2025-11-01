import datetime
import calendar
import curses
import typing
from core.base import Widget, draw_widget, Config
from .config import PRIMARY_COLOR_NUMBER


def draw(widget: Widget) -> None:
    draw_widget(widget)

    today = datetime.date.today()
    year, month, day = today.year, today.month, today.day

    # Month header
    month_name = today.strftime('%B %Y')
    widget.win.addstr(1, 2, month_name)

    # Weekday headers
    weekdays = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
    widget.win.addstr(2, 2, ' '.join(weekdays))

    # Calendar days
    cal = calendar.Calendar(firstweekday=0)  # Monday first
    row = 3
    col = 2
    for i, week in enumerate(cal.monthdayscalendar(year, month)):
        for d in week:
            if d == 0:
                widget.win.addstr(row, col, ' ')
            elif d == day:
                widget.win.addstr(row, col, f'{d:02}', curses.color_pair(PRIMARY_COLOR_NUMBER) | curses.A_BOLD)
            else:
                widget.win.addstr(row, col, f'{d:02}')
            col += 3
        col = 2
        row += 1


def build(stdscr: typing.Any, config: Config) -> Widget:
    return Widget(
        config.name, config.title, config, draw, config.interval, config.dimensions, stdscr
    )
