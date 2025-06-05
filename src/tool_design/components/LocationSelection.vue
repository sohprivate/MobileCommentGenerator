<template>
  <div class="location-selection">
    <div class="component-header">
      <h3>地点選択</h3>
    </div>
    
    <div class="selection-content">
      <!-- Region Selection -->
      <div class="region-selection">
        <label for="region-select">地方選択:</label>
        <div class="custom-dropdown">
          <select 
            id="region-select"
            v-model="selectedRegion"
            @change="handleRegionChange"
            class="region-select"
          >
            <option value="">すべての地方</option>
            <option value="北海道地方">北海道地方</option>
            <option value="東北地方">東北地方</option>
            <option value="関東地方">関東地方</option>
            <option value="中部地方">中部地方</option>
            <option value="近畿地方">近畿地方</option>
            <option value="中国地方">中国地方</option>
            <option value="四国地方">四国地方</option>
            <option value="九州地方">九州地方</option>
            <option value="沖縄地方">沖縄地方</option>
          </select>
          <div class="dropdown-arrow">▼</div>
        </div>
      </div>

      <!-- Select All Controls -->
      <div class="select-all-section">
        <div class="select-all-controls">
          <button 
            @click="selectAllLocations" 
            class="control-btn select-all-btn"
            :disabled="filteredLocations.length === 0"
          >
            すべて選択
          </button>
          <button 
            @click="clearAllSelections" 
            class="control-btn clear-all-btn"
            :disabled="selectedLocations.length === 0"
          >
            すべてクリア
          </button>
          <button 
            @click="selectRegionLocations" 
            class="control-btn region-btn"
            :disabled="!selectedRegion || getRegionLocations().length === 0"
          >
            {{ selectedRegion || '地方' }}を選択
          </button>
        </div>
        <div class="selection-info">
          <span class="selection-count">{{ selectedLocations.length }}地点選択中</span>
          <span class="total-count">/ {{ filteredLocations.length }}地点</span>
        </div>
      </div>

      <!-- Location Grid -->
      <div class="location-grid">
        <div 
          v-for="location in filteredLocations" 
          :key="location"
          class="location-item"
          :class="{ selected: selectedLocations.includes(location) }"
          @click="toggleLocation(location)"
        >
          <div class="location-checkbox">
            <input 
              type="checkbox" 
              :checked="selectedLocations.includes(location)"
              @click.stop
              readonly
            />
          </div>
          <div class="location-details">
            <span class="location-name">{{ location }}</span>
            <span class="location-region">{{ getAreaName(location) }}</span>
          </div>
        </div>
      </div>

      <!-- Selected Locations Summary -->
      <div class="selected-summary" v-if="selectedLocations.length > 0">
        <h4>選択済み地点 ({{ selectedLocations.length }})</h4>
        <div class="selected-tags">
          <span 
            v-for="location in selectedLocations.slice(0, 10)" 
            :key="location"
            class="location-tag"
            @click="toggleLocation(location)"
          >
            {{ location }}
            <span class="remove-tag">×</span>
          </span>
          <span v-if="selectedLocations.length > 10" class="more-tags">
            他{{ selectedLocations.length - 10 }}地点...
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  selectedLocation: {
    type: String,
    default: '東京'
  }
})

const emit = defineEmits(['location-changed', 'locations-changed'])

const selectedRegion = ref('')
const selectedLocations = ref([props.selectedLocation])
const locations = ref([])

// Computed property for filtered locations based on selected region
const filteredLocations = computed(() => {
  if (!selectedRegion.value) {
    return locations.value
  }
  return locations.value.filter(location => getAreaName(location) === selectedRegion.value)
})

// Load locations from CSV file
const loadLocationsFromCSV = async () => {
  try {
    const response = await fetch('/地点名.csv')
    const data = await response.text()
    
    // Parse CSV data (simple parsing, assuming one location per line)
    const parsedLocations = data.split('\n')
      .map(line => line.trim())
      .filter(line => line && !line.startsWith('//')) // Remove empty lines and comments
    
    // Update locations ref
    locations.value = parsedLocations
    
    console.log(`Loaded ${locations.value.length} locations from CSV`)
  } catch (error) {
    console.error('Error loading locations from CSV:', error)
    // Fallback to default locations if CSV loading fails
    locations.value = ['東京', '大阪', '名古屋', '福岡', '札幌']
  }
}

// Load locations when component is mounted
onMounted(() => {
  loadLocationsFromCSV()
})

// Region change handler
const handleRegionChange = () => {
  
}

// Toggle location selection
const toggleLocation = (location) => {
  const index = selectedLocations.value.indexOf(location)
  if (index === -1) {
    selectedLocations.value.push(location)
  } else {
    selectedLocations.value.splice(index, 1)
  }
  emitLocationChanges()
}

// Select all filtered locations
const selectAllLocations = () => {
  filteredLocations.value.forEach(location => {
    if (!selectedLocations.value.includes(location)) {
      selectedLocations.value.push(location)
    }
  })
  emitLocationChanges()
}

// Clear all selections
const clearAllSelections = () => {
  selectedLocations.value = []
  emitLocationChanges()
}

// Select all locations in the current region
const selectRegionLocations = () => {
  const regionLocations = getRegionLocations()
  regionLocations.forEach(location => {
    if (!selectedLocations.value.includes(location)) {
      selectedLocations.value.push(location)
    }
  })
  emitLocationChanges()
}

// Get locations in the selected region
const getRegionLocations = () => {
  if (!selectedRegion.value) return []
  return locations.value.filter(location => getAreaName(location) === selectedRegion.value)
}


const emitLocationChanges = () => {
  emit('locations-changed', selectedLocations.value)
  
  if (selectedLocations.value.length > 0) {
    emit('location-changed', selectedLocations.value[0])
  }
}

const getAreaName = (location) => {
  
  const areaMapping = {
    // 北海道地方
    '稚内': '北海道地方',
    '旭川': '北海道地方',
    '留萌': '北海道地方',
    '札幌': '北海道地方',
    '岩見沢': '北海道地方',
    '倶知安': '北海道地方',
    '網走': '北海道地方',
    '北見': '北海道地方',
    '紋別': '北海道地方',
    '根室': '北海道地方',
    '釧路': '北海道地方',
    '帯広': '北海道地方',
    '室蘭': '北海道地方',
    '浦河': '北海道地方',
    '函館': '北海道地方',
    '江差': '北海道地方',
    
    // 東北地方
    '青森': '東北地方',
    'むつ': '東北地方',
    '八戸': '東北地方',
    '盛岡': '東北地方',
    '宮古': '東北地方',
    '大船渡': '東北地方',
    '秋田': '東北地方',
    '横手': '東北地方',
    '仙台': '東北地方',
    '白石': '東北地方',
    '山形': '東北地方',
    '米沢': '東北地方',
    '酒田': '東北地方',
    '新庄': '東北地方',
    '福島': '東北地方',
    '小名浜': '東北地方',
    '若松': '東北地方',
    
    // 関東地方
    '東京': '関東地方',
    '大島': '関東地方',
    '八丈島': '関東地方',
    '父島': '関東地方',
    '横浜': '関東地方',
    '小田原': '関東地方',
    'さいたま': '関東地方',
    '熊谷': '関東地方',
    '秩父': '関東地方',
    '千葉': '関東地方',
    '銚子': '関東地方',
    '館山': '関東地方',
    '水戸': '関東地方',
    '土浦': '関東地方',
    '前橋': '関東地方',
    'みなかみ': '関東地方',
    '宇都宮': '関東地方',
    '大田原': '関東地方',
    
    // 中部地方
    '新潟': '中部地方',
    '長岡': '中部地方',
    '高田': '中部地方',
    '相川': '中部地方',
    '金沢': '中部地方',
    '輪島': '中部地方',
    '富山': '中部地方',
    '伏木': '中部地方',
    '福井': '中部地方',
    '敦賀': '中部地方',
    '長野': '中部地方',
    '松本': '中部地方',
    '飯田': '中部地方',
    '甲府': '中部地方',
    '河口湖': '中部地方',
    '名古屋': '中部地方',
    '豊橋': '中部地方',
    '静岡': '中部地方',
    '網代': '中部地方',
    '三島': '中部地方',
    '浜松': '中部地方',
    '岐阜': '中部地方',
    '高山': '中部地方',
    
    // 近畿地方
    '津': '近畿地方',
    '尾鷲': '近畿地方',
    '大阪': '近畿地方',
    '神戸': '近畿地方',
    '豊岡': '近畿地方',
    '京都': '近畿地方',
    '舞鶴': '近畿地方',
    '奈良': '近畿地方',
    '風屋': '近畿地方',
    '大津': '近畿地方',
    '彦根': '近畿地方',
    '和歌山': '近畿地方',
    '潮岬': '近畿地方',
    
    // 中国地方
    '広島': '中国地方',
    '庄原': '中国地方',
    '岡山': '中国地方',
    '津山': '中国地方',
    '下関': '中国地方',
    '山口': '中国地方',
    '柳井': '中国地方',
    '萩': '中国地方',
    '松江': '中国地方',
    '浜田': '中国地方',
    '西郷': '中国地方',
    '鳥取': '中国地方',
    '米子': '中国地方',
    
    // 四国地方
    '徳島': '四国地方',
    '日和佐': '四国地方',
    '高松': '四国地方',
    '松山': '四国地方',
    '宇和島': '四国地方',
    '高知': '四国地方',
    '室戸岬': '四国地方',
    '清水': '四国地方',
    
    // 九州・沖縄地方
    '福岡': '九州地方',
    '八幡': '九州地方',
    '飯塚': '九州地方',
    '久留米': '九州地方',
    '大分': '九州地方',
    '中津': '九州地方',
    '日田': '九州地方',
    '佐伯': '九州地方',
    '長崎': '九州地方',
    '佐世保': '九州地方',
    '厳原': '九州地方',
    '福江': '九州地方',
    '佐賀': '九州地方',
    '伊万里': '九州地方',
    '熊本': '九州地方',
    '阿蘇乙姫': '九州地方',
    '牛深': '九州地方',
    '人吉': '九州地方',
    '宮崎': '九州地方',
    '延岡': '九州地方',
    '都城': '九州地方',
    '高千穂': '九州地方',
    '鹿児島': '九州地方',
    '鹿屋': '九州地方',
    '種子島': '九州地方',
    '名瀬': '九州地方',
    '那覇': '沖縄地方',
    '名護': '沖縄地方',
    '久米島': '沖縄地方',
    '宮古島': '沖縄地方',
    '石垣島': '沖縄地方',
    '与那国島': '沖縄地方'
  }
  
  // マッピングに存在しない場合は、地点名から地域を推測
  if (areaMapping[location]) {
    return areaMapping[location]
  } else {
    // 地名の特徴から地方を推測する
    if (location.includes('北海道')) return '北海道地方'
    if (location.match(/青森|岩手|宮城|秋田|山形|福島/)) return '東北地方'
    if (location.match(/東京|神奈川|埼玉|千葉|茨城|栃木|群馬/)) return '関東地方'
    if (location.match(/新潟|富山|石川|福井|山梨|長野|岐阜|静岡|愛知/)) return '中部地方'
    if (location.match(/三重|滋賀|京都|大阪|兵庫|奈良|和歌山/)) return '近畿地方'
    if (location.match(/鳥取|島根|岡山|広島|山口/)) return '中国地方'
    if (location.match(/徳島|香川|愛媛|高知/)) return '四国地方'
    if (location.match(/福岡|佐賀|長崎|熊本|大分|宮崎|鹿児島/)) return '九州地方'
    if (location.match(/沖縄/)) return '沖縄地方'
    
    return '不明'
  }
}
</script>

<style scoped>
.location-selection {
  background: linear-gradient(135deg, #E8F0FE 0%,#F3F8FF 100%);
  border-radius: 16px;
  padding: 0;
  box-shadow: 0 4px 12px rgba(12, 65, 154, 0.1);
  margin-bottom: 24px;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 600px;
}

.component-header {
  margin-bottom: 0;
  padding: 20px 24px;
  border-bottom: 2px solid #0C419A;
  background: linear-gradient(135deg, #0C419A 0%, #6BA2FC 100%);
  color: white;
  border-radius: 16px 16px 0 0;
  flex-shrink: 0;
  min-height: 60px;
  display: flex;
  align-items: center;
}

.component-header h3 {
  color: white;
  font-size: 1.4rem;
  font-weight: 700;
  margin: 0;
  font-family: 'Montserrat', sans-serif;
}

.selection-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 24px;
  flex: 1;
  overflow-y: auto;
}

/* Region Selection */
.region-selection {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.region-selection label {
  font-weight: 600;
  color: #0C419A;
  font-size: 0.95rem;
}

/* Select All Section */
.select-all-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 12px;
  border: 1px solid rgba(107, 162, 252, 0.3);
}

.select-all-controls {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.control-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
  flex: 1;
  min-width: 120px;
}

.select-all-btn {
  background: linear-gradient(135deg, #28a745 0%, #20a640 100%);
  color: white;
}

.select-all-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(40, 167, 69, 0.3);
}

.clear-all-btn {
  background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
  color: white;
}

.clear-all-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(220, 53, 69, 0.3);
}

.region-btn {
  background: linear-gradient(135deg, #6BA2FC 0%, #0C419A 100%);
  color: white;
}

.region-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(12, 65, 154, 0.3);
}

.control-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.selection-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.9rem;
  color: #0C419A;
  font-weight: 500;
}

.selection-count {
  font-weight: 700;
  color: #28a745;
}

/* Location Grid */
.location-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
  padding: 8px;
  border: 1px solid rgba(107, 162, 252, 0.3);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.5);
}

.location-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: white;
  border-radius: 8px;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.3s ease;
}

.location-item:hover {
  border-color: #6BA2FC;
  box-shadow: 0 2px 8px rgba(107, 162, 252, 0.2);
}

.location-item.selected {
  border-color: #0C419A;
  background: linear-gradient(135deg, #F8FBFF 0%, #E8F0FE 100%);
}

.location-checkbox input {
  width: 16px;
  height: 16px;
  accent-color: #0C419A;
}

.location-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.location-name {
  font-weight: 600;
  color: #0C419A;
  font-size: 0.95rem;
}

.location-region {
  font-size: 0.8rem;
  color: #6BA2FC;
  font-weight: 500;
}

/* Selected Summary */
.selected-summary {
  margin-top: 8px;
}

.selected-summary h4 {
  color: #0C419A;
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 12px 0;
}

.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.location-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: linear-gradient(135deg, #6BA2FC 0%, #0C419A 100%);
  color: white;
  border-radius: 16px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.location-tag:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(12, 65, 154, 0.3);
}

.remove-tag {
  font-weight: bold;
  font-size: 1rem;
  line-height: 1;
}

.more-tags {
  padding: 6px 12px;
  background: rgba(107, 162, 252, 0.2);
  color: #0C419A;
  border-radius: 16px;
  font-size: 0.85rem;
  font-weight: 500;
}

.custom-dropdown {
  position: relative;
  display: inline-block;
  width: 100%;
}

.region-select,
.source-select {
  width: 100%;
  padding: 12px 40px 12px 16px;
  border: 2px solid #6BA2FC;
  border-radius: 12px;
  background: linear-gradient(135deg, #FFFFFF 0%, #F8FBFF 100%);
  color: #0C419A;
  font-size: 1rem;
  font-weight: 600;
  appearance: none;
  cursor: pointer;
  transition: all 0.3s ease;
}

.region-select:hover,
.source-select:hover {
  border-color: #0C419A;
  box-shadow: 0 2px 8px rgba(12, 65, 154, 0.15);
}

.region-select:focus,
.source-select:focus {
  outline: none;
  border-color: #0C419A;
  box-shadow: 0 0 0 3px rgba(107, 162, 252, 0.3);
}

.dropdown-arrow {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #6BA2FC;
  font-size: 0.8rem;
  pointer-events: none;
  transition: transform 0.3s ease;
}

.custom-dropdown:hover .dropdown-arrow {
  color: #0C419A;
}

.data-source-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.source-dropdown {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.source-dropdown label {
  font-weight: 600;
  color: #0C419A;
  font-size: 0.95rem;
}

.data-sources {
  margin-top: 8px;
}

.data-sources h4 {
  color: #0C419A;
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 12px 0;
}

.source-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.source-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
  border: 1px solid rgba(107, 162, 252, 0.3);
}

.source-icon {
  font-size: 1.2rem;
}

.source-name {
  flex: 1;
  color: #0C419A;
  font-weight: 500;
}

.source-status {
  font-size: 0.85rem;
  padding: 4px 8px;
  border-radius: 12px;
  font-weight: 500;
}

.source-status.active {
  background: #28a745;
  color: white;
}

/* Mobile Responsive */
@media (max-width: 768px) {
  .location-grid {
    grid-template-columns: 1fr;
  }
  
  .select-all-controls {
    flex-direction: column;
  }
  
  .control-btn {
    min-width: auto;
  }
}

@media (max-width: 480px) {
  .location-selection {
    padding: 16px;
    margin-bottom: 16px;
  }
  
  .component-header h3 {
    font-size: 1.2rem;
  }
  
  .selected-tags {
    gap: 6px;
  }
  
  .location-tag {
    font-size: 0.8rem;
    padding: 4px 8px;
  }
}
</style>
