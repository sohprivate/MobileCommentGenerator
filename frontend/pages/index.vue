<template>
  <div class="weather-app">
    <!-- Page Header -->
    <header class="app-header">
      <h1>MobileSlack天気コメント</h1>
      <p>天気データからSlack用コメントを自動生成</p>
    </header>

    <!-- Main Content Grid -->
    <main class="main-content">
      <div class="content-grid">
        <!-- Location Selection Section -->
        <LocationSelection 
          :selected-location="selectedLocation"
          @location-changed="handleLocationChange"
          @locations-changed="handleLocationsChange"
        />

        <WeatherData 
          :coordinates="coordinates"
          :weather-data-source="weatherDataSource"
          :loading="isLoadingWeather"
          :weather-data="currentWeatherData"
          @coordinates-changed="handleCoordinatesChange"
          @data-source-changed="handleWeatherDataSourceChange"
          @fetch-weather="handleFetchWeather"
        />

        <!-- Generate Settings -->
        <!-- Comment Generation Button -->
        <div class="generate-section">
          <h3>コメント生成</h3>
          <button 
            @click="handleGenerate"
            :disabled="isGenerating || selectedLocations.length === 0"
            class="generate-button"
          >
            {{ isGenerating ? '生成中...' : 'コメントを生成' }}
          </button>
          <p class="generate-info">過去コメントの組み合わせで自動生成（16字以内）</p>
        </div>

        <GeneratedComment 
          :comments="generatedComments"
          :is-loading="isGenerating"
          :error="error"
          @regenerate="handleGenerate"
          @clear="handleClear"
        />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useApi } from '~/composables/useApi'
import type { 
  Location, 
  Coordinates, 
  GenerateSettings, 
  GeneratedComment,
  WeatherData 
} from '~/types'

// API composable
const api = useApi()

// State management
const weatherDataSource = ref<'manual' | 'api'>('manual')
const coordinates = ref<Coordinates>({
  latitude: 35.6762,
  longitude: 139.6503
})
const generateSettings = ref<GenerateSettings>({
  method: '実例ベース',
  count: 5,
  includeEmoji: true,
  includeAdvice: false,
  politeForm: true,
  targetTime: '12h'
})
const generatedComments = ref<GeneratedComment[]>([])
const isGenerating = ref(false)
const isLoadingWeather = ref(false)
const selectedLocations = ref<string[]>([])
const selectedLocation = ref<string>('')
const currentWeatherData = ref<WeatherData | null>(null)
const error = ref<string | null>(null)

// API health check on mount
onMounted(async () => {
  const isHealthy = await api.checkHealth()
  if (!isHealthy) {
    console.warn('Backend API is not available. Some features may not work.')
  }
})

// Handler for single location selection change
const handleLocationChange = (location: string) => {
  selectedLocation.value = location
  selectedLocations.value = [location]
}

// Handler for multiple locations selection changes
const handleLocationsChange = (locations: string[]) => {
  selectedLocations.value = locations
  if (locations.length > 0) {
    selectedLocation.value = locations[0]
  }
}

const handleWeatherDataSourceChange = (newSource: 'manual' | 'api') => {
  weatherDataSource.value = newSource
}

const handleCoordinatesChange = (newCoords: Coordinates) => {
  coordinates.value = newCoords
}

const handleSettingsChange = (newSettings: GenerateSettings) => {
  generateSettings.value = newSettings
}

// Fetch weather data from API
const handleFetchWeather = async () => {
  if (weatherDataSource.value !== 'api') return
  
  isLoadingWeather.value = true
  error.value = null
  
  try {
    const response = await api.fetchWeatherData(
      coordinates.value, 
      generateSettings.value.targetTime
    )
    
    if (response.success && response.data) {
      currentWeatherData.value = response.data
    } else {
      error.value = response.error || '天気データの取得に失敗しました'
    }
  } catch (err) {
    error.value = '天気データの取得中にエラーが発生しました'
    console.error('Weather fetch error:', err)
  } finally {
    isLoadingWeather.value = false
  }
}

// Generate comments using API
const handleGenerate = async () => {
  isGenerating.value = true
  error.value = null
  
  try {
    // 天気データが必要な場合は先に取得
    if (weatherDataSource.value === 'api' && !currentWeatherData.value) {
      await handleFetchWeather()
    }
    
    const response = await api.generateComments(
      selectedLocations.value.length > 0 ? selectedLocations.value : [selectedLocation.value || '東京'],
      generateSettings.value,
      currentWeatherData.value || undefined
    )
    
    if (response.success && response.data) {
      generatedComments.value = response.data
    } else {
      error.value = response.error || 'コメント生成に失敗しました'
    }
  } catch (err) {
    error.value = 'コメント生成中にエラーが発生しました'
    console.error('Generate error:', err)
  } finally {
    isGenerating.value = false
  }
}

const handleClear = () => {
  generatedComments.value = []
  error.value = null
  currentWeatherData.value = null
}
</script>

<style scoped>
.weather-app {
  min-height: 100vh;
  background: white;
}

.app-header {
  background: #0C419A;
  color: white;
  text-align: center;
  padding: 2rem 1rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.app-header h1 {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.app-header p {
  font-size: 1.1rem;
  opacity: 0.9;
}

.main-content {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: auto auto;
  gap: 2rem;
  align-items: stretch;
  min-height: calc(100vh - 200px); /* Account for header height */
}

/* Generate section styles */
.generate-section {
  background: #ffffff;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.generate-section h3 {
  color: #0C419A;
  margin-bottom: 1rem;
  font-size: 1.25rem;
  font-weight: 600;
}

.generate-button {
  width: 100%;
  padding: 1rem 2rem;
  background: #0C419A;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.generate-button:hover:not(:disabled) {
  background: #0a356d;
  transform: translateY(-1px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.generate-button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.generate-info {
  margin-top: 0.5rem;
  color: #666;
  font-size: 0.9rem;
  text-align: center;
}

/* Component styles continue... */
</style>