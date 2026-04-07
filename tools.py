import requests
import os
from datetime import datetime
from ddgs import DDGS
from sympy import symbols, solve, simplify, diff, integrate, sympify, Eq
from dotenv import load_dotenv

load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")


# Advanced Math Solver using SymPy
def calculator(query):
    """
    Advanced mathematical solver that can handle:
    - Basic arithmetic (e.g. '45 * 8')
    - Solving equations (e.g. 'x**2 - 2*x + 1 = 0')
    - Simplifying expressions (e.g. '(x+1)**2')
    - Calculus (e.g. 'diff(x**2, x)')
    """
    try:
        query = query.replace('^', '**')
        
        if '=' in query:
            left, right = query.split('=')
            # Identify symbols (usually 'x' but could be others)
            # For simplicity, assume 'x' is the primary variable or check for single letters
            eq = Eq(sympify(left.strip()), sympify(right.strip()))
            # Auto-detect variables
            vars = eq.free_symbols
            if not vars:
                return str(solve(eq))
            
            solution = solve(eq, list(vars))
            return f"Solutions for {list(vars)}: {solution}"
        
        # Otherwise, try to simplify/evaluate
        result = sympify(query).evalf()
        if hasattr(result, 'is_number') and not result.is_number:
            return str(simplify(query))
            
        return str(result)
            
    except Exception as e:
        try:
            return str(eval(query, {"__builtins__": None}, {}))
        except:
            return f"Error: {str(e)}"


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
if __name__ == '__main__':
    # --- QUICK MATH ENGINE TEST ---
    from sympy import symbols, solve, simplify, diff, integrate, sympify, Eq
    queries = [
        'x**2 - 2*x + 1 = 0',  # Double Root (D=0)
        'x^2 + 5x + 6 = 0',    # Two Real Roots (D>0)
        'x**2 + x + 1 = 0',    # Complex Roots (D<0)
        'diff(x**3, x)',       # Calculus
        '45 * 8 / 2'           # Basic Math
    ]

    print('--- STARTING TOOLS.PY TEST ---\n')
    for q in queries:
        print(f'INPUT: {q}')
        print(f'RESULT:\n{calculator(q)}')
        print('-' * 30 + '\n')
