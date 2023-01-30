import peewee
from flask_restful import Api, Resource, reqparse
from flask import make_response, jsonify
from flask import current_app
from playhouse.shortcuts import model_to_dict

from app.weather.models import City, Country
from weather.getting_weather import main as getting_weather


class CityAPI(Resource):
    """API for city"""

    def __init__(self):
        self.request = None
        self.api_key = current_app.config['WEATHER_API_KEY']
        self.regparse = reqparse.RequestParser()
        self.regparse.add_argument('name', type=str, required=True, location='json')
        self.regparse.add_argument('country_id', type=int, required=True, location='json')

    def get(self, city_id):
        """Handle get request"""
        city = City.select().where(City.id == city_id).first()
        if city is None:
            message = {'message': f'city with id {city_id} not found'}
            return make_response(jsonify(message))
        json_response = model_to_dict(city)
        del json_response['country']
        json_response['country_id'] = city.country.id
        return make_response(jsonify(json_response), 200)

    def put(self, city_id):
        """Handle PUT request to update city with city_id"""
        self.request = self.regparse.parse_args()
        self.request.name = self.request.name.capitalize()

        city = City().select().where(City.id == city_id).first()
        city_check = City().select().where(City.name == self.request.name).first()

        check_country_code = getting_weather(self.request.name, self.api_key)

        if 'error' in check_country_code:
            return make_response(jsonify(check_country_code), 404)

        check_country_code = check_country_code['country']
        country = Country.select().where(Country.code == check_country_code).first()

        if city_check:
            response = {'message': f'{self.request.name} already in database.'}
            return make_response(jsonify(response), 200)

        if country.id != self.request.country_id:
            response = {'message': f'incorrect country id {self.request.country_id} correct is {country.id}.'}
            return make_response(jsonify(response), 200)

        city.name = self.request.name
        city.country = country
        city.save()
        return make_response('', 204)

    def delete(self, city_id):
        """Handle DELETE request to delete city with city_id"""
        city = City.select().where(City.id == city_id).first()
        if not city:
            response = {'message': f'City with {city_id} not found'}
            return make_response(jsonify(response), 404)
        try:
            city.delete_instance(recursive=False)
        except peewee.IntegrityError:
            message = {'error': f'Cannot delete city with id {city_id}, '
                                f'because another users has relation to this city'}
            return make_response(jsonify(message), 500)
        return make_response('', 204)


def init_app(app):
    with app.app_context():
        api = Api(app, decorators=[current_app.config['CSRF'].exempt])
        api.add_resource(CityAPI, '/api/v1/cities/<int:city_id>/')
