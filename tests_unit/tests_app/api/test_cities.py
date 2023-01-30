import unittest
import random
from unittest.mock import MagicMock, patch
from peewee import fn

from app import create_app
from app.weather.models import City, Country
from weather.fill_country_db import main as fill_country_db, FILENAME as COUNTRY_CODES_JSON


class TestCitiesAPI(unittest.TestCase):
    app = None
    db = None
    ctx = None
    client = None
    cities = None
    cities_api_url = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = create_app('testing')
        cls.db = cls.app.config['db']
        fill_country_db(COUNTRY_CODES_JSON, cls.db)
        cls.cities = ['Barcelona', 'Tokyo', 'Chicago', 'Washington']
        cls.cities_api_url = '/api/v1/cities/'

        cls.ctx = cls.app.test_request_context()
        cls.ctx.push()
        cls.client = cls.app.test_client()

    def test_aa_post_add_cities(self):
        for city in self.cities:
            response = self.client.post(
                self.cities_api_url,
                json={'name': city},
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 201)
            self.assertFalse(response.get_data(as_text=True))
            city_instance = City.select().where(City.name == city).first()
            self.assertTrue(city_instance)

    @patch('weather.getting_weather.requests')
    def test_ab_post_with_error_in_json_response(self, requests_mock):
        city = 'Wrong_city_name'
        error_json = {'message': 'City not found'}

        request_response_mock = MagicMock()
        request_response_mock.status_code = 404
        request_response_mock.json.return_value = error_json
        requests_mock.get.return_value = request_response_mock
        response = self.client.post(
            self.cities_api_url,
            json={'name': city},
            content_type='application/json'
        )
        response_json = response.get_json()
        code = response.status_code

        self.assertEqual({'error': 'City not found'}, response_json)
        self.assertEqual(code, 500)

    def test_ac_post_add_city_already_exist(self):
        city = random.choice(self.cities)
        response = self.client.post(
            self.cities_api_url,
            json={'name': city},
            content_type='application/json'
        )
        response_json = response.get_json()
        code = response.status_code
        self.assertEqual(code, 200)
        self.assertEqual(
            {'message': f'{city} already in database.'},
            response_json
        )

    def test_ad_get_cities(self):
        response = self.client.get(self.cities_api_url)
        response_json = response.get_json()
        code = response.status_code
        self.assertEqual(code, 200)
        for city in response_json:
            city_instance = City.select().where(City.id == city['id']).first()
            self.assertEqual(city['id'], city_instance.id)
            self.assertEqual(city['country_id'], city_instance.country.id)
            self.assertEqual(city['name'], city_instance.name)

    def test_ae_put_update_city(self):
        response_get_cities = random.choice(self.client.get(self.cities_api_url).get_json())
        new_city_name = 'Paris'
        new_country_code = 'FR'
        country = Country.select().where(Country.code == new_country_code).first()
        response_get_cities['country_id'] = country.id
        response_get_cities['name'] = new_city_name

        response = self.client.put(
            self.cities_api_url,
            json=response_get_cities,
            content_type='application/json'
        )
        code = response.status_code
        data = response.get_data(as_text=True)
        self.assertEqual(code, 204)
        self.assertFalse(data)

        updated_city = City.select().where(City.id == response_get_cities['id']).first()
        self.assertEqual(new_city_name, updated_city.name)
        self.assertEqual(new_country_code, updated_city.country.code)

    def test_af_put_update_city_without_city_id(self):
        response_get_cities = random.choice(self.client.get(self.cities_api_url).get_json())
        del response_get_cities['id']

        response = self.client.put(
            self.cities_api_url,
            json=response_get_cities,
            content_type='application/json'
        )
        code = response.status_code
        response_json = response.get_json()

        self.assertEqual(code, 200)
        self.assertEqual({'message': 'field id is necessary.'}, response_json)

    def test_ag_put_update_city_without_country_id(self):
        response_get_cities = random.choice(self.client.get(self.cities_api_url).get_json())
        del response_get_cities['country_id']

        response = self.client.put(
            self.cities_api_url,
            json=response_get_cities,
            content_type='application/json'
        )
        code = response.status_code
        response_json = response.get_json()

        self.assertEqual(code, 200)
        self.assertEqual({'message': 'field country_id is necessary.'}, response_json)

    def test_ag_put_update_city_with_non_exist_city_id(self):
        response_get_cities = random.choice(self.client.get(self.cities_api_url).get_json())
        max_city_id = City.select(fn.MAX(City.id)).scalar()
        response_get_cities['id'] = max_city_id + 1

        response = self.client.put(
            self.cities_api_url,
            json=response_get_cities,
            content_type='application/json'
        )
        code = response.status_code
        response_json = response.get_json()

        self.assertEqual(code, 200)
        self.assertEqual(
            {'message': f'city with id {max_city_id + 1} not found.'},
            response_json
        )

    def test_ah_put_update_city_with_non_exist_country_id(self):
        response_get_cities = random.choice(self.client.get(self.cities_api_url).get_json())
        max_country_id = Country.select(fn.MAX(Country.id)).scalar()
        response_get_cities['country_id'] = max_country_id + 1

        response = self.client.put(
            self.cities_api_url,
            json=response_get_cities,
            content_type='application/json'
        )
        code = response.status_code
        response_json = response.get_json()

        self.assertEqual(code, 200)
        self.assertEqual(
            {'message': f'country with id {max_country_id + 1} not found.'},
            response_json
        )

    def test_ai_put_update_city_with_wrong_country_id(self):
        response_get_cities = random.choice(self.client.get(self.cities_api_url).get_json())
        correct_id = response_get_cities['country_id']
        wrong_country_id = random.choice(
            Country.select(Country.id).where(Country.id != response_get_cities['country_id'])
        )
        response_get_cities['country_id'] = wrong_country_id.id

        response = self.client.put(
            self.cities_api_url,
            json=response_get_cities,
            content_type='application/json'
        )
        code = response.status_code
        response_json = response.get_json()

        self.assertEqual(code, 200)
        self.assertEqual(
            {'message': f'incorrect country id {wrong_country_id} correct is {correct_id}.'},
            response_json
        )

    def test_aj_delete_all_cities(self):
        cities_qty = City.select().count()

        self.assertTrue(cities_qty)
        response = self.client.delete(self.cities_api_url)
        code = response.status_code
        data = response.get_data()

        self.assertEqual(code, 204)
        self.assertFalse(data)

        cities_qty = City.select().count()
        self.assertFalse(cities_qty)
