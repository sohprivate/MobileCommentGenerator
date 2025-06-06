<template>
  <div class="weather-data">
    <div class="component-header">
      <h3>天気データ入力</h3>
    </div>
    
    <div class="data-content">
      <!-- Weather Data Source Selection -->
      <div class="data-source-section">
        <h4>データソース選択</h4>
        <div class="custom-dropdown">
          <select 
            :value="weatherDataSource"
            @change="handleDataSourceChange"
            class="dropdown-select"
          >
            <option value="manual">手動入力</option>
            <option value="api">WxTech API</option>
          </select>
          <div class="dropdown-arrow">▼</div>
        </div>
      </div>

      <!-- Coordinates Input -->
      <div class="coordinates-section compact">
        <h4>座標設定</h4>
        <div class="coordinate-inputs compact">
          <div class="input-group">
            <label for="latitude">緯度:</label>
            <div class="coordinate-control compact">
              <button 
                @click="adjustLatitude(-0.01)"
                class="adjust-btn minus compact"
                type="button"
              >
                -
              </button>
              <input
                id="latitude"
                type="number"
                step="0.0001"
                :value="coordinates.latitude"
                @input="handleLatitudeChange"
                class="coordinate-input compact"
                placeholder="35.6762"
                min="-90"
                max="90"
              />
              <button 
                @click="adjustLatitude(0.01)"
                class="adjust-btn plus compact"
                type="button"
              >
                +
              </button>
            </div>
          </div>
          <div class="input-group">
            <label for="longitude">経度:</label>
            <div class="coordinate-control compact">
              <button 
                @click="adjustLongitude(-0.01)"
                class="adjust-btn minus compact"
                type="button"
              >
                -
              </button>
              <input
                id="longitude"
                type="number"
                step="0.0001"
                :value="coordinates.longitude"
                @input="handleLongitudeChange"
                class="coordinate-input compact"
                placeholder="139.6503"
                min="-180"
                max="180"
              />
              <button 
                @click="adjustLongitude(0.01)"
                class="adjust-btn plus compact"
                type="button"
              >
                +
              </button>
            </div>
          </div>
        </div>
        <div v-if="coordinateError" class="error-message">
          {{ coordinateError }}
        </div>
      </div>

      <!-- Weather API Settings -->
      <div class="api-section">
        <h4>気象データAPI</h4>
        <div class="api-info">
          <div class="api-item">
            <span class="api-label">API:</span>
            <span class="api-value">WxTech API</span>
            <span class="api-status" :class="{ connected: !loading && !error, error: error }">
              {{ loading ? '読込中...' : error ? 'エラー' : '接続済み' }}
            </span>
          </div>
          <div v-if="weatherDataSource === 'api'" class="api-controls">
            <button 
              @click="fetchWeatherData" 
              class="fetch-btn"
              :disabled="loading"
            >
              {{ loading ? '取得中...' : '最新データを取得' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Weather Information Display -->
      <div v-if="weatherData" class="weather-info">
        <h4>取得した天気データ</h4>
        <div class="weather-details">
          <div class="weather-item">
            <span class="weather-label">地点:</span>
            <span class="weather-value">{{ weatherData.location || '不明' }}</span>
          </div>
          <div v-if="weatherData.temperature !== undefined" class="weather-item">
            <span class="weather-label">気温:</span>
            <span class="weather-value">{{ weatherData.temperature }}°C</span>
          </div>
          <div v-if="weatherData.humidity !== undefined" class="weather-item">
            <span class="weather-label">湿度:</span>
            <span class="weather-value">{{ weatherData.humidity }}%</span>
          </div>
          <div v-if="weatherData.windSpeed !== undefined" class="weather-item">
            <span class="weather-label">風速:</span>
            <span class="weather-value">{{ weatherData.windSpeed }}m/s</span>
          </div>
          <div v-if="weatherData.weatherCondition" class="weather-item">
            <span class="weather-label">天気:</span>
            <span class="weather-value">{{ weatherData.weatherCondition }}</span>
          </div>
        </div>
      </div>

      <!-- Manual Weather Entry (when manual mode) -->
      <div v-if="weatherDataSource === 'manual'" class="manual-entry">
        <h4>手動天気データ入力</h4>
        <div class="manual-form">
          <div class="form-group">
            <label for="manual-temp">気温 (°C):</label>
            <input
              id="manual-temp"
              type="number"
              v-model.number="manualWeatherData.temperature"
              @input="updateManualData"
              class="form-input"
              step="0.1"
            />
          </div>
          <div class="form-group">
            <label for="manual-humidity">湿度 (%):</label>
            <input
              id="manual-humidity"
              type="number"
              v-model.number="manualWeatherData.humidity"
              @input="updateManualData"
              class="form-input"
              min="0"
              max="100"
            />
          </div>
          <div class="form-group">
            <label for="manual-wind">風速 (m/s):</label>
            <input
              id="manual-wind"
              type="number"
              v-model.number="manualWeatherData.windSpeed"
              @input="updateManualData"
              class="form-input"
              step="0.1"
              min="0"
            />
          </div>
          <div class="form-group">
            <label for="manual-condition">天気状況:</label>
            <select
              id="manual-condition"
              v-model="manualWeatherData.weatherCondition"
              @change="updateManualData"
              class="form-input"
            >
              <option value="">選択してください</option>
              <option value="晴れ">晴れ</option>
              <option value="曇り">曇り</option>
              <option value="雨">雨</option>
              <option value="雪">雪</option>
              <option value="霧">霧</option>
              <option value="雷雨">雷雨</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, defineProps, defineEmits } from 'vue'
import type { Coordinates, WeatherData } from '~/types'

// Props
interface Props {
  coordinates: Coordinates
  weatherDataSource: 'manual' | 'api'
  loading?: boolean
  weatherData?: WeatherData | null
}

const props = defineProps<Props>()

// Emits
interface Emits {
  (e: 'coordinates-changed', coordinates: Coordinates): void
  (e: 'data-source-changed', source: 'manual' | 'api'): void
  (e: 'fetch-weather'): void
  (e: 'manual-weather-changed', data: WeatherData): void
}

const emit = defineEmits<Emits>()

// State
const error = ref<string | null>(null)
const coordinateError = ref<string | null>(null)
const manualWeatherData = ref<WeatherData>({
  location: '手動入力',
  temperature: undefined,
  humidity: undefined,
  windSpeed: undefined,
  weatherCondition: '',
  timestamp: new Date().toISOString()
})

// Validation
const isValidLatitude = (lat: number): boolean => lat >= -90 && lat <= 90
const isValidLongitude = (lng: number): boolean => lng >= -180 && lng <= 180

// Methods
const handleDataSourceChange = (event: Event) => {
  const target = event.target as HTMLSelectElement
  emit('data-source-changed', target.value as 'manual' | 'api')
}

const handleLatitudeChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  const value = parseFloat(target.value)
  
  if (isNaN(value)) {
    coordinateError.value = '緯度は数値で入力してください'
    return
  }
  
  if (!isValidLatitude(value)) {
    coordinateError.value = '緯度は-90から90の範囲で入力してください'
    return
  }
  
  coordinateError.value = null
  emit('coordinates-changed', {
    ...props.coordinates,
    latitude: value
  })
}

const handleLongitudeChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  const value = parseFloat(target.value)
  
  if (isNaN(value)) {
    coordinateError.value = '経度は数値で入力してください'
    return
  }
  
  if (!isValidLongitude(value)) {
    coordinateError.value = '経度は-180から180の範囲で入力してください'
    return
  }
  
  coordinateError.value = null
  emit('coordinates-changed', {
    ...props.coordinates,
    longitude: value
  })
}

const adjustLatitude = (delta: number) => {
  const newLatitude = props.coordinates.latitude + delta
  if (isValidLatitude(newLatitude)) {
    emit('coordinates-changed', {
      ...props.coordinates,
      latitude: Math.round(newLatitude * 10000) / 10000
    })
  }
}

const adjustLongitude = (delta: number) => {
  const newLongitude = props.coordinates.longitude + delta
  if (isValidLongitude(newLongitude)) {
    emit('coordinates-changed', {
      ...props.coordinates,
      longitude: Math.round(newLongitude * 10000) / 10000
    })
  }
}

const fetchWeatherData = () => {
  emit('fetch-weather')
}

const updateManualData = () => {
  emit('manual-weather-changed', {
    ...manualWeatherData.value,
    timestamp: new Date().toISOString()
  })
}

// Watch for errors in props
watch(() => props.weatherData, (newData) => {
  if (newData && 'error' in newData) {
    error.value = '天気データの取得に失敗しました'
  } else {
    error.value = null
  }
})
</script>

<style scoped>
.weather-data {
  background: linear-gradient(135deg, #FEF3E8 0%, #FFF8F3 100%);
  border-radius: 16px;
  padding: 0;
  box-shadow: 0 4px 12px rgba(252, 128, 11, 0.1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.component-header {
  background: linear-gradient(135deg, #FC800B 0%, #FFB366 100%);
  color: white;
  padding: 1.5rem 2rem;
  border-bottom: 3px solid #FFB366;
}

.component-header h3 {
  font-size: 1.4rem;
  font-weight: 700;
  margin: 0;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
}

.data-content {
  padding: 2rem;
  overflow-y: auto;
  flex: 1;
}

.data-source-section, .coordinates-section, .api-section, .weather-info, .manual-entry {
  margin-bottom: 2rem;
}

.data-source-section h4, .coordinates-section h4, .api-section h4, .weather-info h4, .manual-entry h4 {
  color: #FC800B;
  font-weight: 600;
  margin-bottom: 1rem;
  font-size: 1.1rem;
}

.custom-dropdown {
  position: relative;
  width: 100%;
}

.dropdown-select {
  width: 100%;
  padding: 16px 20px;
  padding-right: 40px;
  font-size: 1rem;
  border: 2px solid #FEF3E8;
  border-radius: 12px;
  background: white;
  appearance: none;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(252, 128, 11, 0.05);
}

.dropdown-select:hover {
  border-color: #FFB366;
  box-shadow: 0 4px 12px rgba(255, 179, 102, 0.2);
}

.dropdown-select:focus {
  outline: none;
  border-color: #FC800B;
  box-shadow: 0 0 0 3px rgba(252, 128, 11, 0.1);
}

.dropdown-arrow {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
  color: #FFB366;
  font-size: 0.8rem;
}

/* Compact coordinate inputs */
.coordinates-section.compact {
  margin-bottom: 1.5rem;
}

.coordinate-inputs.compact {
  display: flex;
  gap: 1.5rem;
  align-items: flex-start;
}

.input-group {
  flex: 1;
}

.input-group label {
  display: block;
  font-weight: 500;
  color: #374151;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.coordinate-control.compact {
  display: flex;
  align-items: center;
  gap: 0;
  background: white;
  border-radius: 10px;
  border: 2px solid #FEF3E8;
  overflow: hidden;
  transition: all 0.3s ease;
}

.coordinate-control.compact:hover {
  border-color: #FFB366;
  box-shadow: 0 2px 8px rgba(255, 179, 102, 0.2);
}

.coordinate-control.compact:focus-within {
  border-color: #FC800B;
  box-shadow: 0 0 0 3px rgba(252, 128, 11, 0.1);
}

.coordinate-input.compact {
  flex: 1;
  padding: 12px 16px;
  font-size: 0.95rem;
  border: none;
  background: transparent;
  text-align: center;
  -moz-appearance: textfield;
}

.coordinate-input.compact::-webkit-inner-spin-button,
.coordinate-input.compact::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.coordinate-input.compact:focus {
  outline: none;
}

.adjust-btn.compact {
  padding: 12px 18px;
  background: transparent;
  border: none;
  font-size: 1.2rem;
  font-weight: 600;
  color: #6B7280;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.adjust-btn.compact:hover {
  background: #FEF3E8;
  color: #FC800B;
}

.adjust-btn.compact:active {
  background: #FC800B;
  color: white;
}

.adjust-btn.minus.compact {
  border-right: 1px solid #E5E7EB;
}

.adjust-btn.plus.compact {
  border-left: 1px solid #E5E7EB;
}

/* API Section */
.api-info {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  border: 2px solid #FEF3E8;
  box-shadow: 0 2px 8px rgba(252, 128, 11, 0.05);
}

.api-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.5rem;
}

.api-item:last-child {
  margin-bottom: 0;
}

.api-label {
  font-weight: 600;
  color: #374151;
  min-width: 80px;
}

.api-value {
  flex: 1;
  color: #6B7280;
}

.api-status {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
}

.api-status.connected {
  background: #D1FAE5;
  color: #065F46;
}

.api-status.error {
  background: #FEE2E2;
  color: #991B1B;
}

.api-controls {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #E5E7EB;
}

.fetch-btn {
  width: 100%;
  padding: 12px 20px;
  background: linear-gradient(135deg, #FC800B 0%, #FFB366 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(252, 128, 11, 0.2);
}

.fetch-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(252, 128, 11, 0.3);
}

.fetch-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Error message */
.error-message {
  color: #dc3545;
  font-size: 0.85rem;
  margin-top: 0.5rem;
}

/* Weather info display */
.weather-info {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  border: 2px solid #FEF3E8;
  box-shadow: 0 2px 8px rgba(252, 128, 11, 0.05);
}

.weather-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.weather-item {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid #E5E7EB;
}

.weather-label {
  font-weight: 600;
  color: #374151;
}

.weather-value {
  color: #6B7280;
}

/* Manual entry form */
.manual-form {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  font-weight: 500;
  color: #374151;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.form-input {
  padding: 12px 16px;
  border: 2px solid #FEF3E8;
  border-radius: 10px;
  font-size: 0.95rem;
  transition: all 0.3s ease;
}

.form-input:focus {
  outline: none;
  border-color: #FC800B;
  box-shadow: 0 0 0 3px rgba(252, 128, 11, 0.1);
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .coordinate-inputs.compact {
    flex-direction: column;
    gap: 1rem;
  }
  
  .input-group {
    width: 100%;
  }
  
  .manual-form {
    grid-template-columns: 1fr;
  }
}
</style>