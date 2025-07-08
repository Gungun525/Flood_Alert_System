# send_alerts.py
import pandas as pd
import requests
import joblib
import csv
from googletrans import Translator
from twilio.rest import Client

# Config (replace with your real values)
API_KEY = 'dcd1e59fdf98dd5953683ad7e3f27651'
TWILIO_SID = 'AC239b59d54ff986da5080d3e9bb54e387'
TWILIO_TOKEN = 'fe32a0010c4df367068fab0736206ff2'
FROM_PHONE = '+15739833157'  # your verified Twilio number

# Load ML model
model = joblib.load('flood_model.pkl')
translator = Translator()
client = Client(TWILIO_SID, TWILIO_TOKEN)

# Load all users from users.csv
with open('data/users.csv', 'r') as file:
    users = list(csv.reader(file))

# Loop through users
for phone, city, language in users:
    try:
        # Get weather data
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        weather = requests.get(url).json()

        if 'main' not in weather:
            print(f"❌ Could not fetch weather for {city}")
            continue

        rainfall = weather.get("rain", {}).get("1h", 0)
        humidity = weather['main']['humidity']
        temperature = weather['main']['temp']
        river_level = 8.5 if rainfall > 80 else 5.0

        # Prepare features
        df = pd.DataFrame([{
            'rainfall': rainfall,
            'river_level': river_level,
            'humidity': humidity,
            'temperature': temperature
        }])

        # Predict
        prediction = model.predict(df)[0]

        if prediction == 1:
            msg = "⚠️ Flood Alert: Heavy rainfall expected. Stay alert and move to higher ground."
            translated_msg = translator.translate(msg, dest=language).text
            client.messages.create(body=translated_msg,
                                   from_=FROM_PHONE,
                                   to=phone)
            print(f"✅ Alert sent to {phone} for city {city}")
        else:
            print(f"✅ No flood risk for {phone} in {city}")

    except Exception as e:
        print(f"❌ Error for {phone} in {city}: {e}")
