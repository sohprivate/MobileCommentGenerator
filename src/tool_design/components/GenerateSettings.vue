<template>
  <div class="generate-settings">
    <div class="component-header">
      <h3>生成設定</h3>
    </div>
    
    <div class="settings-content">
      <!-- Generation Method -->
      <div class="method-section">
        <h4>生成方法</h4>
        <div class="method-dropdown">
          <div class="custom-dropdown">
            <select 
              :value="settings.method"
              @change="handleMethodChange"
              class="method-select"
            >
              <option value="実例ベース">実例ベース（推奨）</option>
              <option value="パターンベース">パターンベース</option>
              <option value="WeatherSummarizer">WeatherSummarizer(本格版）</option>
            </select>
            <div class="dropdown-arrow">▼</div>
          </div>
        </div>
      </div>

      <!-- Comment Count -->
      <div class="count-section">
        <h4>生成数</h4>
        <div class="count-controls">
          <label for="count-slider">コメント数: {{ settings.count }}個</label>
          <div class="slider-container">
            <input
              id="count-slider"
              type="range"
              min="1"
              max="10"
              :value="settings.count"
              @input="handleCountChange"
              class="count-slider"
            />
            <div class="slider-labels">
              <span>1</span>
              <span>5</span>
              <span>10</span>
            </div>
          </div>
          <div class="count-buttons">
            <button 
              v-for="num in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]"
              :key="num"
              @click="setCount(num)"
              :class="['count-btn', { active: settings.count === num }]"
            >
              {{ num }}
            </button>
          </div>
        </div>
      </div>

      <!-- Advanced Options -->
      <div class="advanced-section">
        <h4>詳細設定</h4>
        <div class="advanced-options">
          <label class="option-checkbox">
            <input
              type="checkbox"
              :checked="settings.includeEmoji"
              @change="handleEmojiChange"
            />
            <span>絵文字を含める</span>
          </label>
          <label class="option-checkbox">
            <input
              type="checkbox"
              :checked="settings.includeAdvice"
              @change="handleAdviceChange"
            />
            <span>服装アドバイスを含める</span>
          </label>
          <label class="option-checkbox">
            <input
              type="checkbox"
              :checked="settings.politeForm"
              @change="handlePoliteFormChange"
            />
            <span>敬語を使用する</span>
          </label>
        </div>
      </div>

      <!-- Content spacer to push button to bottom -->
      <div class="content-spacer"></div>

      <!-- Generate Button -->
      <div class="button-container">
        <button 
          @click="handleGenerate"
          :disabled="isGenerating"
          class="generate-button"
        >
          <span class="button-icon">✨</span>
          <span v-if="isGenerating">生成中...</span>
          <span v-else>コメント生成</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  settings: {
    type: Object,
    default: () => ({
      method: 'standard',
      count: 5,
      includeEmoji: true,
      includeAdvice: false,
      politeForm: true
    })
  }
})

const emit = defineEmits(['settings-changed', 'generate'])

const isGenerating = ref(false)

const handleMethodChange = (event) => {
  const newSettings = {
    ...props.settings,
    method: event.target.value
  }
  emit('settings-changed', newSettings)
}

const handleCountChange = (event) => {
  const newSettings = {
    ...props.settings,
    count: parseInt(event.target.value)
  }
  emit('settings-changed', newSettings)
}

const setCount = (count) => {
  const newSettings = {
    ...props.settings,
    count
  }
  emit('settings-changed', newSettings)
}

const handleEmojiChange = (event) => {
  const newSettings = {
    ...props.settings,
    includeEmoji: event.target.checked
  }
  emit('settings-changed', newSettings)
}

const handleAdviceChange = (event) => {
  const newSettings = {
    ...props.settings,
    includeAdvice: event.target.checked
  }
  emit('settings-changed', newSettings)
}

const handlePoliteFormChange = (event) => {
  const newSettings = {
    ...props.settings,
    politeForm: event.target.checked
  }
  emit('settings-changed', newSettings)
}

const handleGenerate = () => {
  isGenerating.value = true
  emit('generate')
  

  setTimeout(() => {
    isGenerating.value = false
  }, 2500)
}
</script>

<style scoped>
.generate-settings {
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

.settings-content {
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

.method-section,
.count-section,
.advanced-section {
  margin-bottom: 0;
}

.method-section h4,
.count-section h4,
.advanced-section h4 {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 12px;
  color: #0C419A;
}

.method-dropdown {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.custom-dropdown {
  position: relative;
  display: inline-block;
  width: 100%;
}

.method-select {
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

.method-select:hover {
  border-color: #0C419A;
  box-shadow: 0 2px 8px rgba(12, 65, 154, 0.15);
}

.method-select:focus {
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

.count-controls {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.count-controls label {
  font-weight: 600;
  color: #0C419A;
  font-size: 0.95rem;
}

.slider-container {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin: 1rem 0;
}

.count-slider {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #e1e5e9;
  outline: none;
  appearance: none;
}

.count-slider::-webkit-slider-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #6BA2FC;
  cursor: pointer;
  appearance: none;
}

.count-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #6BA2FC;
  cursor: pointer;
  border: none;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: #6c757d;
  margin-top: 0.25rem;
}

.count-buttons {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 0.25rem;
  margin-top: 0.5rem;
}

.count-btn {
  padding: 0.375rem 0.5rem;
  border: 2px solid #e1e5e9;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 500;
  font-size: 0.85rem;
  min-height: 32px;
}

.count-btn:hover {
  border-color: #6BA2FC;
}

.count-btn.active {
  background: #6BA2FC;
  color: white;
  border-color: #6BA2FC;
}

.advanced-options {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.option-checkbox {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.option-checkbox:hover {
  background: #e9ecef;
}

.option-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
}

.generate-button {
  width: 100%;
  padding: 1rem 1.5rem;
  background: linear-gradient(135deg, #0C419A 0%, #6BA2FC 100%);
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
  min-height: 56px;
}

.generate-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(12, 65, 154, 0.3);
}

.generate-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.button-icon {
  font-size: 1.2rem;
}

@media (max-width: 480px) {
  .settings-content {
    padding: 1rem;
  }
  
  .count-buttons {
    grid-template-columns: repeat(5, 1fr);
    gap: 0.2rem;
  }
  
  .count-btn {
    padding: 0.25rem 0.375rem;
    font-size: 0.8rem;
    min-height: 28px;
  }
  
  .method-option {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
}
</style>
