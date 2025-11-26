import datetime
import calendar
from twidgets.core.base import (
    Widget,
    Config,
    CursesWindowType,
    draw_widget,
    safe_addstr,
    UIState,
    BaseConfig,
    CursesBold,
    convert_color_number_to_curses_pair,
    add_widget_content
)


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
                safe_addstr(
                    widget, row, col, f'{d:02}',
                    convert_color_number_to_curses_pair(base_config.PRIMARY_PAIR_NUMBER) | CursesBold)
            else:
                safe_addstr(widget, row, col, f'{d:02}')
            col += 3
        col = 2
        row += 1


def draw_help(widget: Widget, ui_state: UIState, base_config: BaseConfig) -> None:
    draw_widget(widget, ui_state, base_config)

    add_widget_content(
        widget,
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
