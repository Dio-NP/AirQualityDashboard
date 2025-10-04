// WebSocket service for real-time data updates
export class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private onDataCallback: ((data: any) => void) | null = null;
  private onStatusCallback: ((status: 'connected' | 'disconnected' | 'error') => void) | null = null;

  constructor(private url: string = 'ws://localhost:8000/ws/alerts') {}

  connect() {
    try {
      this.ws = new WebSocket(this.url);
      
      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.onStatusCallback?.('connected');
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.onDataCallback?.(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.onStatusCallback?.('disconnected');
        this.attemptReconnect();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.onStatusCallback?.('error');
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.attemptReconnect();
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        this.connect();
      }, this.reconnectDelay * this.reconnectAttempts);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  onData(callback: (data: any) => void) {
    this.onDataCallback = callback;
  }

  onStatus(callback: (status: 'connected' | 'disconnected' | 'error') => void) {
    this.onStatusCallback = callback;
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket is not connected');
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// Fallback polling service when WebSocket is not available
export class PollingService {
  private intervalId: NodeJS.Timeout | null = null;
  private onDataCallback: ((data: any) => void) | null = null;

  constructor(private apiClient: any) {}

  start(intervalMs: number = 5000) {
    this.stop(); // Stop any existing polling
    
    this.intervalId = setInterval(async () => {
      try {
        // Poll for new data
        const data = await this.apiClient.getAQIData(34.0522, -118.2437, 24);
        this.onDataCallback?.(data);
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, intervalMs);
  }

  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  onData(callback: (data: any) => void) {
    this.onDataCallback = callback;
  }
}
