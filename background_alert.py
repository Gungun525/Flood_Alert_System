# background_alert.py
import pandas as pd
import requests
import joblib
import csv
from googletrans import Translator
from twilio.rest import Client

# Config
API_KEY = 'dcd1e59fdf98dd5953683ad7e3f27651'
TWILIO_SID = 'AC239b59d54ff986da5080d3e9bb54e387'
TWILIO_TOKEN = 'acd6f079a578cc7d9f8a4f24d2a91b7a'
FROM_PHONE = '+15739833157'

model = joblib.load('flood_model.pkl')
translator = Translator()
client = Client(TWILIO_SID, TWILIO_TOKEN)

# Load users
with open('users.csv', 'r') as file:
    users = list(csv.reader(file))

# Check for each user
for phone, city, language in users:
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        weather = requests.get(url).json()

        rainfall = weather.get("rain", {}).get("1h", 0)
        humidity = weather['main']['humidity']
        temperature = weather['main']['temp']
        river_level = 8.5 if rainfall > 80 else 5.0

        df = pd.DataFrame([{
            'rainfall': rainfall,
            'river_level': river_level,
            'humidity': humidity,
            'temperature': temperature
        }])
        prediction = model.predict(df)[0]

        if prediction == 1:
            msg = "⚠️ Flood Alert: Heavy rainfall expected. Stay alert and move to higher ground."
            translated = translator.translate(msg, dest=language).text
            client.messages.create(body=translated, from_=FROM_PHONE, to=phone)
            print(f"✅ Alert sent to {phone}")
        else:
            print(f"✅ No risk for {phone}")
    except Exception as e:
        print(f"❌ Error for {phone}: {e}")
