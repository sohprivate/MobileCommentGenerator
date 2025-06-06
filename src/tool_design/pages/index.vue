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
        <GenerateSettings 
          :settings="generateSettings"
          @settings-changed="handleSettingsChange"
          @generate="handleGenerate"
        />

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

@media (min-width: 1200px) {
  .content-grid {
    grid-template-columns: 1fr 1fr 1fr;
    grid-template-rows: auto auto;
  }
}


.content-grid > *:nth-child(1),
.content-grid > *:nth-child(2),
.content-grid > *:nth-child(3) {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 600px;
}


.content-grid > *:nth-child(4) {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  min-height: 400px;
}

.location-section {
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(107, 162, 252, 0.2);
  overflow: hidden;
  grid-column: span 2;
}

@media (min-width: 1200px) {
  .location-section {
    grid-column: span 1;
  }
}

.component-header {
  background: linear-gradient(135deg, #0C419A 0%, #6BA2FC 100%);
  color: white;
  padding: 1.5rem 2rem;
  border-bottom: 3px solid #6BA2FC;
}

.component-header h3 {
  font-size: 1.4rem;
  font-weight: 700;
  margin: 0;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
}

.location-content {
  padding: 2rem;
}

/* Responsive Design */
@media (max-width: 1024px) {
  .content-grid {
    grid-template-columns: 1fr 1fr;
    grid-template-rows: auto auto auto;
  }
  
  .content-grid > *:nth-child(3) {
    grid-column: 1 / -1;
  }
}

@media (max-width: 768px) {
  .content-grid {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto auto auto;
    gap: 1.5rem;
  }
  
  .content-grid > *:nth-child(1),
  .content-grid > *:nth-child(2),
  .content-grid > *:nth-child(3) {
    grid-column: 1;
    min-height: 500px;
  }
  
  .content-grid > *:nth-child(4) {
    grid-column: 1;
  }
  
  .app-header h1 {
    font-size: 2rem;
  }
  
  .main-content {
    padding: 1rem;
  }
  
  .location-content {
    padding: 1.5rem;
  }
  
  .component-header {
    padding: 1rem 1.5rem;
  }
  
  .component-header h3 {
    font-size: 1.2rem;
  }
}

@media (max-width: 480px) {
  .app-header {
    padding: 1.5rem 1rem;
  }
  
  .app-header h1 {
    font-size: 1.8rem;
  }
  
  .app-header p {
    font-size: 1rem;
  }
  
  .location-content {
    padding: 1rem;
  }
  
  .dropdown-select {
    font-size: 0.9rem;
    padding: 14px 18px;
  }
  
  .japan-svg {
    height: 200px;
  }
}
</style>