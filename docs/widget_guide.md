## 3. Adding new widgets

### 3.1 Create `config/widgets/custom.yaml`

Configure `name`, `title`, `enable`, `interval`, `height`, `width`, `y` and `x`
For simple widgets, set `interval = 0` (see [Docs](configuration_guide.md))

(Make sure to name the `.yaml` and `.py` the same way)

### 3.2 Create `widgets/custom.py`

#### 3.2.1 Imports

Import:
```python
from .base import Widget, Config, draw_widget, add_widget_content
```

Also import if needed:
```python
from .config import PRIMARY_COLOR_NUMBER, SECONDARY_COLOR_NUMBER
import typing
```

#### 3.2.2 Simple widgets
Then define a `draw` function:

```python
def draw(widget: Widget) -> None:
```

Start the function with:
```python
draw_widget(widget)
```

#### 3.2.3 Add widget content

Add content with:
```python
info: list[str] = ['line1', 'line2', 'line3', 'line4', 'line5']
add_widget_content(widget, info)
```

Advanced: For precise text positioning or colors a the terminal widget

```python
row: int = 3
col: int = 2
text: str = 'Example text'

widget.win.addstr(row, col, text, curses.color_pair(PRIMARY_COLOR_NUMBER) | curses.A_BOLD)
```

#### 3.2.4 Widgets with heavy loading

If your widget requires heavy loading, API calls or the data doesn't need to be reloaded every frame, add: 

```python
def update(_widget: Widget) -> dict[str, typing.Any]:
```

And modify the `draw` function to accept `info`
(`info` will be passed automatically from the `update` function by the scheduler):

```python
def draw(widget: Widget, info: dict[str, typing.Any]) -> None:
```

You can adapt the time, when the `update` function will be called again (reload) by changing
`interval` in `config/widgets/custom.yaml`

#### 3.2.5 Using secrets

Import:
```python
from utils.config_loader import get_secret
```

To get secrets, use:
```python
data: typing.Any = get_secret(key)
```

Example:
```python
api_key: str = get_secret('WEATHER_API_KEY')
```

#### 3.2.6 Building widget

Simple widgets:

```python
def build(stdscr: typing.Any, config: Config) -> Widget:
    return Widget(
        config.name, config.title, config, draw, config.interval, config.dimensions, stdscr
    )
```

Widgets with heavy loading:

```python
def build(stdscr: typing.Any, config: Config) -> Widget:
    return Widget(
        config.name, config.title, config, draw, config.interval, config.dimensions, stdscr, update
    )
```

### 3.3 Add it to your widget layout
In `main.py`, you will see three markers:

`# Add more widgets here (1)` — Place your widget import statements here

```python
import widgets.custom as custom
```

`# Add more widgets here (2)` — Build your widget instances here

```python
custom_widget: base.Widget = custom.build(stdscr, load_widget_config('custom'))
```

`# Add more widgets here (3)` — Add the widget instance to the dashboard widget mapping dictionary

```python
'custom': custom_widget
```

> These markers are **placeholders** to help you integrate new widgets without breaking existing code.
