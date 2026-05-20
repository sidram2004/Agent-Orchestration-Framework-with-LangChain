import requests
import os
from datetime import datetime
from duckduckgo_search import DDGS
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
        query = query.lower().strip()
        
        # Extract city from queries like "weather in mumbai" or just "mumbai"
        if "weather" in query:
            match = re.search(r"weather\s+(?:in\s+|for\s+)?([a-z\s]+)", query)
            if match:
                city = match.group(1).strip()
            else:
                city = query.replace("weather", "").strip()
        else:
            city = query
            
        if not city:
            return "City not found"
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


def current_time(query):
    """Return current time for any city or country using timezone offset."""
    from datetime import datetime, timedelta, timezone

    # Map country names to capitals to avoid API ambiguity (e.g., "Poland" -> Poland, Maine, USA)
    COUNTRY_CAPITALS = {
        "poland": "warsaw", "germany": "berlin", "france": "paris", "uk": "london",
        "united kingdom": "london", "italy": "rome", "spain": "madrid", "canada": "ottawa",
        "australia": "canberra", "japan": "tokyo", "china": "beijing", "russia": "moscow",
        "india": "new delhi", "brazil": "brasilia", "mexico": "mexico city", "egypt": "cairo",
        "south africa": "pretoria", "turkey": "ankara", "netherlands": "amsterdam",
        "switzerland": "bern", "sweden": "stockholm", "norway": "oslo", "portugal": "lisbon",
        "greece": "athens", "austria": "vienna", "belgium": "brussels", "thailand": "bangkok",
        "vietnam": "hanoi", "singapore": "singapore", "malaysia": "kuala lumpur",
        "indonesia": "jakarta", "philippines": "manila", "south korea": "seoul",
        "usa": "new york", "united states": "new york", "america": "new york",
        "pakistan": "islamabad", "bangladesh": "dhaka", "sri lanka": "colombo",
        "nigeria": "lagos", "kenya": "nairobi", "iran": "tehran", "iraq": "baghdad",
        "saudi arabia": "riyadh", "uae": "dubai", "united arab emirates": "dubai",
        "ukraine": "kyiv", "argentina": "buenos aires", "colombia": "bogota",
        "chile": "santiago", "denmark": "copenhagen", "finland": "helsinki",
        "romania": "bucharest", "hungary": "budapest", "czech republic": "prague",
    }

    query = str(query).lower().strip()
    city = None

    # Extract city/country name from query
    if " in " in query:
        city = query.split(" in ")[-1].strip()
    elif "of " in query:
        city = query.split(" of ")[-1].strip()
    elif query and query != "time":
        city = query

    # Map country name to its capital for accurate timezone lookup
    if city and city in COUNTRY_CAPITALS:
        city = COUNTRY_CAPITALS[city]

    # Fetch timezone offset via OpenWeatherMap and calculate local time
    if city:
        try:
            api_key = os.getenv("WEATHER_API_KEY")
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
            response = requests.get(url, timeout=5)
            data = response.json()

            if response.status_code == 200:
                offset = data.get("timezone", 0)
                utc_now = datetime.now(timezone.utc)
                local_time = utc_now + timedelta(seconds=offset)

                city_name = data.get("name", city.title())
                country = data.get("sys", {}).get("country", "")
                fmt_time = local_time.strftime("%I:%M:%S %p — %A, %d %B %Y")

                return f"Current time in {city_name}, {country}: {fmt_time} (UTC{offset/3600:+.1f})"
        except Exception as e:
            print(f"[Time Tool API Error] {e}")

    # Fallback: return local server time
    return datetime.now().strftime("Local Server Time: %I:%M:%S %p — %A, %d %B %Y")
