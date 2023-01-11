import re
import os
import requests
import json
from pathlib import Path

from weather import data as json_data


def get_weather(city: str, api_id: str):
    """Get weather to city name"""
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_id}&units=metric'
    response = requests.get(url)

    if response.status_code != 200:
        message = f'openweathermap.org returned non-200 code. Actual code is: {response.status_code},' \
                  f' message is: {response.json()["message"]}'
        raise RuntimeError(message)

    return response.json()


def get_weather_icon_url(icon_name: str):
    """Get weather url icon"""
    icon_url = f'http://openweathermap.org/img/w/{icon_name}.png'
    return icon_url


def parse_weather_data(city_weather: dict):
    """Parse weather data"""
    icon_name = city_weather['weather'][0]['icon']
    country_code = city_weather['sys']['country']

    icon_url = get_weather_icon_url(icon_name)
    latitude = city_weather['coord']['lat']
    longitude = city_weather['coord']['lon']
    sky = city_weather['weather'][0]['description']
    temperature = city_weather['main']['temp']
    wind_speed = city_weather['wind']['speed']

    weather_data = {
        'icon_url': icon_url,
        'latitude': latitude,
        'longitude': longitude,
        'sky': sky,
        'temperature': temperature,
        'wind_speed': wind_speed,
        'country': country_code
    }

    return weather_data


def write_city_weather_to_json(city_name: str, city_weather: dict):
    """Write json file with weather data"""
    country_code = city_weather["sys"]["country"]
    city_filename = f'{city_name.lower()}_{country_code.lower()}.json'
    path_to_city_filename = os.path.join(PATH_TO_JSON, city_filename)
    with open(path_to_city_filename, 'w') as file:
        json.dump(city_weather, file, indent=4)


def read_city_weather_from_json():
    """Read all json files from data directory"""
    json_files = [json_file for json_file in os.listdir(PATH_TO_JSON) if '.json' in json_file]
    cities_weather = {}
    for filename in json_files:
        path_to_file = os.path.join(PATH_TO_JSON, filename)
        with open(path_to_file) as weather_file:
            city_weather = json.load(weather_file)
            city_country_code = filename.split('.')[0]
            cities_weather[city_country_code] = city_weather
    return cities_weather


def main(city_name: str, api_id: str):
    """Main controller"""
    try:
        city_weather = get_weather(city_name, api_id)
        # write_city_weather_to_json(city_name, city_weather)
    except RuntimeError as error:
        message = re.findall(r'(?<=message is: ).*', str(error)).pop().capitalize()
        return {'error': message}
    weather_data = parse_weather_data(city_weather)
    return weather_data


PATH_TO_JSON = Path(json_data.__file__).parent

# API_ID = 'cfd36353845324a3d7fee472955de516'
# print(main('madrid', API_ID))
# print(read_city_weather_from_json())
