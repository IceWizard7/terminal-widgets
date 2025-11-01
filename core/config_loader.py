from pathlib import Path
import yaml
from dotenv import load_dotenv
import typing
from core.base import Config
import os

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / 'config'
WIDGETS_DIR = CONFIG_DIR / 'widgets'

load_dotenv(CONFIG_DIR / 'secrets.env')


def load_yaml(path: Path) -> dict[str, typing.Any]:
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def load_base_config() -> dict[str, typing.Any]:
    base_path = CONFIG_DIR / 'base.yaml'
    return load_yaml(base_path) if base_path.exists() else {}


def load_widget_config(widget_name: str) -> Config:
    path = WIDGETS_DIR / f'{widget_name}.yaml'
    if not path.exists():
        raise FileNotFoundError(f'Config for widget "{widget_name}" not found.')
    pure_yaml: dict[str, typing.Any] = load_yaml(path)

    return Config(**pure_yaml)


def get_secret(name: str, default: typing.Any | None = None) -> str | None:
    return os.getenv(name, default)
