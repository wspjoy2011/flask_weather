import os
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict

import web
from app.weather.models import Country, City, UserCity
from weather.country_codes import read_codes_data_from_json, FILENAME


def get_path_to_db():
    """Get path to database"""
    path_to_base_dir = Path(web.__file__).parent
    path_to_env_file = os.path.join(path_to_base_dir, '.flaskenv')
    load_dotenv(path_to_env_file)
    db_name = os.environ.get('DATABASE')
    path_to_db = os.path.join(path_to_base_dir, db_name)
    return path_to_db


def convert_data_from_json_to_db(countries: List[Dict[str, str]], db):
    """Convert data from json file to db"""
    db.create_tables([Country, City, UserCity])
    Country.delete().execute()

    for country in countries:
        country_instance = Country(
            code=country['code'],
            name=country['name'],
            flag=f'https://www.countryflagicons.com/FLAT/32/{country["code"]}.png'
        )
        country_instance.save()


def main(filename: str, db):
    """Main controller"""
    countries = read_codes_data_from_json(filename)
    convert_data_from_json_to_db(countries, db)


# main(FILENAME)
