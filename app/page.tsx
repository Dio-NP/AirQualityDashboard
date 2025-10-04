'use client';

import { useState, useEffect, useRef } from 'react';
import dynamic from 'next/dynamic';
import { Search, AlertTriangle, Mail, Activity, Cloud, Wind, Sun, Moon, Phone, Settings, RefreshCw, Download, TrendingUp, Shield, Heart, Eye, Zap, Menu as MenuIcon, Share2, RotateCcw, MapPin, X } from 'lucide-react';
import { APIClient, DirectAPIClient } from '../services/apiClient';
import { fetchAirNowByLatLon, fetchAirQualityForecast } from './services/airnowClient';
import { WebSocketService, PollingService } from '../services/websocket';

// Dynamic imports for better performance
const Map = dynamic(() => import('@/components/Map'), { ssr: false });
const Legend = dynamic(() => import('@/components/Legend'), { ssr: false });
const LiveDataPanel = dynamic(() => import('@/components/LiveDataPanel'), { ssr: false });
const WeatherOverlay = dynamic(() => import('@/components/WeatherOverlay'), { ssr: false });

interface AQIData {
  lat: number;
  lon: number;
  aqi: number;
  category: string;
  color: string;
  pollutants: {
    o3: number;
    no2: number;
    pm25: number;
  };
}

export default function HomePage() {
  const [pollutantDynamics, setPollutantDynamics] = useState(true);
  const [atmosphericDynamics, setAtmosphericDynamics] = useState(false);
  const [timeframe, setTimeframe] = useState('hourly');
  const [aqiData, setAqiData] = useState<AQIData | null>({
    lat: 34.0522,
    lon: -118.2437,
    aqi: 145,
    category: 'UNHEALTHY',
    color: '#ff0000',
    pollutants: {
      o3: 68,
      no2: 42,
      pm25: 18
    }
  });
  const [email, setEmail] = useState('');
  const [systemStatus, setSystemStatus] = useState({
    satellite: 'ONLINE',
    groundNetwork: 'ONLINE',
    dataLatency: '2.3s',
    lastUpdate: new Date().toLocaleTimeString()
  });
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [useRealData, setUseRealData] = useState(false);
  const [isLiveMode, setIsLiveMode] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('Connecting...');
  const [isBackendAvailable, setIsBackendAvailable] = useState(false);
  const [dataRefreshRate, setDataRefreshRate] = useState(30000); // 30 seconds
  const [phoneNumber, setPhoneNumber] = useState('');
  const [showPhoneInput, setShowPhoneInput] = useState(false);
  const [notificationMessage, setNotificationMessage] = useState('');

  // Initialize services
  const [wsService] = useState(() => new WebSocketService());
  const [pollingService] = useState(() => new PollingService(apiClient));

  // API client
  const apiClient = new DirectAPIClient();

  // Helper functions
  const getAQICategory = (aqi: number): string => {
    if (aqi <= 50) return 'GOOD';
    if (aqi <= 100) return 'MODERATE';
    if (aqi <= 150) return 'UNHEALTHY FOR SENSITIVE GROUPS';
    if (aqi <= 200) return 'UNHEALTHY';
    if (aqi <= 300) return 'VERY UNHEALTHY';
    return 'HAZARDOUS';
  };

  const getAQIColor = (aqi: number): string => {
    if (aqi <= 50) return '#00FF00';
    if (aqi <= 100) return '#FFFF00';
    if (aqi <= 150) return '#FF9900';
    if (aqi <= 200) return '#FF0000';
    if (aqi <= 300) return '#990099';
    return '#660000';
  };

  // Check backend availability
  const checkBackendHealth = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/health');
      const isHealthy = response.ok;
      setIsBackendAvailable(isHealthy);
      setConnectionStatus(isHealthy ? 'Connected' : 'Disconnected');
      return isHealthy;
    } catch (error) {
      setIsBackendAvailable(false);
      setConnectionStatus('Disconnected');
      return false;
    }
  };

  // Fetch real air quality data
  const fetchRealData = async (lat: number = 34.0522, lon: number = -118.2437) => {
    try {
      // First check if backend is available
      const isHealthy = await checkBackendHealth();
      if (!isHealthy) {
        console.warn('Backend not available, using simulated data');
        return;
      }

      // Fetch air quality data from our backend
      const airQualityData = await fetchAirNowByLatLon(lat, lon);
      
      if (airQualityData && airQualityData.pollutants) {
        const pollutants = {
          o3: airQualityData.pollutants.O3?.value ?? Math.random() * 100,
          no2: airQualityData.pollutants.NO2?.value ?? Math.random() * 50,
          pm25: airQualityData.pollutants['PM2.5']?.value ?? Math.random() * 30,
        };

        setAqiData({
          lat: lat,
          lon: lon,
          aqi: airQualityData.aqi,
          category: airQualityData.category,
          color: airQualityData.color,
          pollutants: pollutants
        });

        // Update system status
        setSystemStatus(prev => ({
          ...prev,
          lastUpdate: new Date().toLocaleTimeString(),
          dataLatency: '1.2s'
        }));
      }
    } catch (error) {
      console.error('Failed to fetch real data:', error);
      // Fallback to simulated data
      setAqiData(prev => prev ? {
        ...prev,
        aqi: Math.floor(Math.random() * 200) + 50,
        category: getAQICategory(Math.floor(Math.random() * 200) + 50),
        color: getAQIColor(Math.floor(Math.random() * 200) + 50)
      } : null);
    }
  };

  // Real-time data updates with WebSocket and polling fallback
  useEffect(() => {
    if (!isLiveMode) return;

    // Set up WebSocket connection
    wsService.onData((data: any) => {
      if (data.aqi) {
        setAqiData({
          lat: data.lat || aqiData?.lat || 34.0522,
          lon: data.lon || aqiData?.lon || -118.2437,
          aqi: data.aqi,
          category: getAQICategory(data.aqi),
          color: getAQIColor(data.aqi),
          pollutants: data.pollutants || aqiData?.pollutants || { o3: 0, no2: 0, pm25: 0 }
        });
      }
    });

    wsService.onStatus((status: any) => {
      setConnectionStatus(status);
    });

    // Start WebSocket connection
    if (isBackendAvailable) {
      wsService.connect();
    } else {
      // Fallback to polling
      pollingService.onData((data: any) => {
        if (data.aqi) {
          setAqiData(prev => prev ? {
            ...prev,
            aqi: data.aqi,
            category: getAQICategory(data.aqi),
            color: getAQIColor(data.aqi),
            pollutants: data.pollutants || prev.pollutants
          } : null);
        }
      });

      pollingService.start(dataRefreshRate);
    }

    return () => {
      wsService.disconnect();
      pollingService.stop();
    };
  }, [isLiveMode, isBackendAvailable, dataRefreshRate, wsService, pollingService, aqiData?.lat, aqiData?.lon]);

  // Initial data fetch
  useEffect(() => {
    if (useRealData) {
      fetchRealData();
    }
  }, [useRealData]);

  // Periodic backend health check
  useEffect(() => {
    const interval = setInterval(checkBackendHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  // Handle real data toggle
  const handleRealDataToggle = () => {
    setUseRealData(!useRealData);
    if (!useRealData) {
      fetchRealData();
    }
  };

  // Handle live mode toggle
  const handleLiveModeToggle = () => {
    setIsLiveMode(!isLiveMode);
  };

  // Handle timeframe change
  const handleTimeframeChange = (newTimeframe: string) => {
    setTimeframe(newTimeframe);
    if (useRealData) {
      fetchRealData();
    }
  };

  // Handle alert protocol
  const handleAlertProtocol = async () => {
    if (!phoneNumber) {
      setShowPhoneInput(true);
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/api/alerts/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          phone: phoneNumber,
          message: `Air Quality Alert: AQI ${aqiData?.aqi} - ${aqiData?.category} at ${aqiData?.lat}, ${aqiData?.lon}`
        }),
      });

      if (response.ok) {
        setNotificationMessage('Alert sent successfully!');
        setTimeout(() => setNotificationMessage(''), 3000);
      }
    } catch (error) {
      console.error('Failed to send alert:', error);
      setNotificationMessage('Failed to send alert');
      setTimeout(() => setNotificationMessage(''), 3000);
    }
  };

  // Handle email subscription
  const handleEmailSubscription = async () => {
    if (!email) return;

    try {
      const response = await fetch('http://localhost:8000/api/alerts/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      if (response.ok) {
        setNotificationMessage('Successfully subscribed to alerts!');
        setTimeout(() => setNotificationMessage(''), 3000);
      }
    } catch (error) {
      console.error('Failed to subscribe:', error);
      setNotificationMessage('Failed to subscribe');
      setTimeout(() => setNotificationMessage(''), 3000);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 text-white">
      {/* Background stars */}
      <div className="fixed inset-0 bg-black opacity-20">
        <div className="absolute inset-0" style={{
          backgroundImage: `radial-gradient(2px 2px at 20px 30px, #eee, transparent),
                           radial-gradient(2px 2px at 40px 70px, rgba(255,255,255,0.8), transparent),
                           radial-gradient(1px 1px at 90px 40px, #fff, transparent),
                           radial-gradient(1px 1px at 130px 80px, rgba(255,255,255,0.6), transparent),
                           radial-gradient(2px 2px at 160px 30px, #ddd, transparent)`,
          backgroundRepeat: 'repeat',
          backgroundSize: '200px 100px'
        }} />
      </div>

      {/* Header */}
      <header className="relative z-10 bg-slate-800/90 backdrop-blur-sm border-b border-blue-500/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-400 to-cyan-400 rounded-lg flex items-center justify-center">
                  <Activity className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-white">NASA</h1>
                  <p className="text-xs text-cyan-400">TEMPO Air Quality</p>
                </div>
              </div>
            </div>

            <div className="hidden md:flex items-center space-x-6">
              <button className="text-white hover:text-cyan-400 transition-colors">Dashboard</button>
              <button className="text-gray-400 hover:text-white transition-colors">Science & Data</button>
              <button className="text-gray-400 hover:text-white transition-colors">Alerts</button>
              <button className="text-gray-400 hover:text-white transition-colors">Profile</button>
            </div>

            <div className="flex items-center space-x-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="Search locations..."
                  className="pl-10 pr-4 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent"
                />
              </div>
              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                className="md:hidden p-2 rounded-lg bg-slate-700/50 hover:bg-slate-600/50 transition-colors"
              >
                <MenuIcon className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10">
        {/* Hero Section */}
        <section className="py-12 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-8">
              <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
                North America Air Quality Monitoring
              </h2>
              <p className="text-xl text-gray-300 mb-8">
                Precision from Orbit
              </p>
              <button
                onClick={handleRealDataToggle}
                className="bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white font-bold py-3 px-8 rounded-lg transition-all duration-300 transform hover:scale-105 shadow-lg"
              >
                {useRealData ? 'Using Real Data' : 'Explore Real-Time Data'}
              </button>
            </div>

            {/* Map Section */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              {/* Map */}
              <div className="lg:col-span-3">
                <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-semibold text-white">Interactive Map</h3>
                    <div className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full ${isBackendAvailable ? 'bg-green-400' : 'bg-red-400'}`} />
                      <span className="text-sm text-gray-400">{connectionStatus}</span>
                    </div>
                  </div>
                  <div className="h-96 rounded-lg overflow-hidden">
                    <Map
                      lat={aqiData?.lat || 34.0522}
                      lon={aqiData?.lon || -118.2437}
                      aqiData={aqiData}
                      onLocationChange={(lat, lon) => {
                        if (useRealData) {
                          fetchRealData(lat, lon);
                        }
                      }}
                    />
                  </div>
                </div>
              </div>

              {/* Sidebar */}
              <div className="lg:col-span-1">
                <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 p-6">
                  <h3 className="text-lg font-semibold text-cyan-400 mb-4">Current AQI</h3>
                  
                  {/* AQI Display */}
                  <div className="text-center mb-6">
                    <div className="text-6xl font-bold mb-2" style={{ color: aqiData?.color || '#ff0000' }}>
                      {aqiData?.aqi || 0}
                    </div>
                    <div className="text-lg text-white font-medium">
                      {aqiData?.category || 'UNKNOWN'}
                    </div>
                  </div>

                  {/* Toggle Switches */}
                  <div className="space-y-4 mb-6">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-300">Pollutant Overlay</span>
                      <button
                        onClick={() => setPollutantDynamics(!pollutantDynamics)}
                        className={`w-12 h-6 rounded-full transition-colors ${
                          pollutantDynamics ? 'bg-cyan-500' : 'bg-gray-600'
                        }`}
                      >
                        <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
                          pollutantDynamics ? 'translate-x-6' : 'translate-x-0.5'
                        }`} />
                      </button>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-300">Atmospheric Dynamics</span>
                      <button
                        onClick={() => setAtmosphericDynamics(!atmosphericDynamics)}
                        className={`w-12 h-6 rounded-full transition-colors ${
                          atmosphericDynamics ? 'bg-cyan-500' : 'bg-gray-600'
                        }`}
                      >
                        <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
                          atmosphericDynamics ? 'translate-x-6' : 'translate-x-0.5'
                        }`} />
                      </button>
                    </div>
                  </div>

                  {/* Atmospheric Composition */}
                  <div className="mb-6">
                    <h4 className="text-sm font-medium text-gray-300 mb-3">Atmospheric Composition</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-xs text-gray-400">O₃</span>
                        <span className="text-sm text-white">{aqiData?.pollutants.o3?.toFixed(1) || 0} ppb</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-xs text-gray-400">NO₂</span>
                        <span className="text-sm text-white">{aqiData?.pollutants.no2?.toFixed(1) || 0} µg/m³</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-xs text-gray-400">PM2.5</span>
                        <span className="text-sm text-white">{aqiData?.pollutants.pm25?.toFixed(1) || 0} µg/m³</span>
                      </div>
                    </div>
                  </div>

                  {/* Time Selector */}
                  <div className="mb-6">
                    <h4 className="text-sm font-medium text-gray-300 mb-3">Time Range</h4>
                    <div className="flex space-x-2">
                      {['Hourly', '24-Hr', '7-Day'].map((period) => (
                        <button
                          key={period}
                          onClick={() => handleTimeframeChange(period.toLowerCase())}
                          className={`px-3 py-1 rounded-full text-xs transition-colors ${
                            timeframe === period.toLowerCase()
                              ? 'bg-cyan-500 text-white'
                              : 'bg-slate-700 text-gray-400 hover:bg-slate-600'
                          }`}
                        >
                          {period}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Alert Button */}
                  <button
                    onClick={handleAlertProtocol}
                    className="w-full bg-red-500 hover:bg-red-600 text-white font-medium py-2 px-4 rounded-lg transition-colors"
                  >
                    Initiate Alert Protocol
                  </button>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Footer Cards */}
        <section className="py-12 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Mission Overview */}
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 p-6">
                <h3 className="text-xl font-semibold text-cyan-400 mb-2">Mission Overview</h3>
                <p className="text-gray-300 mb-4">NASA's TEMPO: A New Frontier in Air Observation</p>
                <button className="text-cyan-400 hover:text-cyan-300 font-medium">
                  Explore the Mission Data →
                </button>
              </div>

              {/* Environmental Intelligence */}
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 p-6">
                <h3 className="text-xl font-semibold text-cyan-400 mb-2">Environmental Intelligence</h3>
                <p className="text-gray-300 mb-4">Understanding Pollutants: Impact & Mitigation Strategies</p>
                <button className="text-cyan-400 hover:text-cyan-300 font-medium">
                  Access Full Research Archive →
                </button>
              </div>

              {/* Subscription Gateway */}
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 p-6">
                <h3 className="text-xl font-semibold text-cyan-400 mb-2">Subscription Gateway</h3>
                <p className="text-gray-300 mb-4">Receive Critical Air Quality Notifications</p>
                <div className="space-y-3">
                  <input
                    type="email"
                    placeholder="your.email@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-400"
                  />
                  <button
                    onClick={handleEmailSubscription}
                    className="w-full bg-cyan-500 hover:bg-cyan-600 text-white font-medium py-2 px-4 rounded-lg transition-colors"
                  >
                    Activate Alerts
                  </button>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Phone Input Modal */}
      {showPhoneInput && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-xl p-6 w-96 max-w-sm mx-4">
            <h3 className="text-lg font-semibold text-white mb-4">Enter Phone Number</h3>
            <input
              type="tel"
              placeholder="+1 (555) 123-4567"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-400 mb-4"
            />
            <div className="flex space-x-3">
              <button
                onClick={() => setShowPhoneInput(false)}
                className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setShowPhoneInput(false);
                  handleAlertProtocol();
                }}
                className="flex-1 bg-cyan-500 hover:bg-cyan-600 text-white font-medium py-2 px-4 rounded-lg transition-colors"
              >
                Send Alert
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Notification Toast */}
      {notificationMessage && (
        <div className="fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50">
          {notificationMessage}
        </div>
      )}
    </div>
  );
}