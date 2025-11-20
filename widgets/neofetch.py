import datetime
import subprocess
import psutil
import locale
import platform
import os
import curses
import typing
from core.base import Widget, Config, draw_widget, safe_addstr, ConfigLoader, UIState, BaseConfig


def run_cmd(cmd: str) -> str | None:
    result = subprocess.run(cmd, shell=True, text=True,
                            capture_output=True)
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def return_macos_info() -> list[str]:
    boot_time: datetime.datetime = datetime.datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.datetime.now() - boot_time
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    uptime_string: str = f'{days} days, {hours} hours, {minutes} mins'

    system_lang = locale.getlocale()[0] or 'Unknown'
    encoding = locale.getpreferredencoding() or 'UTF-8'

    user_name: str = os.getenv('USER') or os.getenv('LOGNAME') or 'Unknown'
    hostname: str = platform.node()
    os_version: str = ' '.join(v for v in platform.mac_ver() if isinstance(v, str))
    host_version: str | None = run_cmd('sysctl -n hw.model')
    kernel: str = platform.release()
    terminal: str | None = os.environ.get('TERM_PROGRAM')

    brew_packages: str | None = run_cmd('brew list | wc -l')
    zsh_version: str | None = run_cmd('zsh --version')
    display_info: str | None = run_cmd('/usr/sbin/system_profiler SPDisplaysDataType | grep Resolution')
    if not isinstance(display_info, str):
        display_info = 'Resolution: Unknown'
    terminal_font = run_cmd('defaults read com.apple.Terminal "Default Window Settings"')
    cpu_info: str = (f'{run_cmd("sysctl -n machdep.cpu.brand_string")}'
                     f' ({psutil.cpu_count(logical=False)} Cores @ {psutil.cpu_freq().max} MHz)')

    gpu_info: str | None = None
    try:
        gpu_output: str | None = run_cmd('/usr/sbin/system_profiler SPDisplaysDataType')
        if gpu_output is not None:
            gpu_info = (f'{" ".join(gpu_output.split("Chipset Model: ")[1].split()[:2])}'
                        f' ({gpu_output.split("Total Number of Cores: ")[1].split()[0]} Cores)')
    except Exception:
        pass

    return [
        f'                    \'c.          {user_name}@{hostname}',
        f'                 ,xNMM.          -------------------- ',
        f'               .OMMMMo           OS: macOS {os_version}',
        f'               OMMM0,            Host: {host_version}',
        f'     .;loddo:\' loolloddol;.      Kernel: {kernel}',
        f'   cKMMMMMMMMMMNWMMMMMMMMMM0:    Uptime: {uptime_string}',
        f' .KMMMMMMMMMMMMMMMMMMMMMMMWd.    Packages: {brew_packages} (brew)',
        f' XMMMMMMMMMMMMMMMMMMMMMMMX.      Shell: {zsh_version}',
        f';MMMMMMMMMMMMMMMMMMMMMMMM:       {display_info}',
        f':MMMMMMMMMMMMMMMMMMMMMMMM:       Language: {system_lang}',
        f'.MMMMMMMMMMMMMMMMMMMMMMMMX.      Encoding: {encoding}',
        f' kMMMMMMMMMMMMMMMMMMMMMMMMWd.    Terminal: {terminal}',
        f' .XMMMMMMMMMMMMMMMMMMMMMMMMMMk   Terminal Font: {terminal_font}',
        f'  .XMMMMMMMMMMMMMMMMMMMMMMMMK.   CPU: {cpu_info}',
        f'    kMMMMMMMMMMMMMMMMMMMMMMd     GPU: {gpu_info}',
        f'     ;KMMMMMMMWXXWMMMMMMMk.      ',
        f'       .cooc,.    .,coo:.        '
    ]


def return_raspi_info() -> list[str]:
    boot_time: datetime.datetime = datetime.datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.datetime.now() - boot_time
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    uptime_string: str = f'{days} days, {hours} hours, {minutes} mins'

    system_lang = locale.getlocale()[0] or 'Unknown'
    encoding = locale.getpreferredencoding() or 'UTF-8'

    user_name: str = os.getenv('USER') or os.getenv('LOGNAME') or 'Unknown'
    hostname: str = platform.node()
    os_info: str = platform.platform().split('+')[0]
    host_version: str = (run_cmd('cat /sys/firmware/devicetree/base/model') or 'Unknown Model').replace('\x00', '')
    kernel: str = platform.release()
    terminal: str = (
            os.environ.get('TERM_PROGRAM')
            or os.environ.get('TERM')
            or os.environ.get('COLORTERM')
            or ('SSH' if os.environ.get('SSH_TTY') else 'Unknown')
    )
    terminal_font: str = 'N/A'

    pkg_packages: str = run_cmd('dpkg --get-selections | wc -l') or 'Unknown'
    shell_path: str = os.getenv('SHELL', 'bash')
    try:
        raw_shell_version: str | None = run_cmd(f'{shell_path} --version | head -n 1')
        shell_version: str = shell_path
        if raw_shell_version is not None:
            shell_version = (raw_shell_version.split('version ')[1].split(' ')[0]
                             or shell_path)
    except IndexError:
        shell_version = 'Unknown'

    cpu_info: str = 'Unknown CPU'
    raw_cpu_info: str | None = platform.processor() or run_cmd(
        'cat /proc/cpuinfo | grep "Model name" | head -n 1 | cut -d: -f2')
    if raw_cpu_info is None:
        raw_cpu_info = run_cmd('lscpu | grep "Model name" | awk -F: "{print $2}"')
        if raw_cpu_info is not None:
            cpu_info = raw_cpu_info.split('Model name:')[1].strip() or 'Unknown CPU'
    else:
        cpu_info = raw_cpu_info.strip()

    if os.environ.get('DISPLAY'):
        display_info: str | None = (run_cmd('xdpyinfo 2>/dev/null | grep "dimensions:" | awk "{print $2}"')
                                    or 'Display: Unknown')
    else:
        # Try using tvservice (Pi HDMI detection)
        display_info = run_cmd('tvservice -s | grep -o "[0-9]*x[0-9]*"') or 'Display: Headless'

    gpu_info: str = (run_cmd('vcgencmd version | grep version') or run_cmd(
        'lspci | grep -i "vga\\|3d\\|display"') or 'Unknown').strip()

    return [
        f'',
        f'       _,met$$$$$gg.          {user_name}@{hostname}',
        f'    ,g$$$$$$$$$$$$$$$P.       --------------',
        f'  ,g$$P"     """Y$$.".        OS: {os_info}',
        f' ,$$P\'              `$$$.     Host: {host_version}',
        f'\',$$P       ,ggs.     `$$b:   Kernel: {kernel}',
        f'`d$$\'     ,$P"\'   .    $$$    Uptime: {uptime_string}',
        f' $$P      d$\'     ,    $$P    Packages: {pkg_packages} (dpkg)',
        f' $$:      $$.   -    ,d$$\'    Shell: {shell_version}',
        f' $$;      Y$b._   _,d$P\'      {display_info}',
        f' Y$$.    `.`"Y$$$$P"\'         Language: {system_lang}',
        f' `$$b      "-.__              Encoding: {encoding}',
        f'  `Y$$                        Terminal: {terminal}',
        f'   `Y$$.                      Terminal Font: {terminal_font}',
        f'     `$$b.                    CPU: {cpu_info}',
        f'       `Y$$b.                 GPU: {gpu_info}',
        f'          `"Y$b._             ',
        f'              `"""            '
    ]


def update(_widget: Widget, _config_loader: ConfigLoader) -> list[str]:
    system_type: str = _widget.config.system_type

    if system_type == 'macos':
        return return_macos_info()
    elif system_type == 'raspbian':
        return return_raspi_info()
    else:
        return [
            f'Invalid system_type "{system_type}" not supported.'
        ]


def draw(widget: Widget, ui_state: UIState, base_config: BaseConfig, lines: list[str]) -> None:
    draw_widget(widget, ui_state, base_config)

    colors = [i for i in range(1, 18)]

    for i, line in enumerate(lines):
        safe_addstr(widget, 1 + i, 2, line, curses.color_pair(colors[i % len(colors)] + 6))


def build(stdscr: typing.Any, config: Config) -> Widget:
    return Widget(
        config.name, config.title, config, draw, config.interval, config.dimensions, stdscr,
        update_func=update,
        switch_window_update_func=None
    )
