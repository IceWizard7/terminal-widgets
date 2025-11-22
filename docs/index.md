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
├── MANIFEST.in
├── README.md
├── docs
│    └── *.md
├── examples
│    └── example_1.png
├── pyproject.toml
├── requirements.txt
├── setup.cfg
├── setup.py
└── twidgets
    ├── __init__.py
    ├── __main__.py
    ├── cli.py
    ├── config
    │   ├── base.yaml
    │   ├── secrets.env
    │   ├── secrets.env.example
    │   └── widgets
    │       ├── calendar.yaml
    │       ├── clock.yaml
    │       ├── greetings.yaml
    │       ├── mode.yaml
    │       ├── neofetch.yaml
    │       ├── news.yaml
    │       ├── resources.yaml
    │       ├── todo.yaml
    │       ├── todo_save_file.txt
    │       └── weather.yaml
    ├── core
    │   ├── __init__.py
    │   └── base.py
    ├── main.py
    └── widgets
        ├── __init__.py
        ├── calendar_widget.py
        ├── clock_widget.py
        ├── greetings_widget.py
        ├── mode_widget.py
        ├── neofetch_widget.py
        ├── news_widget.py
        ├── resources_widget.py
        ├── todo_widget.py
        └── weather_widget.py
```
