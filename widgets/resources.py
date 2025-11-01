import typing
import psutil
import shutil
from core.base import Widget, draw_widget, add_widget_content, Config


def update(_widget: Widget) -> list[str]:
    cpu = psutil.cpu_percent()
    cpu_cores = psutil.cpu_count(logical=False)
    cpu_freq = psutil.cpu_freq()
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    disk_usage = shutil.disk_usage('/')
    network = psutil.net_io_counters()

    old_bytes_sent: int = _widget.internal_data.get('bytes_sent')
    old_bytes_recv: int = _widget.internal_data.get('bytes_recv')

    new_bytes_sent: int = network.bytes_sent
    new_bytes_recv: int = network.bytes_recv

    difference_bytes_sent: float = 0.0
    difference_bytes_recv: float = 0.0

    if _widget.config.interval is not None:
        if old_bytes_sent is not None:
            difference_bytes_sent = (new_bytes_sent - old_bytes_sent) / _widget.config.interval
        if old_bytes_recv is not None:
            difference_bytes_recv = (new_bytes_recv - old_bytes_recv) / _widget.config.interval

    _widget.internal_data = {
        'bytes_sent': new_bytes_sent,
        'bytes_recv': new_bytes_recv,
    }

    return [
        f'CPU: {cpu:04.1f}% ({cpu_cores} Cores @ {cpu_freq.max} MHz)',
        f'Memory: {round(memory.used / (1024 ** 2), 2)} MiB / {round(memory.total / (1024 ** 2), 2)} MiB',
        f'Swap: {round(swap.used / (1024 ** 2), 2)} MiB / {round(swap.total / (1024 ** 2), 2)} MiB',
        f'Disk: {round(disk_usage.used / (1024 ** 3), 2)} GiB / {round(disk_usage.total / (1024 ** 3), 2)} GiB',
        f'Network sent: {round(difference_bytes_sent / (1024 ** 2), 2)} MiB / s',
        f'Network received: {round(difference_bytes_recv / (1024 ** 2), 2)} MiB / s',
    ]


def draw(widget: Widget, content: list[str]) -> None:
    draw_widget(widget)
    add_widget_content(widget, content)


def build(stdscr: typing.Any, config: Config) -> Widget:
    return Widget(
        config.name, config.title, config, draw, config.interval, config.dimensions, stdscr, update
    )
