// types/index.ts - TypeScript type definitions

export interface Location {
  name: string
  latitude: number
  longitude: number
  area?: string
}

export interface Coordinates {
  latitude: number
  longitude: number
}

export interface GenerateSettings {
  method: string
  count: number
  includeEmoji: boolean
  includeAdvice: boolean
  politeForm: boolean
  targetTime: string
}

export interface GeneratedComment {
  id: string
  location: string
  comment: string
  timestamp: string
  score?: number
}

export interface WeatherData {
  temperature: number
  condition: string
  humidity: number
  windSpeed: number
  timestamp: string
}

export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
}

// Workflow related types
export interface WorkflowStatus {
  available: boolean
  version: string
  lastUpdate: string
}