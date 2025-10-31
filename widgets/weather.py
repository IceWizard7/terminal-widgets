import requests
import typing
from .base import Widget, Config, draw_widget, add_widget_content
from utils.config_loader import get_secret


def update(_widget: Widget) -> list[str]:
    api_key: str = get_secret('WEATHER_API_KEY')
    city: str = get_secret('WEATHER_CITY')
    units: str = get_secret('WEATHER_UNIT')
    url: str = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units={units}'
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
    except Exception:
        return [
            'Weather data not available.',
            '',
            'Check your internet',
            'connection, API key',
            'and configuration.'
        ]

    if data.get('cod') != 200:
        return [
            'Weather data not available.',
            '',
            'Check your internet',
            'connection, API key',
            'and configuration.'
        ]

    main_data = data['main']
    weather = data['weather'][0]
    wind = data['wind']

    if units == 'metric':
        return [
            f'City: {data["name"]}, {data["sys"]["country"]}',
            f'Temperature: {main_data["temp"]}°C',
            f'Condition: {weather["description"]}',
            f'Humidity: {main_data["humidity"]}%',
            f'Wind Speed: {wind["speed"]} m/s',
            f'',
            f'Unit: {units}'
        ]

    elif units == 'imperial':
        return [
            f'City: {data["name"]}, {data["sys"]["country"]}',
            f'Temperature: {main_data["temp"]}°F',
            f'Condition: {weather["description"]}',
            f'Humidity: {main_data["humidity"]}%',
            f'Wind Speed: {wind["speed"]} mph',
            f'',
            f'Unit: {units}'
        ]

    elif units == 'standard':
        return [
            f'City: {data["name"]}, {data["sys"]["country"]}',
            f'Temperature: {main_data["temp"]}K',
            f'Condition: {weather["description"]}',
            f'Humidity: {main_data["humidity"]}%',
            f'Wind Speed: {wind["speed"]} m/s',
            f'',
            f'Unit: {units}'
        ]

    else:
        return [
            f'Unit is not supported.',
            f'Please enter "metric",',
            f'"standard" or "imperial".',
        ]


def draw(widget: Widget, info: list[str]) -> None:
    draw_widget(widget)
    add_widget_content(widget, info)


def build(stdscr: typing.Any, config: Config) -> Widget:
    return Widget(
        config.name, config.title, config, draw, config.interval, config.dimensions, stdscr, update
    )
