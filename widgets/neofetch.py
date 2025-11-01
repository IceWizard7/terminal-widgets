import datetime
import subprocess
import psutil
import shutil
import locale
import platform
import os
import curses
import typing
from core.base import Widget, Config, draw_widget, safe_addstr


def update(_widget: Widget) -> dict[str, typing.Any]:
    def run_cmd(cmd: str) -> str | None:
        result = subprocess.run(cmd, shell=True, text=True,
                                capture_output=True)
        if result.returncode == 0:
            return result.stdout.strip()
        return None

    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.datetime.now() - boot_time
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    system_lang = locale.getlocale()[0] or 'Unknown'
    encoding = locale.getpreferredencoding() or 'UTF-8'

    brew_packages = run_cmd('brew list | wc -l')
    zsh_version = run_cmd('zsh --version')
    display_info = run_cmd('/usr/sbin/system_profiler SPDisplaysDataType | grep Resolution')
    if not isinstance(display_info, str):
        display_info = 'Resolution: Unknown'
    terminal_font = run_cmd('defaults read com.apple.Terminal "Default Window Settings"')
    cpu_info = f'{run_cmd("sysctl -n machdep.cpu.brand_string")} ({platform.processor()})'

    gpu_info = None
    try:
        gpu_output: str | None = run_cmd('/usr/sbin/system_profiler SPDisplaysDataType')
        if gpu_output is not None:
            gpu_info = (f'{" ".join(gpu_output.split("Chipset Model: ")[1].split()[:2])}'
                        f' ({gpu_output.split("Total Number of Cores: ")[1].split()[0]} Cores)')
    except Exception:
        pass

    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    disk_usage = shutil.disk_usage("/")

    return {
        'user_name': os.getenv('USER') or os.getenv('LOGNAME') or 'Unknown',
        'hostname': platform.node(),
        'os': ' '.join(v for v in platform.mac_ver() if isinstance(v, str)),
        'host': run_cmd('sysctl -n hw.model'),
        'kernel': platform.release(),
        'uptime': f'{days} days, {hours} hours, {minutes} mins',
        'brew_packages': brew_packages,
        'zsh_version': zsh_version,
        'display_info': display_info,
        'system_lang': system_lang,
        'encoding': encoding,
        'terminal': os.environ.get('TERM_PROGRAM'),
        'terminal_font': terminal_font,
        'cpu_info': cpu_info,
        'gpu_info': gpu_info,
        'used_mem': round(memory.used / (1024 ** 2), 2),
        'total_mem': round(memory.total / (1024 ** 2), 2),
        'used_disk': round(disk_usage.used / (1024 ** 3), 2),
        'total_disk': round(disk.total / (1024 ** 3), 2)
    }


def draw(widget: Widget, info: dict[str, typing.Any]) -> None:
    draw_widget(widget)

    lines = [
        f'                    \'c.          {info["user_name"]}@{info["hostname"]} ',
        f'                 ,xNMM.          -------------------- ',
        f'               .OMMMMo           OS: macOS {info["os"]}',
        f'               OMMM0,            Host: {info["host"]} ',
        f'     .;loddo:\' loolloddol;.      Kernel: {info["kernel"]} ',
        f'   cKMMMMMMMMMMNWMMMMMMMMMM0:    Uptime: {info["uptime"]} ',
        f' .KMMMMMMMMMMMMMMMMMMMMMMMWd.    Packages: {info["brew_packages"]} (brew) ',
        f' XMMMMMMMMMMMMMMMMMMMMMMMX.      Shell: {info["zsh_version"]} ',
        f';MMMMMMMMMMMMMMMMMMMMMMMM:       {info["display_info"]} ',
        f':MMMMMMMMMMMMMMMMMMMMMMMM:       Language: {info["system_lang"]} ',
        f'.MMMMMMMMMMMMMMMMMMMMMMMMX.      Encoding: {info["encoding"]} ',
        f' kMMMMMMMMMMMMMMMMMMMMMMMMWd.    Terminal: {info["terminal"]} ',
        f' .XMMMMMMMMMMMMMMMMMMMMMMMMMMk   Terminal Font: {info["terminal_font"]} ',
        f'  .XMMMMMMMMMMMMMMMMMMMMMMMMK.   CPU: {info["cpu_info"]} ',
        f'    kMMMMMMMMMMMMMMMMMMMMMMd     GPU: {info["gpu_info"]} ',
        f'     ;KMMMMMMMWXXWMMMMMMMk.      Disk: {info["used_disk"]} GiB / {info["total_disk"]} GiB',
        f'       .cooc,.    .,coo:.        Memory: {info["used_mem"]} MiB / {info["total_mem"]} MiB'
    ]

    colors = [i for i in range(1, 18)]

    for i, line in enumerate(lines):
        safe_addstr(widget, 1 + i, 2, line, curses.color_pair(colors[i % len(colors)] + 1))


def build(stdscr: typing.Any, config: Config) -> Widget:
    return Widget(
        config.name, config.title, config, draw, config.interval, config.dimensions, stdscr, update
    )
