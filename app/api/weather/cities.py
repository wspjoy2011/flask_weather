import peewee
from flask_restful import Api, Resource, reqparse
from flask import make_response, jsonify
from flask import current_app

from app.weather.models import City, Country
from weather.getting_weather import main as getting_weather

# /api/v1/cities/1
# GET = all_cities 200
# POST = add city 201
# PUT = update_cities 204
# DELETE = delete_all_cities 204


class CitiesAPI(Resource):
    """API for cities"""
    def __init__(self):
        self.cities = None
        self.request = None
        self.api_key = current_app.config['WEATHER_API_KEY']
        self.regparse = reqparse.RequestParser()
        self.regparse.add_argument('name', type=str, required=True, location='json')
        self.regparse.add_argument('id', type=int, required=False, location='json')
        self.regparse.add_argument('country_id', type=int, required=False, location='json')

    def get(self):
        """HTTP method GET"""
        self.cities = City.select()
        self.cities = self.prepare_cities_to_json()
        return make_response(jsonify(self.cities), 200)

    def post(self):
        """HTTP method POST"""
        self.request = self.regparse.parse_args()
        self.request.name = self.request.name.capitalize()
        city_weather = getting_weather(self.request.name, self.api_key)
        if 'error' in city_weather:
            return make_response(jsonify(city_weather), 500)
        country = Country.select().where(Country.code == city_weather['country']).first()
        city_check = City.select().where(City.name == self.request.name).first()
        if city_check:
            response = {'message': f'{self.request.name} already in database.'}
            return make_response(jsonify(response), 200)
        city = City(
            name=self.request.name,
            country=country.id
        )
        city.save()
        return make_response('', 201)

    def put(self):
        """HTTP method PUT"""
        self.request = self.regparse.parse_args()
        self.request.name = self.request.name.capitalize()

        if not self.request.id:
            response = {'message': 'field id is necessary.'}
            return make_response(jsonify(response), 200)

        if not self.request.country_id:
            response = {'message': 'field country_id is necessary.'}
            return make_response(jsonify(response), 200)

        city = City.select().where(City.id == self.request.id).first()
        country = Country.select().where(Country.id == self.request.country_id).first()

        if not city:
            response = {'message': f'city with id {self.request.id} not found.'}
            return make_response(jsonify(response), 200)

        if not country:
            response = {'message': f'country with id {self.request.country_id} not found.'}
            return make_response(jsonify(response), 200)

        check_country_code = getting_weather(self.request.name, self.api_key)['country']
        country = Country.select().where(Country.code == check_country_code).first()

        if country.id != self.request.country_id:
            response = {'message': f'incorrect country id {self.request.country_id} correct is {country.id}.'}
            return make_response(jsonify(response), 200)

        city.name = self.request.name
        city.country = country
        city.save()
        return make_response('', 204)

    def delete(self):
        """HTTP method DELETE"""
        try:
            City.delete().execute()
        except peewee.IntegrityError:
            message = {'error': f'Cannot delete these cities, '
                                f'because another users has relation'}
            return make_response(jsonify(message), 500)
        return make_response('', 204)

    def prepare_cities_to_json(self):
        """Prepare cities for json format"""
        cities = []
        for city in self.cities:
            city_temp = {
                'id': city.id,
                'name': city.name,
                'country_id': city.country.id
            }
            cities.append(city_temp)
        return cities


def init_app(app):
    with app.app_context():
        api = Api(app, decorators=[current_app.config['CSRF'].exempt])
        api.add_resource(CitiesAPI, '/api/v1/cities/')
