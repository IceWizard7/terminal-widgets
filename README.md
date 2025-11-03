## Terminal Widgets

This tool lets you design and run dynamic, customizable dashboards directly
inside your terminal, combining modular widgets, real-time data updates, and flexible layout management for a highly
interactive CLI experience.

---
### 1. Get started
1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the dashboard: `python main.py`

> ⚠️ Make sure you are using Python Version 3.14+


For full documentation see [Setup Guide](docs/setup_guide.md)

---

### 2. Configuration

2.1 Configure your secrets in: `config/secrets.env`

Example:
```dotenv
WEATHER_API_KEY='your_api_key'
WEATHER_CITY='Berlin,DE'
WEATHER_UNITS='metric'
NEWS_FEED_URL='https://feeds.bbci.co.uk/news/rss.xml?edition=uk'
NEWS_FEED_NAME='BCC'
```

2.2 Adjust widgets and layouts in: `config/widgets/*.yaml`

Example:
```yaml
name: 'clock'
title: ' ⏲ Clock'
enable: True
interval: 1
height: 5
width: 30
y: 4
x: 87
```

For full documentation see [Configuration Guide](docs/configuration_guide.md)

---

### 3. Adding new widgets
See [Widget Guide](docs/widget_guide.md)

---

### 4. License

See [License](LICENSE)
