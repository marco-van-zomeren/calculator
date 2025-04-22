
from fastapi import FastAPI, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import swisseph as swe
import datetime

app = FastAPI()

# Allow frontend/AI access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

swe.set_ephe_path(".")

# Input schema for /api/interpret
class InterpretRequest(BaseModel):
    birth: str
    lat: float
    lon: float

def degree_to_zodiac(deg):
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    idx = int(deg // 30)
    sign = signs[idx % 12]
    pos = deg % 30
    return f"{pos:.2f}° {sign}"

@app.get("/api/planets")
def get_planets(birth: str = Query(...), lat: float = Query(...), lon: float = Query(...)):
    return calculate_positions(birth, lat, lon)

@app.post("/api/interpret")
def interpret_chart(data: InterpretRequest):
    astro = calculate_positions(data.birth, data.lat, data.lon)

    def describe(planet, value):
        if "°" in value:
            sign = value.split("°")[1].strip()
            return f"{planet} in {sign}"
        return f"{planet}: {value}"

    phrases = [describe(k, v) for k, v in astro.items()]
    summary = "Your chart shows: " + ", ".join(phrases) + "."

    return {
        "summary": summary,
        "raw": astro
    }

def calculate_positions(birth, lat, lon):
    dt = datetime.datetime.fromisoformat(birth)
    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60)

    planet_ids = {
        "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
        "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE,
        "Pluto": swe.PLUTO
    }

    result = {}
    for name, pid in planet_ids.items():
        lon_lat = swe.calc_ut(jd, pid)[0]
        result[name] = degree_to_zodiac(lon_lat[0])

    cusps, ascmc = swe.houses(jd, lat, lon, b'P')
    result["Ascendant"] = degree_to_zodiac(ascmc[0])
    result["Midheaven"] = degree_to_zodiac(ascmc[1])

    return result
