import requests
import os
from dotenv import load_dotenv

load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# Calculator Tool
def calculator(Query):
    try:
        result = str(eval(Query))
        return f"Result: {result}"
    except Exception:
        return "Invalid mathematical expression."


# Weather Tool
def weather_api(city):

    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"

        response = requests.get(url)
        data = response.json()

        if data["cod"] != 200:
            return "City not found."

        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        description = data["weather"][0]["description"]
        wind = data["wind"]["speed"]

        weather_report = f"""
Weather Report for {city}

Temperature: {temp} °C
Condition: {description}
Humidity: {humidity} %
Wind Speed: {wind} m/s
"""

        return weather_report

    except Exception:
        return "Weather service currently unavailable."