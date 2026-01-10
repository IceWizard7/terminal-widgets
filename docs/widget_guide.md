## 3. Adding new widgets

### 3.1 Define Configuration (`.yaml`)

Create the configuration file at `~/.config/twidgets/widgets/custom.yaml`

> **Naming schemes are described [here](#33-adding-widgets-to-your-layout).** \
> You can create an infinite number of widgets, the file names `custom.yaml` and `custom_widget.py` are just examples.

Configure `name`, `title`, `enabled`, `interval`, `height`, `width`, `y` and `x`.
For simple widgets, set `interval = 0` (see [Configuration Guide](configuration_guide.md))

### 3.2 Write the Widget Logic (`.py`)
Create the Python file for the widget at `~/.config/twidgets/py_widgets/custom_widget.py`

> **Naming schemes are described [here](#33-adding-widgets-to-your-layout).** \
> You can create an infinite number of widgets, the file names `custom.yaml` and `custom_widget.py` are just examples.

> Note that the built-in widgets are located in your python installation, at
> `(python_installation_path)/lib/(python-version)/site-packages/twidgets/widgets/*_widget.py`

#### 3.2.1 Imports

Import:
```python
from twidgets.core.base import Widget, WidgetContainer, Config, CursesWindowType
```

#### 3.2.2 Simple widgets
Then define a `draw` function:

```python
def draw(widget: Widget, widget_container: WidgetContainer) -> None:
```

Start the function with:
```python
draw_widget(widget, widget_container)
```

which will initialise the widget title and make it loadable and highlightable.

#### 3.2.3 Add widget content

Add content with:
```python
content: list[str] = ['line1', 'line2', 'line3', 'line4', 'line5']
widget.add_widget_content(content)
```

> Advanced: For precise text positioning or colours in a terminal widget use `safe_addstr`

```python
from twidgets.core.base import CursesColors

y: int = 3
x: int = 2
text: str = 'Example text'

widget.safe_addstr(y, x, text, [widget_container.base_config.PRIMARY_PAIR_NUMBER], [CursesColors.BOLD])
```

#### 3.2.4 Widgets with heavy loading

If your widget requires heavy loading, API calls or the data does not need to be reloaded every frame,
move the update logic into its own function:  

Import if needed:
```python
import typing
```

```python
def update(widget: Widget, widget_container: WidgetContainer) -> typing.Any:
```

> Note that `widget` and `widget_container` will **always** be passed to your update function,
> so make sure to keep these arguments, even if they are unused.

Additionally, modify the `draw` function to accept `info`.
(`info` will be passed automatically from the `update` function by the scheduler):

```python
def draw(widget: Widget, widget_container: WidgetContainer, info: typing.Any) -> None:
```

Example:
```python
def draw(widget: Widget, widget_container: WidgetContainer, info: list[str]) -> None:
    draw_widget(widget, widget_container)
    widget.add_widget_content(info)
```

You can adapt the time, when the `update` function will be called again (reloading the data) by changing
`interval` in `~/.config/twidgets/widgets/custom.yaml`

> To integrate this, see [building widget](#328-building-widget).

#### 3.2.5 Custom mouse, keyboard, initialise & help functions

#### 3.2.5.1 Mouse actions

Example:

```python
def mouse_click_action(widget: Widget, mx: int, my: int, b_state: int, widget_container: WidgetContainer) -> None:
    # Click relative to widget border
    local_y: int = my - widget.dimensions.y - 1  # -1 for top border
```

This function will get called whenever a mouse click happens (in your widget), so you can use it, for example, to make
clickable buttons.

> Note that the widget border colour will automatically be updated on every mouse click,
> without utilising your `mouse_click_action` function.

#### 3.2.5.2 Keyboard actions

Example:

```python
from twidgets.core.base import CursesKeys

def keyboard_press_action(widget: Widget, key: int, widget_container: WidgetContainer) -> None:
    if key in (CursesKeys.ENTER, 10, 13):  # Enter key + enter key codes
        confirm = widget.prompt_user_input('Confirm deletion (y): ')
        if confirm.lower().strip() in ['y']:
            some_func(widget, ...)
```

This function will get called whenever a key is pressed while your widget is highlighted.

#### 3.2.5.3 Initialise functions

Example:

```python
def init(widget: Widget, widget_container: WidgetContainer) -> None:
    load_todos(widget)  # Custom initialising logic, eg. loading todos
```

This function will get called initially when `twidgets` starts or when the user manually reloads it.

#### 3.2.5.4 Help functions

Example:

```python
def draw_help(widget: Widget, widget_container: WidgetContainer) -> None:
    draw_widget(widget, widget_container)

    widget.add_widget_content(
        [
            f'Help page ({widget.name} widget)',
            '',
            'Displays information about something.'
        ]
    )
```

This function will get called whenever the help key (default: `h`) is pressed for your widget.

#### 3.2.5.5 Integrating custom functions

> To integrate any custom function, see [building widget](#328-building-widget).

#### 3.2.6 Using secrets

Import if needed:
```python
import typing
```

Inside your update function:
```python
def update(widget: Widget, widget_container: WidgetContainer) -> typing.Any:
```

You can then use:
```python
data: typing.Any = widget_container.config_loader.get_secret(key)
```
to retrieve secrets.

Example:
```python
def update(widget: Widget, widget_container: WidgetContainer) -> typing.Any:
    api_key: str = widget_container.config_loader.get_secret('WEATHER_API_KEY')
```
TODO: Remove all occurrences of vars starting with _
TODO: Remove BaseConfig & UIState

> Note that this can only be used in the `update` function, so secrets do not get reloaded every frame.

#### 3.2.7 Adding custom data to your widget configuration

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
It only checks `base.yaml` for integrity, as well as `name`,
`title`, `enabled`, `interval`, `height`, `width`, `y` and `x` for every widget.
> 
> To detect if these attributes are missing, see the next section.

#### 3.2.7.1 Config specific Errors

Example:

```python
from twidgets.core.base import (
    ConfigSpecificException,
    LogMessages,
    LogMessage,
    LogLevels
)
def draw(widget: Widget, widget_container: WidgetContainer) -> None:
    if not widget.config.some_value:  # Will be None if no attribute is found
        raise ConfigSpecificException(LogMessages([LogMessage(
            f'Configuration for some_value is missing / incorrect ("{widget.name}" widget)',
            LogLevels.ERROR.key)]))
```

With this you can add custom error messages to your widget, for example if certain attributes are missing.

#### 3.2.8 Building widget

If your widget has an `update`, `mouse_click_action`, `keyboard_press_action`, `init` or a `draw_help` function,
specify them here. (See the comments for examples)

```python
def build(stdscr: CursesWindowType, config: Config) -> Widget:
    return Widget(
        config.name, config.title, config, draw, config.interval, config.dimensions, stdscr,  # exactly this order!
        update_func=None,  # update_func=update
        mouse_click_func=None,  # mouse_click_func=mouse_click_action
        keyboard_func=None,  # keyboard_func=keyboard_press_action
        init_func=None,  # init_func=init
        help_func=None  # help_func=draw_help
    )
```

### 3.3 Adding widgets to your layout
While integration is automatic, your files must still follow a specific naming convention for the system
to recognise them as a valid widget:

- **YAML Configuration File** (`~/.config/twidgets/widgets/`):
    * Must end with: **`.yaml`**
    * *Examples:*
    * `hello123.yaml`, `mycoolwidget.yaml`, `weather.yaml`

- **Python Widget File** (`~/.config/twidgets/py_widgets/`):
    * Must end with: **`_widget.py`**
    * *Examples:*
    * `hello123_widget.py`, `mycoolwidget_widget.py`, `weather_widget.py`

> **Note:** Make sure to name the `.yaml` and `.py` files the same way (excluding suffixes)
