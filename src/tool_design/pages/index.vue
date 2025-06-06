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
          @locations-changed="handleLocationsChange"
        />

        <WeatherData 
          :coordinates="coordinates"
          :weatherDataSource="weatherDataSource"
          @coordinates-changed="handleCoordinatesChange"
          @data-source-changed="handleWeatherDataSourceChange"
        />

        <!-- Generate Settings -->
        <GenerateSettings 
          :settings="generateSettings"
          @settings-changed="handleSettingsChange"
          @generate="handleGenerate"
        />

        <GeneratedComment 
          :comments="generatedComments"
          :isLoading="isGenerating"
          @regenerate="handleGenerate"
          @clear="handleClear"
        />
      </div>
    </main>
  </div>
</template>

<script setup>
const weatherDataSource = ref('手動入力')
const coordinates = ref({
  latitude: 35.6762,
  longitude: 139.6503
})
const generateSettings = ref({
  method: '実例ベース',
  count: 5,
  includeEmoji: true,
  includeAdvice: false,
  politeForm: true
})
const generatedComments = ref([])
const isGenerating = ref(false)
const selectedLocations = ref([])

// Prefecture coordinates mapping for location selection　（not sure if this is needed...)
const prefectureCoordinates = {
  '北海道': { latitude: 43.0642, longitude: 141.3469 },
  '青森県': { latitude: 40.8244, longitude: 140.7400 },
  '岩手県': { latitude: 39.7036, longitude: 141.1527 },
  '宮城県': { latitude: 38.2682, longitude: 140.8721 },
  '秋田県': { latitude: 39.7186, longitude: 140.1024 },
  '山形県': { latitude: 38.2404, longitude: 140.3633 },
  '福島県': { latitude: 37.7503, longitude: 140.4676 },
  '茨城県': { latitude: 36.3418, longitude: 140.4468 },
  '栃木県': { latitude: 36.5657, longitude: 139.8836 },
  '群馬県': { latitude: 36.3911, longitude: 139.0608 },
  '埼玉県': { latitude: 35.8569, longitude: 139.6489 },
  '千葉県': { latitude: 35.6074, longitude: 140.1065 },
  '東京都': { latitude: 35.6762, longitude: 139.6503 },
  '神奈川県': { latitude: 35.4478, longitude: 139.6425 },
  '新潟県': { latitude: 37.9026, longitude: 139.0232 },
  '富山県': { latitude: 36.6953, longitude: 137.2113 },
  '石川県': { latitude: 36.5946, longitude: 136.6256 },
  '福井県': { latitude: 36.0652, longitude: 136.2216 },
  '山梨県': { latitude: 35.6642, longitude: 138.5684 },
  '長野県': { latitude: 36.6513, longitude: 138.1810 },
  '岐阜県': { latitude: 35.3912, longitude: 136.7223 },
  '静岡県': { latitude: 34.9769, longitude: 138.3831 },
  '愛知県': { latitude: 35.1815, longitude: 136.9066 },
  '三重県': { latitude: 34.7303, longitude: 136.5086 },
  '滋賀県': { latitude: 35.0045, longitude: 135.8686 },
  '京都府': { latitude: 35.0211, longitude: 135.7556 },
  '大阪府': { latitude: 34.6937, longitude: 135.5023 },
  '兵庫県': { latitude: 34.6913, longitude: 135.1830 },
  '奈良県': { latitude: 34.6851, longitude: 135.8325 },
  '和歌山県': { latitude: 34.2261, longitude: 135.1675 },
  '鳥取県': { latitude: 35.5038, longitude: 134.2384 },
  '島根県': { latitude: 35.4723, longitude: 133.0505 },
  '岡山県': { latitude: 34.6618, longitude: 133.9349 },
  '広島県': { latitude: 34.3963, longitude: 132.4596 },
  '山口県': { latitude: 34.1860, longitude: 131.4706 },
  '徳島県': { latitude: 34.0658, longitude: 134.5594 },
  '香川県': { latitude: 34.3401, longitude: 134.0434 },
  '愛媛県': { latitude: 33.8416, longitude: 132.7657 },
  '高知県': { latitude: 33.5597, longitude: 133.5311 },
  '福岡県': { latitude: 33.5904, longitude: 130.4017 },
  '佐賀県': { latitude: 33.2494, longitude: 130.2989 },
  '長崎県': { latitude: 32.7503, longitude: 129.8777 },
  '熊本県': { latitude: 32.7898, longitude: 130.7417 },
  '大分県': { latitude: 33.2382, longitude: 131.6126 },
  '宮崎県': { latitude: 31.9077, longitude: 131.4202 },
  '鹿児島県': { latitude: 31.5602, longitude: 130.5581 },
  '沖縄県': { latitude: 26.2124, longitude: 127.6792 }
}

// Handler for location selection changes
const handleLocationsChange = (locations) => {
  selectedLocations.value = locations
  // If locations are selected, update coordinates to the first one
  if (locations.length > 0 && prefectureCoordinates[locations[0]]) {
    coordinates.value = prefectureCoordinates[locations[0]]
  }
}

const handleWeatherDataSourceChange = (newSource) => {
  weatherDataSource.value = newSource
}

const handleCoordinatesChange = (newCoords) => {
  coordinates.value = newCoords
}

const handleSettingsChange = (newSettings) => {
  generateSettings.value = newSettings
}

const handleGenerate = async () => {
  isGenerating.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    const baseComments = [
      '今日は雲が多めですが、気温は過ごしやすそうですね！☁️',
      '少し肌寒いかもしれません。羽織物があると良いでしょう。🧥',
      '湿度が高めなので、熱中症にお気をつけください。💧',
      '風が強いようです。傘の持参をお勧めします。🌬️',
      '晴れ間も見えるので、お出かけ日和かもしれませんね！☀️',
      '今日は暖かくて過ごしやすい一日になりそうです。🌞',
      '雨の予報が出ています。お出かけの際はご注意ください。☔',
      '気温の変化が激しそうです。体調管理にお気をつけください。🌡️',
      '穏やかな天気で、散歩には最適な日ですね。🚶‍♀️',
      '夕方から天気が崩れる予報です。早めの帰宅をお勧めします。🌅'
    ]
    
    let selectedComments = baseComments.slice(0, generateSettings.value.count)
    
    selectedComments = selectedComments.map(comment => {
      let modifiedComment = comment
      
      if (!generateSettings.value.includeEmoji) {
        modifiedComment = modifiedComment.replace(/[^\w\s！？。、（）]/g, '')
      }
      
      if (generateSettings.value.method === 'business') {
        modifiedComment = modifiedComment.replace(/ですね/g, 'でございます')
        modifiedComment = modifiedComment.replace(/です/g, 'でございます')
      } else if (generateSettings.value.method === 'creative') {
        const creativeWords = ['素敵な', 'とても', 'きっと', 'なんだか']
        const randomWord = creativeWords[Math.floor(Math.random() * creativeWords.length)]
        modifiedComment = randomWord + modifiedComment
      }
      
      return modifiedComment
    })
    
    generatedComments.value = selectedComments
  } catch (error) {
    console.error('コメント生成エラー:', error)
  } finally {
    isGenerating.value = false
  }
}

const handleClear = () => {
  generatedComments.value = []
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
