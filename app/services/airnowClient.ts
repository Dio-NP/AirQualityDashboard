// Air quality client that uses our backend API (which includes AirNow integration)

export async function fetchAirNowByLatLon(lat: number, lon: number) {
  const url = `http://localhost:8000/api/air-quality/current?lat=${lat}&lon=${lon}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

export async function fetchAirNowByZip(zip: string) {
  // For now, we'll use a default location for zip codes
  // In a real implementation, you'd geocode the zip to lat/lon
  const defaultLat = 34.0522; // Los Angeles
  const defaultLon = -118.2437;
  return fetchAirNowByLatLon(defaultLat, defaultLon);
}

export async function fetchAirQualityForecast(lat: number, lon: number, hours: number = 24) {
  const url = `http://localhost:8000/api/air-quality/forecast?lat=${lat}&lon=${lon}&hours=${hours}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}


