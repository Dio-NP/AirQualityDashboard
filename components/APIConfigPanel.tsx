'use client';

import React, { useState } from 'react';
import { Settings, CheckCircle, AlertCircle } from 'lucide-react';

interface APIConfigPanelProps {
  apiKeys: {
    airnow: string;
    openweather: string;
    nasa: string;
  };
  onApiKeysChange: (keys: { airnow: string; openweather: string; nasa: string }) => void;
  isBackendAvailable: boolean;
}

export default function APIConfigPanel({ apiKeys, onApiKeysChange, isBackendAvailable }: APIConfigPanelProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [tempKeys, setTempKeys] = useState(apiKeys);

  const handleSave = () => {
    onApiKeysChange(tempKeys);
    setIsOpen(false);
  };

  const getAPIStatus = (key: string) => {
    if (!key) return { status: 'missing', icon: AlertCircle, color: 'text-red-500' };
    return { status: 'configured', icon: CheckCircle, color: 'text-green-500' };
  };

  return (
    <div>
      {/* Config Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="flex items-center space-x-2 px-3 py-1 rounded text-sm font-medium bg-gray-600 text-gray-300 hover:bg-gray-500 transition-colors"
      >
        <Settings className="w-4 h-4" />
        <span>API Config</span>
      </button>

      {/* Modal */}
      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">API Configuration</h3>
              <button
                onClick={() => setIsOpen(false)}
                className="text-gray-400 hover:text-white text-xl"
              >
                ×
              </button>
            </div>

            <div className="space-y-4">
              {/* Backend Status */}
              <div className="flex items-center space-x-2 p-3 bg-gray-700 rounded-lg">
                <div className={`w-2 h-2 rounded-full ${isBackendAvailable ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-sm text-gray-300">
                  Backend API: {isBackendAvailable ? 'Connected' : 'Not Available'}
                </span>
              </div>

              {/* API Keys */}
              <div className="space-y-3">
                <h4 className="text-sm font-medium text-gray-300">External API Keys (Optional)</h4>
                
                {/* AirNow API */}
                <div>
                  <label className="block text-xs text-gray-400 mb-1">AirNow API Key</label>
                  <div className="flex items-center space-x-2">
                    <input
                      type="password"
                      value={tempKeys.airnow}
                      onChange={(e) => setTempKeys({...tempKeys, airnow: e.target.value})}
                      className="flex-1 bg-gray-700 text-white px-3 py-2 rounded border border-gray-600 focus:border-blue-500 focus:outline-none text-sm"
                      placeholder="Get from airnowapi.org"
                    />
                    {getAPIStatus(tempKeys.airnow).icon && (
                      <div className={`w-4 h-4 ${getAPIStatus(tempKeys.airnow).color}`}>
                        {React.createElement(getAPIStatus(tempKeys.airnow).icon, { className: "w-4 h-4" })}
                      </div>
                    )}
                  </div>
                </div>

                {/* OpenWeather API */}
                <div>
                  <label className="block text-xs text-gray-400 mb-1">OpenWeather API Key</label>
                  <div className="flex items-center space-x-2">
                    <input
                      type="password"
                      value={tempKeys.openweather}
                      onChange={(e) => setTempKeys({...tempKeys, openweather: e.target.value})}
                      className="flex-1 bg-gray-700 text-white px-3 py-2 rounded border border-gray-600 focus:border-blue-500 focus:outline-none text-sm"
                      placeholder="Get from openweathermap.org"
                    />
                    {getAPIStatus(tempKeys.openweather).icon && (
                      <div className={`w-4 h-4 ${getAPIStatus(tempKeys.openweather).color}`}>
                        {React.createElement(getAPIStatus(tempKeys.openweather).icon, { className: "w-4 h-4" })}
                      </div>
                    )}
                  </div>
                </div>

                {/* NASA API */}
                <div>
                  <label className="block text-xs text-gray-400 mb-1">NASA Earthdata Token</label>
                  <div className="flex items-center space-x-2">
                    <input
                      type="password"
                      value={tempKeys.nasa}
                      onChange={(e) => setTempKeys({...tempKeys, nasa: e.target.value})}
                      className="flex-1 bg-gray-700 text-white px-3 py-2 rounded border border-gray-600 focus:border-blue-500 focus:outline-none text-sm"
                      placeholder="Get from earthdata.nasa.gov"
                    />
                    {getAPIStatus(tempKeys.nasa).icon && (
                      <div className={`w-4 h-4 ${getAPIStatus(tempKeys.nasa).color}`}>
                        {React.createElement(getAPIStatus(tempKeys.nasa).icon, { className: "w-4 h-4" })}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Instructions */}
              <div className="text-xs text-gray-400 space-y-1">
                <p><strong>How to get API keys:</strong></p>
                <p>• AirNow: Free at airnowapi.org</p>
                <p>• OpenWeather: Free at openweathermap.org</p>
                <p>• NASA: Free at earthdata.nasa.gov</p>
              </div>

              {/* Buttons */}
              <div className="flex space-x-3 pt-4">
                <button
                  onClick={handleSave}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 rounded font-medium transition-colors"
                >
                  Save Configuration
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  className="flex-1 bg-gray-600 hover:bg-gray-700 text-white py-2 rounded font-medium transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}