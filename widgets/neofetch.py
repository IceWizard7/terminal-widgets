import datetime
import subprocess
import psutil
import locale
import platform
import os
import curses
import typing
from core.base import Widget, Config, draw_widget, safe_addstr


def update(_widget: Widget) -> list[str]:
    def run_cmd(cmd: str) -> str | None:
        result = subprocess.run(cmd, shell=True, text=True,
                                capture_output=True)
        if result.returncode == 0:
            return result.stdout.strip()
        return None

    system_type: str = _widget.config.system_type

    if system_type == 'macos':
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
        host_version: str = run_cmd('sysctl -n hw.model')
        kernel: str = platform.release()
        system_lang: str = system_lang
        encoding: str = encoding
        terminal: str = os.environ.get('TERM_PROGRAM')

        brew_packages: str | None = run_cmd('brew list | wc -l')
        zsh_version: str | None = run_cmd('zsh --version')
        display_info: str | None = run_cmd('/usr/sbin/system_profiler SPDisplaysDataType | grep Resolution')
        if not isinstance(display_info, str):
            display_info = 'Resolution: Unknown'
        terminal_font = run_cmd('defaults read com.apple.Terminal "Default Window Settings"')
        cpu_info: str = f'{run_cmd("sysctl -n machdep.cpu.brand_string")} ({platform.processor()})'

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
    elif system_type == 'raspbian':
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
        os_info: str = ' '.join(platform.linux_distribution()) if hasattr(platform,
                                                                          'linux_distribution') else platform.platform()
        host_version: str = (run_cmd('cat /sys/firmware/devicetree/base/model') or 'Unknown Model').replace('\x00', '')
        kernel: str = platform.release()
        system_lang: str = system_lang
        encoding: str = encoding
        terminal: str = os.environ.get('TERM_PROGRAM')
        terminal_font = run_cmd('defaults read com.apple.Terminal "Default Window Settings"')

        pkg_packages: str = run_cmd('dpkg --get-selections | wc -l') or 'Unknown'
        shell_path: str = os.getenv('SHELL', 'bash')
        shell_version: str = run_cmd(f'{shell_path} --version | head -n 1') or shell_path

        cpu_info: str = (platform.processor() or run_cmd(
            'cat /proc/cpuinfo | grep "Model name" | head -n 1 | cut -d: -f2')).strip()
        if not cpu_info:
            cpu_info = run_cmd('lscpu | grep "Model name" | awk -F: "{print $2}"') or 'Unknown CPU'

        display_info: str = run_cmd('xdpyinfo | grep "dimensions:" | awk "{print $2}"') or 'Resolution: Unknown'

        gpu_info: str = (run_cmd('vcgencmd version | grep version') or run_cmd(
            'lspci | grep -i "vga\\|3d\\|display"') or 'GPU: Unknown').strip()

        return [
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
    else:
        return [
            'Invalid system_type.'
        ]


def draw(widget: Widget, lines: list[str]) -> None:
    draw_widget(widget)

    colors = [i for i in range(1, 18)]

    for i, line in enumerate(lines):
        safe_addstr(widget, 1 + i, 2, line, curses.color_pair(colors[i % len(colors)] + 1))


def build(stdscr: typing.Any, config: Config) -> Widget:
    return Widget(
        config.name, config.title, config, draw, config.interval, config.dimensions, stdscr, update
    )
