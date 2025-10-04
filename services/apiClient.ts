// API Client for real data integration
export class APIClient {
  private baseURL: string;
  private apiKey: string | null = null;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.baseURL = baseURL;
  }

  // Set API key for authenticated requests
  setApiKey(key: string) {
    this.apiKey = key;
  }

  // Get headers for API requests
  private getHeaders() {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }
    
    return headers;
  }

  // Check if backend API is available
  async checkHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseURL}/api/health`);
      return response.ok;
    } catch {
      return false;
    }
  }

  // Get real AQI data from backend
  async getAQIData(lat: number, lon: number, hours: number = 24) {
    try {
      const response = await fetch(
        `${this.baseURL}/api/forecast/timeline?lat=${lat}&lon=${lon}&hours=${hours}`,
        { headers: this.getHeaders() }
      );
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch AQI data:', error);
      throw error;
    }
  }

  // Ingest real data from various sources
  async ingestData(source: 'openaq' | 'tempo' | 'imerg' | 'pandora', params?: any) {
    try {
      const response = await fetch(`${this.baseURL}/api/ingest/${source}`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(params || {})
      });
      
      if (!response.ok) {
        throw new Error(`Ingestion failed: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`Failed to ingest ${source} data:`, error);
      throw error;
    }
  }

  // Get real-time alerts
  async getAlerts() {
    try {
      const response = await fetch(`${this.baseURL}/api/alerts/sms`, {
        headers: this.getHeaders()
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch alerts: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
      throw error;
    }
  }

  // Create SMS alert
  async createSMSAlert(alertData: {
    phone: string;
    lat: number;
    lon: number;
    threshold_aqi: number;
    hours_ahead: number;
  }) {
    try {
      const response = await fetch(`${this.baseURL}/api/alerts/sms`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(alertData)
      });
      
      if (!response.ok) {
        throw new Error(`Failed to create alert: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to create SMS alert:', error);
      throw error;
    }
  }
}

// Direct API calls to external services (if backend is not available)
export class DirectAPIClient {
  // OpenAQ API (free, no authentication required)
  static async getOpenAQData(country?: string, parameter?: string, limit: number = 1000) {
    try {
      const params = new URLSearchParams();
      if (country) params.append('country', country);
      if (parameter) params.append('parameter', parameter);
      params.append('limit', limit.toString());
      
      const response = await fetch(`https://api.openaq.org/v2/measurements?${params}`);
      
      if (!response.ok) {
        throw new Error(`OpenAQ API Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch OpenAQ data:', error);
      throw error;
    }
  }

  // AirNow API (requires API key)
  static async getAirNowData(lat: number, lon: number, apiKey: string) {
    try {
      const response = await fetch(
        `https://www.airnowapi.org/aq/observation/latLong/?format=application/json&latitude=${lat}&longitude=${lon}&API_KEY=${apiKey}`
      );
      
      if (!response.ok) {
        throw new Error(`AirNow API Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch AirNow data:', error);
      throw error;
    }
  }

  // Weather API (OpenWeatherMap - requires API key)
  static async getWeatherData(lat: number, lon: number, apiKey: string) {
    try {
      const response = await fetch(
        `https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lon}&appid=${apiKey}&units=metric`
      );
      
      if (!response.ok) {
        throw new Error(`Weather API Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch weather data:', error);
      throw error;
    }
  }
}
