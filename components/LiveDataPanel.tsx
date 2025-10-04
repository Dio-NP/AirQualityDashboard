'use client';

import { useState, useEffect } from 'react';
import { Activity, TrendingUp, TrendingDown, AlertTriangle, CheckCircle } from 'lucide-react';

interface LiveDataPanelProps {
  aqiData: {
    lat: number;
    lon: number;
    aqi: number;
    category: string;
    color: string;
  } | null;
}

export default function LiveDataPanel({ aqiData }: LiveDataPanelProps) {
  const [isLive, setIsLive] = useState(true);
  const [trend, setTrend] = useState<'up' | 'down' | 'stable'>('up');
  const [lastUpdate, setLastUpdate] = useState(new Date());

  useEffect(() => {
    const interval = setInterval(() => {
      setLastUpdate(new Date());
      // Simulate trend changes
      const trends = ['up', 'down', 'stable'] as const;
      setTrend(trends[Math.floor(Math.random() * trends.length)]);
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const getTrendIcon = () => {
    switch (trend) {
      case 'up': return <TrendingUp className="w-4 h-4 text-red-500" />;
      case 'down': return <TrendingDown className="w-4 h-4 text-green-500" />;
      default: return <Activity className="w-4 h-4 text-blue-500" />;
    }
  };

  const getHealthStatus = (aqi: number) => {
    if (aqi <= 50) return { status: 'Good', icon: CheckCircle, color: 'text-green-500' };
    if (aqi <= 100) return { status: 'Moderate', icon: Activity, color: 'text-yellow-500' };
    if (aqi <= 150) return { status: 'Unhealthy for Sensitive', icon: AlertTriangle, color: 'text-orange-500' };
    if (aqi <= 200) return { status: 'Unhealthy', icon: AlertTriangle, color: 'text-red-500' };
    return { status: 'Hazardous', icon: AlertTriangle, color: 'text-red-700' };
  };

  const healthStatus = aqiData ? getHealthStatus(aqiData.aqi) : null;

  return (
    <div className="bg-gray-700 rounded-xl p-4 border border-gray-600">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Live Data Stream</h3>
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${isLive ? 'bg-green-500 animate-pulse' : 'bg-gray-500'}`}></div>
          <span className="text-sm text-gray-400">LIVE</span>
        </div>
      </div>

      {aqiData && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">Current AQI</span>
            <div className="flex items-center space-x-2">
              {getTrendIcon()}
              <span className="text-sm text-gray-400">{trend}</span>
            </div>
          </div>

          <div className="text-4xl font-bold" style={{ color: aqiData.color }}>
            {aqiData.aqi}
          </div>

          <div className="flex items-center space-x-2">
            {healthStatus && (
              <>
                <healthStatus.icon className={`w-5 h-5 ${healthStatus.color}`} />
                <span className={`font-semibold ${healthStatus.color}`}>
                  {healthStatus.status}
                </span>
              </>
            )}
          </div>

          <div className="text-xs text-gray-400">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </div>

          {/* Real-time chart simulation */}
          <div className="h-16 bg-gray-800 rounded-lg p-2">
            <div className="flex items-end space-x-1 h-full">
              {Array.from({ length: 20 }, (_, i) => (
                <div
                  key={i}
                  className="bg-blue-500 rounded-sm flex-1"
                  style={{
                    height: `${Math.random() * 100}%`,
                    opacity: 0.7
                  }}
                ></div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
