import type { 
  Location, 
  WeatherData, 
  GenerateSettings, 
  GeneratedComment, 
  ApiResponse,
  Coordinates 
} from '~/types'

export const useApi = () => {
  const config = useRuntimeConfig()
  const baseURL = config.public.apiBaseUrl || 'http://localhost:8000'

  // 共通のエラーハンドリング
  const handleApiError = (error: any): ApiResponse<any> => {
    console.error('API Error:', error)
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'API通信エラーが発生しました'
    }
  }

  // 地点データを取得
  const fetchLocations = async (): Promise<ApiResponse<Location[]>> => {
    try {
      const response = await $fetch<Location[]>(`${baseURL}/api/locations`)
      return {
        success: true,
        data: response
      }
    } catch (error) {
      return handleApiError(error)
    }
  }

  // 天気データを取得
  const fetchWeatherData = async (coordinates: Coordinates, targetTime: '12h' | '24h' = '12h'): Promise<ApiResponse<WeatherData>> => {
    try {
      const response = await $fetch<WeatherData>(`${baseURL}/api/weather`, {
        method: 'POST',
        body: {
          latitude: coordinates.latitude,
          longitude: coordinates.longitude,
          target_time: targetTime
        }
      })
      return {
        success: true,
        data: response
      }
    } catch (error) {
      return handleApiError(error)
    }
  }

  // コメントを生成
  const generateComments = async (
    locations: string[],
    settings: GenerateSettings,
    weatherData?: WeatherData
  ): Promise<ApiResponse<GeneratedComment[]>> => {
    try {
      const response = await $fetch<GeneratedComment[]>(`${baseURL}/api/generate-comments`, {
        method: 'POST',
        body: {
          locations,
          settings: {
            method: settings.method,
            count: settings.count,
            include_emoji: settings.includeEmoji,
            include_advice: settings.includeAdvice,
            polite_form: settings.politeForm,
            target_time: settings.targetTime || '12h'
          },
          weather_data: weatherData
        }
      })
      return {
        success: true,
        data: response
      }
    } catch (error) {
      return handleApiError(error)
    }
  }

  // バックエンドのヘルスチェック
  const checkHealth = async (): Promise<boolean> => {
    try {
      await $fetch(`${baseURL}/health`)
      return true
    } catch {
      return false
    }
  }

  return {
    fetchLocations,
    fetchWeatherData,
    generateComments,
    checkHealth
  }
}