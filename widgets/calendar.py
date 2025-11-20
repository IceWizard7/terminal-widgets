import datetime
import calendar
import curses
import typing
from core.base import Widget, draw_widget, Config, safe_addstr, UIState, BaseConfig


def draw(widget: Widget, ui_state: UIState, base_config: BaseConfig) -> None:
    draw_widget(widget, ui_state, base_config)

    today = datetime.date.today()
    year, month, day = today.year, today.month, today.day

    # Month header
    month_name = today.strftime('%B %Y')
    safe_addstr(widget, 1, 2, month_name)

    # Weekday headers
    weekdays = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
    safe_addstr(widget, 2, 2, ' '.join(weekdays))

    # Calendar days
    cal = calendar.Calendar(firstweekday=0)  # Monday first
    row = 3
    col = 2
    for i, week in enumerate(cal.monthdayscalendar(year, month)):
        for d in week:
            if d == 0:
                safe_addstr(widget, row, col, ' ')
            elif d == day:
                safe_addstr(widget, row, col, f'{d:02}', curses.color_pair(base_config.PRIMARY_PAIR_NUMBER) |
                            curses.A_BOLD)
            else:
                safe_addstr(widget, row, col, f'{d:02}')
            col += 3
        col = 2
        row += 1


def build(stdscr: typing.Any, config: Config) -> Widget:
    return Widget(
        config.name, config.title, config, draw, config.interval, config.dimensions, stdscr,
        update_func=None,
        switch_window_update_func=None
    )
