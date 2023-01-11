import os
import unittest
from unittest.mock import patch, MagicMock
from flask import url_for
from flask_login import login_user, logout_user
from random import choice, sample
from pathlib import Path

import weather
from app import create_app
from generate_data.db.create_test_database import create_db, USERS, PROFILES, ROLES
from app.auth.models import Role, User
from app.weather.models import Country, UserCity, City
from weather.getting_weather import main as main_weather, parse_weather_data, read_city_weather_from_json
from weather.fill_country_db import main as main_fill_weather, FILENAME as countries_json


PATH_TO_COUNTRIES_JSON = os.path.join(Path(weather.__file__).parent, countries_json)


class UsersTestCase(unittest.TestCase):
    """Test users"""
    ctx = None
    roles = None
    profiles = None
    users = None
    db = None
    app = None

    @classmethod
    def setUpClass(cls):
        """Before all tests"""
        cls.app = create_app('testing')
        cls.app.config['WTF_CSRF_ENABLED'] = False
        cls.api_key = cls.app.config['WEATHER_API_KEY']
        cls.db = cls.app.config['db']
        cls.users = USERS
        cls.profiles = PROFILES
        cls.roles = ROLES
        cls.cities = read_city_weather_from_json()
        create_db(cls.db, cls.users, cls.profiles, cls.roles)
        main_fill_weather(PATH_TO_COUNTRIES_JSON, cls.db)

        cls.ctx = cls.app.test_request_context()
        cls.ctx.push()
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        """After each test"""
        cls.ctx.pop()

    @patch('weather.getting_weather.requests')
    def test_1_weather_index_page_with_city(self,  requests_mock):
        """Get city weather info from weather index page"""
        city_name = 'tokyo'
        city_tokyo_json = self.cities['tokyo_jp']
        prepared_tokyo = parse_weather_data(city_tokyo_json)
        country = Country.select().where(Country.code == prepared_tokyo['country']).first()
        prepared_tokyo['country'] = country.name

        request_response_mock = MagicMock()
        request_response_mock.status_code = 200
        request_response_mock.json.return_value = city_tokyo_json
        requests_mock.get.return_value = request_response_mock
        response = self.client.post(
            url_for('weather.index'),
            data={
                'city_name': city_name,
                'submit': 'Show'
            },
            follow_redirects=True
        )
        code = response.status_code
        data = response.get_data(as_text=True)
        self.assertEqual(code, 200)
        for field, value in prepared_tokyo.items():
            self.assertIn(str(value), data)

    def test_2_weather_index_page_with_wrong_city_name(self):
        """Get city weather info from weather index page with wrong city name"""
        wrong_city_name = 'wrong_city_name'
        response = self.client.post(
            url_for('weather.index'),
            data={
                'city_name': wrong_city_name,
                'submit': 'Show'
            },
            follow_redirects=True
        )
        code = response.status_code
        data = response.get_data(as_text=True)
        self.assertEqual(code, 200)
        self.assertIn('City not found', data)

    def test_3_weather_add_city_to_user(self):
        """Add city weather into database"""
        random_user = choice(list(User.select()))

        login_user(random_user)
        random_cities = sample(list(self.cities.keys()), 3)
        for city_country_code in random_cities:
            city_name, country_code = city_country_code.split('_')
            country_id = Country.select().where(Country.code == country_code.upper()).first()
            response = self.client.post(
                url_for('weather.add_city'),
                data={
                    'city': city_name,
                    'country': country_id
                },
                follow_redirects=True
            )
            code = response.status_code
            data = response.get_data(as_text=True)
            self.assertEqual(code, 200)
            self.assertIn(f'City: {city_name.capitalize()} added to list of user {random_user.name}', data)
            self.assertEqual(response.request.path, url_for('weather.index'))
        logout_user()

    def test_4_weather_add_already_exist_city_to_user(self):
        """Add city weather into database already exist"""
        users_cities = UserCity.select()
        random_user_city = choice(list(users_cities))
        user = User.select().where(User.id == random_user_city.user_id).first()
        city = City.select().where(City.id == random_user_city.city_id).first()

        login_user(user)
        response = self.client.post(
            url_for('weather.add_city'),
            data={
                'city': city.name,
                'country': city.country
            },
            follow_redirects=True
        )
        code = response.status_code
        data = response.get_data(as_text=True)
        self.assertEqual(code, 200)
        self.assertIn(f'City {city.name} already in list of user {user.name}', data)
        self.assertEqual(response.request.path, url_for('main.index'))
        logout_user()

    def test_5_weather_delete_cities_from_user(self):
        """Delete cities from user"""
        users_cities = UserCity.select()
        random_user_cities = sample(list(users_cities), k=2)
        user = User.select().where(User.id == random_user_cities[0].user_id).first()
        cities_idx = [user_city.city_id for user_city in random_user_cities]
        cities_names = []
        for city_id in cities_idx:
            city = City.select().where(City.id == city_id).first()
            cities_names.append(city.name)

        login_user(user)
        response = self.client.post(
            url_for('weather.delete_cities'),
            data={
                'selectors': cities_idx,
            },
            follow_redirects=True
        )
        code = response.status_code
        data = response.get_data(as_text=True)
        self.assertEqual(code, 200)
        self.assertIn(f'Deleted: {", ".join(reversed(cities_names))}', data)
        self.assertEqual(response.request.path, url_for('weather.show_city'))
        logout_user()
