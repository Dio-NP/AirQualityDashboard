'use client';

import { useState } from 'react';

interface LegendProps {
  pollutant: 'NO2' | 'O3' | 'PM25';
  onPollutantChange?: (p: 'NO2' | 'O3' | 'PM25') => void;
}

export default function Legend({ pollutant, onPollutantChange }: LegendProps) {
  const [open, setOpen] = useState(true);

  const ramp = [
    { c: '#00FF00', v: 'Good' },
    { c: '#FFFF00', v: 'Moderate' },
    { c: '#FF9900', v: 'USG' },
    { c: '#FF0000', v: 'Unhealthy' },
    { c: '#990099', v: 'Very Unhealthy' },
    { c: '#660000', v: 'Hazardous' },
  ];

  return (
    <div className="absolute bottom-4 right-4 z-20">
      <div className="bg-gray-800/80 backdrop-blur-md border border-gray-700 rounded-lg shadow-xl p-3 min-w-[220px]">
        <div className="flex items-center justify-between mb-2">
          <div className="text-sm text-gray-200 font-semibold">Legend</div>
          <button onClick={() => setOpen(!open)} className="text-gray-400 hover:text-white text-xs">{open ? 'Hide' : 'Show'}</button>
        </div>
        {open && (
          <>
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-xs text-gray-400">Pollutant</span>
              <select
                value={pollutant}
                onChange={(e) => onPollutantChange?.(e.target.value as any)}
                className="bg-gray-700 text-white text-xs px-2 py-1 rounded border border-gray-600"
              >
                <option value="NO2">NO₂</option>
                <option value="O3">O₃</option>
                <option value="PM25">PM₂.₅</option>
              </select>
            </div>
            <div className="space-y-1">
              {ramp.map((r, i) => (
                <div key={i} className="flex items-center space-x-2 text-xs">
                  <div className="w-6 h-3 rounded-sm" style={{ background: r.c }} />
                  <span className="text-gray-300">{r.v}</span>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}


