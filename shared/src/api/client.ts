import axios, { AxiosInstance } from 'axios';
import type { Location, GenerateSettings, GeneratedComment, WeatherData } from '../types';

export class ApiClient {
  private client: AxiosInstance;

  constructor(baseURL?: string) {
    // APIサーバーは8000番ポートで起動
    const apiUrl = baseURL || process.env.NUXT_PUBLIC_API_URL || process.env.VITE_API_URL || 'http://localhost:8000';
    
    this.client = axios.create({
      baseURL: apiUrl,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    this.client.interceptors.request.use(
      (config) => {
        console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => Promise.reject(error)
    );

    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('[API Error]', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  async getLocations(): Promise<Location[]> {
    const response = await this.client.get('/api/locations');
    return response.data;
  }

  async generateComment(settings: GenerateSettings): Promise<GeneratedComment> {
    const response = await this.client.post('/api/generate', settings);
    return response.data;
  }

  async getHistory(limit: number = 10): Promise<GeneratedComment[]> {
    const response = await this.client.get('/api/history', {
      params: { limit },
    });
    return response.data;
  }

  async getWeatherData(locationId: string): Promise<WeatherData> {
    const response = await this.client.get(`/api/weather/${locationId}`);
    return response.data;
  }
}

export const createApiClient = (baseURL?: string) => new ApiClient(baseURL);