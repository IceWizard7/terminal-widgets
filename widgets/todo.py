import curses
import typing
from core.base import Widget, Config, draw_widget, safe_addstr, UIState, BaseConfig
import json


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
    with open(widget.config.save_path, 'w') as file:
        if 'todos' in widget.draw_data:
            json.dump(widget.draw_data['todos'], file)
        else:
            json.dump({}, file)


def load_todos(widget: Widget) -> None:
    # If file doesn't exist, set todos = {}
    try:
        with open(widget.config.save_path, 'r') as file:
            data = json.load(file)
        data = {int(k): v for k, v in data.items()}
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    data = {int(k): v for k, v in data.items()}

    widget.draw_data['todos'] = data
    widget.draw_data['todo_count'] = max(data.keys(), default=0) + 1


def remove_highlighted_line(widget: Widget) -> None:
    widget.draw_data['selected_line'] = None


def mouse_click_action(todo_widget: Widget, _mx: int, _my: int, _b_state: int, ui_state: UIState) -> None:
    todos = list(todo_widget.draw_data.get('todos', {}).values())
    if not todos or ui_state.highlighted != todo_widget:
        todo_widget.draw_data['selected_line'] = None
        return

    # Click relative to widget border
    local_y: int = _my - todo_widget.dimensions.y - 1  # -1 for top border
    if 0 <= local_y < min(len(todos), todo_widget.dimensions.height - 2):
        # Compute which part of todos is currently visible
        abs_index = todo_widget.draw_data.get('selected_line', 0) or 0
        start = max(abs_index - (todo_widget.dimensions.height - 2)//2, 0)
        if start + (todo_widget.dimensions.height - 2) > len(todos):
            start = max(len(todos) - (todo_widget.dimensions.height - 2), 0)

        # Absolute index of clicked line
        clicked_index = start + local_y
        if clicked_index >= len(todos):
            clicked_index = len(todos) - 1

        todo_widget.draw_data['selected_line'] = clicked_index
    else:
        todo_widget.draw_data['selected_line'] = None


def render_todos(todos: list[str], highlighted_line: int | None, max_render: int) -> tuple[list[str], int | None]:
    if len(todos) <= max_render:
        return todos.copy(), highlighted_line  # everything fits, no slicing needed

    if highlighted_line is None:
        # No highlight → show first items
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


def draw(widget: Widget, ui_state: UIState, base_config: BaseConfig) -> None:
    draw_widget(widget, ui_state, base_config, widget.title)

    if ui_state.previously_highlighted != ui_state.highlighted:  # changed
        if ui_state.previously_highlighted == widget and ui_state.highlighted != widget:
            remove_highlighted_line(widget)

    todos, rel_index = render_todos(
        list(widget.draw_data.get('todos', {}).values()),
        widget.draw_data.get('selected_line'),
        widget.config.max_rendering if widget.config.max_rendering else 3
    )

    for i, todo in enumerate(todos):
        if rel_index is not None and i == rel_index:
            safe_addstr(widget, 1 + i, 1, todo[:widget.dimensions.width - 2],
                        curses.A_REVERSE | curses.color_pair(base_config.SECONDARY_PAIR_NUMBER))
        else:
            safe_addstr(widget, 1 + i, 1, todo[:widget.dimensions.width - 2])


def build(stdscr: typing.Any, config: Config) -> Widget:
    return Widget(
        config.name, config.title, config, draw, config.interval, config.dimensions, stdscr,
        update_func=None,
        mouse_click_func=mouse_click_action
    )
