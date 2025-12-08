<br/>
<div align="center">
  <h3 align="center">🖥 Terminal Widgets</h3>

  <p align="center">
    This tool enables you to create and run fully customizable dashboards directly in your terminal.
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
![Stats](https://img.shields.io/pypi/v/twidgets)
![Stats](https://img.shields.io/pypi/pyversions/twidgets)
![Stats](https://img.shields.io/pypi/l/twidgets)
![Stats](https://static.pepy.tech/badge/twidgets)
![Stats](https://static.pepy.tech/badge/twidgets/month)

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

#### 2.1 Changing standard colors and configuration at `~/.config/twidgets/base.yaml`

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
> You can create an infinite amount of widgets, the file names `custom.yaml` and `custom_widget.py` are just examples.

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
```

#### 3.2 Write the Widget Logic (`.py`)
Create the widget's Python file at `~/.config/twidgets/py_widgets/custom_widget.py`

Then define `draw` and `build` functions.

Example:

```python
from twidgets.core.base import Widget, draw_widget, add_widget_content, Config, UIState, BaseConfig, CursesWindowType
import typing

# Define the draw function for content
def draw(widget: Widget, ui_state: UIState, base_config: BaseConfig) -> None:
    # Initialize the widget title, make it loadable and highlightable
    draw_widget(widget, ui_state, base_config)

    # Add your content (list of strings)
    content: list[str] = [
        'Welcome to my new widget!',
        'This is a test.',
        'It was very easy to create.'
    ]
    add_widget_content(widget, content)

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

### 🌅 **4. Examples**

![Example 1 of Terminal Widgets](examples/example_1.png)
![Example 2 of Terminal Widgets](examples/example_2.png)
![Example 3 of Terminal Widgets](examples/example_3.png)

For all examples see [Examples](examples/index.md).

---

### 🧩 **5. Contributing**

Help the project grow: create an issue or pull request!

---

### 📜 **6. License**

See [License](LICENSE)
