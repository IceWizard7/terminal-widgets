## 2. Configuration Guide

### 2.1 Configure secrets
Edit the `.env` file located at `config/secrets.env` to add your API keys and preferred settings.
> ⚠️ Make sure to NEVER share your secrets with anybody.

Example:
```dotenv
WEATHER_API_KEY='your_api_key'
WEATHER_CITY='Berlin,DE'
WEATHER_UNITS='metric'
NEWS_FEED_URL='https://feeds.bbci.co.uk/news/rss.xml?edition=uk'
NEWS_FEED_NAME='BBC'
```

### 2.2 Adjust widgets and layouts

Each widget has its own .yaml file under `config/widgets/`

You can adjust name, title, enabled status, position, size, and refresh interval

Widgets refresh their display internally 15 times per second.
The `interval` setting controls how often the widget fetches new data via its `update` function.
This mainly matters for high-load widgets such as Weather or News, where frequent API calls may be expensive.

> Most widgets don’t need a high interval. Heavy-load widgets like Weather or News benefit from controlling this.

Example:
```yaml
name: 'clock'  # Will be shown in the mode box
title: ' ⏲ Clock '  # Will be shown at the top of the widget
enable: True  # Whether the widget will be shown or not (True / False)
interval: 0  # (0 = None) This widget doesn't have any update function (doesn't require heavy loading / API calls)
height: 5  # Height of Widget
width: 30  # Width of Widget
y: 4  # Position of Widget (y)
x: 87  # Position of Widget (x)
```
