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

  // コメントを生成 - ワークフロー統合
  const generateComments = async (
    locations: string[],
    settings: GenerateSettings,
    weatherData?: WeatherData
  ): Promise<ApiResponse<GeneratedComment[]>> => {
    try {
      // 新しいワークフロー統合エンドポイントを使用
      const response = await $fetch<{
        success: boolean;
        final_comment: string;
        generation_metadata: any;
        error?: string;
      }>(`${baseURL}/api/generate-comment`, {
        method: 'POST',
        body: {
          location_name: locations[0] || '東京', // 現在は単一地点に対応
          target_datetime: new Date().toISOString(),
          llm_provider: settings.method === '実例ベース' ? 'openai' : 'gemini',
          generation_settings: {
            include_emoji: settings.includeEmoji,
            include_advice: settings.includeAdvice,
            polite_form: settings.politeForm,
            comment_count: settings.count
          },
          weather_data: weatherData
        }
      })
      
      // ワークフローレスポンスを GeneratedComment 形式に変換
      if (response.success && response.final_comment) {
        const generatedComments: GeneratedComment[] = [{
          id: Date.now().toString(),
          text: response.final_comment,
          location: locations[0] || '東京',
          timestamp: new Date().toISOString(),
          weather_condition: response.generation_metadata?.weather_condition || '不明',
          method: settings.method,
          metadata: response.generation_metadata || {}
        }]
        
        return {
          success: true,
          data: generatedComments
        }
      } else {
        return {
          success: false,
          error: response.error || 'コメント生成に失敗しました'
        }
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

  // ワークフロー統合のステータス確認
  const checkWorkflowIntegration = async (): Promise<ApiResponse<boolean>> => {
    try {
      const response = await $fetch<{status: string, workflow_available: boolean}>(`${baseURL}/api/workflow/status`)
      return {
        success: true,
        data: response.workflow_available
      }
    } catch (error) {
      return handleApiError(error)
    }
  }

  return {
    fetchLocations,
    fetchWeatherData,
    generateComments,
    checkHealth,
    checkWorkflowIntegration
  }
}
