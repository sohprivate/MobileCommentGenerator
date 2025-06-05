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
            <option value="手動入力">手動入力</option>
            <option value="サンプルデータ">サンプルデータ</option>
            <option value="実況データ(WxTech API)">実況データ(WxTech API)</option>
            <option value="予報データ(WxTech API)">予報データ(WxTech API)</option>
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
      </div>

      <!-- Weather API Settings -->
      <div class="api-section">
        <h4>気象データAPI</h4>
        <div class="api-info">
          <div class="api-item">
            <span class="api-label">API:</span>
            <span class="api-value">WxtechAPI</span>
            <span class="api-status connected">接続済み</span>
          </div>
          <div class="api-item">
            <span class="api-label">更新間隔:</span>
            <span class="api-value">1時間毎</span>
          </div>
        </div>
      </div>

      <!-- Current Weather Preview -->
      <div class="weather-preview">
        <h4>現在の天気データ</h4>
        <div class="weather-grid">
          <div class="weather-item">
            <span class="weather-icon">🌡️</span>
            <div class="weather-details">
              <span class="weather-label">気温</span>
              <span class="weather-value">{{ currentWeather.temperature }}°C</span>
            </div>
          </div>
          <div class="weather-item">
            <span class="weather-icon">💧</span>
            <div class="weather-details">
              <span class="weather-label">湿度</span>
              <span class="weather-value">{{ currentWeather.humidity }}%</span>
            </div>
          </div>
          <div class="weather-item">
            <span class="weather-icon">🌬️</span>
            <div class="weather-details">
              <span class="weather-label">風速</span>
              <span class="weather-value">{{ currentWeather.windSpeed }}m/s</span>
            </div>
          </div>
          <div class="weather-item">
            <span class="weather-icon">☁️</span>
            <div class="weather-details">
              <span class="weather-label">天候</span>
              <span class="weather-value">{{ currentWeather.condition }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Content spacer to push button to bottom -->
      <div class="content-spacer"></div>

      <!-- Fetch Data Button -->
      <div class="button-container">
        <button 
          @click="fetchWeatherData"
          :disabled="isLoading"
          class="fetch-weather-button"
        >
          <span class="button-icon"></span>
          <span v-if="isLoading">データ取得中...</span>
          <span v-else>実況データを取得</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  coordinates: {
    type: Object,
    default: () => ({
      latitude: 35.6762,
      longitude: 139.6503
    })
  },
  weatherDataSource: {
    type: String,
    default: '実況データ'
  }
})

const emit = defineEmits(['coordinates-changed', 'data-source-changed'])

const isLoading = ref(false)
const currentWeather = ref({
  temperature: 22,
  humidity: 65,
  windSpeed: 3.2,
  condition: '曇り'
})

const handleDataSourceChange = (event) => {
  emit('data-source-changed', event.target.value)
}

const handleLatitudeChange = (event) => {
  const newCoords = {
    ...props.coordinates,
    latitude: parseFloat(event.target.value) || 0
  }
  emit('coordinates-changed', newCoords)
}

const handleLongitudeChange = (event) => {
  const newCoords = {
    ...props.coordinates,
    longitude: parseFloat(event.target.value) || 0
  }
  emit('coordinates-changed', newCoords)
}

const adjustLatitude = (delta) => {
  const newLat = Math.round((props.coordinates.latitude + delta) * 10000) / 10000
  const newCoords = {
    ...props.coordinates,
    latitude: Math.max(-90, Math.min(90, newLat))
  }
  emit('coordinates-changed', newCoords)
}

const adjustLongitude = (delta) => {
  const newLng = Math.round((props.coordinates.longitude + delta) * 10000) / 10000
  const newCoords = {
    ...props.coordinates,
    longitude: Math.max(-180, Math.min(180, newLng))
  }
  emit('coordinates-changed', newCoords)
}

const fetchWeatherData = async () => {
  isLoading.value = true
  try {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    // Simulate weather data update
    currentWeather.value = {
      temperature: Math.round(Math.random() * 20 + 10),
      humidity: Math.round(Math.random() * 40 + 40),
      windSpeed: (Math.random() * 5 + 1).toFixed(1),
      condition: ['晴れ', '曇り', '雨', '雪'][Math.floor(Math.random() * 4)]
    }
  } catch (error) {
    console.error('天気データ取得エラー:', error)
  } finally {
    isLoading.value = false
  }
}

// Fetch initial data on mount
onMounted(() => {
  fetchWeatherData()
})
</script>

<style scoped>
.weather-data {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(12, 65, 154, 0.1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 600px;
}

.component-header {
  background: linear-gradient(135deg, #0C419A 0%, #6BA2FC 100%);
  color: white;
  padding: 20px 24px;
  text-align: center;
  flex-shrink: 0;
  min-height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.component-header h3 {
  font-size: 1.4rem;
  font-weight: 700;
  margin: 0;
  color: white;
}

.data-content {
  padding: 24px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.content-spacer {
  flex: 1;
}

.button-container {
  margin-top: auto;
  padding-top: 24px;
  border-top: 1px solid rgba(107, 162, 252, 0.2);
}

.data-source-section,
.coordinates-section,
.api-section,
.weather-preview {
  margin-bottom: 0;
}

.data-source-section h4,
.coordinates-section h4,
.api-section h4,
.weather-preview h4 {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 12px;
  color: #0C419A;
}

.custom-dropdown {
  position: relative;
}

.dropdown-select {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #6BA2FC;
  border-radius: 12px;
  background: linear-gradient(135deg, #FFFFFF 0%, #F8FBFF 100%);
  color: #0C419A;
  font-weight: 600;
  font-size: 1rem;
  appearance: none;
  outline: none;
  cursor: pointer;
}

.dropdown-arrow {
  position: absolute;
  top: 50%;
  right: 12px;
  transform: translateY(-50%);
  font-size: 1rem;
  color: #0C419A;
}

.coordinates-section h4,
.api-section h4,
.weather-preview h4 {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
  color: #333;
}

.coordinate-inputs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.input-group label {
  font-weight: 600;
  color: #0C419A;
  font-size: 0.95rem;
}

.coordinate-control {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px;
  background: linear-gradient(135deg, #FFFFFF 0%, #F8FBFF 100%);
  border: 2px solid #6BA2FC;
  border-radius: 12px;
}

.adjust-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, #6BA2FC 0%, #0C419A 100%);
  color: white;
  font-size: 1.2rem;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.adjust-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(12, 65, 154, 0.3);
}

.adjust-btn:active {
  transform: scale(0.95);
}

.coordinate-input {
  flex: 1;
  padding: 8px 12px;
  border: none;
  background: transparent;
  font-size: 1rem;
  color: #0C419A;
  font-weight: 600;
  text-align: center;
  outline: none;
}

.api-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.api-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
}

.api-label {
  font-weight: 500;
  color: #666;
  min-width: 80px;
}

.api-value {
  flex: 1;
  font-weight: 600;
  color: #333;
}

.api-status {
  font-size: 0.875rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-weight: 500;
}

.api-status.connected {
  background: #d4edda;
  color: #155724;
}

.weather-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.weather-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.weather-icon {
  font-size: 1.5rem;
}

.weather-details {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.weather-label {
  font-size: 0.875rem;
  color: #666;
}

.weather-value {
  font-weight: 600;
  color: #333;
}

.fetch-weather-button {
  width: 100%;
  padding: 1rem 1.5rem !important;
  background: linear-gradient(135deg, #6BA2FC 0%, #0C419A 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  min-height: 56px !important;
  height: 56px !important;
  box-sizing: border-box;
}

.fetch-weather-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(12, 65, 154, 0.3);
}

.fetch-weather-button:active {
  transform: translateY(0);
}

.fetch-weather-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.button-icon {
  font-size: 1.2rem;
}

/* Compact styles for smaller coordinate section */
.coordinates-section.compact {
  margin: 0.5rem 0 1rem 0;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
}

.coordinates-section.compact h4 {
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
  text-align: center;
}

.coordinate-inputs.compact {
  gap: 0.5rem;
  grid-template-columns: 1fr 1fr;
}

.coordinate-control.compact {
  padding: 0.4rem;
  gap: 0.4rem;
  border-radius: 4px;
  border-width: 1px;
}

.adjust-btn.compact {
  width: 26px;
  height: 26px;
  font-size: 0.9rem;
  min-width: 26px;
}

.coordinate-input.compact {
  padding: 6px 8px;
  font-size: 0.85rem;
  min-width: 80px;
  max-width: 100px;
}

.input-group label {
  font-size: 0.75rem;
  margin-bottom: 0.125rem;
}

@media (max-width: 768px) {
  .coordinate-inputs {
    grid-template-columns: 1fr;
  }
  
  .weather-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .data-content {
    padding: 1rem;
  }
  
  .api-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
}
</style>
