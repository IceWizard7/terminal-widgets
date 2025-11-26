import requests
from twidgets.core.base import (
    Widget,
    Config,
    CursesWindowType,
    draw_widget,
    add_widget_content,
    ConfigLoader,
    UIState,
    BaseConfig
)


def update(_widget: Widget, _config_loader: ConfigLoader) -> list[str]:
    api_key: str | None = _config_loader.get_secret('WEATHER_API_KEY')
    city: str | None = _config_loader.get_secret('WEATHER_CITY')
    units: str | None = _config_loader.get_secret('WEATHER_UNIT')

    if api_key is None or city is None or units is None:
        return [
            'Weather data not available.',
            '',
            'Check your API key',
            'and configuration.'
        ]

    url: str = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units={units}'
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
    except requests.exceptions.RequestException:
        return [
            'Weather data not available.',
            '',
            'Check your internet',
            'connection.'
        ]

    if data.get('cod') != 200:  # Anything else (unexpected)
        return [
            'Weather data not available.',
            f'Error: ({data.get("cod")})',
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


def draw(widget: Widget, ui_state: UIState, base_config: BaseConfig, info: list[str]) -> None:
    draw_widget(widget, ui_state, base_config)
    add_widget_content(widget, info)


def draw_help(widget: Widget, ui_state: UIState, base_config: BaseConfig) -> None:
    draw_widget(widget, ui_state, base_config)

    add_widget_content(
        widget,
        [
            f'Help page ({widget.name} widget)',
            '',
            'Displays current weather.'
        ]
    )


def build(stdscr: CursesWindowType, config: Config) -> Widget:
    return Widget(
        config.name, config.title, config, draw, config.interval, config.dimensions, stdscr,
        update_func=update,
        mouse_click_func=None,
        keyboard_func=None,
        init_func=None,
        help_func=draw_help
    )
