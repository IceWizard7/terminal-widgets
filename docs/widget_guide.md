## 3. Adding new widgets

### 3.1. ⚙️ Define Configuration (`.yaml`)

Create the configuration file at `~/.config/twidgets/widgets/custom.yaml`

Configure `name`, `title`, `enabled`, `interval`, `height`, `width`, `y` and `x`
For simple widgets, set `interval = 0` (see [Configuration Guide](configuration_guide.md))

### 3.2. 🐍 Write the Widget Logic (`.py`)
> **Note:** Make sure to name the `.yaml` and `.py` files the same way (excluding suffixes)

Create the widget's Python file at `~/.config/twidgets/py_widgets/custom_widget.py`

#### 3.2.1 Imports

Import:
```python
from twidgets.core.base import Widget, draw_widget, add_widget_content, Config, UIState, BaseConfig, CursesWindowType
```

#### 3.2.2 Simple widgets
Then define a `draw` function:

```python
def draw(widget: Widget, ui_state: UIState, base_config: BaseConfig) -> None:
```

Start the function with:
```python
draw_widget(widget, ui_state, base_config)
```

which will initialize the widget title and make it loadable, highlightable, etc.

#### 3.2.3 Add widget content

Add content with:
```python
content: list[str] = ['line1', 'line2', 'line3', 'line4', 'line5']
add_widget_content(widget, content)
```

Advanced: For precise text positioning or colors in a terminal widget

```python
from twidgets.core.base import (
    safe_addstr,
    convert_color_number_to_curses_pair,
    CursesBold
)  # Adding content with precise positioning / colors

row: int = 3
col: int = 2
text: str = 'Example text'

safe_addstr(
    widget, row, col, text,
    convert_color_number_to_curses_pair(base_config.PRIMARY_PAIR_NUMBER) | CursesBold)
```

#### 3.2.4 Widgets with heavy loading

If your widget requires heavy loading, API calls or the data doesn't need to be reloaded every frame, add: 

```python
from twidgets.core.base import ConfigLoader
import typing

def update(_widget: Widget, _config_loader: ConfigLoader) -> typing.Any:
```

And modify the `draw` function to accept `info`
(`info` will be passed automatically from the `update` function by the scheduler):

```python
def draw(widget: Widget, ui_state: UIState, base_config: BaseConfig, info: typing.Any) -> None:
```

You can adapt the time, when the `update` function will be called again (reloading the data) by changing
`interval` in `~/.config/twidgets/widgets/custom.yaml`

#### 3.2.5 Custom mouse, keyboard actions & initialize functions

Mouse actions example:

```python
def mouse_click_action(custom_widget: Widget, _mx: int, _my: int, _b_state: int, ui_state: UIState) -> None:
    if ui_state.highlighted != custom_widget:
        custom_widget.draw_data['selected_line'] = None
        return
        
    # Click relative to widget border
    local_y: int = _my - custom_widget.dimensions.y - 1  # -1 for top border
```

This function will get called whenever a mouse click happens, so you can use it to for example make clickable buttons.

> Note that the widget border color will automatically be updated on every mouse click.

Keyboard actions example:

```python
from twidgets.core.base import prompt_user_input, CursesKeys

def keyboard_press_action(custom_widget: Widget, key: typing.Any, ui_state: UIState, base_config: BaseConfig) -> None:
    if key in (CursesKeys.ENTER, 10, 13):  # Enter key + enter key codes
        confirm = prompt_user_input(custom_widget, 'Confirm deletion (y): ')
        if confirm.lower().strip() in ['y']:
            some_func(custom_widget, ...)
```

This function will get called whenever a key is pressed.

Initialize function example:

```python
def init(widget: Widget, _ui_state: UIState, _base_config: BaseConfig) -> None:
    load_todos(widget)
```

This function will get called initially when `twidgets` is starting, or when the user manually reloads.

#### 3.2.6 Using secrets

Import:
```python
from twidgets.core.base import ConfigLoader  # Loading secrets (secrets.env)
import typing
```

To get secrets, use:
```python
data: typing.Any = _config_loader.get_secret(key)
```

Example:
```python
api_key: str = _config_loader.get_secret('WEATHER_API_KEY')
```

#### 3.2.7 Adding custom data to config

Example:

Python:
```python
custom_attribute: typing.Any = widget.config.custom_attribute
```

YAML:
```yaml
custom_attribute: 'this is a custom attribute!'
```

> Note that this will not be checked by the ConfigScanner.
It only checks `base.yaml` for integrity, as well as "name",
"title", "enabled", "interval", "height", "width", "y" and "x" for every widget. \
To detect if these attributes are missing, see the next section.

#### 3.2.7.1 Config specific Errors

Example:

```python
from twidgets.core.base import (
    ConfigSpecificException,
    LogMessages,
    LogMessage,
    LogLevels
)

raise ConfigSpecificException(LogMessages([LogMessage(
    f'Configuration for some_value is missing / incorrect ("{widget.name}" widget)',
    LogLevels.ERROR.key)]))
```

With this you can add custom error messages for all users to your widget.

#### 3.2.8 Building widget

```python
def build(stdscr: CursesWindowType, config: Config) -> Widget:
    return Widget(
        config.name, config.title, config, draw, config.interval, config.dimensions, stdscr,
        update_func=None,  # update_func=update
        mouse_click_func=None,  # mouse_click_func=mouse_click_action
        keyboard_func=None,  # keyboard_func=keyboard_press_action
        init_func=None  # init_func=init
    )
```

### 3.3 Adding your Widget to the Layout
While integration is automatic, your files must still follow a specific naming convention for the system
to recognize them as a valid widget:

* **YAML Configuration File (`~/.config/twidgets/widgets/`):**
    * Must end with: **`.yaml`**
    * *Examples:*
    * `hello123.yaml`, `mycoolwidget.yaml`, `weather.yaml`

* **Python Widget File (`~/.config/twidgets/py_widgets/`):**
    * Must end with: **`_widget.py`**
    * *Examples:*
    * `hello123_widget.py`, `mycoolwidget_widget.py`, `weather_widget.py`
