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
├── README.md
├── config
│         ├── base.yaml
│         ├── secrets.env
│         └── widgets
│             └── *.yaml
├── core
│     ├── __init__.py
│     ├── base.py
│     └── config_loader.py
├── docs
│    ├── configuration_guide.md
│    ├── index.md
│    ├── setup_guide.md
│    └── widget_guide.md
├── main.py
├── requirements.txt
└── widgets
    └── *.py
```
