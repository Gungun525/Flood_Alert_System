# app.py
from flask import Flask, request, render_template
import pandas as pd
import requests
import joblib
from googletrans import Translator
from twilio.rest import Client
import csv

import os  # 🔐 For environment variables

# Secure Config using environment variables
API_KEY = os.environ.get('API_KEY')
TWILIO_SID = os.environ.get('TWILIO_SID')
TWILIO_TOKEN = os.environ.get('TWILIO_TOKEN')
FROM_PHONE = os.environ.get('FROM_PHONE')


# Init
app = Flask(__name__)
model = joblib.load('flood_model.pkl')
translator = Translator()
client = Client(TWILIO_SID, TWILIO_TOKEN)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    country_code = request.form['country_code']
    phone_number = request.form['phone']
    city = request.form['city']
    language = request.form['language']
    mode = request.form['mode']

    full_phone = f"{country_code}{phone_number}"

    # Save user info
    with open('users.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([full_phone, city, language])

    if mode == 'demo':
        rainfall = 120
        humidity = 90
        temperature = 27
        river_level = 8.6
    else:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        weather = requests.get(url).json()

        if 'main' not in weather:
            return f"<h3>❌ Error: Could not fetch weather for '{city}'. Please check the city name.</h3>"

        rainfall = weather.get("rain", {}).get("1h", 0)
        humidity = weather['main']['humidity']
        temperature = weather['main']['temp']
        river_level = 8.5 if rainfall > 80 else 5.0

    # Prepare input and predict
    df = pd.DataFrame([{
        'rainfall': rainfall,
        'river_level': river_level,
        'humidity': humidity,
        'temperature': temperature
    }])
    prediction = model.predict(df)[0]

    # Prepare message
    msg = "⚠️ Flood Alert: Heavy rainfall expected. Stay alert and move to higher ground."
    translated = translator.translate(msg, dest=language).text

    if prediction == 1:
        # ✅ Send to current user
        try:
            client.messages.create(body=translated,
                                   from_=FROM_PHONE,
                                   to=full_phone)
        except Exception as e:
            return f"<h3>❌ Failed to send SMS to current user: {e}</h3>"

        # ✅ Send to all saved users (including current user, avoids duplicate)
        try:
            with open('users.csv', 'r') as file:
                users = list(csv.reader(file))

            for saved_phone, saved_city, saved_lang in users:
                try:
                    translated_msg = translator.translate(msg,
                                                          dest=saved_lang).text
                    client.messages.create(body=translated_msg,
                                           from_=FROM_PHONE,
                                           to=saved_phone)
                except Exception as e:
                    print(f"❌ Failed to send SMS to {saved_phone}: {e}")
        except Exception as e:
            print(f"❌ Error reading users.csv: {e}")

        weather_status = "flood" if mode == "demo" else weather['weather'][0][
            'main'].lower()

        return render_template('result.html',
                               city=city,
                               rainfall=rainfall,
                               humidity=humidity,
                               temperature=temperature,
                               river_level=river_level,
                               weather_status=weather_status,
                               flood_predicted=True,
                               translated=translated)

    else:
        weather_status = weather['weather'][0]['main'].lower()

        return render_template('result.html',
                               city=city,
                               rainfall=rainfall,
                               humidity=humidity,
                               temperature=temperature,
                               river_level=river_level,
                               weather_status=weather_status,
                               flood_predicted=False,
                               translated=None)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
