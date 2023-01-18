import requests
import sqlalchemy.exc
import sys
from datetime import datetime, timedelta
from flask import Flask, request, redirect, url_for
from flask import render_template
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
db = SQLAlchemy(app)


class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)

    def __repr__(self):
        return '<City name: %r>' % self.name


with app.app_context():
    db.create_all()


def get_api_key():
    """for some stupid reason tests do not work if the code reads api key from file"""
    return '9c0153c3b569259d845e969c161b1106'
    # with open('key.txt', 'r', encoding='utf-8') as f:
        # return f.read().strip()


def day_part(time_point: datetime):
    if '12:00' <= time_point.strftime('%H:%M') < '17:00':
        return 'card day'
    elif '21:00' <= time_point.strftime('%H:%M') < '05:00':
        return 'card night'
    else:
        return 'card evening-morning'


def get_weather_data(name):
    params = {'q': name, 'appid': get_api_key(), 'units': 'metric'}
    url = r'https://api.openweathermap.org/data/2.5/weather'
    data = requests.get(url=url, params=params).json()
    local_time = datetime.utcfromtimestamp(data['dt']) + timedelta(seconds=data['timezone'])
    return {'cod': data['cod'],
            'city': data['name'].upper(),
            'temp': int(data['main']['temp']),
            'state': data['weather'][0]['main'],
            'card_class': day_part(local_time)}


@app.route('/', methods=['GET', 'POST'])
def index():
    cities_weather = []
    if request.method == 'POST':
        try:
            city_name = request.form.get('city_name').upper()
            new_city = City(name=city_name)
            db.session.add(new_city)
            db.session.commit()
        except sqlalchemy.exc.IntegrityError as e:
            print(e)
        finally:
            return redirect(url_for('index'))
    else:
        db_cities = db.session.execute(db.select(City.name)).scalars().all()
        if db_cities:
            cities_weather = [get_weather_data(city) for city in db_cities]
        return render_template('index.html', cities=cities_weather)


# don't change the following way to run flask:
if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()
