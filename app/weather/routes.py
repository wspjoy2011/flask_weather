from flask import (
    render_template,
    redirect,
    request,
    url_for,
    flash,
    current_app
)

from app.weather import weather
from app.weather.forms import CityForm
from weather.getting_weather import main as getting_weather
from app.weather.models import Country, City


@weather.route('/', methods=['GET', 'POST'])
def index():
    """Weather page"""
    form = CityForm()
    city_weather = None
    country = None
    city_name = None

    if form.validate_on_submit():
        api_key = current_app.config['WEATHER_API_KEY']
        city_name = form.city_name.data
        city_weather = getting_weather(city_name, api_key)
        if 'error' in city_weather:
            flash(city_weather['error'])
            return redirect(url_for('weather.index'))
        country = Country.select().where(Country.code == city_weather['country']).first()
        city_weather['country'] = country.name

    return render_template(
        'weather/get_weather.html',
        title='Get city weather',
        form=form,
        city_name=city_name,
        country=country,
        city_weather=city_weather
    )


@weather.route('/show/city')
def show_city():
    """Show added city"""
    api_key = current_app.config['WEATHER_API_KEY']
    cities = City().select()
    cities_weather = []
    for city in cities:
        city_weather = getting_weather(city.name, api_key)
        if 'error' in city_weather:
            flash(city_weather['error'])
            return redirect(url_for('weather.index'))
        city_weather['id'] = city.id
        city_weather['city'] = city.name
        city_weather['country'] = city.country.name
        cities_weather.append(city)
    pagination = ''
    return render_template(
        'weather/show_cities_weather.html',
        title='Weather in cities',
        cities_weather=cities_weather,
        pagination=pagination
    )


@weather.route('/add/city', methods=['POST'])
def add_city():
    """Add city to monitoring"""
    if request.method == 'POST':
        city = request.form.get('city').capitalize()
        country = request.form.get('country')

        check_city = City.select().where(City.name == city).first()
        if not check_city:
            city_instance = City(
                name=city,
                country=country
            )
            city_instance.save()
            flash(f'City: {city} added to db')
        else:
            flash(f'City: {city} already in db')

    return redirect(url_for('weather.index'))

