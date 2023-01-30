from flask import make_response, jsonify, current_app
from flask_restful import Api, Resource
from playhouse.shortcuts import model_to_dict

from app.weather.models import Country


class CountryAPI(Resource):
    """Api for country"""

    def get(self, country_id):
        """Handle get request"""
        country = Country.select().where(Country.id == country_id).first()
        if not country:
            message = {'message': f'Country with {country_id} not found'}
            return make_response(jsonify(message), 404)
        return make_response(jsonify(model_to_dict(country)), 200)


def init_app(app):
    with app.app_context():
        api = Api(app, decorators=[current_app.config['CSRF'].exempt])
        api.add_resource(CountryAPI, '/api/v1/countries/<int:country_id>/')
