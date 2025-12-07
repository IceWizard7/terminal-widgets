import json
import pathlib
from twidgets.core.base import (
    Widget,
    Config,
    CursesWindowType,
    draw_widget,
    safe_addstr,
    UIState,
    BaseConfig,
    prompt_user_input,
    CursesReverse,
    convert_color_number_to_curses_pair,
    CursesKeys,
    ConfigSpecificException,
    LogMessages,
    LogMessage,
    LogLevels,
    add_widget_content
)


def add_todo(widget: Widget, title: str) -> None:
    if 'todos' in widget.draw_data:
        widget.draw_data['todos'][widget.draw_data['todo_count']] = f'({widget.draw_data["todo_count"]}) {title}'
        widget.draw_data['todo_count'] += 1
    else:
        widget.draw_data['todos'] = {1: f'(1) {title}'}
        widget.draw_data['todo_count'] = 2
    save_todos(widget)  # auto-save


def remove_todo(widget: Widget, line: int) -> None:
    if 'todos' in widget.draw_data:
        keys = list(widget.draw_data['todos'].keys())
        todo_id = keys[line]
        widget.draw_data['todos'].pop(todo_id, None)
    save_todos(widget)  # auto-save


def save_todos(widget: Widget) -> None:
    # If file doesn't exist, this will create it

    if widget.config.save_path:
        file_path = pathlib.Path(widget.config.save_path).expanduser()
        with open(file_path, 'w') as file:
            if 'todos' in widget.draw_data:
                json.dump(widget.draw_data['todos'], file)
            else:
                json.dump({}, file)
    else:
        raise ConfigSpecificException(LogMessages([LogMessage(
            f'Configuration for save_path is missing / incorrect ("{widget.name}" widget)',
            LogLevels.ERROR.key)]))


def load_todos(widget: Widget) -> None:
    # If file doesn't exist, set todos = {}
    if widget.config.save_path:
        try:
            file_path = pathlib.Path(widget.config.save_path).expanduser()
            with open(file_path, 'r') as file:
                data = json.load(file)
            data = {int(k): v for k, v in data.items()}
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}
    else:
        raise ConfigSpecificException(LogMessages([LogMessage(
            f'Configuration for save_path is missing / incorrect ("{widget.name}" widget)',
            LogLevels.ERROR.key)]))

    data = {int(k): v for k, v in data.items()}

    widget.draw_data['todos'] = data
    widget.draw_data['todo_count'] = max(data.keys(), default=0) + 1


def remove_highlighted_line(widget: Widget) -> None:
    widget.draw_data['selected_line'] = None


def mouse_click_action(widget: Widget, _mx: int, _my: int, _b_state: int, ui_state: UIState) -> None:
    load_todos(widget)

    if widget.help_mode:
        return

    todos = list(widget.draw_data.get('todos', {}).values())
    if not todos or ui_state.highlighted != widget:
        widget.draw_data['selected_line'] = None
        return

    # Click relative to widget border
    local_y: int = _my - widget.dimensions.current_y - 1  # -1 for top border
    if 0 <= local_y < min(len(todos), widget.dimensions.current_height - 2):
        # Compute which part of todos is currently visible
        abs_index = widget.draw_data.get('selected_line', 0) or 0
        start = max(abs_index - (widget.dimensions.current_height - 2)//2, 0)
        if start + (widget.dimensions.current_height - 2) > len(todos):
            start = max(len(todos) - (widget.dimensions.current_height - 2), 0)

        # Absolute index of clicked line
        clicked_index = start + local_y
        if clicked_index >= len(todos):
            clicked_index = len(todos) - 1

        widget.draw_data['selected_line'] = clicked_index
    else:
        widget.draw_data['selected_line'] = None


def keyboard_press_action(widget: Widget, key: int, _ui_state: UIState, _base_config: BaseConfig) -> None:
    load_todos(widget)

    if widget.help_mode:
        return

    if 'todos' not in widget.draw_data:
        return
    len_todos = len(widget.draw_data['todos'])
    selected = widget.draw_data.get('selected_line', 0)

    if not isinstance(selected, int):
        selected = 0

    # Navigation
    if key == CursesKeys.UP:
        selected -= 1
    elif key == CursesKeys.DOWN:
        selected += 1

    # Wrap around
    if selected < 0:
        selected = len_todos - 1

    if selected > (len_todos - 1):  # If you delete the last to-do, this will wrap around to 0
        selected = 0

    widget.draw_data['selected_line'] = selected

    # Add new to_do
    if key in (CursesKeys.ENTER, 10, 13):
        new_todo = prompt_user_input(widget, 'New To-Do: ')
        if new_todo.strip():
            add_todo(widget, new_todo.strip())

    # Delete to_do
    elif key in (CursesKeys.BACKSPACE, 127, 8):  # Backspace
        if len_todos > 0:
            confirm = prompt_user_input(widget, 'Confirm deletion (y): ')
            if confirm.lower().strip() in ['y']:
                remove_todo(widget, widget.draw_data['selected_line'])


def render_todos(todos: list[str], highlighted_line: int | None, max_render: int) -> tuple[list[str], int | None]:
    if len(todos) <= max_render:
        return todos.copy(), highlighted_line  # everything fits, no slicing needed

    if highlighted_line is None:
        # No highlight -> show first items
        start = 0
    else:
        radius = max_render // 2
        # Compute slice around highlighted line
        start = max(highlighted_line - radius, 0)

        # Make sure we don't go past the list
        if start + max_render > len(todos):
            start = max(len(todos) - max_render, 0)

    end = start + max_render
    visible_todos = todos[start:end]

    if highlighted_line is None:
        rel_index = None
    else:
        rel_index = highlighted_line - start

    # Ellipsis if needed
    if end < len(todos):
        visible_todos.append('...')
        if rel_index is not None and rel_index >= max_render:
            rel_index = max_render - 1  # highlight the last visible line

    return visible_todos, rel_index


def init(widget: Widget, _ui_state: UIState, _base_config: BaseConfig) -> None:
    load_todos(widget)


def draw(widget: Widget, ui_state: UIState, base_config: BaseConfig) -> None:
    draw_widget(widget, ui_state, base_config, widget.title)

    if ui_state.highlighted != widget:
        remove_highlighted_line(widget)

    todos, rel_index = render_todos(
        list(widget.draw_data.get('todos', {}).values()),
        widget.draw_data.get('selected_line'),
        widget.config.max_rendering if widget.config.max_rendering else 3
    )

    for i, todo in enumerate(todos):
        if rel_index is not None and i == rel_index:
            safe_addstr(
                widget, 1 + i, 1, todo[:widget.dimensions.current_width - 2],
                CursesReverse | convert_color_number_to_curses_pair(base_config.SECONDARY_PAIR_NUMBER))
        else:
            safe_addstr(widget, 1 + i, 1, todo[:widget.dimensions.current_width - 2])


def draw_help(widget: Widget, ui_state: UIState, base_config: BaseConfig) -> None:
    draw_widget(widget, ui_state, base_config)

    add_widget_content(
        widget,
        [
            f'Help page ({widget.name} widget)',
            '',
            'Keybinds: ',
            'Enter - New Todo',
            'Backspace - Delete Todo',
            'Arrow Keys - Navigation',
            '',
            'Displays todos.'
        ]
    )


def build(stdscr: CursesWindowType, config: Config) -> Widget:
    return Widget(
        config.name, config.title, config, draw, config.interval, config.dimensions, stdscr,
        update_func=None,
        mouse_click_func=mouse_click_action,
        keyboard_func=keyboard_press_action,
        init_func=init,
        help_func=draw_help
    )
