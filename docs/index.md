<br/>
<div align="center">
  <h3 align="center">🖥 Terminal Widgets</h3>

  <p align="center">
    This tool enables you to create and run fully customisable dashboards directly in your terminal.
    <br />
  </p>
</div>

![Example Image of Terminal Widgets](../examples/example_1.png)
![PyPI Version](https://img.shields.io/pypi/v/twidgets)
![Python Versions](https://img.shields.io/pypi/pyversions/twidgets)
![License](https://img.shields.io/pypi/l/twidgets)
![Downloads (all time)](https://static.pepy.tech/badge/twidgets)
![Downloads (last month)](https://static.pepy.tech/badge/twidgets/month)

### ⚠️ **Note:** This package is only compatible with Unix-based systems.

---

## 1. Getting started

See the **[Setup Guide](setup_guide.md)** for installation instructions.

---

## 2. Configuration

See the **[Configuration Guide](configuration_guide.md)** for setting up secrets and widgets.

---

## 3. Adding Widgets

See the **[Widget Guide](widget_guide.md)** for creating and integrating custom widgets.

---

## 4. Project Structure

```text
.
├── LICENSE
├── PYPI-README.md
├── README.md
├── docs
│   └── *.md
├── examples
│   ├── example_*.png
│   └── index.md
├── mypy.ini
├── pyproject.toml
├── requirements-dev.txt
├── tests
│   ├── *.txt
│   └── *.py
└── twidgets
    ├── __init__.py
    ├── __main__.py
    ├── cli.py
    ├── config
    │   ├── __init__.py
    │   ├── base.yaml
    │   ├── py_widgets
    │   │   └── *.py
    │   ├── secrets.env.example
    │   └── widgets
    │       ├── +.txt
    │       └── *.yaml
    ├── core
    │   ├── __init__.py
    │   └── base.py
    └── main.py
```