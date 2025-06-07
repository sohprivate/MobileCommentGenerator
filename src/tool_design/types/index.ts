// 地点データの型定義
export interface Location {
  name: string
  latitude: number
  longitude: number
  area?: string
}

// 座標の型定義
export interface Coordinates {
  latitude: number
  longitude: number
}

// 天気データの型定義
export interface WeatherData {
  location: string
  temperature?: number
  humidity?: number
  windSpeed?: number
  precipitation?: number
  weatherCondition?: string
  timestamp?: string
}

// コメント生成設定の型定義
export interface GenerateSettings {
  method: 'practical' | 'creative' | 'business' | '実例ベース'
  count: number
  includeEmoji: boolean
  includeAdvice: boolean
  politeForm: boolean
  targetTime?: '12h' | '24h'
}

// 生成されたコメントの型定義
export interface GeneratedComment {
  id: string
  text: string
  location?: string
  timestamp: string
  weather?: WeatherData
}

// APIレスポンスの型定義
export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
}

// API エラーの型定義
export interface ApiError {
  message: string
  code?: string
  details?: any
}