import psutil
import shutil
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
    cpu = psutil.cpu_percent()
    cpu_cores = psutil.cpu_count(logical=False)
    max_freq_mhz = 0.0
    try:
        freq = psutil.cpu_freq()

        if freq is not None:
            max_freq = freq.max
            # If the value is suspiciously small (like 4), assume it's in GHz
            if max_freq < 100:  # anything below 100 MHz is definitely wrong
                max_freq_mhz = max_freq * 1000
            else:
                max_freq_mhz = max_freq
    except Exception:
        pass
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    disk_usage = shutil.disk_usage('/')
    network = psutil.net_io_counters()

    old_bytes_sent: int = _widget.internal_data.get('bytes_sent')
    old_bytes_recv: int = _widget.internal_data.get('bytes_recv')

    new_bytes_sent: int = network.bytes_sent
    new_bytes_recv: int = network.bytes_recv

    difference_bytes_sent_mib: float = 0.0
    difference_bytes_recv_mib: float = 0.0

    if _widget.config.interval is not None:
        if old_bytes_sent is not None:
            difference_bytes_sent_mib = round(((new_bytes_sent - old_bytes_sent) / _widget.config.interval) /
                                              (1024 ** 2), 2)
        if old_bytes_recv is not None:
            difference_bytes_recv_mib = round(((new_bytes_recv - old_bytes_recv) / _widget.config.interval) /
                                              (1024 ** 2), 2)

    _widget.internal_data = {
        'bytes_sent': new_bytes_sent,
        'bytes_recv': new_bytes_recv,
    }

    # memory.used returns something else...
    memory_used_mib: float = round((memory.total - memory.available) / (1024 ** 2), 2)
    memory_total_mib: float = round(memory.total / (1024 ** 2), 2)
    memory_percent: float = round(memory_used_mib * 100 / memory_total_mib, 2)

    swap_used_mib: float = round(swap.used / (1024 ** 2), 2)
    swap_total_mib: float = round(swap.total / (1024 ** 2), 2)

    try:
        swap_percent: float = round(swap_used_mib * 100 / swap_total_mib, 2)
    except ZeroDivisionError:
        swap_percent = 0.0

    disk_used_gib: float = round(disk_usage.used / (1024 ** 3), 2)
    disk_total_gib: float = round(disk_usage.total / (1024 ** 3), 2)

    try:
        disk_percent: float = round(disk_used_gib * 100 / disk_total_gib, 2)
    except ZeroDivisionError:
        disk_percent = 0.0

    return [
        f'CPU: {cpu:04.1f}% ({cpu_cores} Cores @ {max_freq_mhz} MHz)',
        f'Memory: {memory_used_mib} MiB / {memory_total_mib} MiB ({memory_percent}%)',
        f'Swap: {swap_used_mib} MiB / {swap_total_mib} MiB ({swap_percent}%)',
        f'Disk: {disk_used_gib} GiB / {disk_total_gib} GiB ({disk_percent}%)',
        f'Network sent: {difference_bytes_sent_mib} MiB / s',
        f'Network received: {difference_bytes_recv_mib} MiB / s',
    ]


def draw(widget: Widget, ui_state: UIState, base_config: BaseConfig, content: list[str]) -> None:
    draw_widget(widget, ui_state, base_config)
    add_widget_content(widget, content)


def draw_help(widget: Widget, ui_state: UIState, base_config: BaseConfig) -> None:
    draw_widget(widget, ui_state, base_config)

    add_widget_content(
        widget,
        [
            f'Help page ({widget.name} widget)',
            '',
            'Displays resource usage of your computer.'
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
