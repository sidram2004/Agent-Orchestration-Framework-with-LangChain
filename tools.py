import requests
import os
from datetime import datetime
from ddgs import DDGS
from sympy import symbols, solve, simplify, diff, integrate, sympify, Eq
from dotenv import load_dotenv

load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")


def calculator(query):
    """Advanced math solver: arithmetic, algebra, equations, calculus."""
    try:
        query = query.replace('^', '**')
        if '=' in query:
            left, right = query.split('=', 1)
            eq = Eq(sympify(left.strip()), sympify(right.strip()))
            vars_ = eq.free_symbols
            if not vars_:
                return str(solve(eq))
            solution = solve(eq, list(vars_))
            return f"Solutions for {list(vars_)}: {solution}"
        result = sympify(query).evalf()
        if hasattr(result, 'is_number') and not result.is_number:
            return str(simplify(query))
        return str(result)
    except Exception as e:
        try:
            return str(eval(query, {"__builtins__": None}, {}))
        except:
            return f"Error: {str(e)}"


def weather_tool(query):
    """Real-time weather for a city."""
    try:
        import re
        api_key = os.getenv("WEATHER_API_KEY")
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
        temp      = data["main"]["temp"]
        humidity  = data["main"]["humidity"]
        condition = data["weather"][0]["description"]
        wind      = data["wind"]["speed"]
        return f"{city.title()}: {temp}°C, {condition}, Humidity {humidity}%, Wind {wind} m/s"
    except:
        return "Weather service unavailable"


def web_search(query):
    """DuckDuckGo web search."""
    try:
        results = DDGS().text(query, max_results=8)
        return "\n\n".join([f"Source: {r['body']}" for r in results])
    except Exception:
        return "Search failed"


def unit_converter(query):
    """Convert units: km↔m, °C↔°F, kg↔g."""
    try:
        import re
        query = query.lower()
        value_match = re.search(r"\d+(\.\d+)?", query)
        if not value_match:
            return "Invalid conversion"
        value = float(value_match.group())
        if "km" in query and " m" in query:  return str(value * 1000) + " m"
        if " m" in query and "km" in query:  return str(value / 1000) + " km"
        if "c" in query and "f" in query:    return str(value * 9/5 + 32) + " °F"
        if "f" in query and "c" in query:    return str((value - 32) * 5/9) + " °C"
        if "kg" in query and "g" in query:   return str(value * 1000) + " g"
        if " g" in query and "kg" in query:  return str(value / 1000) + " kg"
        return "Conversion not supported"
    except:
        return "Invalid conversion"


def current_time(_):
    """Return current time."""
    return datetime.now().strftime("%H:%M:%S — %A, %d %B %Y")