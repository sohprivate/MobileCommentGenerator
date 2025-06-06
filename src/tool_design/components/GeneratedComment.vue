<template>
  <div class="generated-comment">
    <div class="component-header">
      <h3>生成されたコメント</h3>
      <span v-if="comments.length > 0" class="comment-count">
        {{ comments.length }}個のコメント
      </span>
    </div>
    
    <div class="comment-content">
      <!-- Loading State -->
      <div v-if="isLoading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>コメントを生成中です...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="error-state">
        <div class="error-icon">⚠️</div>
        <p class="error-message">{{ error }}</p>
        <button @click="retry" class="retry-button">再試行</button>
      </div>

      <!-- Empty State -->
      <div v-else-if="comments.length === 0" class="empty-state">
        <div class="empty-icon">💬</div>
        <p>「コメントを生成する」ボタンを押して、天気コメントを作成してください。</p>
      </div>

      <!-- Generated Comments -->
      <div v-else class="comments-list">
        <div class="comments-header">
          <div class="timestamp-section">
            <button 
              @click="copyTimestamp"
              :class="['copy-timestamp-btn', { copied: timestampCopied }]"
            >
              <span v-if="timestampCopied">✓</span>
              <span v-else>📋</span>
            </button>
            <div class="timestamp">
              <div class="date">{{ formatDate() }}</div>
              <div class="time">{{ formatTime() }}</div>
            </div>
          </div>
        </div>
        
        <div 
          v-for="(comment, index) in displayedComments"
          :key="comment.id"
          class="comment-item"
        >
          <div class="comment-header">
            <span class="comment-number">#{{ index + 1 }}</span>
            <button 
              @click="copyComment(comment.text, index)"
              :class="['copy-button', { copied: copiedIndex === index }]"
            >
              <span v-if="copiedIndex === index">✓ コピー済み</span>
              <span v-else>📋 コピー</span>
            </button>
          </div>
          <div class="comment-text">
            {{ comment.text }}
          </div>
          <div v-if="comment.location" class="comment-meta">
            <span class="meta-location">📍 {{ comment.location }}</span>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="action-buttons">
          <button @click="copyAllComments" class="action-button copy-all">
            <span class="button-icon">📋</span>
            全てコピー
          </button>
          <button @click="clearComments" class="action-button clear">
            <span class="button-icon">🗑️</span>
            クリア
          </button>
          <button @click="regenerateComments" class="action-button regenerate">
            <span class="button-icon">🔄</span>
            再生成
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, defineProps, defineEmits } from 'vue'
import type { GeneratedComment } from '~/types'

// Props
interface Props {
  comments: GeneratedComment[]
  isLoading?: boolean
  error?: string | null
}

const props = defineProps<Props>()

// Emits
interface Emits {
  (e: 'regenerate'): void
  (e: 'clear'): void
}

const emit = defineEmits<Emits>()

// State
const copiedIndex = ref(-1)
const copyTimeout = ref<NodeJS.Timeout | null>(null)
const timestampCopied = ref(false)

// Computed
const displayedComments = computed(() => {
  return props.comments.map((comment, index) => {
    if (typeof comment === 'string') {
      // 後方互換性のため、文字列の場合は GeneratedComment オブジェクトに変換
      return {
        id: `comment-${index}`,
        text: comment,
        timestamp: new Date().toISOString()
      }
    }
    return comment
  })
})

// Methods
const formatDate = () => {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}/${month}/${day}`
}

const formatTime = () => {
  const now = new Date()
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  return `${hours}:${minutes}`
}

const copyComment = async (comment: string, index: number) => {
  try {
    await navigator.clipboard.writeText(comment)
    copiedIndex.value = index
    
    if (copyTimeout.value) {
      clearTimeout(copyTimeout.value)
    }
    
    copyTimeout.value = setTimeout(() => {
      copiedIndex.value = -1
    }, 2000)
  } catch (err) {
    console.error('Failed to copy comment:', err)
    // フォールバック: テキストエリアを使用
    const textarea = document.createElement('textarea')
    textarea.value = comment
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    
    copiedIndex.value = index
    if (copyTimeout.value) {
      clearTimeout(copyTimeout.value)
    }
    copyTimeout.value = setTimeout(() => {
      copiedIndex.value = -1
    }, 2000)
  }
}

const copyTimestamp = async () => {
  const timestamp = `【${formatDate()} ${formatTime()}】`
  try {
    await navigator.clipboard.writeText(timestamp)
    timestampCopied.value = true
    setTimeout(() => {
      timestampCopied.value = false
    }, 2000)
  } catch (err) {
    console.error('Failed to copy timestamp:', err)
  }
}

const copyAllComments = async () => {
  const allText = displayedComments.value.map(c => c.text).join('\n')
  try {
    await navigator.clipboard.writeText(allText)
    // 全てのコメントを一時的にコピー済み表示にする
    copiedIndex.value = -2 // 特別な値で全てコピーを示す
    setTimeout(() => {
      copiedIndex.value = -1
    }, 2000)
  } catch (err) {
    console.error('Failed to copy all comments:', err)
  }
}

const clearComments = () => {
  emit('clear')
}

const regenerateComments = () => {
  emit('regenerate')
}

const retry = () => {
  emit('regenerate')
}

// Cleanup
onUnmounted(() => {
  if (copyTimeout.value) {
    clearTimeout(copyTimeout.value)
  }
})
</script>

<style scoped>
.generated-comment {
  background: linear-gradient(135deg, #FEE8F3 0%, #FFF3F8 100%);
  border-radius: 16px;
  padding: 0;
  box-shadow: 0 4px 12px rgba(252, 11, 128, 0.1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.component-header {
  background: linear-gradient(135deg, #FC0B80 0%, #FF66B3 100%);
  color: white;
  padding: 1.5rem 2rem;
  border-bottom: 3px solid #FF66B3;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.component-header h3 {
  font-size: 1.4rem;
  font-weight: 700;
  margin: 0;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
}

.comment-count {
  background: rgba(255, 255, 255, 0.2);
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 600;
}

.comment-content {
  padding: 2rem;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* Loading State */
.loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  text-align: center;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #FEE8F3;
  border-top-color: #FC0B80;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-state p, .error-state p {
  color: #6B7280;
  font-size: 1.1rem;
}

/* Error State */
.error-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.error-message {
  color: #dc3545;
  margin-bottom: 1rem;
}

.retry-button {
  padding: 10px 20px;
  background: #FC0B80;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.retry-button:hover {
  background: #e00b72;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(252, 11, 128, 0.3);
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  text-align: center;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.empty-state p {
  color: #6B7280;
  font-size: 1.1rem;
  max-width: 80%;
}

/* Comments List */
.comments-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.comments-header {
  margin-bottom: 1rem;
}

.timestamp-section {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: white;
  padding: 12px 16px;
  border-radius: 10px;
  border: 2px solid #FEE8F3;
  box-shadow: 0 2px 8px rgba(252, 11, 128, 0.05);
}

.copy-timestamp-btn {
  padding: 8px 12px;
  background: #FC0B80;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 1rem;
}

.copy-timestamp-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(252, 11, 128, 0.3);
}

.copy-timestamp-btn.copied {
  background: #10B981;
}

.timestamp {
  display: flex;
  gap: 1rem;
  font-weight: 600;
  color: #374151;
}

.date, .time {
  font-size: 1.1rem;
}

/* Comment Item */
.comment-item {
  background: white;
  border: 2px solid #FEE8F3;
  border-radius: 12px;
  padding: 1.5rem;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(252, 11, 128, 0.05);
}

.comment-item:hover {
  border-color: #FF66B3;
  box-shadow: 0 4px 12px rgba(255, 102, 179, 0.2);
  transform: translateY(-1px);
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.comment-number {
  font-weight: 700;
  color: #FC0B80;
  font-size: 1.1rem;
}

.copy-button {
  padding: 8px 16px;
  background: linear-gradient(135deg, #FC0B80 0%, #FF66B3 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.9rem;
}

.copy-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(252, 11, 128, 0.3);
}

.copy-button.copied {
  background: linear-gradient(135deg, #10B981 0%, #34D399 100%);
}

.comment-text {
  font-size: 1.1rem;
  line-height: 1.6;
  color: #374151;
  word-wrap: break-word;
}

.comment-meta {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: #6B7280;
}

.meta-location {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}

/* Action Buttons */
.action-buttons {
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 2px solid #FEE8F3;
}

.action-button {
  flex: 1;
  padding: 14px 20px;
  border: 2px solid transparent;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-size: 0.95rem;
}

.button-icon {
  font-size: 1.2rem;
}

.copy-all {
  background: #E8F0FE;
  color: #0C419A;
  border-color: #6BA2FC;
}

.copy-all:hover {
  background: #6BA2FC;
  color: white;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(107, 162, 252, 0.3);
}

.clear {
  background: #FFF0F0;
  color: #dc3545;
  border-color: #ffcccc;
}

.clear:hover {
  background: #dc3545;
  color: white;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(220, 53, 69, 0.3);
}

.regenerate {
  background: #F0FFF8;
  color: #0BFC67;
  border-color: #66FFB3;
}

.regenerate:hover {
  background: #0BFC67;
  color: white;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(11, 252, 103, 0.3);
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .comment-content {
    padding: 1.5rem;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .action-button {
    width: 100%;
  }
  
  .timestamp {
    flex-direction: column;
    gap: 0.25rem;
  }
  
  .date, .time {
    font-size: 1rem;
  }
}

@media (max-width: 480px) {
  .component-header {
    padding: 1rem 1.5rem;
  }
  
  .component-header h3 {
    font-size: 1.2rem;
  }
  
  .comment-item {
    padding: 1rem;
  }
  
  .comment-text {
    font-size: 1rem;
  }
  
  .action-button {
    padding: 12px 16px;
    font-size: 0.9rem;
  }
}
</style>