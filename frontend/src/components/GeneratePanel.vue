<template>
  <div class="generate-panel" v-if="taskId">
    <div class="studio-container">
      <!-- Header -->
      <div class="studio-header">
        <div class="studio-badge">
          <span class="live-dot"></span>
          录音棚
        </div>
        <h3>AI圆桌派录音棚</h3>
        <p class="stage-name">{{ currentStageLabel }}</p>
      </div>

      <!-- Studio Scene -->
      <div class="studio-scene">
        <div class="scene-bg">
          <div class="bg-gradient"></div>
          <div class="bg-grid"></div>
        </div>
        
        <!-- Podium/Table -->
        <div class="podium">
          <div class="podium-surface">
            <div class="podium-logo">
              <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14.5H8v-5l3.5-3.5V16.5zm5 0h-3v-8.5l3.5 3.5v5z"/>
              </svg>
            </div>
          </div>
          <div class="podium-base"></div>
        </div>

        <!-- Host -->
        <div class="person host" :class="{ speaking: isSpeaking('host') }">
          <div class="mic"></div>
          <div class="avatar host-avatar">
            <span class="avatar-emoji">🎙️</span>
          </div>
          <div class="person-info">
            <span class="name">主持人</span>
            <span class="role">林晨曦</span>
          </div>
          <div class="sound-bar" :class="{ active: isSpeaking('host') }">
            <span></span><span></span><span></span>
          </div>
        </div>

        <!-- Guest 1 -->
        <div class="person guest-1" :class="{ speaking: isSpeaking('guest-a') }">
          <div class="mic"></div>
          <div class="avatar guest-1-avatar">
            <span class="avatar-emoji">💻</span>
          </div>
          <div class="person-info">
            <span class="name">技术专家</span>
            <span class="role">赵明远</span>
          </div>
          <div class="sound-bar" :class="{ active: isSpeaking('guest-a') }">
            <span></span><span></span><span></span>
          </div>
        </div>

        <!-- Guest 2 -->
        <div class="person guest-2" :class="{ speaking: isSpeaking('guest-b') }">
          <div class="mic"></div>
          <div class="avatar guest-2-avatar">
            <span class="avatar-emoji">🚀</span>
          </div>
          <div class="person-info">
            <span class="name">创业者</span>
            <span class="role">苏婉清</span>
          </div>
          <div class="sound-bar" :class="{ active: isSpeaking('guest-b') }">
            <span></span><span></span><span></span>
          </div>
        </div>

        <!-- Guest 3 -->
        <div class="person guest-3" :class="{ speaking: isSpeaking('guest-c') }">
          <div class="mic"></div>
          <div class="avatar guest-3-avatar">
            <span class="avatar-emoji">📚</span>
          </div>
          <div class="person-info">
            <span class="name">伦理学家</span>
            <span class="role">陈志恒</span>
          </div>
          <div class="sound-bar" :class="{ active: isSpeaking('guest-c') }">
            <span></span><span></span><span></span>
          </div>
        </div>

        <!-- Wave Animation -->
        <div class="wave-container">
          <div class="wave"></div>
          <div class="wave"></div>
          <div class="wave"></div>
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

const props = defineProps({ taskId: String })
const emit = defineEmits(['completed'])

const stages = [
  { key: 'news', label: '获取资讯' },
  { key: 'topic', label: '选定话题' },
  { key: 'research', label: '深度搜索' },
  { key: 'planning', label: '节目策划' },
  { key: 'dialogue', label: '生成文本' },
  { key: 'audio', label: '音频拼接' },
  { key: 'done', label: '完成' },
]

const currentStage = ref('')
const detail = ref('')
const error = ref('')
const currentSpeaker = ref('')
const isCompleted = ref(false)
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

function isSpeaking(participant) {
  return currentSpeaker.value === participant
}

function simulateSpeaking() {
  const speakers = ['host', 'guest-a', 'guest-b', 'guest-c']
  let idx = 0
  speakerInterval = setInterval(() => {
    if (currentStage.value === 'dialogue' || currentStage.value === 'audio') {
      currentSpeaker.value = speakers[idx % speakers.length]
      idx++
    } else {
      currentSpeaker.value = ''
    }
  }, 2500)
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
        clearInterval(speakerInterval)
        setTimeout(() => emit('completed'), 2500)
      }
      if (data.status === 'failed') {
        error.value = data.detail
        eventSource.close()
        clearInterval(speakerInterval)
        setTimeout(() => emit('completed'), 3000)
      }
    } catch (e) {
      console.error('SSE parse error:', e)
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
  margin-top: 1rem;
}

.studio-container {
  position: relative;
  background: white;
  border-radius: var(--radius-xl);
  padding: 1.75rem;
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

/* Header */
.studio-header {
  text-align: center;
  margin-bottom: 1.5rem;
}

.studio-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  padding: 5px 12px;
  border-radius: var(--radius-full);
  font-size: 0.75rem;
  font-weight: 600;
  color: #ef4444;
  margin-bottom: 0.75rem;
}

.studio-badge .live-dot {
  width: 6px;
  height: 6px;
  background: #ef4444;
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
  color: var(--color-text);
  margin-bottom: 0.25rem;
}

.stage-name {
  color: var(--color-text-secondary);
  font-size: 0.9rem;
}

/* Studio Scene */
.studio-scene {
  position: relative;
  background: linear-gradient(180deg, #f8f9fc 0%, #eef0f5 100%);
  border-radius: var(--radius-lg);
  padding: 2rem 1.5rem;
  min-height: 220px;
  margin-bottom: 1.5rem;
  overflow: hidden;
}

.scene-bg {
  position: absolute;
  inset: 0;
}

.bg-gradient {
  position: absolute;
  top: -50%;
  left: -20%;
  width: 60%;
  height: 100%;
  background: radial-gradient(ellipse, rgba(99, 102, 241, 0.1) 0%, transparent 70%);
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(rgba(99, 102, 241, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(99, 102, 241, 0.05) 1px, transparent 1px);
  background-size: 20px 20px;
}

/* Podium */
.podium {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.podium-surface {
  width: 100px;
  height: 16px;
  background: linear-gradient(180deg, #e2e8f0 0%, #cbd5e1 100%);
  border-radius: 8px 8px 0 0;
}

.podium-logo {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin: -8px auto 0;
}

.podium-base {
  width: 80px;
  height: 20px;
  background: linear-gradient(180deg, #cbd5e1 0%, #94a3b8 100%);
  border-radius: 0 0 4px 4px;
}

/* People */
.person {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: all 0.3s ease;
}

.person.speaking {
  transform: scale(1.05);
}

.host {
  left: 50%;
  top: 15%;
  transform: translateX(-50%);
}

.host.speaking {
  transform: translateX(-50%) scale(1.08);
}

.guest-1 {
  left: 12%;
  top: 45%;
}

.guest-2 {
  left: 30%;
  top: 65%;
}

.guest-3 {
  right: 30%;
  top: 65%;
}

.mic {
  position: absolute;
  top: -15px;
  width: 16px;
  height: 20px;
  background: #64748b;
  border-radius: 8px 8px 4px 4px;
}

.mic::after {
  content: '';
  position: absolute;
  top: 4px;
  left: 50%;
  transform: translateX(-50%);
  width: 6px;
  height: 6px;
  background: #94a3b8;
  border-radius: 50%;
}

.avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: all 0.3s ease;
}

.host-avatar {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
}

.guest-1-avatar { background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); }
.guest-2-avatar { background: linear-gradient(135deg, var(--color-accent-warm) 0%, #b45309 100%); }
.guest-3-avatar { background: linear-gradient(135deg, var(--color-success) 0%, #047857 100%); }

.person.speaking .avatar {
  box-shadow: 0 0 20px rgba(99, 102, 241, 0.4);
}

.avatar-emoji {
  font-size: 1.25rem;
}

.host .avatar-emoji { font-size: 1.5rem; }

.person-info {
  text-align: center;
  margin-top: 6px;
}

.person-info .name {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text);
}

.person-info .role {
  display: block;
  font-size: 0.65rem;
  color: var(--color-text-muted);
}

/* Sound Bar */
.sound-bar {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 12px;
  margin-top: 4px;
  opacity: 0;
  transition: opacity 0.3s;
}

.sound-bar.active { opacity: 1; }

.sound-bar span {
  width: 2px;
  background: var(--color-primary);
  border-radius: 1px;
  animation: soundBar 0.4s ease-in-out infinite alternate;
}

.sound-bar span:nth-child(1) { height: 4px; animation-delay: 0s; }
.sound-bar span:nth-child(2) { height: 8px; animation-delay: 0.1s; }
.sound-bar span:nth-child(3) { height: 6px; animation-delay: 0.2s; }

@keyframes soundBar {
  0% { transform: scaleY(0.5); }
  100% { transform: scaleY(1); }
}

/* Wave */
.wave-container {
  position: absolute;
  bottom: 8px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 3px;
}

.wave {
  width: 3px;
  height: 16px;
  background: linear-gradient(180deg, var(--color-primary) 0%, var(--color-accent) 100%);
  border-radius: 2px;
  animation: waveAnim 0.8s ease-in-out infinite;
}

.wave:nth-child(1) { animation-delay: 0s; }
.wave:nth-child(2) { animation-delay: 0.15s; }
.wave:nth-child(3) { animation-delay: 0.3s; }

@keyframes waveAnim {
  0%, 100% { transform: scaleY(0.5); opacity: 0.4; }
  50% { transform: scaleY(1); opacity: 1; }
}

/* Progress */
.progress-bar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 1.25rem;
  position: relative;
}

.progress-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  position: relative;
}

.step-dot {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-border-light);
  border: 2px solid var(--color-border);
  transition: all 0.3s ease;
  z-index: 1;
}

.progress-step.active .step-dot {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  border-color: var(--color-primary);
  color: white;
  box-shadow: 0 0 12px rgba(99, 102, 241, 0.4);
}

.progress-step.completed .step-dot {
  background: var(--color-success);
  border-color: var(--color-success);
  color: white;
}

.step-label {
  font-size: 0.7rem;
  color: var(--color-text-muted);
  margin-top: 6px;
  text-align: center;
}

.progress-step.active .step-label {
  color: var(--color-primary);
  font-weight: 600;
}

.progress-step.completed .step-label {
  color: var(--color-success);
}

.step-line {
  position: absolute;
  top: 12px;
  left: calc(50% + 14px);
  right: calc(-50% + 14px);
  height: 2px;
  background: var(--color-border);
}

.step-line.filled {
  background: var(--color-success);
}

/* Status */
.status-box {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0.875rem 1rem;
  background: var(--color-border-light);
  border-radius: var(--radius-md);
}

.status-icon {
  width: 32px;
  height: 32px;
  background: rgba(99, 102, 241, 0.1);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary);
  flex-shrink: 0;
}

.status-text {
  color: var(--color-text-secondary);
  font-size: 0.85rem;
  flex: 1;
}

.error-text {
  color: #ef4444;
  font-size: 0.85rem;
  font-weight: 500;
  width: 100%;
}

/* Completion */
.complete-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.95);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.complete-box {
  text-align: center;
  animation: popIn 0.4s ease;
}

@keyframes popIn {
  0% { transform: scale(0.8); opacity: 0; }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); opacity: 1; }
}

.complete-icon {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, var(--color-success) 0%, #059669 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin: 0 auto 1rem;
}

.complete-box h4 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 0.25rem;
}

.complete-box p {
  color: var(--color-text-muted);
  font-size: 0.9rem;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Responsive */
@media (max-width: 700px) {
  .studio-scene {
    min-height: 180px;
    padding: 1.5rem 1rem;
  }
  
  .host { top: 12%; }
  .guest-1 { left: 5%; top: 40%; }
  .guest-2 { left: 25%; top: 60%; }
  .guest-3 { right: 25%; top: 60%; }
  
  .avatar {
    width: 36px;
    height: 36px;
  }
  
  .host-avatar {
    width: 44px;
    height: 44px;
  }
  
  .avatar-emoji { font-size: 1rem; }
  .host .avatar-emoji { font-size: 1.25rem; }
  
  .step-label {
    font-size: 0.6rem;
  }
}
</style>
