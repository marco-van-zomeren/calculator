
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import swisseph as swe
import datetime
import requests
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://designonacid.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)

swe.set_ephe_path(".")

class InterpretRequest(BaseModel):
    birth: str
    lat: float
    lon: float

@app.post("/api/interpret")
def interpret_chart(data: InterpretRequest):
    dt = datetime.datetime.fromisoformat(data.birth)
    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60)

    planet_ids = {
        "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
        "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE,
        "Pluto": swe.PLUTO
    }

    def degree_to_zodiac(deg):
        signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                 "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        idx = int(deg // 30)
        sign = signs[idx % 12]
        pos = deg % 30
        return f"{pos:.2f}° {sign}"

    result = {}
    for name, pid in planet_ids.items():
        lon_lat = swe.calc_ut(jd, pid)[0]
        result[name] = degree_to_zodiac(lon_lat[0])

    cusps, ascmc = swe.houses(jd, data.lat, data.lon, b'P')
    result["Ascendant"] = degree_to_zodiac(ascmc[0])
    result["Midheaven"] = degree_to_zodiac(ascmc[1])

    def describe(planet, value):
        if "°" in value:
            sign = value.split("°")[1].strip()
            return f"{planet} in {sign}"
        return f"{planet}: {value}"

    summary = "Your chart shows: " + ", ".join(describe(k, v) for k, v in result.items()) + "."
    return { "summary": summary, "raw": result }

@app.post("/api/chat")
async def chat_with_ai(request: Request):
    data = await request.json()
    message = data.get("text", "")
    prompt = f"""
You are a knowledgeable astrology assistant. A user will tell you their birth details like:
"I was born Sept 12, 1988 at 12:20 in Alblasserdam".

1. Extract birth datetime and location.
2. Estimate lat/lon based on known city.
3. Call this API:

https://calculator-vlhx.onrender.com/api/interpret

Include this data:
{{"birth": "1988-09-12T12:20", "lat": 51.87, "lon": 4.66}}

Send a POST request and use the summary returned as your reply.

User: {message}
"""

    api_key = os.getenv("TOGETHER_API_KEY", "sk-YOUR-TOGETHER-KEY")
    res = requests.post(
        "https://api.together.xyz/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "mistral-7b-instruct",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
    )
    return res.json()["choices"][0]["message"]["content"]
