<template>
  <div class="generate-panel" v-if="taskId">
    <div class="studio-container">
      <!-- Studio Header -->
      <div class="studio-header">
        <h3>AI圆桌派录音棚</h3>
        <p class="live-indicator">
          <span class="live-dot"></span>
          <span>{{ currentStageLabel || '准备中' }}</span>
        </p>
      </div>

      <!-- Virtual Podcast Room -->
      <div class="podcast-room">
        <!-- Host -->
        <div class="participant host" :class="getSpeakingClass('host')">
          <div class="avatar">
            <svg viewBox="0 0 24 24" width="40" height="40" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
            </svg>
          </div>
          <div class="participant-info">
            <span class="name">主持人</span>
            <div class="speaking-wave" :class="{ active: isSpeaking('host') }"></div>
          </div>
        </div>

        <!-- Guests -->
        <div class="guests-container">
          <div class="participant guest-a" :class="getSpeakingClass('guest-a')">
            <div class="avatar">
              <svg viewBox="0 0 24 24" width="36" height="36" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
              </svg>
            </div>
            <div class="participant-info">
              <span class="name">技术专家</span>
              <div class="speaking-wave" :class="{ active: isSpeaking('guest-a') }"></div>
            </div>
          </div>

          <div class="participant guest-b" :class="getSpeakingClass('guest-b')">
            <div class="avatar">
              <svg viewBox="0 0 24 24" width="36" height="36" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.ari 3.22-6 3.22z"/>
              </svg>
            </div>
            <div class="participant-info">
              <span class="name">产品经理</span>
              <div class="speaking-wave" :class="{ active: isSpeaking('guest-b') }"></div>
            </div>
          </div>
        </div>

        <!-- Mic Stand -->
        <div class="mic-stand">
          <div class="mic-head"></div>
          <div class="mic-pole"></div>
          <div class="mic-base"></div>
        </div>
      </div>

      <!-- Stage Progress -->
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

      <!-- Current Detail -->
      <div class="detail-container">
        <p class="detail-text">{{ detail }}</p>
        <p v-if="error" class="error-text">{{ error }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

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
const currentSpeaker = ref('')
let eventSource = null
let speakerInterval = null

const currentStageLabel = computed(() => {
  const stage = stages.find(s => s.key === currentStage.value)
  return stage ? stage.label : ''
})

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
  if (cls === 'completed') return '✓'
  if (cls === 'active') return '○'
  return '·'
}

function getSpeakingClass(participant) {
  return currentSpeaker.value === participant ? 'speaking' : ''
}

function isSpeaking(participant) {
  return currentSpeaker.value === participant
}

function simulateSpeaking() {
  const speakers = ['host', 'guest-a', 'guest-b', '']
  let idx = 0

  speakerInterval = setInterval(() => {
    // Only simulate speaking during dialogue and tts stages
    if (currentStage.value === 'dialogue' || currentStage.value === 'tts') {
      currentSpeaker.value = speakers[idx % speakers.length]
      idx++
    } else {
      currentSpeaker.value = ''
    }
  }, 3000)
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
        clearInterval(speakerInterval)
        setTimeout(() => emit('completed'), 1500)
      }
      if (data.status === 'failed') {
        error.value = data.detail
        eventSource.close()
        clearInterval(speakerInterval)
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

  simulateSpeaking()
})

onUnmounted(() => {
  if (eventSource) eventSource.close()
  if (speakerInterval) clearInterval(speakerInterval)
})
</script>

<style scoped>
.generate-panel {
  margin-bottom: 2rem;
}

.studio-container {
  background: white;
  border-radius: 24px;
  padding: 2rem;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
}

.studio-header {
  text-align: center;
  margin-bottom: 2rem;
}

.studio-header h3 {
  font-size: 1.6rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.live-indicator {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #6b7280;
}

.live-dot {
  width: 8px;
  height: 8px;
  background: #ef4444;
  border-radius: 50%;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

.podcast-room {
  position: relative;
  background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
  border-radius: 20px;
  padding: 2rem;
  min-height: 240px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 2rem;
}

.podcast-room::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 80%;
  height: 100%;
  background: radial-gradient(ellipse at center, rgba(99, 102, 241, 0.1) 0%, transparent 70%);
}

.participant {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
  z-index: 1;
}

.host {
  position: absolute;
  top: 50%;
  left: 20%;
  transform: translateY(-50%);
}

.guests-container {
  position: absolute;
  right: 20%;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.guest-a {
  transform: translateY(-20px);
}

.guest-b {
  transform: translateY(20px);
}

.avatar {
  width: 56px;
  height: 56px;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  color: #6b7280;
}

.host .avatar {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
}

.guest-a .avatar {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
}

.guest-b .avatar {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.participant.speaking .avatar {
  transform: scale(1.15);
  box-shadow: 0 0 20px rgba(99, 102, 241, 0.4);
}

.participant-info {
  text-align: center;
}

.name {
  font-size: 0.8rem;
  font-weight: 600;
  color: #6b7280;
}

.speaking-wave {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
  height: 16px;
  margin-top: 4px;
  opacity: 0;
  transition: opacity 0.3s;
}

.speaking-wave.active {
  opacity: 1;
}

.speaking-wave::before,
.speaking-wave::after {
  content: '';
  width: 3px;
  height: 8px;
  background: #6366f1;
  border-radius: 2px;
  animation: wave 0.5s ease-in-out infinite alternate;
}

.speaking-wave::after {
  animation-delay: 0.25s;
}

@keyframes wave {
  0% { height: 4px; }
  100% { height: 12px; }
}

.mic-stand {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
}

.mic-head {
  width: 40px;
  height: 60px;
  background: linear-gradient(180deg, #374151 0%, #1f2937 100%);
  border-radius: 8px 8px 4px 4px;
  margin: 0 auto;
  position: relative;
}

.mic-head::before {
  content: '';
  position: absolute;
  top: 8px;
  left: 50%;
  transform: translateX(-50%);
  width: 28px;
  height: 28px;
  background: radial-gradient(circle, #6b7280 0%, #374151 100%);
  border-radius: 50%;
}

.mic-pole {
  width: 8px;
  height: 100px;
  background: linear-gradient(90deg, #4b5563 0%, #6b7280 50%, #4b5563 100%);
  margin: 0 auto;
}

.mic-base {
  width: 60px;
  height: 12px;
  background: linear-gradient(180deg, #374151 0%, #1f2937 100%);
  border-radius: 6px;
  margin: 0 auto;
}

.stages {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.stage-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 10px;
  font-size: 0.85rem;
  font-weight: 500;
  transition: all 0.3s ease;
}

.stage-item.completed {
  background: #f0fdf4;
  color: #16a34a;
  border: 1px solid #bbf7d0;
}

.stage-item.active {
  background: linear-gradient(135deg, #e0e7ff 0%, #fae8ff 100%);
  color: #6366f1;
  border: 1px solid #c4b5fd;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.2);
}

.stage-item.pending {
  background: #f3f4f6;
  color: #9ca3af;
}

.stage-icon {
  font-weight: 700;
  font-size: 1rem;
}

.detail-container {
  text-align: center;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}

.detail-text {
  color: #6b7280;
  font-size: 0.9rem;
  line-height: 1.6;
}

.error-text {
  color: #dc2626;
  font-size: 0.9rem;
  margin-top: 0.5rem;
  font-weight: 500;
}
</style>
