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
          v-for="(comment, index) in comments"
          :key="index"
          class="comment-item"
        >
          <div class="comment-header">
            <span class="comment-number">#{{ index + 1 }}</span>
            <button 
              @click="copyComment(comment, index)"
              :class="['copy-button', { copied: copiedIndex === index }]"
            >
              <span v-if="copiedIndex === index">✓ コピー済み</span>
              <span v-else>📋 コピー</span>
            </button>
          </div>
          <div class="comment-text">
            {{ comment }}
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

<script setup>
const props = defineProps({
  comments: {
    type: Array,
    default: () => []
  },
  isLoading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['regenerate', 'clear'])

const copiedIndex = ref(-1)
const copyTimeout = ref(null)
const timestampCopied = ref(false)

const formatDate = () => {
  const now = new Date()
  return now.toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

const formatTime = () => {
  const now = new Date()
  return now.toLocaleTimeString('ja-JP', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const copyTimestamp = async () => {
  try {
    const timestamp = `${formatDate()} ${formatTime()}`
    await navigator.clipboard.writeText(timestamp)
    timestampCopied.value = true
    
    setTimeout(() => {
      timestampCopied.value = false
    }, 2000)
  } catch (error) {
    console.error('タイムスタンプのコピーに失敗しました:', error)
  }
}

const copyComment = async (comment, index) => {
  try {
    await navigator.clipboard.writeText(comment)
    copiedIndex.value = index
    
    // Clear the copied state after 2 seconds
    if (copyTimeout.value) {
      clearTimeout(copyTimeout.value)
    }
    copyTimeout.value = setTimeout(() => {
      copiedIndex.value = -1
    }, 2000)
  } catch (error) {
    console.error('コピーに失敗しました:', error)
  }
}

const copyAllComments = async () => {
  try {
    const allComments = props.comments.join('\n\n')
    await navigator.clipboard.writeText(allComments)
    
    // Show feedback for all comments copied
    copiedIndex.value = -2 // Special value for "all copied"
    if (copyTimeout.value) {
      clearTimeout(copyTimeout.value)
    }
    copyTimeout.value = setTimeout(() => {
      copiedIndex.value = -1
    }, 2000)
  } catch (error) {
    console.error('全コメントのコピーに失敗しました:', error)
  }
}

const clearComments = () => {
  emit('clear')
}

const regenerateComments = () => {
  emit('regenerate')
}

onUnmounted(() => {
  if (copyTimeout.value) {
    clearTimeout(copyTimeout.value)
  }
})
</script>

<style scoped>
.generated-comment {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(12, 65, 154, 0.1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 400px;
}

.component-header {
  background: linear-gradient(135deg, #0C419A 0%, #6BA2FC 100%);
  color: white;
  padding: 20px 24px;
  border-bottom: 3px solid #6BA2FC;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
  min-height: 60px;
}

.component-header h3 {
  font-size: 1.4rem;
  font-weight: 700;
  margin: 0;
  color: white;
}

.comment-count {
  font-size: 0.875rem;
  background: rgba(255, 255, 255, 0.2);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.comment-content {
  padding: 24px;
  flex: 1;
  overflow-y: auto;
}

.loading-state {
  text-align: center;
  padding: 3rem 1rem;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e1e5e9;
  border-top: 4px solid #6BA2FC;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-state p {
  color: #666;
  font-size: 1.1rem;
}

.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  color: #666;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.empty-state p {
  font-size: 1.1rem;
  line-height: 1.6;
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.comments-header {
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e1e5e9;
}

.timestamp-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.copy-timestamp-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, #6BA2FC 0%, #0C419A 100%);
  color: white;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.copy-timestamp-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(12, 65, 154, 0.3);
}

.copy-timestamp-btn.copied {
  background: #28a745;
}

.timestamp {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.date {
  font-size: 1rem;
  font-weight: 600;
  color: #0C419A;
}

.time {
  font-size: 0.9rem;
  color: #6BA2FC;
}

.comment-item {
  border: 2px solid #e1e5e9;
  border-radius: 8px;
  overflow: hidden;
  transition: border-color 0.2s ease;
}

.comment-item:hover {
  border-color: #6BA2FC;
}

.comment-header {
  background: #f8f9fa;
  padding: 0.75rem 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.comment-number {
  font-weight: 600;
  color: #666;
}

.copy-button {
  padding: 0.5rem 0.75rem;
  background: #6BA2FC;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.copy-button:hover {
  background: #5a91e6;
}

.copy-button.copied {
  background: #28a745;
}

.comment-text {
  padding: 1rem;
  font-size: 1rem;
  line-height: 1.6;
  color: #333;
  white-space: pre-wrap;
}

.action-buttons {
  display: flex;
  gap: 0.75rem;
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 2px solid #e1e5e9;
}

.action-button {
  flex: 1;
  padding: 0.75rem;
  border: 2px solid transparent;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.action-button.copy-all {
  background: #6BA2FC;
  color: white;
}

.action-button.copy-all:hover {
  background: #5a91e6;
  transform: translateY(-2px);
}

.action-button.clear {
  background: #dc3545;
  color: white;
}

.action-button.clear:hover {
  background: #c82333;
  transform: translateY(-2px);
}

.action-button.regenerate {
  background: #28a745;
  color: white;
}

.action-button.regenerate:hover {
  background: #218838;
  transform: translateY(-2px);
}

.button-icon {
  font-size: 1rem;
}

@media (max-width: 768px) {
  .action-buttons {
    flex-direction: column;
  }
  
  .comment-header {
    flex-direction: column;
    gap: 0.5rem;
    align-items: flex-start;
  }
}

@media (max-width: 480px) {
  .comment-content {
    padding: 1rem;
  }
  
  .component-header {
    flex-direction: column;
    gap: 0.5rem;
    align-items: flex-start;
  }
}
</style>
