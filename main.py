
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import swisseph as swe
import datetime

app = FastAPI()

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://designonacid.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set the path for ephemeris files
swe.set_ephe_path(".")  # make sure .se1 files are in this folder

@app.get("/api/planets")
def get_planets(
    birth: str = Query(...),
    lat: float = Query(...),
    lon: float = Query(...)
):
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
        result[name] = f"{lon_lat[0]:.2f}°"

    # Add Ascendant and Midheaven
    cusps, ascmc = swe.houses(jd, lat, lon, b'P')
    result["Ascendant"] = f"{ascmc[0]:.2f}°"
    result["Midheaven"] = f"{ascmc[1]:.2f}°"

    return result
