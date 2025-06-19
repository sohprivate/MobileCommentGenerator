// 既存のNuxt.js版と共通の型定義
export interface Location {
  id: string;
  name: string;
  prefecture: string;
  region: string;
  latitude?: number;
  longitude?: number;
}

export interface GenerateSettings {
  location: Location;
  llmProvider: 'openai' | 'gemini' | 'anthropic';
  temperature?: number;
  targetDateTime?: string;
}

export interface GeneratedComment {
  id: string;
  comment: string;
  adviceComment?: string;
  weather: WeatherData;
  timestamp: string;
  confidence: number;
  location: Location;
  settings: GenerateSettings;
}

export interface WeatherData {
  current: CurrentWeather;
  forecast: ForecastWeather[];
  trend?: WeatherTrend;
}

export interface CurrentWeather {
  temperature: number;
  humidity: number;
  pressure: number;
  windSpeed: number;
  windDirection: string;
  description: string;
  icon: string;
}

export interface ForecastWeather {
  datetime: string;
  temperature: {
    min: number;
    max: number;
  };
  humidity: number;
  precipitation: number;
  description: string;
  icon: string;
}

export interface WeatherTrend {
  trend: 'improving' | 'worsening' | 'stable';
  confidence: number;
  description: string;
}