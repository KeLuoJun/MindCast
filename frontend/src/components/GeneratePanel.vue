<template>
  <div class="generate-panel" v-if="taskId">
    <div class="studio-container">
      <!-- Header -->
      <div class="studio-header">
        <div class="studio-badge">
          <span class="live-dot"></span>
          录音棚
        </div>
        <h3>MindCast 录音棚</h3>
        <p class="stage-name">{{ currentStageLabel }}</p>
      </div>

      <!-- Studio Scene -->
      <div class="studio-scene">
        <div class="scene-bg">
          <div class="bg-gradient"></div>
          <div class="bg-grid"></div>
        </div>
        
        <!-- Host Area -->
        <div class="host-section">
          <div class="person host" :class="{ speaking: isSpeaking('host') }">
            <div class="avatar host-avatar">
              <span class="avatar-emoji"></span>
              <div class="mic-glow" v-if="isSpeaking('host')"></div>
            </div>
            <div class="person-info">
              <span class="role">主持人</span>
              <span class="name">林晨曦</span>
            </div>
            <div class="sound-bar" :class="{ active: isSpeaking('host') }">
              <span></span><span></span><span></span><span></span>
            </div>
          </div>
        </div>

        <!-- Desktop Environment -->
        <div class="studio-desk">
          <div class="desk-surface">
            <div class="desk-logo">MindCast</div>
          </div>
        </div>

        <!-- Guests Area -->
        <div class="guests-section">
          <div 
            v-for="(guest, idx) in selectedGuestObjects" 
            :key="guest.name"
            class="person guest" 
            :class="[`guest-${idx + 1}`, { speaking: isSpeaking(`guest-${idx}`) }]"
          >
            <div 
              class="avatar guest-avatar" 
              :style="{ background: getAvatarGradient(guest.mbti) }"
            >
              <span class="avatar-initial">{{ guest.name.charAt(0) }}</span>
              <div class="mic-glow" v-if="isSpeaking(`guest-${idx}`)"></div>
            </div>
            <div class="person-info">
              <span class="role">{{ guest.occupation }}</span>
              <span class="name">{{ guest.name }}</span>
            </div>
            <div class="sound-bar" :class="{ active: isSpeaking(`guest-${idx}`) }">
              <span></span><span></span><span></span><span></span>
            </div>
          </div>
        </div>

        <!-- Atmospheric Elements -->
        <div class="studio-decorations">
          <div class="lamp lamp-left"></div>
          <div class="lamp lamp-right"></div>
        </div>
      </div>

      <!-- Progress -->
      <div class="progress-bar">
        <div
          v-for="(stage, idx) in stages"
          :key="stage.key"
          class="progress-step"
          :class="getStageClass(stage.key)"
        >
          <div class="step-dot">
            <svg v-if="getStageClass(stage.key) === 'completed'" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="3">
              <polyline points="20,6 9,17 4,12"/>
            </svg>
          </div>
          <span class="step-label">{{ stage.label }}</span>
          <div v-if="idx < stages.length - 1" class="step-line" :class="{ filled: getStageClass(stage.key) === 'completed' }"></div>
        </div>
      </div>

      <!-- Status -->
      <div class="status-box">
        <div class="status-icon">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="16" x2="12" y2="12"/>
            <line x1="12" y1="8" x2="12.01" y2="8"/>
          </svg>
        </div>
        <p class="status-text">{{ detail || '等待执行...' }}</p>
        <button
          v-if="!isCompleted && !error"
          class="btn-cancel"
          :disabled="cancelling"
          @click="cancelTask"
        >
          {{ cancelling ? '终止中...' : '终止生成' }}
        </button>
        <p v-if="error" class="error-text">{{ error }}</p>
      </div>

      <!-- Completion -->
      <transition name="fade">
        <div v-if="isCompleted" class="complete-overlay">
          <div class="complete-box">
            <div class="complete-icon">
              <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="16,8 10,14 8,12"/>
              </svg>
            </div>
            <h4>生成完成！</h4>
            <p>即将跳转...</p>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useWorkflowStore } from '../stores/workflow'

const props = defineProps({ taskId: String })
const emit = defineEmits(['completed'])

const store = useWorkflowStore()

const stages = [
  { key: 'news', label: '获取资讯' },
  { key: 'topic', label: '选定话题' },
  { key: 'research', label: '深度搜索' },
  { key: 'planning', label: '节目策划' },
  { key: 'dialogue', label: '生成文本' },
  { key: 'article', label: '撰写文章' },
  { key: 'audio', label: '音频拼接' },
  { key: 'done', label: '完成' },
]

const currentStage = ref('')
const detail = ref('')
const error = ref('')
const cancelling = ref(false)
const currentSpeaker = ref('')
const isCompleted = ref(false)
let eventSource = null
let speakerInterval = null

const selectedGuestObjects = computed(() => {
  return store.guests.filter(g => store.selectedGuests.includes(g.name))
})

const currentStageLabel = computed(() => {
  if (currentStage.value === 'cancelled') return '已终止'
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

function isSpeaking(participant) {
  return currentSpeaker.value === participant
}

function getAvatarGradient(mbti) {
  const gradients = {
    'INTJ': 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
    'INTP': 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
    'ENTJ': 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
    'ENTP': 'linear-gradient(135deg, #ec4899 0%, #db2777 100%)',
    'INFJ': 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    'INFP': 'linear-gradient(135deg, #14b8a6 0%, #0d9488 100%)',
    'ENFJ': 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)',
    'ENFP': 'linear-gradient(135deg, #f43f5e 0%, #e11d48 100%)',
    'ISTJ': 'linear-gradient(135deg, #64748b 0%, #475569 100%)',
    'ISFJ': 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
    'ESTJ': 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
    'ESFJ': 'linear-gradient(135deg, #a855f7 0%, #9333ea 100%)',
    'ISTP': 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)',
    'ISFP': 'linear-gradient(135deg, #84cc16 0%, #65a30d 100%)',
    'ESTP': 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
    'ESFP': 'linear-gradient(135deg, #fb923c 0%, #f97316 100%)'
  }
  return gradients[mbti] || 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)'
}

function simulateSpeaking() {
  speakerInterval = setInterval(() => {
    if (currentStage.value === 'dialogue' || currentStage.value === 'audio') {
      const participants = ['host', ...selectedGuestObjects.value.map((_, i) => `guest-${i}`)]
      const randomIdx = Math.floor(Math.random() * participants.length)
      currentSpeaker.value = participants[randomIdx]
    } else {
      currentSpeaker.value = ''
    }
  }, 2500)
}

async function cancelTask() {
  if (!props.taskId || cancelling.value) return
  cancelling.value = true
  try {
    await fetch(`/api/tasks/${props.taskId}/cancel`, { method: 'POST' })
    detail.value = '任务已终止'
    currentStage.value = 'cancelled'
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
    if (speakerInterval) {
      clearInterval(speakerInterval)
      speakerInterval = null
    }
    setTimeout(() => emit('completed', null), 600)
  } catch (e) {
    error.value = '终止失败，请重试'
  } finally {
    cancelling.value = false
  }
}

onMounted(() => {
  eventSource = new EventSource(`/api/status/${props.taskId}`)
  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      currentStage.value = data.stage || ''
      detail.value = data.detail || ''
      if (data.status === 'completed') {
        isCompleted.value = true
        eventSource.close()
        eventSource = null
        clearInterval(speakerInterval)
        speakerInterval = null
        const episodeId = data.episode_id || null
        setTimeout(() => emit('completed', episodeId), 2500)
      }
      if (data.status === 'failed') {
        error.value = data.detail
        eventSource.close()
        eventSource = null
        clearInterval(speakerInterval)
        speakerInterval = null
        setTimeout(() => emit('completed', null), 3000)
      }
      if (data.status === 'cancelled') {
        detail.value = data.detail || '任务已终止'
        currentStage.value = 'cancelled'
        if (eventSource) {
          eventSource.close()
          eventSource = null
        }
        if (speakerInterval) {
          clearInterval(speakerInterval)
          speakerInterval = null
        }
        setTimeout(() => emit('completed', null), 600)
      }
    } catch (e) {
      console.error('SSE parse error:', e)
    }
  }
  eventSource.onerror = () => {
    error.value = '连接中断'
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
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
  margin-top: 1rem;
}

.studio-container {
  position: relative;
  background: var(--c-surface);
  border-radius: var(--r-xl);
  border: 2px solid var(--c-border);
  padding: 1.75rem;
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

/*  Header  */
.studio-header {
  text-align: center;
  margin-bottom: 1.5rem;
}

.studio-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 107, 53, 0.1);
  border: 2px solid rgba(255, 107, 53, 0.2);
  padding: 5px 14px;
  border-radius: var(--r-full);
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--c-primary);
  margin-bottom: 0.75rem;
}

.studio-badge .live-dot {
  width: 6px;
  height: 6px;
  background: var(--c-primary);
  border-radius: 50%;
  animation: livePulse 1.5s infinite;
}

@keyframes livePulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(0.8); }
}

.studio-header h3 {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--c-text-1);
  margin-bottom: 0.25rem;
}

.stage-name {
  color: var(--c-text-2);
  font-size: 0.9rem;
}

/*  Studio Scene  */
.studio-scene {
  position: relative;
  background: linear-gradient(180deg, #fffcf9 0%, #fef3e7 100%);
  border-radius: var(--r-xl);
  border: 1px solid var(--c-border);
  padding: 3rem 1.5rem 1rem;
  min-height: 320px;
  margin-bottom: 2rem;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.scene-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.bg-gradient {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 200px;
  background: radial-gradient(circle at 50% 0%, rgba(255, 107, 53, 0.1) 0%, transparent 70%);
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(rgba(240, 224, 212, 0.3) 1px, transparent 1px),
    linear-gradient(90deg, rgba(240, 224, 212, 0.3) 1px, transparent 1px);
  background-size: 30px 30px;
}

/*  Host & Guest Sections  */
.host-section {
  position: relative;
  z-index: 5;
  margin-bottom: 2rem;
}

.guests-section {
  display: flex;
  justify-content: center;
  gap: 3rem;
  width: 100%;
  position: relative;
  z-index: 5;
  margin-bottom: 2.5rem;
}

.person {
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: all 0.4s var(--ease-bounce);
}

.person.speaking {
  transform: translateY(-8px) scale(1.05);
}

.avatar {
  position: relative;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 15px rgba(45, 27, 14, 0.15);
  border: 4px solid white;
}

.host-avatar {
  width: 72px;
  height: 72px;
  background: linear-gradient(135deg, var(--c-primary) 0%, var(--c-primary-hover) 100%);
}

.guest-avatar {
  width: 64px;
  height: 64px;
}

.avatar-initial {
  font-size: 1.5rem;
  font-weight: 700;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.avatar-emoji {
  font-size: 2rem;
}

.mic-glow {
  position: absolute;
  inset: -10px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 107, 53, 0.3) 0%, transparent 70%);
  animation: glowPulse 2s infinite ease-in-out;
}

@keyframes glowPulse {
  0% { transform: scale(0.9); opacity: 0.5; }
  50% { transform: scale(1.1); opacity: 0.8; }
  100% { transform: scale(0.9); opacity: 0.5; }
}

.person-info {
  text-align: center;
  margin-top: 10px;
}

.person-info .role {
  display: block;
  font-size: 0.7rem;
  color: var(--c-text-3);
  margin-bottom: 2px;
}

.person-info .name {
  display: block;
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--c-text-1);
}

/*  Desktop UI  */
.studio-desk {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 90%;
  height: 80px;
  perspective: 1000px;
}

.desk-surface {
  width: 100%;
  height: 100%;
  background: linear-gradient(180deg, #f7f0e9 0%, #e8ddd1 100%);
  border-radius: 50% 50% 0 0 / 100% 100% 0 0;
  border: 1px solid var(--c-border);
  display: flex;
  justify-content: center;
  align-items: flex-end;
  padding-bottom: 12px;
}

.desk-logo {
  font-family: 'Inter', sans-serif;
  font-weight: 900;
  font-size: 12px;
  letter-spacing: 4px;
  color: rgba(45, 27, 14, 0.15);
  text-transform: uppercase;
}

/*  Sound Bar  */
.sound-bar {
  display: flex;
  align-items: center;
  gap: 3px;
  height: 20px;
  margin-top: 8px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.sound-bar.active { opacity: 1; }

.sound-bar span {
  width: 3px;
  background: var(--c-primary);
  border-radius: 4px;
}

.speaking .sound-bar span:nth-child(1) { animation: soundWave 0.5s infinite ease-in-out alternate; }
.speaking .sound-bar span:nth-child(2) { animation: soundWave 0.7s -0.2s infinite ease-in-out alternate; }
.speaking .sound-bar span:nth-child(3) { animation: soundWave 0.4s -0.3s infinite ease-in-out alternate; }
.speaking .sound-bar span:nth-child(4) { animation: soundWave 0.6s -0.1s infinite ease-in-out alternate; }

@keyframes soundWave {
  from { height: 4px; }
  to { height: 16px; }
}

/*  Decor  */
.studio-decorations .lamp {
  position: absolute;
  top: 20px;
  width: 4px;
  height: 100px;
  background: linear-gradient(180deg, var(--c-border) 0%, transparent 100%);
}

.lamp-left { left: 40px; }
.lamp-right { right: 40px; }

.lamp::before {
  content: '';
  position: absolute;
  top: -10px;
  left: -8px;
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  box-shadow: 0 0 20px rgba(255, 107, 53, 0.2);
}

/*  Progress  */
.progress-bar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 2rem;
  padding: 0 1rem;
}

.progress-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  position: relative;
}

.step-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--c-bg);
  border: 2px solid var(--c-border);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  z-index: 2;
  color: transparent;
}

.progress-step.active .step-dot {
  background: var(--c-primary);
  border-color: var(--c-primary);
  transform: scale(1.2);
  box-shadow: 0 0 15px rgba(255, 107, 53, 0.3);
}

.progress-step.completed .step-dot {
  background: var(--c-success);
  border-color: var(--c-success);
  color: white;
}

.step-label {
  font-size: 0.75rem;
  color: var(--c-text-3);
  margin-top: 10px;
  font-weight: 500;
}

.progress-step.active .step-label {
  color: var(--c-primary);
  font-weight: 700;
}

.progress-step.completed .step-label {
  color: var(--c-success);
}

.step-line {
  position: absolute;
  top: 14px;
  left: 55%;
  width: 90%;
  height: 2px;
  background: var(--c-border);
  z-index: 1;
}

.step-line.filled {
  background: var(--c-success);
}

/*  Status Bar  */
.status-box {
  background: #fdfaf7;
  border: 1px solid #eee1d7;
  border-radius: var(--r-xl);
  padding: 1rem 1.25rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.status-icon {
  width: 40px;
  height: 40px;
  background: white;
  border: 1px solid #eee1d7;
  box-shadow: 0 2px 6px rgba(0,0,0,0.02);
  border-radius: 12px;
  color: var(--c-primary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-text {
  flex: 1;
  font-size: 0.9rem;
  color: var(--c-text-2);
  line-height: 1.5;
}

.btn-cancel {
  padding: 6px 16px;
  border: 1px solid #eee1d7;
  border-radius: var(--r-full);
  background: white;
  color: var(--c-text-2);
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-cancel:hover:not(:disabled) {
  border-color: var(--c-primary);
  color: var(--c-primary);
}

.btn-cancel:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-text {
  color: #ef4444;
  font-size: 0.85rem;
  font-weight: 500;
  margin-top: 4px;
}

/*  Completion  */
.complete-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255, 252, 249, 0.9);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 20;
}

.complete-box {
  text-align: center;
}

.complete-icon {
  width: 64px;
  height: 64px;
  background: var(--c-success);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin: 0 auto 1rem;
  box-shadow: 0 4px 15px rgba(46, 204, 113, 0.3);
}

.complete-box h4 {
  font-size: 1.2rem;
  margin-bottom: 0.5rem;
}

/*  Transitions  */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.4s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

@media (max-width: 600px) {
  .guests-section {
    gap: 1rem;
    flex-wrap: wrap;
  }
  .avatar {
    width: 48px;
    height: 48px;
  }
  .host-avatar {
    width: 60px;
    height: 60px;
  }
  .studio-scene {
    min-height: 400px;
  }
  .step-label {
    display: none;
  }
}
</style>
