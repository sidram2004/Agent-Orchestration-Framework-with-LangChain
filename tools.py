import requests
import os
from datetime import datetime
from ddgs import DDGS
from dotenv import load_dotenv

load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")


# Calculator Tool
def calculator(query):
    try:
        result = eval(query, {"__builtins__": None}, {})
        return str(result)
    except Exception:
        return "Invalid mathematical expression"


# Weather Tool (FIXED)
def weather_tool(query):
    try:
        import requests, os, re

        api_key = os.getenv("WEATHER_API_KEY")

        # 🔥 Extract clean city
        query = query.lower()
        match = re.search(r"(?:weather\s*(?:in)?\s*)?([a-zA-Z\s]+)", query)

        if not match:
            return "City not found"

        city = match.group(1).strip()

        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

        response = requests.get(url)
        data = response.json()

        if response.status_code != 200:
            return "City not found"

        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        condition = data["weather"][0]["description"]
        wind = data["wind"]["speed"]

        return f"{city.title()}: {temp}°C, {condition}, Humidity {humidity}%, Wind {wind} m/s"

    except:
        return "Weather service unavailable"
# Web Search Tool
def web_search(query):
    try:
        results = DDGS().text(query, max_results=8)
        return "\n\n".join([f"Source snippet: {r['body']}" for r in results])
    except Exception:
        return "Search failed"


# Unit Converter
def unit_converter(query):
    try:
        import re

        query = query.lower()

        #  Extract number
        value_match = re.search(r"\d+(\.\d+)?", query)
        if not value_match:
            return "Invalid conversion"

        value = float(value_match.group())

        #  Detect units
        if "km" in query and "m" in query:
            return value * 1000

        if "m" in query and "km" in query:
            return value / 1000

        if "c" in query and "f" in query:
            return value * 9/5 + 32

        if "f" in query and "c" in query:
            return (value - 32) * 5/9

        if "kg" in query and "g" in query:
            return value * 1000

        if "g" in query and "kg" in query:
            return value / 1000

        return "Conversion not supported"

    except:
        return "Invalid conversion"

#  Time Tool
def current_time(_):
    return datetime.now().strftime("%H:%M:%S")