<template>
  <div class="generate-panel" v-if="taskId">
    <h3>🔄 生成进度</h3>
    <div class="stages">
      <div
        v-for="stage in stages"
        :key="stage.key"
        class="stage-item"
        :class="getStageClass(stage.key)"
      >
        <span class="stage-icon">{{ getStageIcon(stage.key) }}</span>
        <span class="stage-label">{{ stage.label }}</span>
      </div>
    </div>
    <p class="detail-text">{{ detail }}</p>
    <p v-if="error" class="error-text">❌ {{ error }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({ taskId: String })
const emit = defineEmits(['completed'])

const stages = [
  { key: 'news', label: '获取资讯' },
  { key: 'topic', label: '选定话题' },
  { key: 'research', label: '深度搜索' },
  { key: 'planning', label: '节目策划' },
  { key: 'dialogue', label: '生成文本' },
  { key: 'tts', label: '语音合成' },
  { key: 'audio', label: '音频拼接' },
  { key: 'done', label: '完成' },
]

const currentStage = ref('')
const detail = ref('')
const error = ref('')
let eventSource = null

function getStageClass(key) {
  const stageKeys = stages.map(s => s.key)
  const currentIdx = stageKeys.indexOf(currentStage.value)
  const itemIdx = stageKeys.indexOf(key)
  if (itemIdx < currentIdx) return 'completed'
  if (itemIdx === currentIdx) return 'active'
  return 'pending'
}

function getStageIcon(key) {
  const cls = getStageClass(key)
  if (cls === 'completed') return '✅'
  if (cls === 'active') return '⏳'
  return '⬜'
}

onMounted(() => {
  eventSource = new EventSource(`/api/status/${props.taskId}`)
  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      currentStage.value = data.stage || ''
      detail.value = data.detail || ''
      if (data.status === 'completed') {
        eventSource.close()
        setTimeout(() => emit('completed'), 1500)
      }
      if (data.status === 'failed') {
        error.value = data.detail
        eventSource.close()
        setTimeout(() => emit('completed'), 3000)
      }
    } catch (e) {
      console.error('Failed to parse SSE:', e)
    }
  }
  eventSource.onerror = () => {
    error.value = '连接中断'
    eventSource.close()
  }
})

onUnmounted(() => {
  if (eventSource) eventSource.close()
})
</script>

<style scoped>
.generate-panel {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.generate-panel h3 {
  margin-bottom: 1rem;
}

.stages {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.stage-item {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.3rem 0.6rem;
  border-radius: 8px;
  font-size: 0.85rem;
}

.stage-item.completed {
  color: #34c759;
}

.stage-item.active {
  color: #667eea;
  font-weight: 600;
}

.stage-item.pending {
  color: #c7c7cc;
}

.detail-text {
  color: #515154;
  font-size: 0.9rem;
}

.error-text {
  color: #ff3b30;
  font-size: 0.9rem;
  margin-top: 0.5rem;
}
</style>
