<br/>
<div align="center">
  <h3 align="center">🖥 Terminal Widgets</h3>

  <p align="center">
    This tool enables you to create and run fully customisable dashboards directly in your terminal.
    <br />
    <br />
    <a href="#-1-getting-started">Getting started</a> •
    <a href="#-2-configuration">Configuration</a> •
    <a href="#-3-adding-new-widgets">Adding new widgets</a> •
    <a href="#-4-examples">Examples</a> •
    <a href="#-5-contributing">Contributing</a> •
    <a href="#-6-license">License</a>
  </p>
</div>

![Example Image of Terminal Widgets](examples/example_1.png)
![PyPI Version](https://img.shields.io/pypi/v/twidgets)
![Python Versions](https://img.shields.io/pypi/pyversions/twidgets)
![License](https://img.shields.io/pypi/l/twidgets)
![Downloads (all time)](https://static.pepy.tech/badge/twidgets)
![Downloads (last month)](https://static.pepy.tech/badge/twidgets/month)

### ⚠️ **Note:** This package is only compatible with Unix-based systems.

---

### 🚀 **1. Getting started**

#### 1.1 Installation from PyPI

1. Install: `pip install twidgets`
2. Initialize: `twidgets init`
3. Run: `twidgets`
> ⚠️ Requires Python Version 3.10+

#### 1.2 Installation from Source
1. Clone this repository
2. Install dependencies: `pip install -r requirements-dev.txt `
3. Initialize configuration: `python -m twidgets init`
4. Run: `python -m twidgets`
> ⚠️ Requires Python Version 3.10+

For full documentation see [Setup Guide](docs/setup_guide.md).

---

### ✨ **2. Configuration**

#### 2.1 Changing standard colours and configuration at `~/.config/twidgets/base.yaml`

If you let anything blank, it will fall back to the standard configuration \
However, you will get warned.

Example:
```yaml
use_standard_terminal_background: False

background_color:
  r: 31  # Red value
  g: 29  # Green value
  b: 67  # Blue value
  
...
```

#### 2.2 Configure secrets at `~/.config/twidgets/secrets.env`

Example:
```dotenv
WEATHER_API_KEY='your_api_key'
WEATHER_CITY='Berlin,DE'
WEATHER_UNITS='metric'
NEWS_FEED_URL='https://feeds.bbci.co.uk/news/rss.xml?edition=uk'
NEWS_FEED_NAME='BCC'
```

#### 2.3 Adjust widgets and layouts at `~/.config/twidgets/widgets/*.yaml`

Example:
```yaml
name: 'clock'
title: ' ⏲ Clock'
enabled: True
interval: 1
height: 5
width: 30
y: 4
x: 87
z: 0

weekday_format: '%A'  # day of the week
date_format: '%d.%m.%Y'  # us: '%m.%d.%Y', international: '%Y-%m-%d'
time_format: '%H:%M:%S'  # time
```

For full documentation see [Configuration Guide](docs/configuration_guide.md).

---

### ⭐ **3. Adding new widgets**
Adding new widgets is very easy. For a simple widget, that does not require heavy loading (no `update` function),
you only need to define a configuration and 2 python functions

> **Naming schemes are described [here](docs/widget_guide.md#33-adding-widgets-to-your-layout).** \
> You can create an infinite number of widgets, the file names `custom.yaml` and `custom_widget.py` are just examples.

#### 3.1 Define Configuration (`.yaml`)

Create the configuration file at `~/.config/twidgets/widgets/custom.yaml` and set `interval = 0` for simple widgets:

```yaml
name: custom
title: My Custom Widget
enabled: true
interval: 0  # For simple widgets (no heavy loading, no `update` function)
height: 7
width: 30
y: 1
x: 1
z: 1
```

#### 3.2 Write the Widget Logic (`.py`)
Create the widget's Python file at `~/.config/twidgets/py_widgets/custom_widget.py`

Then define `draw` and `build` functions.

Example:

```python
from twidgets.core.base import Widget, WidgetContainer, Config, CursesWindowType

# Define the draw function for content
def draw(widget: Widget, widget_container: WidgetContainer) -> None:
    # Initialize the widget title, make it loadable and highlightable
    draw_widget(widget, widget_container)

    # Add your content (list of strings)
    content: list[str] = [
        'Welcome to my new widget!',
        'This is a test.',
        'It was very easy to create.'
    ]
    widget.add_widget_content(content)

# Define the build function
def build(stdscr: CursesWindowType, config: Config) -> Widget:
    return Widget(
        config.name, config.title, config, draw, config.interval, config.dimensions, stdscr,  # exactly this order!
        update_func=None,
        mouse_click_func=None,
        keyboard_func=None,
        init_func=None,
        help_func=None
    )
```

For full documentation see [Widget Guide](docs/widget_guide.md).

---

### **4. Upgrading to 2.0 ⚠️**

Version 2.0 introduces breaking changes. Please see the [migration guide](docs/migration/v1.3-v2.0.md) for instructions on updating your code.

---

### 🌅 **5. Examples**

![Example 1 of Terminal Widgets](examples/example_1.png)
![Example 2 of Terminal Widgets](examples/example_2.png)
![Example 3 of Terminal Widgets](examples/example_3.png)

For all examples see [Examples](examples/index.md).

---

### 🧩 **6. Contributing**

Help the project grow: create an issue or pull request!

---

### 📜 **7. License**

See [License](LICENSE)
