## 2. Configuration Guide

### 2.1 Changing standard colours and configuration
Edit the `base.yaml` file in `~/.config/twidgets/base.yaml` to change standard colours and configuration.

If you let anything blank, it will fall back to the standard configuration. \
However, you will get warned.

Example:
```yaml
use_standard_terminal_background: False  # Whether to use the standard terminal background, or
# the specified background_color; True / False

background_color:
  r: 31  # Red value
  g: 29  # Green value
  b: 67  # Blue value
  
error_color:
  r: 255  # Red value
  g: 0  # Green value
  b: 0  # Blue value
  
# ...

# Any key (a-z, 0-9) works
# Quotes are necessary, e.g. '7', or 'd'
quit_key: 'q'
reload_key: 'r'
help_key: 'h'

# Whether to disable the help mode of a widget if you highlight a different one; True / False
reset_help_mode_after_escape: True
```

### 2.2 Configure secrets
Edit / create the `secrets.env` file located at `~/.config/twidgets/secrets.env`
to add your API keys and preferred settings.
> ⚠️ Make sure to **NEVER** share your secrets with anybody.

Example (Full example provided in `~/.config/twidgets/secrets.env.example`):
```dotenv
WEATHER_API_KEY='your_api_key'
WEATHER_CITY='Berlin,DE'
WEATHER_UNITS='metric'
NEWS_FEED_URL='https://feeds.bbci.co.uk/news/rss.xml?edition=uk'
NEWS_FEED_NAME='BBC'
```

### 2.3 Adjust widgets and layouts

Each widget has its own `.yaml` file in `~/.config/twidgets/widgets/`

You can adjust name, title, enabled status, position, size, and refresh interval.

Widgets refresh their content internally 15 times per second.
The `interval` setting controls how often the widget fetches new data via its `update` function.
This mainly matters for high-load widgets such as weather or news, where frequent API calls may be expensive.

Example:
```yaml
name: 'clock'  # Will be shown in the mode widget
title: ' ⏲ Clock '  # Will be shown at the top of the widget
enabled: True  # Whether the widget will be shown or not (True / False)
interval: 0  # (0 = None) This widget doesn't have any update function (doesn't require heavy loading / API calls)
height: 5  # Height of Widget
width: 30  # Width of Widget
y: 4  # Position of Widget (y)
x: 87  # Position of Widget (x)
z: 0 # See below for explanation

# Custom attributes of the clock widget
weekday_format: '%A'  # day of the week
date_format: '%d.%m.%Y'  # us: '%m.%d.%Y', international: '%Y-%m-%d'
time_format: '%H:%M:%S'  # time
```

### 2.4 z-index

Each widget has a `z` attribute. This can be any integer. If two or more widgets overlay, the widget with the highest
z-index will be shown on top, and all other widgets will only be shown partially. If the `z` attributes are equal,
the widget that got loaded last will appear on top. The order of widget loading order is based
on the implementation of `pathlib.Path.iterdir()` on your platform. (Usually ordered by widget file name)
