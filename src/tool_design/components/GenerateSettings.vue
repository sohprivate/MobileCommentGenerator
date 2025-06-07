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
              <option value="practical">パターンベース</option>
              <option value="creative">クリエイティブ</option>
              <option value="business">ビジネス</option>
            </select>
            <div class="dropdown-arrow">▼</div>
          </div>
        </div>
      </div>

      <!-- Target Time Selection -->
      <div class="target-time-section">
        <h4>予報時間</h4>
        <div class="time-buttons">
          <button 
            @click="setTargetTime('12h')"
            :class="['time-btn', { active: settings.targetTime === '12h' }]"
          >
            12時間後
          </button>
          <button 
            @click="setTargetTime('24h')"
            :class="['time-btn', { active: settings.targetTime === '24h' }]"
          >
            24時間後
          </button>
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
          <span v-if="!isGenerating" class="button-content">
            <svg class="button-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2v10m0 0l4-4m-4 4l-4-4m10 9v3a2 2 0 01-2 2H5a2 2 0 01-2-2v-3"></path>
            </svg>
            コメントを生成
          </span>
          <span v-else class="button-content">
            <svg class="spinner-icon" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" opacity="0.25"></circle>
              <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
            </svg>
            生成中...
          </span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'
import type { GenerateSettings } from '~/types'

// Props
interface Props {
  settings: GenerateSettings
}

const props = defineProps<Props>()
const isGenerating = ref(false)

// Emits
interface Emits {
  (e: 'settings-changed', settings: GenerateSettings): void
  (e: 'generate'): void
}

const emit = defineEmits<Emits>()

// Methods
const handleMethodChange = (event: Event) => {
  const target = event.target as HTMLSelectElement
  emit('settings-changed', {
    ...props.settings,
    method: target.value as GenerateSettings['method']
  })
}

const handleCountChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  emit('settings-changed', {
    ...props.settings,
    count: parseInt(target.value)
  })
}

const setCount = (count: number) => {
  emit('settings-changed', {
    ...props.settings,
    count
  })
}

const setTargetTime = (time: '12h' | '24h') => {
  emit('settings-changed', {
    ...props.settings,
    targetTime: time
  })
}

const handleEmojiChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  emit('settings-changed', {
    ...props.settings,
    includeEmoji: target.checked
  })
}

const handleAdviceChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  emit('settings-changed', {
    ...props.settings,
    includeAdvice: target.checked
  })
}

const handlePoliteFormChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  emit('settings-changed', {
    ...props.settings,
    politeForm: target.checked
  })
}

const handleGenerate = async () => {
  isGenerating.value = true
  emit('generate')
  // Reset after parent handles the generation
  setTimeout(() => {
    isGenerating.value = false
  }, 100)
}
</script>

<style scoped>
.generate-settings {
  background: linear-gradient(135deg, #E8FEF0 0%, #F3FFF8 100%);
  border-radius: 16px;
  padding: 0;
  box-shadow: 0 4px 12px rgba(11, 252, 103, 0.1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.component-header {
  background: linear-gradient(135deg, #0BFC67 0%, #66FFB3 100%);
  color: white;
  padding: 1.5rem 2rem;
  border-bottom: 3px solid #66FFB3;
}

.component-header h3 {
  font-size: 1.4rem;
  font-weight: 700;
  margin: 0;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
}

.settings-content {
  padding: 2rem;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* Method Section */
.method-section, .target-time-section, .count-section, .advanced-section {
  margin-bottom: 2rem;
}

.method-section h4, .target-time-section h4, .count-section h4, .advanced-section h4 {
  color: #0BFC67;
  font-weight: 600;
  margin-bottom: 1rem;
  font-size: 1.1rem;
}

.custom-dropdown {
  position: relative;
  width: 100%;
}

.method-select {
  width: 100%;
  padding: 16px 20px;
  padding-right: 40px;
  font-size: 1rem;
  border: 2px solid #E8FEF0;
  border-radius: 12px;
  background: white;
  appearance: none;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(11, 252, 103, 0.05);
}

.method-select:hover {
  border-color: #66FFB3;
  box-shadow: 0 4px 12px rgba(102, 255, 179, 0.2);
}

.method-select:focus {
  outline: none;
  border-color: #0BFC67;
  box-shadow: 0 0 0 3px rgba(11, 252, 103, 0.1);
}

.dropdown-arrow {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
  color: #66FFB3;
  font-size: 0.8rem;
}

/* Target Time Section */
.time-buttons {
  display: flex;
  gap: 1rem;
}

.time-btn {
  flex: 1;
  padding: 12px 20px;
  border: 2px solid #E8FEF0;
  border-radius: 10px;
  background: white;
  color: #374151;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.time-btn:hover {
  border-color: #66FFB3;
  background: #F0FFF8;
}

.time-btn.active {
  background: linear-gradient(135deg, #0BFC67 0%, #66FFB3 100%);
  border-color: #0BFC67;
  color: white;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(11, 252, 103, 0.3);
}

/* Count Section */
.count-controls label {
  display: block;
  font-weight: 500;
  color: #374151;
  margin-bottom: 1rem;
  font-size: 0.95rem;
}

.slider-container {
  margin-bottom: 1.5rem;
}

.count-slider {
  width: 100%;
  height: 8px;
  background: #E5E7EB;
  border-radius: 4px;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
  margin-bottom: 0.5rem;
}

.count-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 24px;
  height: 24px;
  background: linear-gradient(135deg, #0BFC67 0%, #66FFB3 100%);
  border: 3px solid white;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(11, 252, 103, 0.3);
  transition: all 0.3s ease;
}

.count-slider::-webkit-slider-thumb:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(11, 252, 103, 0.4);
}

.count-slider::-moz-range-thumb {
  width: 24px;
  height: 24px;
  background: linear-gradient(135deg, #0BFC67 0%, #66FFB3 100%);
  border: 3px solid white;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(11, 252, 103, 0.3);
  transition: all 0.3s ease;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  color: #6B7280;
}

.count-buttons {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 0.5rem;
}

.count-btn {
  padding: 10px;
  border: 2px solid #E8FEF0;
  border-radius: 8px;
  background: white;
  color: #374151;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.count-btn:hover {
  border-color: #66FFB3;
  background: #F0FFF8;
  transform: translateY(-1px);
}

.count-btn.active {
  background: linear-gradient(135deg, #0BFC67 0%, #66FFB3 100%);
  border-color: #0BFC67;
  color: white;
  box-shadow: 0 2px 8px rgba(11, 252, 103, 0.3);
}

/* Advanced Options */
.advanced-options {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.option-checkbox {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  padding: 12px 16px;
  background: white;
  border: 2px solid #E8FEF0;
  border-radius: 10px;
  transition: all 0.3s ease;
  user-select: none;
}

.option-checkbox:hover {
  border-color: #66FFB3;
  background: #F0FFF8;
}

.option-checkbox input[type="checkbox"] {
  width: 20px;
  height: 20px;
  accent-color: #0BFC67;
  cursor: pointer;
}

.option-checkbox span {
  font-weight: 500;
  color: #374151;
}

/* Content Spacer */
.content-spacer {
  flex: 1;
  min-height: 1rem;
}

/* Generate Button */
.button-container {
  margin-top: auto;
  padding-top: 1rem;
  border-top: 2px solid #E8FEF0;
}

.generate-button {
  width: 100%;
  padding: 18px 24px;
  background: linear-gradient(135deg, #0BFC67 0%, #66FFB3 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1.1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(11, 252, 103, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
}

.generate-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(11, 252, 103, 0.4);
}

.generate-button:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(11, 252, 103, 0.3);
}

.generate-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.button-content {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.button-icon {
  width: 24px;
  height: 24px;
}

.spinner-icon {
  width: 24px;
  height: 24px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .count-buttons {
    grid-template-columns: repeat(5, 1fr);
  }
  
  .time-buttons {
    flex-direction: column;
  }
  
  .time-btn {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .settings-content {
    padding: 1.5rem;
  }
  
  .count-buttons {
    grid-template-columns: repeat(5, 1fr);
    gap: 0.4rem;
  }
  
  .count-btn {
    padding: 8px;
    font-size: 0.9rem;
  }
}
</style>