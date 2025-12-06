## Terminal Widgets Documentation

Welcome to the Terminal Widgets project!
This dashboard lets you monitor Weather, News, Clock, Calendar, and more in a modular interface.

---

## Setup
- See the [Setup Guide](setup_guide.md) for installation.
- Configure secrets and widgets as explained in the [Configuration Guide](configuration_guide.md).

---

## Adding Widgets
- Learn how to create and integrate new widgets in the [Widget Guide](widget_guide.md).

---


## Project Structure

```text
.
├── LICENSE
├── PYPI-README.md
├── README.md
├── docs
│    └── *.md
├── examples
│    └── example_*.png
├── pyproject.toml
└── twidgets
    ├── __init__.py
    ├── __main__.py
    ├── cli.py
    ├── config
    │   ├── __init__.py
    │   ├── base.yaml
    │   ├── secrets.env.example
    │   └── widgets
    │       ├── *.txt
    │       └── *.yaml
    ├── core
    │   ├── __init__.py
    │   └── base.py
    ├── main.py
    └── widgets
        ├── __init__.py
        └── *.py
```
