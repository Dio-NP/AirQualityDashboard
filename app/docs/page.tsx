"use client";
import * as React from 'react';

const Section = ({ title, children }: { title: string; children: React.ReactNode }) => (
  <section className="p-4 border rounded bg-white">
    <h2 className="text-lg font-semibold mb-2">{title}</h2>
    <div className="prose prose-sm max-w-none text-gray-800">{children}</div>
  </section>
);

export default function DocsPage() {
  return (
    <main className="mx-auto max-w-6xl p-4 space-y-4">
      <h1 className="text-2xl font-semibold">About the NASA AQI App</h1>
      <Section title="What this app does">
        <p>
          This app forecasts local air quality (AQI) by integrating satellite (TEMPO), ground measurements
          (Pandora, OpenAQ, AirNow) and weather/precipitation (HRRR/MERRA-2/IMERG). It visualizes forecasts, station
          points and provenance, and can validate satellite data against ground sensors.
        </p>
      </Section>

      <Section title="Key data sources">
        <ul>
          <li><b>TEMPO</b>: NO2/HCHO/Aerosol Index via NASA Earthdata/Harmony.</li>
          <li><b>Pandora</b>: Column observations from Pandonia Global Network.</li>
          <li><b>OpenAQ & AirNow</b>: Ground-level PM2.5/NO2/O3.</li>
          <li><b>IMERG</b>: Half-hourly precipitation (Early/Late/Final).</li>
        </ul>
      </Section>

      <Section title="How to run locally">
        <ol>
          <li>Start backend: <code>cd app; python -m uvicorn main:app --host 0.0.0.0 --port 8000</code></li>
          <li>Start frontend: <code>cd web; npm run dev</code> then open <code>http://localhost:3000</code>.</li>
        </ol>
      </Section>

      <Section title="API quick start">
        <p>Interactive API docs: <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">http://localhost:8000/docs</a></p>
        <ul>
          <li><code>POST /api/ingest/openaq</code> – params: <code>country</code>, <code>parameter</code>, <code>limit</code>, <code>schedule</code></li>
          <li><code>POST /api/ingest/tempo</code> – params: <code>product</code>, <code>time_range</code>, <code>version</code>, <code>nrt</code>, <code>schedule</code></li>
          <li><code>POST /api/ingest/imerg</code> – params: <code>product</code>, <code>time_range</code>, <code>schedule</code></li>
          <li><code>POST /api/ingest/pandora</code> – params: <code>url</code>, <code>parameter</code>, <code>schedule</code></li>
          <li><code>GET /api/forecast/aqi/timeline</code> – params: <code>lat</code>, <code>lon</code>, <code>hours</code></li>
        </ul>
      </Section>

      <Section title="Buttons on the homepage">
        <ul>
          <li><b>Start Tour</b>: launches a guided overlay explaining each panel.</li>
          <li><b>Predict AQI</b>: requests a prediction for the current inputs.</li>
          <li><b>Geolocate</b>: uses your browser to set map inputs to your location.</li>
          <li><b>Reset</b>: restores default LA example coordinates.</li>
          <li><b>Copy Link</b>: copies a shareable URL with current inputs.</li>
          <li><b>Copy curl (OpenAQ)</b>: copies a ready-to-run curl command for ground-data ingestion.</li>
          <li><b>Ingest OpenAQ / TEMPO / IMERG / Pandora</b>: triggers backend ingestion (status appears next to the buttons).</li>
          <li><b>Download Forecast CSV</b>: exports the 24h forecast table.</li>
        </ul>
      </Section>

      <Section title="Provenance and validation">
        <p>
          The frontend shows dataset metadata (attributes, variables) gathered from Zarr stores and validation metrics
          for TEMPO vs Pandora (matches, bias, RMSE, correlation). You can download the collocation as CSV.
        </p>
      </Section>
    </main>
  );
}


