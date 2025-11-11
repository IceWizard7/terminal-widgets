<br/>
<div align="center">
  <h3 align="center">🖥 Terminal Widgets</h3>

  <p align="center">
    This tool lets you design and run dynamic, customizable dashboards directly inside your terminal.
    It combines modular widgets, real-time data updates, and flexible layout management for a highly
    interactive CLI experience.
    <br />
    <br />
    <a href="#-1-getting-started">Getting started</a> •
    <a href="#-2-configuration">Configuration</a> •
    <a href="#-3-adding-new-widgets">Adding new widgets</a> •
    <a href="#-4-license">License</a>
  </p>
</div>

---

### 🚀 **1. Getting started**

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the dashboard: `python main.py`

> ⚠️ Make sure you are using Python Version 3.14+


For full documentation see [Setup Guide](docs/setup_guide.md)

---

### ✨ **2. Configuration**

2.1 Changing standard colors and configuration in `config/base.yaml`

If you remove anything or let anything blank, it will just fall back to the standard configuration. \
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

2.2 Configure your secrets in: `config/secrets.env`

Example:
```dotenv
WEATHER_API_KEY='your_api_key'
WEATHER_CITY='Berlin,DE'
WEATHER_UNITS='metric'
NEWS_FEED_URL='https://feeds.bbci.co.uk/news/rss.xml?edition=uk'
NEWS_FEED_NAME='BCC'
```

2.3 Adjust widgets and layouts in: `config/widgets/*.yaml`

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
```

For full documentation see [Configuration Guide](docs/configuration_guide.md)

---

### ⭐ **3. Adding new widgets**
See [Widget Guide](docs/widget_guide.md)

---

### 📜 **4. License**

See [License](LICENSE)
