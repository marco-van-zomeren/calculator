
const express = require('express');
const fetch = require('node-fetch');
const cors = require('cors');
const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());

const planetCodes = {
  Sun: '10',
  Moon: '301',
  Mercury: '199',
  Venus: '299',
  Mars: '499',
  Jupiter: '599',
  Saturn: '699',
  Uranus: '799',
  Neptune: '899',
  Pluto: '999'
};

const baseUrl = "https://ssd.jpl.nasa.gov/api/horizons.api";

async function fetchLongitude(planet, birth, lat, lon, elevation = 0) {
  const cleanBirth = birth.replace("T", " ");
  const center = `coord@399,${lat},${lon},${elevation}`;
  const url = `${baseUrl}?format=text&COMMAND='${planet}'&OBJ_DATA='NO'&MAKE_EPHEM='YES'&EPHEM_TYPE='OBSERVER'&CENTER='${center}'&START_TIME='${cleanBirth}'&STOP_TIME='${cleanBirth}'&STEP_SIZE='1 m'&QUANTITIES='1'`;

  try {
    const res = await fetch(url);
    const text = await res.text();
    const match = text.match(/\$\$SOE([\s\S]*?)\$\$EOE/);
    if (!match) return null;

    const line = match[1].trim().split("\n")[0];
    const parts = line.trim().split(/\s+/);
    const longitude = parseFloat(parts[2]);
    return isNaN(longitude) ? null : longitude;
  } catch (err) {
    console.error(`Error fetching ${planet}:`, err.message);
    return null;
  }
}

app.get('/api/planets', async (req, res) => {
  const { birth, lat, lon } = req.query;
  if (!birth || !lat || !lon) {
    return res.status(400).json({ error: "Missing parameters: birth, lat, lon required" });
  }

  const results = {};
  for (const [planetName, code] of Object.entries(planetCodes)) {
    const deg = await fetchLongitude(code, birth, lat, lon);
    results[planetName] = deg !== null ? `${deg.toFixed(2)}°` : "Error";
    await new Promise(r => setTimeout(r, 200)); // avoid rate-limiting
  }

  res.json(results);
});

app.listen(PORT, () => {
  console.log(`✅ Server running at http://localhost:${PORT}`);
});
