<template>
  <div class="location-selection">
    <div class="component-header">
      <h3>地点選択</h3>
    </div>
    
    <div class="selection-content">
      <!-- Loading state -->
      <div v-if="isLoading" class="loading-state">
        <div class="spinner"></div>
        <p>地点データを読み込み中...</p>
      </div>

      <!-- Error state -->
      <div v-else-if="error" class="error-state">
        <p class="error-message">{{ error }}</p>
        <button @click="loadLocations" class="retry-btn">再読み込み</button>
      </div>

      <!-- Main content -->
      <template v-else>
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
              <option v-for="region in regions" :key="region" :value="region">
                {{ region }}
              </option>
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
            :key="location.name"
            class="location-item"
            :class="{ selected: selectedLocations.includes(location.name) }"
            @click="toggleLocation(location.name)"
          >
            <div class="location-checkbox">
              <input 
                type="checkbox" 
                :checked="selectedLocations.includes(location.name)"
                @click.stop
                readonly
              />
            </div>
            <div class="location-details">
              <span class="location-name">{{ location.name }}</span>
              <span class="location-region">{{ location.area || getAreaName(location.name) }}</span>
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
            <span v-if="selectedLocations.length > 10" class="more-locations">
              他{{ selectedLocations.length - 10 }}地点...
            </span>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, defineProps, defineEmits } from 'vue'
import { useApi } from '~/composables/useApi'
import { getAreaName, REGIONS } from '~/constants/locations'
import type { Location } from '~/types'

// Props
interface Props {
  selectedLocation?: string
}

const props = defineProps<Props>()

// Emits
interface Emits {
  (e: 'location-changed', location: string): void
  (e: 'locations-changed', locations: string[]): void
}

const emit = defineEmits<Emits>()

// API composable
const api = useApi()

// State
const selectedRegion = ref<string>('')
const selectedLocations = ref<string[]>([])
const allLocations = ref<Location[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)
const regions = ref(REGIONS)

// Computed
const locations = computed(() => {
  return allLocations.value.map(loc => loc.name)
})

const filteredLocations = computed(() => {
  if (!selectedRegion.value) {
    return allLocations.value
  }
  return allLocations.value.filter(location => {
    const area = location.area || getAreaName(location.name)
    return area === selectedRegion.value
  })
})

// Methods
const loadLocations = async () => {
  isLoading.value = true
  error.value = null
  
  try {
    const response = await api.fetchLocations()
    if (response.success && response.data) {
      allLocations.value = response.data
      
      // 初期選択がある場合は設定
      if (props.selectedLocation) {
        selectedLocations.value = [props.selectedLocation]
      }
    } else {
      // APIが利用できない場合は、CSVファイルから読み込む
      await loadLocationsFromCSV()
    }
  } catch (err) {
    console.error('Failed to load locations:', err)
    // フォールバック: CSVファイルから読み込む
    await loadLocationsFromCSV()
  } finally {
    isLoading.value = false
  }
}

// CSVファイルから地点データを読み込む（フォールバック）
const loadLocationsFromCSV = async () => {
  try {
    const response = await fetch('/地点名.csv')
    const text = await response.text()
    const lines = text.split('\n').filter(line => line.trim())
    
    allLocations.value = lines.slice(1).map(line => {
      const [name] = line.split(',')
      return {
        name: name.trim(),
        latitude: 0,
        longitude: 0,
        area: getAreaName(name.trim())
      }
    })
  } catch (err) {
    error.value = '地点データの読み込みに失敗しました'
    console.error('Failed to load CSV:', err)
  }
}

const toggleLocation = (location: string) => {
  const index = selectedLocations.value.indexOf(location)
  if (index > -1) {
    selectedLocations.value.splice(index, 1)
  } else {
    selectedLocations.value.push(location)
  }
  emitLocationChanges()
}

const selectAllLocations = () => {
  selectedLocations.value = filteredLocations.value.map(loc => loc.name)
  emitLocationChanges()
}

const clearAllSelections = () => {
  selectedLocations.value = []
  emitLocationChanges()
}

const selectRegionLocations = () => {
  const regionLocations = getRegionLocations()
  selectedLocations.value = [...new Set([...selectedLocations.value, ...regionLocations])]
  emitLocationChanges()
}

const handleRegionChange = () => {
  // 地方選択が変更されたときの処理
}

const getRegionLocations = () => {
  if (!selectedRegion.value) return []
  return filteredLocations.value.map(loc => loc.name)
}

const emitLocationChanges = () => {
  emit('locations-changed', selectedLocations.value)
  
  if (selectedLocations.value.length > 0) {
    emit('location-changed', selectedLocations.value[0])
  }
}

// Lifecycle
onMounted(() => {
  loadLocations()
})
</script>

<style scoped>
.location-selection {
  background: linear-gradient(135deg, #E8F0FE 0%,#F3F8FF 100%);
  border-radius: 16px;
  padding: 0;
  box-shadow: 0 4px 12px rgba(12, 65, 154, 0.1);
  overflow: hidden;
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* Loading and Error states */
.loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  min-height: 400px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #E8F0FE;
  border-top-color: #0C419A;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-message {
  color: #dc3545;
  margin-bottom: 1rem;
}

.retry-btn {
  background: #0C419A;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.3s;
}

.retry-btn:hover {
  background: #1a52b3;
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

.selection-content {
  padding: 2rem;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.region-selection {
  margin-bottom: 2rem;
}

.region-selection label {
  display: block;
  font-weight: 600;
  color: #0C419A;
  margin-bottom: 0.5rem;
  font-size: 0.95rem;
}

.custom-dropdown {
  position: relative;
  width: 100%;
}

.region-select {
  width: 100%;
  padding: 16px 20px;
  padding-right: 40px;
  font-size: 1rem;
  border: 2px solid #E8F0FE;
  border-radius: 12px;
  background: white;
  appearance: none;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(12, 65, 154, 0.05);
}

.region-select:hover {
  border-color: #6BA2FC;
  box-shadow: 0 4px 12px rgba(107, 162, 252, 0.2);
}

.region-select:focus {
  outline: none;
  border-color: #0C419A;
  box-shadow: 0 0 0 3px rgba(12, 65, 154, 0.1);
}

.dropdown-arrow {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
  color: #6BA2FC;
  font-size: 0.8rem;
}

.select-all-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.select-all-controls {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.control-btn {
  padding: 10px 20px;
  border: 2px solid transparent;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.select-all-btn {
  background: #E8F0FE;
  color: #0C419A;
  border-color: #6BA2FC;
}

.select-all-btn:hover:not(:disabled) {
  background: #6BA2FC;
  color: white;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(107, 162, 252, 0.3);
}

.clear-all-btn {
  background: #FFF0F0;
  color: #dc3545;
  border-color: #ffcccc;
}

.clear-all-btn:hover:not(:disabled) {
  background: #dc3545;
  color: white;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(220, 53, 69, 0.3);
}

.region-btn {
  background: #F0F8FF;
  color: #1a52b3;
  border-color: #B8D4FF;
}

.region-btn:hover:not(:disabled) {
  background: #1a52b3;
  color: white;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(26, 82, 179, 0.3);
}

.control-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.selection-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.95rem;
}

.selection-count {
  font-weight: 700;
  color: #0C419A;
}

.total-count {
  color: #6B7280;
}

.location-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
  padding: 0.5rem;
  background: white;
  border-radius: 12px;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.05);
}

.location-item {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  background: #F9FAFB;
  border: 2px solid #E5E7EB;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.location-item:hover {
  background: #E8F0FE;
  border-color: #6BA2FC;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(107, 162, 252, 0.2);
}

.location-item.selected {
  background: linear-gradient(135deg, #0C419A 0%, #1a52b3 100%);
  border-color: #0C419A;
  color: white;
  box-shadow: 0 4px 12px rgba(12, 65, 154, 0.3);
}

.location-item.selected .location-region {
  color: rgba(255, 255, 255, 0.9);
}

.location-checkbox {
  margin-right: 12px;
}

.location-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: #0C419A;
  cursor: pointer;
}

.location-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.location-name {
  font-weight: 600;
  font-size: 0.95rem;
}

.location-region {
  font-size: 0.8rem;
  color: #6B7280;
}

.selected-summary {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 2px solid #E8F0FE;
}

.selected-summary h4 {
  color: #0C419A;
  margin-bottom: 1rem;
  font-size: 1.1rem;
}

.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.location-tag {
  display: inline-flex;
  align-items: center;
  background: linear-gradient(135deg, #E8F0FE 0%, #F3F8FF 100%);
  color: #0C419A;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 2px solid #6BA2FC;
}

.location-tag:hover {
  background: #dc3545;
  color: white;
  border-color: #dc3545;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(220, 53, 69, 0.3);
}

.remove-tag {
  margin-left: 8px;
  font-size: 1.2rem;
  font-weight: bold;
  opacity: 0.7;
}

.more-locations {
  display: inline-flex;
  align-items: center;
  color: #6B7280;
  padding: 8px 16px;
  font-size: 0.9rem;
  font-style: italic;
}

/* スクロールバーのスタイル */
.location-grid::-webkit-scrollbar {
  width: 8px;
}

.location-grid::-webkit-scrollbar-track {
  background: #F3F4F6;
  border-radius: 4px;
}

.location-grid::-webkit-scrollbar-thumb {
  background: #9CA3AF;
  border-radius: 4px;
}

.location-grid::-webkit-scrollbar-thumb:hover {
  background: #6B7280;
}
</style>