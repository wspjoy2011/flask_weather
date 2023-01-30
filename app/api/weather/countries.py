from flask import make_response, jsonify, current_app
from flask_restful import Api, Resource

from app.weather.models import Country


class CountriesAPI(Resource):
    """Api for countries"""

    def get(self):
        """Handle get request"""
        countries = list(Country.select().dicts())
        return make_response(jsonify(countries), 200)


def init_app(app):
    with app.app_context():
        api = Api(app, decorators=[current_app.config['CSRF'].exempt])
        api.add_resource(CountriesAPI, '/api/v1/countries/')
