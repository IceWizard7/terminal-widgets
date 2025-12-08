import datetime
import subprocess
import psutil
import locale
import platform
import os
import typing
from twidgets.core.base import (
    Widget,
    Config,
    CursesWindowType,
    draw_widget,
    safe_addstr,
    ConfigLoader,
    UIState,
    BaseConfig,
    convert_color_number_to_curses_pair,
    ConfigSpecificException,
    LogMessages,
    LogMessage,
    LogLevels,
    add_widget_content
)


def run_cmd(cmd: str) -> str | None:
    """Run a shell command and return output if successful, else None."""
    try:
        result: subprocess.CompletedProcess[typing.Any] = subprocess.run(
            cmd, shell=True, text=True, capture_output=True
        )
        if result.returncode == 0:
            return str(result.stdout.strip())
    except Exception:
        pass
    return None


def get_uptime() -> str:
    boot_time: datetime.datetime = datetime.datetime.fromtimestamp(psutil.boot_time())
    uptime: datetime.timedelta = datetime.datetime.now() - boot_time
    days: int = uptime.days
    hours: int
    remainder: int
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes: int
    minutes, _ = divmod(remainder, 60)
    uptime_string: str = f'{days} days, {hours} hours, {minutes} mins'
    return uptime_string


def get_shell_info() -> str:
    shell: str = os.environ.get('SHELL') or 'Unknown'
    version: str | None = run_cmd(f'{shell} --version') if shell != 'Unknown' else None
    final_shell: str = str(version or shell)
    return final_shell


def get_cpu_info() -> str:
    cpu: str = platform.processor().strip() or ''
    if not cpu or cpu.lower() == 'unknown':
        cpu_alt: str | None = run_cmd('grep "model name" /proc/cpuinfo | head -n 1 | cut -d: -f2')
        cpu = cpu_alt.strip() if cpu_alt else 'Unknown CPU'
    try:
        cores: int | None = psutil.cpu_count(logical=False)
        freq_info: psutil._common.scpufreq | None = psutil.cpu_freq()
        freq: float | None = freq_info.max if freq_info else None
        if freq:
            cpu += f' ({cores} Cores @ {int(freq)} MHz)'
    except Exception:
        pass
    return cpu


def get_display_info_linux() -> str:
    display_info: str
    if os.environ.get('DISPLAY'):
        display_info_tmp: str | None = run_cmd('xdpyinfo 2>/dev/null | grep "dimensions:" | awk "{print $2}"')
        display_info = display_info_tmp or 'Display: Unknown'
    else:
        display_info = 'Display: Headless'
    return display_info


def get_gpu_info_linux() -> str:
    gpu_info: str = run_cmd('lspci | grep -i "vga\\|3d\\|display"') or 'Unknown GPU'
    return gpu_info.strip()


def return_macos_info() -> list[str]:
    user_name: str = os.getenv('USER') or os.getenv('LOGNAME') or 'Unknown'
    hostname: str = platform.node()
    uptime_string: str = get_uptime()
    shell: str = get_shell_info()
    system_lang: str = locale.getlocale()[0] or 'Unknown'
    encoding: str = locale.getpreferredencoding() or 'UTF-8'
    terminal: str | None = os.environ.get('TERM_PROGRAM')
    terminal_font: str = run_cmd('defaults read com.apple.Terminal "Default Window Settings"') or 'N/A'
    cpu_info: str = run_cmd('sysctl -n machdep.cpu.brand_string') or 'Unknown CPU'

    gpu_info: str = 'Unknown'
    try:
        gpu_output: str | None = run_cmd('/usr/sbin/system_profiler SPDisplaysDataType')
        if gpu_output:
            lines: list[str] = gpu_output.splitlines()
            for line in lines:
                if 'Chipset Model:' in line:
                    gpu_info = line.split('Chipset Model:')[1].strip()
                    break
    except Exception:
        pass

    display_info: str = run_cmd(
        '/usr/sbin/system_profiler SPDisplaysDataType | grep Resolution'
    ) or 'Resolution: Unknown'
    brew_packages: str = run_cmd('brew list | wc -l') or 'Unknown'

    os_version: str = ' '.join(v for v in platform.mac_ver() if isinstance(v, str))
    host_version: str | None = run_cmd('sysctl -n hw.model')

    return [
        f'                    \'c.          {user_name}@{hostname}',
        f'                 ,xNMM.          -------------------- ',
        f'               .OMMMMo           OS: macOS {os_version}',
        f'               OMMM0,            Host: {host_version}',
        f'     .;loddo:\' loolloddol;.      Kernel: {platform.release()}',
        f'   cKMMMMMMMMMMNWMMMMMMMMMM0:    Uptime: {uptime_string}',
        f' .KMMMMMMMMMMMMMMMMMMMMMMMWd.    Packages: {brew_packages} (brew)',
        f' XMMMMMMMMMMMMMMMMMMMMMMMX.      Shell: {shell}',
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
    uptime: datetime.timedelta = datetime.datetime.now() - boot_time
    days: int = uptime.days
    hours: int
    remainder: int
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes: int
    minutes, _ = divmod(remainder, 60)
    uptime_string: str = f'{days} days, {hours} hours, {minutes} mins'

    user_name: str = os.getenv('USER') or os.getenv('LOGNAME') or 'Unknown'
    hostname: str = platform.node()
    os_info: str = platform.platform().split('+')[0]
    host_version: str = (run_cmd('cat /sys/firmware/devicetree/base/model') or 'Unknown Model').replace('\x00', '')
    kernel: str = platform.release()

    terminal: str = (os.environ.get('TERM_PROGRAM') or os.environ.get('TERM') or os.environ.get('COLORTERM') or
                     ('SSH' if os.environ.get('SSH_TTY') else 'Unknown'))
    terminal_font: str = 'N/A'

    pkg_packages: str = run_cmd('dpkg --get-selections | wc -l') or 'Unknown'

    shell: str = get_shell_info()
    cpu_info: str = get_cpu_info()
    gpu_info: str = (run_cmd('vcgencmd version | grep version') or get_gpu_info_linux()).strip()
    display_info: str = run_cmd('tvservice -s | grep -o "[0-9]*x[0-9]*"') or get_display_info_linux()
    system_lang: str = locale.getlocale()[0] or 'Unknown'
    encoding: str = locale.getpreferredencoding() or 'UTF-8'

    return [
        f'',
        f'     AAAAAAAAA   AAc  AAA        {user_name}@{hostname}',
        f'    AA        AA         A       --------------',
        f'     A     A   A   A     A       OS: {os_info}',
        f'      A      AAAA      AA        Host: {host_version}',
        f'        AFAAAAA AAAAJAA          Kernel: {kernel}',
        f'      AZ   A           A         Uptime: {uptime_string}',
        f'      A  AAAAAAAAA FAA  A        Packages: {pkg_packages} (dpkg)',
        f'     AAAA      A      AAAA       Shell: {shell}',
        f'   AA  A       A          A      {display_info}',
        f'   A   A      AAA     AA  A      Language: {system_lang}',
        f'    A AAAAAAA     AAAAAA AA      Encoding: {encoding}',
        f'     A    AA       A    5A       Terminal: {terminal}',
        f'     Ac    Aw     A     A        Terminal Font: {terminal_font}',
        f'      AA   AAAAAAAA    A         CPU: {cpu_info}',
        f'         AAA       AA            GPU: {gpu_info}',
        f'            AA2vAA               ',
    ]


def return_linux_info() -> list[str]:
    user_name: str = os.getenv('USER') or os.getenv('LOGNAME') or 'Unknown'
    hostname: str = platform.node()
    uptime_string: str = get_uptime()
    shell: str = get_shell_info()
    cpu_info: str = get_cpu_info()
    gpu_info: str = get_gpu_info_linux()
    display_info: str = get_display_info_linux()
    terminal: str = (os.environ.get('TERM_PROGRAM') or os.environ.get('TERM') or os.environ.get('COLORTERM') or
                     ('SSH' if os.environ.get('SSH_TTY') else 'Unknown'))
    terminal_font: str = 'N/A'
    system_lang: str = locale.getlocale()[0] or 'Unknown'
    encoding: str = locale.getpreferredencoding() or 'UTF-8'
    os_info: str = platform.platform()
    kernel: str = platform.release()

    return [
        f'',
        f'       _,met$$$$$gg.          {user_name}@{hostname}',
        f'    ,g$$$$$$$$$$$$$$$P.       --------------',
        f'  ,g$$P"     """Y$$.".        OS: {os_info}',
        f' ,$$P\'              `$$$.     Kernel: {kernel}',
        f'\',$$P       ,ggs.     `$$b:   Uptime: {uptime_string}',
        f'`d$$\'     ,$P"\'   .    $$$    Shell: {shell}',
        f' $$P      d$\'     ,    $$P    {display_info}',
        f' $$:      $$.   -    ,d$$\'    Language: {system_lang}',
        f' $$;      Y$b._   _,d$P\'      Encoding: {encoding}',
        f' Y$$.    `.`"Y$$$$P"\'         Terminal: {terminal}',
        f' `$$b      "-.__              Terminal Font: {terminal_font}',
        f'  `Y$$                        CPU: {cpu_info}',
        f'   `Y$$.                      GPU: {gpu_info}',
        f'     `$$b.                    ',
        f'       `Y$$b.                 ',
        f'          `"Y$b._             ',
        f'              `"""            '
    ]


def update(_widget: Widget, _config_loader: ConfigLoader) -> list[str]:
    system_type: str | None = _widget.config.system_type

    if not system_type:
        raise ConfigSpecificException(LogMessages([LogMessage(
            f'Configuration for system_type is missing / incorrect ("{_widget.name}" widget)',
            LogLevels.ERROR.key)]))

    if system_type == 'macos':
        return return_macos_info()
    elif system_type == 'raspbian':
        return return_raspi_info()
    elif system_type == 'linux':
        return return_linux_info()
    else:
        return [
            f'Invalid system_type "{system_type}" not supported.'
        ]


def draw(widget: Widget, ui_state: UIState, base_config: BaseConfig, lines: list[str]) -> None:
    draw_widget(widget, ui_state, base_config)

    if ui_state.highlighted == widget and widget.help_mode:
        draw_help(widget, ui_state, base_config)
        return

    colors = [i for i in range(1, 18)]

    for i, line in enumerate(lines):
        safe_addstr(widget, 1 + i, 2, line,
                    convert_color_number_to_curses_pair(colors[i % len(colors)] + 6))


def draw_help(widget: Widget, ui_state: UIState, base_config: BaseConfig) -> None:
    draw_widget(widget, ui_state, base_config)

    add_widget_content(
        widget,
        [
            f'Help page ({widget.name} widget)',
            '',
            'Displays information about your computer.'
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
