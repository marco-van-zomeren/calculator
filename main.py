
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import swisseph as swe
import datetime

app = FastAPI()

# Allow frontend from designonacid.com
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://designonacid.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)

swe.set_ephe_path(".")  # Current directory for .se1 files

@app.get("/api/planets")
def get_planets(
    birth: str = Query(...),
    lat: float = Query(...),
    lon: float = Query(...)
) -> Dict[str, str]:
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
        lon_deg, lat, dist = swe.calc_ut(jd, pid)
        result[name] = f"{lon_deg:.2f}°"

    # Ascendant + houses
    cusps, ascmc = swe.houses(jd, lat, lon, b'P')  # Placidus
    result["Ascendant"] = f"{ascmc[0]:.2f}°"
    result["Midheaven"] = f"{ascmc[1]:.2f}°"

    return result
