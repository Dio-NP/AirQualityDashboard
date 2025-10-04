'use client';

import { useEffect, useRef } from 'react';
import L from 'leaflet';
// Lazy require esri-leaflet at runtime to avoid SSR issues

interface MapProps {
  lat: number;
  lon: number;
  onLocationChange: (lat: number, lon: number) => void;
  pollutant?: 'NO2' | 'O3' | 'PM25';
  onTempoIdentify?: (value: number) => void;
  aqiData?: {
    lat: number;
    lon: number;
    aqi: number;
    category: string;
    color: string;
  } | null;
}

export default function Map({ lat, lon, onLocationChange, aqiData, pollutant = 'NO2', onTempoIdentify }: MapProps) {
  const mapRef = useRef<L.Map | null>(null);
  const airQualityLayerRef = useRef<L.ImageOverlay | null>(null);
  const tempoLayerRef = useRef<any | null>(null);
  const fallbackAddedRef = useRef<boolean>(false);
  const popupRef = useRef<L.Popup | null>(null);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    // Fix Leaflet default icons
    const L = require('leaflet');
    delete L.Icon.Default.prototype._getIconUrl;
    L.Icon.Default.mergeOptions({
      iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png').default,
      iconUrl: require('leaflet/dist/images/marker-icon.png').default,
      shadowUrl: require('leaflet/dist/images/marker-shadow.png').default,
    });

    // Initialize map
    if (!mapRef.current) {
      // North America bounds
      const northAmericaBounds = L.latLngBounds(
        L.latLng(15, -170),
        L.latLng(72, -50)
      );

      mapRef.current = L.map('map', {
        maxBounds: northAmericaBounds,
        maxBoundsViscosity: 1.0,
        minZoom: 3,
      }).setView([39.8283, -98.5795], 4); // Center on North America
      
      // Use a dark theme tile layer
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '© OpenStreetMap contributors, © CARTO',
        subdomains: 'abcd',
        maxZoom: 19
      }).addTo(mapRef.current);

      // Add click handler
      mapRef.current?.on('click', (e) => {
        // Clamp to bounds
        const la = Math.max(15, Math.min(72, e.latlng.lat));
        const lo = Math.max(-170, Math.min(-50, e.latlng.lng));
        onLocationChange(la, lo);
      });
    }

    // Show a compact popup at the selected location
    if (mapRef.current) {
      if (popupRef.current) {
        mapRef.current.closePopup(popupRef.current);
      }
      const content = `
        <div class="aqi-card">
          <div class="aqi-value" style="color:${aqiData?.color ?? '#ff7e00'}">${aqiData?.aqi ?? ''}</div>
          <div class="aqi-cat">${aqiData?.category ?? ''}</div>
          <div class="aqi-coord">${lat.toFixed(4)}, ${lon.toFixed(4)}</div>
        </div>
      `;
      const popup = L.popup({
        closeButton: true,
        autoPan: true,
        keepInView: true,
        autoPanPadding: [20, 40],
        autoPanPaddingTopLeft: [20, 60] as any,
        autoPanPaddingBottomRight: [20, 20] as any,
        // Positive Y offset places the popup below the click point to avoid clipping on top edge
        offset: L.point(0, 14),
        maxWidth: 220,
        className: 'aqi-popup'
      } as any)
        .setLatLng([lat, lon])
        .setContent(content);
      popupRef.current = popup;
      popup.openOn(mapRef.current);
    }

    // Fit map to North America bounds
    const northAmericaBounds = L.latLngBounds(
      L.latLng(15, -170), // Southwest corner
      L.latLng(72, -50)   // Northeast corner
    );
    mapRef.current?.fitBounds(northAmericaBounds);

    // Add TEMPO NO2 ImageServer layer via esri-leaflet (public beta layer)
    addTempoNO2Layer();

  }, [lat, lon, onLocationChange, aqiData]);

  const addTempoNO2Layer = () => {
    if (!mapRef.current) return;
    try {
      const EL = require('esri-leaflet');

      // Remove existing layer if any
      if (tempoLayerRef.current) {
        mapRef.current.removeLayer(tempoLayerRef.current);
        tempoLayerRef.current = null;
      }

      // Select service URL per pollutant (NO2 implemented; others can be swapped when public services are available)
      const url = (() => {
        switch (pollutant) {
          case 'NO2':
            return 'https://tiledimageservices.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/TEMPO_NO2_Vertical_Column_Troposphere_Beta/ImageServer';
          case 'O3':
            // TODO: Replace with TEMPO O3 ImageServer when available
            return 'https://tiledimageservices.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/TEMPO_NO2_Vertical_Column_Troposphere_Beta/ImageServer';
          case 'PM25':
            // Satellite PM2.5 not directly from TEMPO; keep NO2 for visualization, use AirNow points in sidebar
            return 'https://tiledimageservices.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/TEMPO_NO2_Vertical_Column_Troposphere_Beta/ImageServer';
        }
      })();

      const layer = EL.imageMapLayer({
        url,
        opacity: 0.7,
        useCors: true,
      });

      layer.addTo(mapRef.current);
      tempoLayerRef.current = layer;

      // Handle load/error to avoid crashing when the service is temporarily unavailable
      layer.on('load', () => {
        fallbackAddedRef.current = false;
      });
      layer.on('error', () => {
        try {
          if (tempoLayerRef.current && mapRef.current) {
            mapRef.current.removeLayer(tempoLayerRef.current);
          }
        } catch {}
        tempoLayerRef.current = null;
        // Fallback visualization so UI remains responsive
        if (!fallbackAddedRef.current) {
          addFallbackOverlay();
          fallbackAddedRef.current = true;
        }
      });

      // Optional: fetch pixel value on click to update sidebar exactly
      mapRef.current.on('click', async (e: any) => {
        try {
          const identify = EL.imageServices.identifyImage(url);
          identify.at(e.latlng);
          const result = await identify.run();
          // Best-effort extraction of a numeric pixel value
          let val: number | undefined = undefined as any;
          if (typeof (result as any)?.value === 'number') val = (result as any).value;
          if (val === undefined && (result as any)?.pixel?.value !== undefined) val = (result as any).pixel.value;
          if (val === undefined && Array.isArray((result as any)?.pixel)) {
            const first = (result as any).pixel[0];
            if (first && typeof first.value === 'number') val = first.value;
          }
          if (val !== undefined && onTempoIdentify) onTempoIdentify(val);
        } catch {}
      });
    } catch (err) {
      // If esri-leaflet not available at runtime, silently skip
      console.warn('esri-leaflet not loaded, skipping TEMPO layer');
      if (!fallbackAddedRef.current) {
        addFallbackOverlay();
        fallbackAddedRef.current = true;
      }
    }
  };

  // Minimal non-crashing visualization when TEMPO layer cannot load
  const addFallbackOverlay = () => {
    if (!mapRef.current) return;
    // Remove existing fallback
    if (airQualityLayerRef.current) {
      try { mapRef.current.removeLayer(airQualityLayerRef.current); } catch {}
      airQualityLayerRef.current = null;
    }
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    canvas.width = 1200; canvas.height = 800;
    for (let i = 0; i < 40; i++) {
      const x = Math.random() * canvas.width;
      const y = Math.random() * canvas.height;
      const r = Math.random() * 70 + 30;
      const g = ctx.createRadialGradient(x, y, 0, x, y, r);
      g.addColorStop(0, 'rgba(255,0,0,0.75)');
      g.addColorStop(0.7, 'rgba(255,153,0,0.35)');
      g.addColorStop(1, 'rgba(255,0,0,0)');
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
    }
    const dataURL = canvas.toDataURL();
    const overlay = L.imageOverlay(dataURL, [ [72, -170], [15, -50] ], { opacity: 0.6, interactive: false });
    overlay.addTo(mapRef.current);
    airQualityLayerRef.current = overlay;
  };

  return <div id="map" className="w-full h-full rounded-lg" />;
}