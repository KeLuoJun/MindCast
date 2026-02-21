<template>
  <div class="workflow-wizard">
    <!-- Progress Steps -->
    <div class="wizard-progress">
      <div
        v-for="(step, idx) in steps"
        :key="step.key"
        class="progress-step"
        :class="{ active: currentStep === idx, completed: currentStep > idx }"
        @click="goToStep(idx)"
      >
        <div class="step-indicator">
          <svg v-if="currentStep > idx" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="3">
            <polyline points="20,6 9,17 4,12"/>
          </svg>
          <span v-else>{{ idx + 1 }}</span>
        </div>
        <span class="step-label">{{ step.label }}</span>
        <div v-if="idx < steps.length - 1" class="step-line" :class="{ filled: currentStep > idx }"></div>
      </div>
    </div>

    <!-- Step Content -->
    <div class="wizard-content">
      <!-- Step 1: Fetch News -->
      <transition name="slide-up" mode="out-in">
        <div v-if="currentStep === 0" class="step-panel" key="step-news">
          <div class="step-header">
            <div class="step-icon news">
              <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 6v6l4 2"/>
              </svg>
            </div>
            <div>
              <h2>获取今日资讯</h2>
              <p>输入感兴趣的话题，获取最新相关资讯</p>
            </div>
          </div>

          <div class="topic-input-group">
            <label class="topic-label">话题方向</label>
            <input
              v-model="topicQuery"
              type="text"
              class="topic-input"
              placeholder="例如：量子计算、新能源汽车、教育改革…（留空则获取综合热点）"
              @keyup.enter="fetchNews"
            />
          </div>

          <button class="btn-fetch" :disabled="fetchingNews" @click="fetchNews">
            <span v-if="fetchingNews" class="spinner"></span>
            <svg v-else viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M23 4v6h-6"/>
              <path d="M1 20v-6h6"/>
              <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
            </svg>
            {{ fetchingNews ? '获取中...' : '立即获取资讯' }}
          </button>

          <transition name="fade">
            <div v-if="newsContent" class="news-result">
              <div class="result-header">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20,6 9,17 4,12"/>
                </svg>
                已获取 {{ newsContent.count }} 篇资讯
              </div>
              <div class="news-list">
                <div
                  v-for="(item, idx) in newsContent.items"
                  :key="idx"
                  class="news-item"
                  :class="{ selected: selectedTopic === item.title }"
                  @click="selectTopic(item.title)"
                >
                  <div class="news-radio">
                    <div class="radio-dot" :class="{ active: selectedTopic === item.title }"></div>
                  </div>
                  <div class="news-content">
                    <h4>{{ item.title }}</h4>
                    <p>{{ item.content?.slice(0, 100) }}...</p>
                  </div>
                </div>
              </div>
              <button class="btn-next" :disabled="!hasNews" @click="nextStep">
                下一步：选择嘉宾
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="5" y1="12" x2="19" y2="12"/>
                  <polyline points="12,5 19,12 12,19"/>
                </svg>
              </button>
            </div>
          </transition>
        </div>

        <!-- Step 2: Select Guests -->
        <div v-else-if="currentStep === 1" class="step-panel" key="step-guests">
          <div class="step-header">
            <div class="step-icon guests">
              <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 00-3-3.87"/>
                <path d="M16 3.13a4 4 0 010 7.75"/>
              </svg>
            </div>
            <div>
              <h2>选择嘉宾</h2>
              <p>选择本期节目的嘉宾（最多 3 位）</p>
            </div>
            <button class="btn-config" @click="$emit('openGuestDrawer')">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="3"/>
                <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/>
              </svg>
              管理嘉宾
            </button>
          </div>

          <div class="guest-selection">
            <div v-if="guests.length === 0" class="empty-guests">
              <div class="empty-icon">
                <svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
                  <circle cx="9" cy="7" r="4"/>
                </svg>
              </div>
              <p>暂无嘉宾，请先创建嘉宾</p>
              <button class="btn-add" @click="$emit('openGuestDrawer')">创建嘉宾</button>
            </div>

            <div v-else class="guest-cards">
              <div
                v-for="guest in guests"
                :key="guest.name"
                class="guest-card"
                :class="{ selected: selectedGuests.includes(guest.name) }"
                @click="toggleGuest(guest.name)"
              >
                <div class="guest-avatar" :style="{ background: getAvatarGradient(guest.mbti) }">
                  {{ guest.name.charAt(0) }}
                </div>
                <div class="guest-info">
                  <h4>{{ guest.name }}</h4>
                  <span class="mbti">{{ guest.mbti }}</span>
                  <span class="occupation">{{ guest.occupation }}</span>
                </div>
                <div class="selection-check">
                  <svg v-if="selectedGuests.includes(guest.name)" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="3">
                    <polyline points="20,6 9,17 4,12"/>
                  </svg>
                </div>
              </div>
            </div>
          </div>

          <div class="step-actions">
            <button class="btn-back" @click="prevStep">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="19" y1="12" x2="5" y2="12"/>
                <polyline points="12,19 5,12 12,5"/>
              </svg>
              返回
            </button>
            <button class="btn-next" :disabled="selectedGuests.length === 0" @click="nextStep">
              下一步：生成播客
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="5" y1="12" x2="19" y2="12"/>
                <polyline points="12,5 19,12 12,19"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- Step 3: Generate -->
        <div v-else-if="currentStep === 2" class="step-panel" key="step-generate">
          <div class="step-header">
            <div class="step-icon generate">
              <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2a3 3 0 00-3 3v7a3 3 0 006 0V5a3 3 0 00-3-3z"/>
                <path d="M19 10v2a7 7 0 01-14 0v-2"/>
                <line x1="12" y1="19" x2="12" y2="22"/>
              </svg>
            </div>
            <div>
              <h2>生成播客</h2>
              <p>选择生成模式并开始生成节目</p>
            </div>
          </div>

          <!-- Topic Summary -->
          <div class="topic-summary">
            <div class="summary-label">当前话题</div>
            <div class="summary-value">{{ effectiveTopic }}</div>
          </div>

          <!-- Guests Summary -->
          <div class="guests-summary">
            <div class="summary-label">已选嘉宾</div>
            <div class="guests-tags">
              <span v-for="name in selectedGuests" :key="name" class="guest-tag">
                {{ getGuestName(name) }}
              </span>
            </div>
          </div>

          <!-- Mode Toggle -->
          <div class="mode-toggle">
            <button
              class="mode-btn"
              :class="{ active: workflowMode === 'one-click' }"
              @click="workflowMode = 'one-click'"
            >
              <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                <polygon points="5,3 19,12 5,21"/>
              </svg>
              一键生成
            </button>
            <button
              class="mode-btn"
              :class="{ active: workflowMode === 'step-by-step' }"
              @click="workflowMode = 'step-by-step'"
            >
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="8" y1="6" x2="21" y2="6"/>
                <line x1="8" y1="12" x2="21" y2="12"/>
                <line x1="8" y1="18" x2="21" y2="18"/>
              </svg>
              分步确认
            </button>
          </div>

          <!-- One-Click Mode -->
          <div v-if="workflowMode === 'one-click'" class="generate-action">
            <button class="btn-generate" :disabled="!canGenerate || generating" @click="startGenerate">
              <span v-if="generating" class="spinner"></span>
              <svg v-else viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="5,3 19,12 5,21"/>
              </svg>
              {{ generating ? '生成中...' : '开始生成播客' }}
            </button>
          </div>

          <!-- Step-by-Step Mode -->
          <div v-else class="step-by-step">
            <button class="btn-generate-outline" :disabled="!canGenerate || generatingScript" @click="generateScriptPreview">
              <span v-if="generatingScript" class="spinner"></span>
              {{ generatingScript ? '生成中...' : '生成文稿预览' }}
            </button>

            <transition name="fade">
              <div v-if="hasScriptDraft" class="script-preview">
                <div class="preview-header">
                  <h3>{{ scriptDraft.title }}</h3>
                  <p>{{ scriptDraft.summary }}</p>
                </div>
                <div class="dialogue-list">
                  <div v-for="(line, idx) in scriptDraft.dialogue" :key="idx" class="dialogue-item">
                    <div class="speaker">
                      <span class="avatar" :class="getSpeakerClass(line.speaker)">{{ line.speaker.charAt(0) }}</span>
                      <span class="name">{{ line.speaker }}</span>
                    </div>
                    <textarea v-model="line.text" rows="2" placeholder="编辑对话..."></textarea>
                  </div>
                </div>
                <button class="btn-confirm-synth" :disabled="synthesizing" @click="confirmScriptSynthesis">
                  <span v-if="synthesizing" class="spinner"></span>
                  {{ synthesizing ? '合成中...' : '确认并合成语音' }}
                </button>
              </div>
            </transition>
          </div>

          <div class="step-actions">
            <button class="btn-back" @click="prevStep">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="19" y1="12" x2="5" y2="12"/>
                <polyline points="12,19 5,12 12,5"/>
              </svg>
              返回
            </button>
          </div>
        </div>
      </transition>
    </div>

    <!-- Generate Panel (when generating) -->
    <GeneratePanel v-if="taskId" :task-id="taskId" @completed="onGenerateCompleted" />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import GeneratePanel from './GeneratePanel.vue'

const props = defineProps({
  guests: { type: Array, default: () => [] },
  selectedGuests: { type: Array, default: () => [] }
})

const emit = defineEmits(['openGuestDrawer', 'update:selectedGuests'])

const steps = [
  { key: 'news', label: '获取资讯' },
  { key: 'guests', label: '选择嘉宾' },
  { key: 'generate', label: '生成播客' }
]

const currentStep = ref(0)
const workflowMode = ref('one-click')
const newsContent = ref(null)
const selectedTopic = ref('')
const customTopic = ref('')
const topicQuery = ref('')
const fetchingNews = ref(false)
const generating = ref(false)
const generatingScript = ref(false)
const synthesizing = ref(false)
const taskId = ref(null)
const scriptDraft = ref(null)

const hasNews = computed(() => newsContent.value !== null)
const effectiveTopic = computed(() => customTopic.value || selectedTopic.value || '')
const hasScriptDraft = computed(() => scriptDraft.value && scriptDraft.value.dialogue?.length > 0)
const canGenerate = computed(() => hasNews.value && !!effectiveTopic.value && selectedGuests.value.length > 0)

const selectedGuests = computed({
  get: () => props.selectedGuests,
  set: (val) => emit('update:selectedGuests', val)
})

function goToStep(idx) {
  if (idx < currentStep.value) {
    currentStep.value = idx
  }
}

function nextStep() {
  if (currentStep.value < steps.length - 1) {
    currentStep.value++
  }
}

function prevStep() {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

async function fetchNews() {
  fetchingNews.value = true
  try {
    const params = new URLSearchParams({ max_results: '10' })
    if (topicQuery.value.trim()) {
      params.set('topic', topicQuery.value.trim())
    }
    const res = await fetch(`/api/debug/news?${params}`)
    const data = await res.json()
    newsContent.value = {
      count: data.count || 0,
      items: data.items || []
    }
    if (newsContent.value.items.length > 0) {
      selectedTopic.value = newsContent.value.items[0].title
    }
    customTopic.value = ''
  } catch (e) {
    console.error('Failed to fetch news:', e)
  } finally {
    fetchingNews.value = false
  }
}

function selectTopic(title) {
  selectedTopic.value = title
  customTopic.value = ''
}

function toggleGuest(name) {
  const current = [...selectedGuests.value]
  const idx = current.indexOf(name)
  if (idx >= 0) {
    current.splice(idx, 1)
  } else if (current.length < 3) {
    current.push(name)
  }
  selectedGuests.value = current
}

function getGuestName(name) {
  const guest = props.guests.find(g => g.name === name)
  return guest ? guest.name : name
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

function getSpeakerClass(speaker) {
  if (speaker.includes('主持')) return 'host'
  if (speaker.includes('技术') || speaker.includes('明远')) return 'tech'
  if (speaker.includes('创业') || speaker.includes('婉清')) return 'pm'
  if (speaker.includes('伦理') || speaker.includes('志恒')) return 'ethics'
  return 'guest'
}

async function startGenerate() {
  if (!canGenerate.value) return
  generating.value = true
  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: effectiveTopic.value,
        selected_guests: selectedGuests.value
      })
    })
    const data = await res.json()
    taskId.value = data.task_id
  } catch (e) {
    console.error('Failed to start generation:', e)
    generating.value = false
  }
}

async function generateScriptPreview() {
  if (!canGenerate.value) return
  generatingScript.value = true
  try {
    const res = await fetch('/api/script/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: effectiveTopic.value,
        selected_guests: selectedGuests.value
      })
    })
    const data = await res.json()
    scriptDraft.value = {
      title: data.title || data.topic || '',
      topic: data.topic || '',
      summary: data.summary || '',
      guests: data.guests || [],
      dialogue: (data.dialogue || []).map(line => ({
        speaker: line.speaker,
        text: line.text,
        emotion: line.emotion || 'neutral'
      }))
    }
  } catch (e) {
    console.error('Failed to generate script preview:', e)
  } finally {
    generatingScript.value = false
  }
}

async function confirmScriptSynthesis() {
  if (!hasScriptDraft.value) return
  synthesizing.value = true
  try {
    const payload = {
      title: scriptDraft.value.title,
      topic: scriptDraft.value.topic,
      summary: scriptDraft.value.summary,
      guests: scriptDraft.value.guests,
      dialogue: scriptDraft.value.dialogue
        .map(line => ({ speaker: line.speaker, text: line.text?.trim(), emotion: line.emotion }))
        .filter(line => line.text)
    }
    const res = await fetch('/api/script/synthesize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    const data = await res.json()
    taskId.value = data.task_id
  } catch (e) {
    console.error('Failed to start synthesis:', e)
    synthesizing.value = false
  }
}

function onGenerateCompleted() {
  generating.value = false
  synthesizing.value = false
  taskId.value = null
  emit('completed')
}

// Expose for parent
defineExpose({
  fetchNews,
  nextStep,
  prevStep
})
</script>

<style scoped>
.workflow-wizard {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

/* Progress */
.wizard-progress {
  display: flex;
  align-items: center;
  padding: 1.25rem 1.5rem;
  background: var(--glass-bg-strong);
  border-bottom: 1px solid var(--glass-border);
}

.progress-step {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  position: relative;
}

.progress-step:last-child {
  flex: 0;
}

.step-indicator {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 600;
  background: var(--color-border-light);
  color: var(--color-text-muted);
  border: 2px solid var(--color-border);
  transition: all var(--transition-normal);
  flex-shrink: 0;
}

.progress-step.active .step-indicator {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  border-color: var(--color-primary);
  color: white;
  box-shadow: 0 0 12px rgba(99, 102, 241, 0.4);
}

.progress-step.completed .step-indicator {
  background: var(--color-success);
  border-color: var(--color-success);
  color: white;
}

.step-label {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--color-text-muted);
  white-space: nowrap;
}

.progress-step.active .step-label {
  color: var(--color-primary);
}

.progress-step.completed .step-label {
  color: var(--color-success);
}

.step-line {
  flex: 1;
  height: 2px;
  background: var(--color-border);
  margin: 0 12px;
}

.step-line.filled {
  background: var(--color-success);
}

/* Content */
.wizard-content {
  padding: 1.5rem;
}

.step-panel {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.step-header {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.step-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.step-icon.news {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(99, 102, 241, 0.08) 100%);
  color: var(--color-primary);
}

.step-icon.guests {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(16, 185, 129, 0.08) 100%);
  color: var(--color-success);
}

.step-icon.generate {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(245, 158, 11, 0.08) 100%);
  color: var(--color-accent-warm);
}

.step-header h2 {
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--color-text);
}

.step-header p {
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.btn-config {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 1px solid var(--color-border);
  background: white;
  border-radius: var(--radius-md);
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-config:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

/* Topic Input */
.topic-input-group {
  margin-bottom: 16px;
}

.topic-label {
  display: block;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
}

.topic-input {
  width: 100%;
  padding: 12px 16px;
  background: var(--color-bg-elevated, rgba(255,255,255,0.06));
  border: 1px solid var(--color-border, rgba(255,255,255,0.1));
  border-radius: var(--radius-md);
  font-size: 0.95rem;
  color: var(--color-text-primary);
  outline: none;
  transition: border-color var(--transition-fast);
  box-sizing: border-box;
}

.topic-input::placeholder {
  color: var(--color-text-tertiary, rgba(255,255,255,0.35));
}

.topic-input:focus {
  border-color: var(--color-primary);
}

/* Fetch Button */
.btn-fetch {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 14px 24px;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-fetch:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.btn-fetch:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* News Result */
.news-result {
  background: var(--glass-bg-strong);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  padding: 1.25rem;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-success);
  margin-bottom: 1rem;
}

.news-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 300px;
  overflow-y: auto;
  margin-bottom: 1rem;
}

.news-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 0.75rem;
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  background: white;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.news-item:hover {
  border-color: var(--color-primary-light);
}

.news-item.selected {
  border-color: var(--color-primary);
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(139, 92, 246, 0.05) 100%);
}

.news-radio {
  flex-shrink: 0;
  padding-top: 2px;
}

.radio-dot {
  width: 18px;
  height: 18px;
  border: 2px solid var(--color-border);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}

.radio-dot.active {
  border-color: var(--color-primary);
}

.radio-dot.active::after {
  content: '';
  width: 8px;
  height: 8px;
  background: var(--color-primary);
  border-radius: 50%;
}

.news-content h4 {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 0.25rem;
  line-height: 1.4;
}

.news-content p {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  line-height: 1.5;
}

/* Guest Selection */
.guest-selection {
  margin-bottom: 1rem;
}

.empty-guests {
  text-align: center;
  padding: 2rem;
  background: var(--color-border-light);
  border-radius: var(--radius-lg);
}

.empty-guests .empty-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 1rem;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
}

.empty-guests p {
  color: var(--color-text-muted);
  margin-bottom: 1rem;
}

.btn-add {
  padding: 10px 20px;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-weight: 500;
  cursor: pointer;
}

.guest-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.guest-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 1rem;
  background: var(--glass-bg-strong);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-normal);
  position: relative;
}

.guest-card:hover {
  border-color: var(--color-primary-light);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.guest-card.selected {
  border-color: var(--color-primary);
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(139, 92, 246, 0.08) 100%);
}

.guest-avatar {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.1rem;
  font-weight: 600;
  flex-shrink: 0;
}

.guest-info {
  flex: 1;
  min-width: 0;
}

.guest-info h4 {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 2px;
}

.guest-info .mbti {
  display: inline-block;
  padding: 1px 6px;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 4px;
  font-size: 0.65rem;
  font-weight: 600;
  color: var(--color-primary);
  margin-right: 6px;
}

.guest-info .occupation {
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.selection-check {
  width: 24px;
  height: 24px;
  border: 2px solid var(--color-border);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.guest-card.selected .selection-check {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

/* Step Actions */
.step-actions {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.btn-back {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  border: 1px solid var(--color-border);
  background: white;
  border-radius: var(--radius-md);
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-back:hover {
  background: var(--color-border-light);
}

.btn-next {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: linear-gradient(135deg, var(--color-success) 0%, #059669 100%);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-next:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.btn-next:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Generate Step */
.topic-summary,
.guests-summary {
  padding: 1rem;
  background: var(--glass-bg-strong);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-md);
}

.summary-label {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  margin-bottom: 0.5rem;
}

.summary-value {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--color-text);
}

.guests-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.guest-tag {
  padding: 4px 10px;
  background: rgba(99, 102, 241, 0.1);
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-primary);
}

/* Mode Toggle */
.mode-toggle {
  display: flex;
  background: var(--color-border-light);
  border-radius: var(--radius-md);
  padding: 4px;
}

.mode-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.mode-btn.active {
  background: white;
  color: var(--color-primary);
  box-shadow: var(--shadow-sm);
}

/* Generate Action */
.generate-action {
  display: flex;
  justify-content: center;
  padding: 1rem 0;
}

.btn-generate {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 16px 32px;
  background: linear-gradient(135deg, var(--color-accent-warm) 0%, #d97706 100%);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-generate:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.btn-generate:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-generate-outline {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  padding: 14px;
  background: white;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--color-text);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-generate-outline:hover:not(:disabled) {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

/* Script Preview */
.script-preview {
  background: white;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 1.25rem;
}

.preview-header {
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--color-border-light);
}

.preview-header h3 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
}

.preview-header p {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
  margin-top: 0.25rem;
}

.dialogue-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-height: 250px;
  overflow-y: auto;
  margin-bottom: 1rem;
}

.dialogue-item {
  display: flex;
  gap: 10px;
}

.speaker {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  width: 60px;
  flex-shrink: 0;
}

.speaker .avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
  color: white;
}

.avatar.host { background: linear-gradient(135deg, var(--color-primary), var(--color-accent)); }
.avatar.tech { background: linear-gradient(135deg, #3b82f6, #1d4ed8); }
.avatar.pm { background: linear-gradient(135deg, var(--color-accent-warm), #b45309); }
.avatar.ethics { background: linear-gradient(135deg, var(--color-success), #047857); }
.avatar.guest { background: linear-gradient(135deg, #64748b, #475569); }

.speaker .name {
  font-size: 0.65rem;
  color: var(--color-text-muted);
}

.dialogue-item textarea {
  flex: 1;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 0.5rem;
  font-size: 0.8rem;
  resize: none;
}

.dialogue-item textarea:focus {
  outline: none;
  border-color: var(--color-primary);
}

.btn-confirm-synth {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 12px;
  background: linear-gradient(135deg, var(--color-success) 0%, #059669 100%);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-confirm-synth:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

/* Spinner */
.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Transitions */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.25s ease;
}

.slide-up-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.slide-up-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Responsive */
@media (max-width: 768px) {
  .wizard-progress {
    overflow-x: auto;
  }
  
  .step-label {
    display: none;
  }
  
  .guest-cards {
    grid-template-columns: 1fr;
  }
}
</style>
