from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Weather(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    max_temp = db.Column(db.Float, nullable=False)
    min_temp = db.Column(db.Float, nullable=False)
    precip = db.Column(db.Float, nullable=False)
    sunrise = db.Column(db.String(10), nullable=False)
    sunset = db.Column(db.String(10), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('city', 'date', name='unique_city_date'),
    )

def create_db():
    with app.app_context():
        db.create_all()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        city = request.form['city']
        try:
            weather_data = fetch_weather_data(city)
            store_weather_data(city, weather_data)
            return redirect(url_for('weather', city=city))
        except Exception as e:
            return f"Error fetching weather data: {e}"

    return render_template('index.html')

@app.route('/weather/<city>')
def weather(city):
    weather_records = Weather.query.filter_by(city=city).all()
    return render_template('weather.html', weather_records=weather_records, city=city)

def fetch_weather_data(city):
    api_key = '785e35cc8917423e9ca114112242908'
    url = f"http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={city}&days=3"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("Error fetching data from the weather API")
    data = response.json()

    forecast_data = []
    for day in data['forecast']['forecastday']:
        forecast_data.append({
            'date': day['date'],
            'max_temp': day['day']['maxtemp_c'],
            'min_temp': day['day']['mintemp_c'],
            'precip': day['day']['totalprecip_mm'],
            'sunrise': day['astro']['sunrise'],
            'sunset': day['astro']['sunset']
        })
    return forecast_data

def store_weather_data(city, weather_data):
    for day in weather_data:
        # Check if a record with the same city and date already exists
        existing_record = Weather.query.filter_by(city=city, date=day['date']).first()

        if existing_record:
            # If it exists, update the existing record
            existing_record.max_temp = day['max_temp']
            existing_record.min_temp = day['min_temp']
            existing_record.precip = day['precip']
            existing_record.sunrise = day['sunrise']
            existing_record.sunset = day['sunset']
        else:
            # If it doesn't exist, create a new record
            new_record = Weather(
                city=city,
                date=day['date'],
                max_temp=day['max_temp'],
                min_temp=day['min_temp'],
                precip=day['precip'],
                sunrise=day['sunrise'],
                sunset=day['sunset']
            )
            db.session.add(new_record)

        # Commit all changes to the database
    db.session.commit()

if __name__ == '__main__':
    create_db()  # Ensure the database is created before running the app
    app.run(debug=True)

