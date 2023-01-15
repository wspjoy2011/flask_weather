import os
import unittest
from unittest.mock import patch, MagicMock
from flask import url_for
from flask_login import login_user, logout_user
from random import choice, sample
from pathlib import Path
from collections import Counter

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

        cls.user = choice(list(User.select()))
        cls.country_codes = ('es', 'us')

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
        cities_names.sort()
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
        self.assertIn(f'Deleted: {", ".join(cities_names)}', data)
        self.assertEqual(response.request.path, url_for('weather.show_city'))
        logout_user()

    def test_6_weather_delete_cities_empty_request(self):
        """Delete cities from user with empty request"""
        user = User.select().first()
        login_user(user)
        response = self.client.post(
            url_for('weather.delete_cities'),
            data={
                'selectors': [],
            },
            follow_redirects=True
        )
        code = response.status_code
        data = response.get_data(as_text=True)
        self.assertEqual(code, 200)
        self.assertIn('Nothing to delete', data)
        self.assertEqual(response.request.path, url_for('weather.show_city'))
        logout_user()

    def test_7_weather_add_cities_to_user_and_check_show_cities_for_user(self):
        """Add to random user a couple cities and check it in show city"""
        cities = [city for city in self.cities if city.split('_')[-1] in self.country_codes]
        UserCity.delete().execute()
        login_user(self.user)
        for city_country_code in cities:
            city_name, country_code = city_country_code.split('_')
            country = Country.select().where(Country.code == country_code.upper()).first()
            self.client.post(
                url_for('weather.add_city'),
                data={
                    'city': city_name,
                    'country': country
                },
                follow_redirects=True
            )
        response = self.client.get((url_for('weather.show_city')))
        code = response.status_code
        data = response.get_data(as_text=True)

        self.assertEqual(code, 200)
        self.assertEqual(response.request.path, url_for('weather.show_city'))
        self.assertEqual(len(self.user.city_user), len(cities))
        cities = [city.split('_')[0].capitalize() for city in cities]

        for counter, user_city_id in enumerate(self.user.city_user, 1):
            city = City.select().where(City.id == user_city_id.city).first()
            self.assertIn(city.name, cities)
            cities.pop(cities.index(city.name))
            check_data = f'<td>\n                    ' \
                         f'<input type="checkbox" name="selectors" class="checkbox" value="{city.id}"/>\n                ' \
                         f'</td>\n                ' \
                         f'<td>{counter}</td>\n                ' \
                         f'<td>\n                    ' \
                         f'<a href="{url_for("weather.show_city_detail", city_name=city.name)}">\n                        ' \
                         f'{city.name}\n                    ' \
                         f'</a>\n                ' \
                         f'</td>\n                ' \
                         f'<td>\n                    ' \
                         f'<a href="{url_for("weather.show_city", country_name=city.country.name)}">\n                        ' \
                         f'{city.country.name}\n'
            self.assertIn(check_data, data)
        self.assertEqual(len(cities), 0)
        logout_user()

    def test_8_weather_show_city_for_user_by_country(self):
        """Check country parameter for user in show city"""
        country_code = choice(self.country_codes)
        cities = [city.split('_')[0].capitalize() for city in self.cities if city.split('_')[-1] == country_code]
        country = Country.select().where(Country.code == country_code.upper()).first()

        login_user(self.user)
        response = self.client.get(url_for('weather.show_city', country_name=country.name))
        code = response.status_code
        data = response.get_data(as_text=True)
        country_cities = Country.select().where(Country.code == country_code.upper()).first()
        user_cities = [city for city in sorted(country_cities.city, key=lambda city: city.name) if city.name in cities]
        self.assertEqual(len(cities), len(user_cities))
        self.assertEqual(code, 200)
        for counter, city in enumerate(user_cities, 1):
            check_data = f'<td>\n                    ' \
                         f'<input type="checkbox" name="selectors" class="checkbox" value="{city.id}"/>\n                ' \
                         f'</td>\n                ' \
                         f'<td>{counter}</td>\n                ' \
                         f'<td>\n                    ' \
                         f'<a href="{url_for("weather.show_city_detail", city_name=city.name)}">\n                        ' \
                         f'{city.name}\n                    ' \
                         f'</a>\n                ' \
                         f'</td>\n                ' \
                         f'<td>\n                    ' \
                         f'<a href="{url_for("weather.show_city", country_name=country.name)}">\n                        ' \
                         f'{city.country.name}\n                    ' \
                         f'</a>\n                ' \
                         f'</td>\n'
            self.assertIn(check_data, data)
        logout_user()

    @patch('weather.getting_weather.requests')
    def test_9_weather_show_city_detail(self, requests_mock):
        """Show city detail in user cities"""
        city = City.select().where(City.id == choice(self.user.city_user).city_id).first()
        city_json = self.cities[f'{city.name.lower()}_{city.country.code.lower()}']

        prepared_city = parse_weather_data(city_json)
        prepared_city['country'] = city.country.name

        request_response_mock = MagicMock()
        request_response_mock.status_code = 200
        request_response_mock.json.return_value = city_json
        requests_mock.get.return_value = request_response_mock

        login_user(self.user)
        response = self.client.get(url_for("weather.show_city_detail", city_name=city.name))
        code = response.status_code
        data = response.get_data(as_text=True)
        self.assertEqual(code, 200)
        self.assertIn(f'<h3>Weather info about city {city.name}, {city.country.name}</h3>', data)
        for field, value in prepared_city.items():
            self.assertIn(str(value), data)
        logout_user()

    def test_10_weather_show_city_detail_form_another_user(self):
        """Show city detail from another user"""
        current_user = choice(User.select())
        another_user = choice(User.select().where(User.id != current_user.id))
        city_another_user, country_code = choice([city.split('_') for city in self.cities])
        country_another_user = Country.select().where(Country.code == country_code.upper()).first()

        login_user(another_user)
        self.client.post(
            url_for('weather.add_city'),
            data={
                'city': city_another_user,
                'country': country_another_user
            },
            follow_redirects=True
        )
        logout_user()

        login_user(current_user)
        response = self.client.get(
            url_for("weather.show_city_detail", city_name=city_another_user[0]),
            follow_redirects=True
        )
        code = response.status_code
        data = response.get_data(as_text=True)
        check_answer_404 = '404 Not Found: The requested URL was not found on the server. ' \
                           'If you entered the URL manually please check your spelling and try again.'
        self.assertEqual(code, 404)
        self.assertIn(check_answer_404, data)
        logout_user()

    @patch('weather.getting_weather.requests')
    def test_11_weather_show_city_detail_with_error(self, requests_mock):
        """Test weather show city detail with error in json response"""
        user = choice(User.select())
        city_name, country_code = choice([city.split('_') for city in self.cities])
        country = Country.select().where(Country.code == country_code.upper()).first()

        login_user(user)
        self.client.post(
            url_for('weather.add_city'),
            data={
                'city': city_name,
                'country': country
            },
            follow_redirects=True
        )
        error_json = {'message': 'City not found'}

        request_response_mock = MagicMock()
        request_response_mock.status_code = 404
        request_response_mock.json.return_value = error_json
        requests_mock.get.return_value = request_response_mock

        response = self.client.get(
            url_for("weather.show_city_detail", city_name=city_name.capitalize()),
            follow_redirects=True
        )
        code = response.status_code
        data = response.get_data(as_text=True)
        self.assertEqual(code, 200)
        self.assertIn(error_json['message'], data)
        self.assertEqual(response.request.path, url_for('weather.index'))
        logout_user()
