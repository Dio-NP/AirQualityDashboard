'use client';

import { useState, useEffect } from 'react';
import { Cloud, Sun, Wind, Droplets, Thermometer } from 'lucide-react';

interface WeatherData {
  temperature: number;
  humidity: number;
  windSpeed: number;
  windDirection: string;
  conditions: string;
  pressure: number;
}

export default function WeatherOverlay() {
  const [weatherData, setWeatherData] = useState<WeatherData>({
    temperature: 72,
    humidity: 45,
    windSpeed: 8,
    windDirection: 'NW',
    conditions: 'Partly Cloudy',
    pressure: 1013
  });

  useEffect(() => {
    const interval = setInterval(() => {
      setWeatherData(prev => ({
        ...prev,
        temperature: prev.temperature + (Math.random() - 0.5) * 2,
        humidity: Math.max(0, Math.min(100, prev.humidity + (Math.random() - 0.5) * 5)),
        windSpeed: Math.max(0, prev.windSpeed + (Math.random() - 0.5) * 2),
        pressure: prev.pressure + (Math.random() - 0.5) * 2
      }));
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  const getWeatherIcon = (conditions: string) => {
    switch (conditions.toLowerCase()) {
      case 'sunny': return <Sun className="w-6 h-6 text-yellow-500" />;
      case 'cloudy': return <Cloud className="w-6 h-6 text-gray-400" />;
      case 'partly cloudy': return <Cloud className="w-6 h-6 text-blue-400" />;
      case 'rainy': return <Droplets className="w-6 h-6 text-blue-500" />;
      default: return <Sun className="w-6 h-6 text-yellow-500" />;
    }
  };

  return (
    <div className="absolute top-4 right-4 bg-black bg-opacity-70 backdrop-blur-sm rounded-lg p-4 text-white">
      <div className="flex items-center space-x-2 mb-2">
        {getWeatherIcon(weatherData.conditions)}
        <span className="font-semibold">Weather Conditions</span>
      </div>
      
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div className="flex items-center space-x-2">
          <Thermometer className="w-4 h-4 text-red-400" />
          <span>{Math.round(weatherData.temperature)}°F</span>
        </div>
        
        <div className="flex items-center space-x-2">
          <Droplets className="w-4 h-4 text-blue-400" />
          <span>{Math.round(weatherData.humidity)}%</span>
        </div>
        
        <div className="flex items-center space-x-2">
          <Wind className="w-4 h-4 text-gray-400" />
          <span>{Math.round(weatherData.windSpeed)} mph {weatherData.windDirection}</span>
        </div>
        
        <div className="text-xs text-gray-300">
          {Math.round(weatherData.pressure)} hPa
        </div>
      </div>
    </div>
  );
}
