<template>
  <div class="workflow-wizard">
    <!-- Progress Steps -->
    <div class="wizard-progress">
      <div
        v-for="(step, idx) in steps"
        :key="step.key"
        class="progress-step"
        :class="{ active: store.currentStep === idx, completed: store.currentStep > idx }"
        @click="goToStep(idx)"
      >
        <div class="step-indicator">
          <svg v-if="store.currentStep > idx" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="3">
            <polyline points="20,6 9,17 4,12"/>
          </svg>
          <span v-else>{{ idx + 1 }}</span>
        </div>
        <span class="step-label">{{ step.label }}</span>
        <div v-if="idx < steps.length - 1" class="step-line" :class="{ filled: store.currentStep > idx }"></div>
      </div>
    </div>

    <!-- Step Content -->
    <div class="wizard-content">
      <!-- Step 1: Fetch News -->
      <transition name="slide-up" mode="out-in">
        <div v-if="store.currentStep === 0" class="step-panel" key="step-news">
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
              v-model="store.topicQuery"
              type="text"
              class="topic-input"
              placeholder="例如：量子计算、新能源汽车、教育改革…（留空则获取综合热点）"
              @keyup.enter="store.fetchNews"
            />
          </div>

          <button class="btn-fetch" :disabled="store.fetchingNews" @click="store.fetchNews">
            <span v-if="store.fetchingNews" class="spinner"></span>
            <svg v-else viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M23 4v6h-6"/>
              <path d="M1 20v-6h6"/>
              <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
            </svg>
            {{ store.fetchingNews ? '获取中...（时间稍长）' : '立即获取资讯' }}
          </button>

          <transition name="fade">
            <div v-if="store.newsContent" class="news-result">
              <div class="result-header">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20,6 9,17 4,12"/>
                </svg>
                已获取 {{ store.newsContent.count }} 篇资讯
              </div>
              <div class="news-list">
                <div
                  v-for="(item, idx) in store.newsContent.items"
                  :key="idx"
                  class="news-item"
                  :class="{ selected: store.selectedTopic === item.title }"
                  @click="store.selectTopic(item.title)"
                >
                  <div class="news-radio">
                    <div class="radio-dot" :class="{ active: store.selectedTopic === item.title }"></div>
                  </div>
                  <div class="news-content">
                    <h4>{{ item.title }}</h4>
                    <p>{{ item.content?.slice(0, 100) }}...</p>
                  </div>
                </div>
              </div>
              <button class="btn-next" :disabled="!store.hasNews" @click="nextStep">
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
        <div v-else-if="store.currentStep === 1" class="step-panel" key="step-guests">
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
            <button class="btn-config" @click="store.guestDrawerOpen = true">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="3"/>
                <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/>
              </svg>
              管理嘉宾
            </button>
          </div>

          <div class="guest-selection">
            <div v-if="store.guests.length === 0" class="empty-guests">
              <div class="empty-icon">
                <svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
                  <circle cx="9" cy="7" r="4"/>
                </svg>
              </div>
              <p>暂无嘉宾，请先创建嘉宾</p>
              <button class="btn-add" @click="store.guestDrawerOpen = true">创建嘉宾</button>
            </div>

            <div v-else class="guest-cards">
              <div
                v-for="guest in store.guests"
                :key="guest.name"
                class="guest-card"
                :class="{ selected: store.selectedGuests.includes(guest.name) }"
                @click="store.toggleGuest(guest.name)"
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
                  <svg v-if="store.selectedGuests.includes(guest.name)" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="3">
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
            <button class="btn-next" :disabled="store.selectedGuests.length === 0" @click="nextStep">
              下一步：生成播客
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="5" y1="12" x2="19" y2="12"/>
                <polyline points="12,5 19,12 12,19"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- Step 3: Generate -->
        <div v-else-if="store.currentStep === 2" class="step-panel" key="step-generate">
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
            <div class="summary-value">{{ store.effectiveTopic }}</div>
          </div>

          <!-- Guests Summary -->
          <div class="guests-summary">
            <div class="summary-label">已选嘉宾</div>
            <div class="guests-tags">
              <span v-for="name in store.selectedGuests" :key="name" class="guest-tag">
                {{ getGuestName(name) }}
              </span>
            </div>
          </div>

          <!-- Mode Toggle -->
          <div class="mode-toggle">
            <button
              class="mode-btn"
              :class="{ active: store.workflowMode === 'one-click' }"
              @click="store.workflowMode = 'one-click'"
            >
              <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                <polygon points="5,3 19,12 5,21"/>
              </svg>
              一键生成
            </button>
            <button
              class="mode-btn"
              :class="{ active: store.workflowMode === 'step-by-step' }"
              @click="store.workflowMode = 'step-by-step'"
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
          <div v-if="store.workflowMode === 'one-click'" class="generate-action">
            <button class="btn-generate" :disabled="!store.canGenerate || store.generating" @click="store.startGenerate">
              <span v-if="store.generating" class="spinner"></span>
              <svg v-else viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="5,3 19,12 5,21"/>
              </svg>
              {{ store.generating ? '生成中...' : '开始生成播客' }}
            </button>
          </div>

          <!-- Step-by-Step Mode -->
          <div v-else class="step-by-step">
            <!-- Idle: show generate button -->
            <button
              v-if="!store.generatingScript && !store.hasScriptDraft"
              class="btn-generate-outline"
              :disabled="!store.canGenerate"
              @click="store.generateScriptPreview"
            >
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="8" y1="6" x2="21" y2="6"/>
                <line x1="8" y1="12" x2="21" y2="12"/>
                <line x1="8" y1="18" x2="21" y2="18"/>
              </svg>
              生成文稿预览
            </button>

            <!-- Generating: visual pipeline + status -->
            <div v-if="store.generatingScript" class="preview-pipeline">
              <div class="pipeline-stages">
                <div
                  v-for="(stage, idx) in previewStages"
                  :key="stage.key"
                  class="pipeline-stage"
                  :class="getPipelineStageClass(stage.key)"
                >
                  <div class="stage-dot">
                    <svg v-if="getPipelineStageClass(stage.key) === 'completed'" viewBox="0 0 24 24" width="10" height="10" fill="none" stroke="currentColor" stroke-width="3">
                      <polyline points="20,6 9,17 4,12"/>
                    </svg>
                    <span v-else-if="getPipelineStageClass(stage.key) === 'active'" class="stage-spinner"></span>
                  </div>
                  <span class="stage-label">{{ stage.label }}</span>
                  <div
                    v-if="idx < previewStages.length - 1"
                    class="stage-line"
                    :class="{ filled: getPipelineStageClass(stage.key) === 'completed' }"
                  ></div>
                </div>
              </div>
              <p class="pipeline-detail">{{ store.previewStageDetail || '正在处理...' }}</p>
              <button class="btn-cancel-preview" :disabled="!store.previewTaskId" @click="store.cancelScriptPreview">
                终止生成
              </button>
            </div>

            <!-- Script Preview (after generation, hidden once speed-adjust begins) -->
            <transition name="fade">
              <div v-if="store.hasScriptDraft && !store.hasAudioAdjustDraft && !store.synthesizing" class="script-preview">
                <div class="preview-header">
                  <h3>{{ store.scriptDraft.title }}</h3>
                  <p>{{ store.scriptDraft.summary }}</p>
                  <button class="btn-regen" @click="store.generateScriptPreview">
                    <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M23 4v6h-6"/>
                      <path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/>
                    </svg>
                    重新生成
                  </button>
                </div>
                <div class="dialogue-list">
                  <div v-for="(line, idx) in store.scriptDraft.dialogue" :key="idx" class="dialogue-item">
                    <div class="speaker">
                      <span class="avatar" :class="getSpeakerClass(line.speaker)">{{ line.speaker.charAt(0) }}</span>
                      <span class="name">{{ line.speaker }}</span>
                    </div>
                    <textarea
                      v-model="line.text"
                      class="auto-textarea"
                      placeholder="编辑对话..."
                      @input="e => autoResizeTextarea(e.target)"
                    ></textarea>
                  </div>
                </div>
                <button class="btn-confirm-synth" :disabled="store.synthesizing" @click="store.confirmScriptSynthesis">
                  <span v-if="store.synthesizing" class="spinner"></span>
                  {{ store.synthesizing ? '合成中...' : '确认并合成语音' }}
                </button>
              </div>
            </transition>

            <transition name="fade">
              <div v-if="store.hasAudioAdjustDraft" class="segment-speed-panel">
                <div class="segment-speed-header">
                  <h3>段级倍速处理</h3>
                  <p>语音已生成，可按文本段调整倍速后重新处理音频</p>
                </div>

                <div class="segment-speed-list">
                  <div v-for="(line, idx) in store.audioAdjustLines" :key="idx" class="segment-speed-item">
                    <div class="segment-line-meta">
                      <div class="segment-line-left">
                        <span class="segment-speaker">{{ line.speaker }}</span>
                        <span class="segment-index">第 {{ idx + 1 }} 段</span>
                      </div>
                      <button class="btn-play-segment" @click="toggleSegmentPlayback(idx, line)">
                        <svg v-if="playingSegmentIndex === idx" viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                          <rect x="6" y="5" width="4" height="14" />
                          <rect x="14" y="5" width="4" height="14" />
                        </svg>
                        <svg v-else viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                          <polygon points="7,5 19,12 7,19" />
                        </svg>
                        {{ playingSegmentIndex === idx ? '停止' : '播放' }}
                      </button>
                    </div>
                    <p class="segment-text">{{ line.text }}</p>
                    <div class="segment-speed-control">
                      <input
                        v-model.number="line.speech_rate"
                        type="range"
                        min="0.5"
                        max="2"
                        step="0.1"
                        @change="normalizeSpeechRate(line)"
                      />
                      <input
                        v-model.number="line.speech_rate"
                        type="number"
                        min="0.5"
                        max="2"
                        step="0.1"
                        class="speed-input"
                        @change="normalizeSpeechRate(line)"
                      />
                      <span class="speed-unit">x</span>
                    </div>
                  </div>
                </div>

                <p v-if="segmentSpeedError" class="segment-speed-error">{{ segmentSpeedError }}</p>

                <div class="segment-speed-actions">
                  <button
                    class="btn-confirm-synth"
                    :disabled="store.applyingSegmentSpeeds"
                    @click="applySegmentSpeeds"
                  >
                    <span v-if="store.applyingSegmentSpeeds" class="spinner"></span>
                    {{ store.applyingSegmentSpeeds ? '处理中...' : '应用&下一步' }}
                  </button>
                  <button class="btn-skip-adjust" @click="skipSegmentSpeedAdjust">跳过并完成</button>
                </div>
              </div>
            </transition>
          </div>

          <div v-if="!isStepBusy" class="step-actions">
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
    <GeneratePanel v-if="store.taskId" :task-id="store.taskId" @completed="store.onGenerateCompleted" />
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onBeforeUnmount } from 'vue'
import { useWorkflowStore } from '../stores/workflow'
import GeneratePanel from './GeneratePanel.vue'

const store = useWorkflowStore()

// ── Preview pipeline stages ──
const previewStages = [
  { key: 'news',     label: '获取资讯' },
  { key: 'topic',    label: '选定话题' },
  { key: 'research', label: '深度研究' },
  { key: 'planning', label: '节目策划' },
  { key: 'dialogue', label: '生成文稿' },
]

const segmentSpeedError = ref('')
const playingSegmentIndex = ref(null)
const segmentPlayer = ref(null)

// Hide the back button and step-actions whenever generation is in flight
const isStepBusy = computed(() =>
  store.generatingScript ||
  store.synthesizing ||
  store.generating ||
  !!store.taskId ||
  store.hasAudioAdjustDraft
)

function getPipelineStageClass(key) {
  const keys = previewStages.map(s => s.key)
  const currentIdx = keys.indexOf(store.previewStage)
  const itemIdx = keys.indexOf(key)
  if (currentIdx === -1) return 'pending'
  if (itemIdx < currentIdx) return 'completed'
  if (itemIdx === currentIdx) return 'active'
  return 'pending'
}

// ── Auto-resize textarea ──
function autoResizeTextarea(el) {
  if (!el) return
  el.style.height = 'auto'
  el.style.height = el.scrollHeight + 'px'
}

watch(() => store.scriptDraft, () => {
  nextTick(() => {
    document.querySelectorAll('.auto-textarea').forEach(autoResizeTextarea)
  })
})

watch(() => store.audioAdjustEpisodeId, () => {
  stopSegmentPlayback()
})

watch(
  () => store.audioAdjustLines.map(line => Number(line.speech_rate) || 1),
  (rates) => {
    if (
      segmentPlayer.value &&
      playingSegmentIndex.value !== null &&
      rates[playingSegmentIndex.value] !== undefined
    ) {
      const rate = Math.max(0.5, Math.min(2, Number(rates[playingSegmentIndex.value]) || 1))
      segmentPlayer.value.playbackRate = rate
    }
  },
  { deep: true }
)

const steps = [
  { key: 'news', label: '获取资讯' },
  { key: 'guests', label: '选择嘉宾' },
  { key: 'generate', label: '生成播客' }
]

function goToStep(idx) {
  if (idx < store.currentStep) store.currentStep = idx
}
function nextStep() {
  if (store.currentStep < steps.length - 1) store.currentStep++
}
function prevStep() {
  if (store.currentStep > 0) store.currentStep--
}

function getGuestName(name) {
  const guest = store.guests.find(g => g.name === name)
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

function normalizeSpeechRate(line) {
  const speed = Number(line.speech_rate)
  if (!Number.isFinite(speed)) {
    line.speech_rate = 1
    return
  }
  line.speech_rate = Math.max(0.5, Math.min(2, Number(speed.toFixed(1))))
}

async function applySegmentSpeeds() {
  segmentSpeedError.value = ''
  stopSegmentPlayback()
  try {
    await store.applySegmentSpeeds()
  } catch (e) {
    segmentSpeedError.value = e?.message || '段级倍速处理失败'
  }
}

function stopSegmentPlayback() {
  if (segmentPlayer.value) {
    segmentPlayer.value.pause()
    segmentPlayer.value.currentTime = 0
    segmentPlayer.value = null
  }
  playingSegmentIndex.value = null
}

function toggleSegmentPlayback(index, line) {
  if (!store.audioAdjustEpisodeId) return

  if (playingSegmentIndex.value === index && segmentPlayer.value) {
    stopSegmentPlayback()
    return
  }

  stopSegmentPlayback()

  const audio = new Audio(
    `/api/episodes/${store.audioAdjustEpisodeId}/segments/${index}/audio?ts=${Date.now()}`
  )
  audio.playbackRate = Math.max(0.5, Math.min(2, Number(line.speech_rate) || 1))
  audio.onended = () => stopSegmentPlayback()
  audio.onerror = () => {
    stopSegmentPlayback()
    segmentSpeedError.value = `第 ${index + 1} 段音频播放失败`
  }

  segmentPlayer.value = audio
  playingSegmentIndex.value = index
  audio.play().catch(() => {
    stopSegmentPlayback()
    segmentSpeedError.value = `第 ${index + 1} 段音频播放失败`
  })
}

function skipSegmentSpeedAdjust() {
  stopSegmentPlayback()
  store.skipSegmentSpeedAdjust()
}

onBeforeUnmount(() => {
  stopSegmentPlayback()
})

defineExpose({ nextStep, prevStep })
</script>

<style scoped>
.workflow-wizard {
  background: var(--c-surface);
  border: 2px solid var(--c-border);
  border-radius: var(--r-2xl);
  overflow: hidden;
  box-shadow: var(--shadow-card);
}

/* Progress */
.wizard-progress {
  display: flex;
  align-items: center;
  padding: 1.5rem 2rem;
  background: var(--c-bg-warm);
  border-bottom: 2px solid var(--c-border);
}

.progress-step {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  position: relative;
}

.progress-step:last-child {
  flex: 0;
}

.step-indicator {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.82rem;
  font-weight: 700;
  background: var(--c-surface);
  color: var(--c-text-3);
  border: 2px solid var(--c-border);
  transition: all var(--dur-normal) var(--ease-bounce);
  flex-shrink: 0;
}

.progress-step.active .step-indicator {
  background: var(--c-primary);
  border-color: var(--c-primary);
  color: white;
  box-shadow: 0 3px 14px rgba(255, 107, 53, 0.35);
  transform: scale(1.1);
}

.progress-step.completed .step-indicator {
  background: var(--c-success);
  border-color: var(--c-success);
  color: white;
}

.step-label {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--c-text-3);
  white-space: nowrap;
}

.progress-step.active .step-label {
  color: var(--c-primary);
  font-weight: 700;
}

.progress-step.completed .step-label {
  color: var(--c-success);
}

.step-line {
  flex: 1;
  height: 3px;
  background: var(--c-border);
  margin: 0 14px;
  border-radius: 2px;
}

.step-line.filled {
  background: var(--c-success);
}

/* Content */
.wizard-content {
  padding: 2rem;
}

.step-panel {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.step-header {
  display: flex;
  align-items: flex-start;
  gap: 1.25rem;
}

.step-icon {
  width: 52px;
  height: 52px;
  border-radius: var(--r-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.step-icon.news {
  background: var(--c-primary-soft);
  color: var(--c-primary);
}

.step-icon.guests {
  background: var(--c-blue-soft);
  color: var(--c-blue);
}

.step-icon.generate {
  background: var(--c-yellow-soft);
  color: #D4A017;
}

.step-header h2 {
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--c-text-1);
  letter-spacing: -0.01em;
}

.step-header p {
  font-size: 0.88rem;
  color: var(--c-text-3);
}

.btn-config {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 2px solid var(--c-border);
  background: var(--c-surface);
  border-radius: var(--r-full);
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--c-text-2);
  cursor: pointer;
  transition: all var(--dur-fast) var(--ease);
}

.btn-config:hover {
  border-color: var(--c-accent);
  color: var(--c-accent);
  background: var(--c-accent-soft);
}

/* Topic Input */
.topic-input-group {
  margin-bottom: 16px;
}

.topic-label {
  display: block;
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--c-text-2);
  margin-bottom: 10px;
}

.topic-input {
  width: 100%;
  padding: 14px 18px;
  background: var(--c-bg);
  border: 2px solid var(--c-border);
  border-radius: var(--r-lg);
  font-size: 0.95rem;
  color: var(--c-text-1);
  font-family: var(--font-sans);
  outline: none;
  transition: all var(--dur-fast) var(--ease);
  box-sizing: border-box;
}

.topic-input::placeholder {
  color: var(--c-text-3);
}

.topic-input:focus {
  border-color: var(--c-primary);
  box-shadow: var(--shadow-focus);
  background: var(--c-surface);
}

/* Fetch Button */
.btn-fetch {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 14px 28px;
  background: var(--c-primary);
  color: white;
  border: none;
  border-radius: var(--r-full);
  font-size: 0.95rem;
  font-weight: 700;
  cursor: pointer;
  font-family: var(--font-sans);
  box-shadow: 0 4px 14px rgba(255, 107, 53, 0.25);
  transition: all var(--dur-normal) var(--ease-bounce);
}

.btn-fetch:hover:not(:disabled) {
  background: var(--c-primary-hover);
  box-shadow: 0 6px 20px rgba(255, 107, 53, 0.35);
  transform: translateY(-2px);
}

.btn-fetch:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* News Result */
.news-result {
  background: var(--c-bg);
  border: 2px solid var(--c-border);
  border-radius: var(--r-xl);
  padding: 1.5rem;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--c-success);
  margin-bottom: 1.25rem;
}

.news-list {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  max-height: 300px;
  overflow-y: auto;
  margin-bottom: 1.25rem;
}

.news-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 1rem;
  border: 2px solid var(--c-border);
  border-radius: var(--r-lg);
  background: var(--c-surface);
  cursor: pointer;
  transition: all var(--dur-fast) var(--ease);
}

.news-item:hover {
  border-color: var(--c-primary);
  background: var(--c-primary-soft);
}

.news-item.selected {
  border-color: var(--c-primary);
  background: var(--c-primary-soft);
  box-shadow: 0 0 0 1px rgba(255, 107, 53, 0.15);
}

.news-radio {
  flex-shrink: 0;
  padding-top: 2px;
}

.radio-dot {
  width: 20px;
  height: 20px;
  border: 2px solid var(--c-border);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--dur-fast) var(--ease);
}

.radio-dot.active {
  border-color: var(--c-primary);
  border-width: 3px;
}

.radio-dot.active::after {
  content: '';
  width: 8px;
  height: 8px;
  background: var(--c-primary);
  border-radius: 50%;
}

.news-content h4 {
  font-size: 0.92rem;
  font-weight: 700;
  color: var(--c-text-1);
  margin-bottom: 0.3rem;
  line-height: 1.4;
}

.news-content p {
  font-size: 0.78rem;
  color: var(--c-text-3);
  line-height: 1.5;
}

/* Guest Selection */
.guest-selection {
  margin-bottom: 1rem;
}

.empty-guests {
  text-align: center;
  padding: 2.5rem;
  background: var(--c-bg);
  border-radius: var(--r-xl);
  border: 2px dashed var(--c-border);
}

.empty-guests .empty-icon {
  width: 68px;
  height: 68px;
  margin: 0 auto 1rem;
  background: var(--c-surface);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-text-3);
}

.empty-guests p {
  color: var(--c-text-3);
  margin-bottom: 1.25rem;
  font-size: .95rem;
}

.btn-add {
  padding: 10px 24px;
  background: var(--c-primary);
  color: white;
  border: none;
  border-radius: var(--r-full);
  font-weight: 700;
  cursor: pointer;
  font-family: var(--font-sans);
  box-shadow: 0 3px 10px rgba(255, 107, 53, 0.25);
}

.guest-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1rem;
}

.guest-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 1.15rem;
  background: var(--c-surface);
  border: 2px solid var(--c-border);
  border-radius: var(--r-xl);
  cursor: pointer;
  transition: all var(--dur-normal) var(--ease);
  position: relative;
}

.guest-card:hover {
  border-color: var(--c-primary);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.guest-card.selected {
  border-color: var(--c-primary);
  background: linear-gradient(135deg, var(--c-primary-soft), rgba(255, 245, 237, 0.5));
  box-shadow: 0 0 0 2px rgba(255, 107, 53, 0.1);
}

.guest-avatar {
  width: 48px;
  height: 48px;
  border-radius: var(--r-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.2rem;
  font-weight: 700;
  flex-shrink: 0;
}

.guest-info {
  flex: 1;
  min-width: 0;
}

.guest-info h4 {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--c-text-1);
  margin-bottom: 4px;
}

.guest-info .mbti {
  display: inline-block;
  padding: 2px 8px;
  background: var(--c-accent-soft);
  border-radius: var(--r-full);
  font-size: 0.68rem;
  font-weight: 700;
  color: var(--c-accent);
  margin-right: 6px;
}

.guest-info .occupation {
  font-size: 0.78rem;
  color: var(--c-text-3);
  font-weight: 500;
}

.selection-check {
  width: 26px;
  height: 26px;
  border: 2px solid var(--c-border);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all var(--dur-fast) var(--ease);
}

.guest-card.selected .selection-check {
  background: var(--c-primary);
  border-color: var(--c-primary);
  color: white;
  box-shadow: 0 2px 8px rgba(255, 107, 53, 0.3);
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
  padding: 10px 20px;
  border: 2px solid var(--c-border);
  background: var(--c-surface);
  border-radius: var(--r-full);
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--c-text-2);
  cursor: pointer;
  font-family: var(--font-sans);
  transition: all var(--dur-fast) var(--ease);
}

.btn-back:hover {
  background: var(--c-bg);
  border-color: var(--c-text-3);
}

.btn-next {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  background: var(--c-success);
  color: white;
  border: none;
  border-radius: var(--r-full);
  font-size: 0.88rem;
  font-weight: 700;
  cursor: pointer;
  font-family: var(--font-sans);
  box-shadow: 0 3px 10px rgba(46, 204, 113, 0.25);
  transition: all var(--dur-normal) var(--ease-bounce);
}

.btn-next:hover:not(:disabled) {
  box-shadow: 0 5px 16px rgba(46, 204, 113, 0.35);
  transform: translateY(-2px);
}

.btn-next:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Generate Step */
.topic-summary,
.guests-summary {
  padding: 1.25rem;
  background: var(--c-bg);
  border: 2px solid var(--c-border);
  border-radius: var(--r-lg);
}

.summary-label {
  font-size: 0.78rem;
  color: var(--c-text-3);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
}

.summary-value {
  font-size: 1rem;
  font-weight: 700;
  color: var(--c-text-1);
}

.guests-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.guest-tag {
  padding: 5px 14px;
  background: var(--c-accent-soft);
  border-radius: var(--r-full);
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--c-accent);
}

/* Mode Toggle */
.mode-toggle {
  display: flex;
  background: var(--c-bg-warm);
  border-radius: var(--r-full);
  padding: 5px;
  border: 2px solid var(--c-border);
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
  color: var(--c-text-3);
  border-radius: var(--r-full);
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  font-family: var(--font-sans);
  transition: all var(--dur-normal) var(--ease);
}

.mode-btn.active {
  background: var(--c-surface);
  color: var(--c-primary);
  box-shadow: var(--shadow-sm);
  font-weight: 700;
}

/* Generate Action */
.generate-action {
  display: flex;
  justify-content: center;
  padding: 1.5rem 0;
}

.btn-generate {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 18px 40px;
  background: linear-gradient(135deg, var(--c-primary) 0%, #FF8F5F 100%);
  color: white;
  border: none;
  border-radius: var(--r-full);
  font-size: 1.05rem;
  font-weight: 800;
  cursor: pointer;
  font-family: var(--font-sans);
  box-shadow: 0 6px 24px rgba(255, 107, 53, 0.35);
  transition: all var(--dur-normal) var(--ease-bounce);
}

.btn-generate:hover:not(:disabled) {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 10px 32px rgba(255, 107, 53, 0.4);
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
  background: var(--c-surface);
  border: 2px solid var(--c-border);
  border-radius: var(--r-full);
  font-size: 0.92rem;
  font-weight: 600;
  color: var(--c-text-1);
  cursor: pointer;
  font-family: var(--font-sans);
  transition: all var(--dur-fast) var(--ease);
}

.btn-generate-outline:hover:not(:disabled) {
  border-color: var(--c-primary);
  color: var(--c-primary);
  background: var(--c-primary-soft);
}

/* Script Preview */
.script-preview {
  background: var(--c-surface);
  border: 2px solid var(--c-border);
  border-radius: var(--r-xl);
  padding: 1.5rem;
}

.preview-header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
  padding-bottom: 1.25rem;
  border-bottom: 2px solid var(--c-border);
}

.preview-header h3 {
  flex: 1;
  min-width: 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--c-text-1);
}

.preview-header p {
  width: 100%;
  font-size: 0.88rem;
  color: var(--c-text-2);
  margin-top: 0.3rem;
  order: 3;
}

.btn-regen {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 14px;
  border: 2px solid var(--c-border);
  background: var(--c-surface);
  border-radius: var(--r-full);
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--c-text-3);
  cursor: pointer;
  font-family: var(--font-sans);
  flex-shrink: 0;
  transition: all var(--dur-fast) var(--ease);
}

.btn-regen:hover {
  border-color: var(--c-primary);
  color: var(--c-primary);
  background: var(--c-primary-soft);
}

/* Preview Pipeline */
.preview-pipeline {
  background: var(--c-bg);
  border: 2px solid var(--c-border);
  border-radius: var(--r-xl);
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.pipeline-stages {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  margin-bottom: 1rem;
}

.pipeline-stage {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.stage-dot {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  border: 2px solid var(--c-border);
  background: var(--c-surface);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all var(--dur-normal) var(--ease-bounce);
}

.pipeline-stage.completed .stage-dot {
  background: var(--c-success);
  border-color: var(--c-success);
  color: white;
}

.pipeline-stage.active .stage-dot {
  background: var(--c-primary);
  border-color: var(--c-primary);
  box-shadow: 0 2px 10px rgba(255, 107, 53, 0.35);
}

.pipeline-stage .stage-label {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--c-text-3);
  margin-left: 6px;
  white-space: nowrap;
}

.pipeline-stage.completed .stage-label {
  color: var(--c-success);
}

.pipeline-stage.active .stage-label {
  color: var(--c-primary);
  font-weight: 700;
}

.stage-line {
  height: 2px;
  width: 28px;
  background: var(--c-border);
  border-radius: 2px;
  margin: 0 4px;
  flex-shrink: 0;
  transition: background var(--dur-normal) var(--ease);
}

.stage-line.filled {
  background: var(--c-success);
}

.stage-spinner {
  width: 10px;
  height: 10px;
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  display: block;
}

.pipeline-detail {
  font-size: 0.82rem;
  color: var(--c-text-2);
  text-align: center;
  animation: fadeInUp 0.4s ease;
}

.btn-cancel-preview {
  margin-top: 0.9rem;
  padding: 7px 14px;
  border: 2px solid var(--c-border);
  background: var(--c-surface);
  color: var(--c-text-2);
  border-radius: var(--r-full);
  font-size: 0.78rem;
  font-weight: 600;
  font-family: var(--font-sans);
  cursor: pointer;
  transition: all var(--dur-fast) var(--ease);
}

.btn-cancel-preview:hover {
  border-color: var(--c-primary);
  color: var(--c-primary);
  background: var(--c-primary-soft);
}

.btn-cancel-preview:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}

.dialogue-list {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  max-height: 55vh;
  overflow-y: auto;
  margin-bottom: 1.25rem;
  padding-right: 4px;
}

.dialogue-item {
  display: flex;
  gap: 12px;
}

.speaker {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  width: 64px;
  flex-shrink: 0;
}

.speaker .avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.78rem;
  font-weight: 700;
  color: white;
}

.avatar.host { background: linear-gradient(135deg, var(--c-primary), #FF8F5F); }
.avatar.tech { background: linear-gradient(135deg, var(--c-blue), #0099CC); }
.avatar.pm { background: linear-gradient(135deg, var(--c-yellow), #D4A017); }
.avatar.ethics { background: linear-gradient(135deg, var(--c-success), #1A9B4E); }
.avatar.guest { background: linear-gradient(135deg, var(--c-accent), var(--c-purple)); }

.speaker .name {
  font-size: 0.68rem;
  color: var(--c-text-3);
  font-weight: 600;
}

.dialogue-item .auto-textarea {
  flex: 1;
  border: 2px solid var(--c-border);
  border-radius: var(--r-md);
  padding: 0.65rem;
  font-size: 0.85rem;
  font-family: var(--font-sans);
  line-height: 1.65;
  resize: none;
  background: var(--c-bg);
  color: var(--c-text-1);
  overflow: hidden;
  min-height: 2.8rem;
  /* CSS auto-resize for modern browsers */
  field-sizing: content;
}

.dialogue-item .auto-textarea:focus {
  outline: none;
  border-color: var(--c-primary);
  background: var(--c-surface);;
}

.btn-confirm-synth {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 14px;
  background: var(--c-success);
  color: white;
  border: none;
  border-radius: var(--r-full);
  font-size: 0.95rem;
  font-weight: 700;
  cursor: pointer;
  font-family: var(--font-sans);
  box-shadow: 0 4px 14px rgba(46, 204, 113, 0.25);
  transition: all var(--dur-normal) var(--ease-bounce);
}

.btn-confirm-synth:hover:not(:disabled) {
  box-shadow: 0 6px 20px rgba(46, 204, 113, 0.35);
  transform: translateY(-2px);
}

.segment-speed-panel {
  margin-top: 1rem;
  border: 1px solid var(--c-border);
  border-radius: var(--r-lg);
  background: var(--c-bg-warm);
  padding: 1rem;
}

.segment-speed-header h3 {
  margin: 0;
  font-size: 1.05rem;
  color: var(--c-text-1);
}

.segment-speed-header p {
  margin: 0.35rem 0 0;
  color: var(--c-text-2);
  font-size: 0.85rem;
}

.segment-speed-list {
  margin-top: 0.85rem;
  max-height: 42vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  padding-right: 4px;
}

.segment-speed-item {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--r-md);
  padding: 0.65rem;
}

.segment-line-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.3rem;
}

.segment-line-left {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.segment-speaker {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--c-text-1);
}

.segment-index {
  font-size: 0.74rem;
  color: var(--c-text-3);
}

.segment-text {
  margin: 0;
  font-size: 0.82rem;
  line-height: 1.55;
  color: var(--c-text-2);
}

.segment-speed-control {
  margin-top: 0.45rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.segment-speed-control input[type="range"] {
  flex: 1;
}

.speed-input {
  width: 56px;
  border: 1px solid var(--c-border);
  border-radius: var(--r-sm);
  padding: 0.3rem 0.35rem;
  font-size: 0.8rem;
  color: var(--c-text-1);
  background: var(--c-surface);
}

.speed-unit {
  font-size: 0.8rem;
  color: var(--c-text-3);
}

.btn-play-segment {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 0.26rem 0.5rem;
  border-radius: var(--r-full);
  border: 1px solid var(--c-border);
  background: var(--c-surface);
  color: var(--c-text-2);
  cursor: pointer;
  font-size: 0.72rem;
  font-weight: 600;
}

.btn-play-segment:hover {
  border-color: var(--c-primary);
  color: var(--c-primary);
}

.segment-speed-actions {
  margin-top: 0.8rem;
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.btn-skip-adjust {
  border: 1px solid var(--c-border);
  background: var(--c-surface);
  color: var(--c-text-2);
  border-radius: var(--r-full);
  padding: 0.68rem 1rem;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-skip-adjust:hover {
  border-color: var(--c-primary);
  color: var(--c-primary);
}

.segment-speed-error {
  margin-top: 0.65rem;
  color: #d92d20;
  font-size: 0.8rem;
}

.segment-speed-panel {
  margin-top: 1rem;
  border: 2px solid var(--c-border);
  border-radius: var(--r-lg);
  background: var(--c-bg);
  padding: 1rem;
}

.segment-speed-header {
  margin-bottom: 0.85rem;
}

.segment-speed-header h3 {
  margin: 0;
  font-size: 1rem;
  color: var(--c-text-1);
}

.segment-speed-header p {
  margin: 0.35rem 0 0;
  font-size: 0.82rem;
  color: var(--c-text-2);
}

.segment-speed-list {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
  max-height: 42vh;
  overflow-y: auto;
  padding-right: 4px;
}

.segment-speed-item {
  border: 1px solid var(--c-border);
  border-radius: var(--r-md);
  background: var(--c-surface);
  padding: 0.65rem;
}

.segment-line-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.35rem;
}

.segment-speaker {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--c-text-1);
}

.segment-index {
  font-size: 0.72rem;
  color: var(--c-text-3);
}

.segment-text {
  margin: 0;
  color: var(--c-text-2);
  font-size: 0.8rem;
  line-height: 1.6;
}

.segment-speed-control {
  margin-top: 0.5rem;
  display: flex;
  align-items: center;
  gap: 8px;
}

.segment-speed-control input[type="range"] {
  flex: 1;
}

.speed-input {
  width: 62px;
  border: 1px solid var(--c-border);
  border-radius: var(--r-sm);
  padding: 4px 6px;
  background: white;
  color: var(--c-text-1);
  font-size: 0.8rem;
}

.speed-unit {
  font-size: 0.8rem;
  color: var(--c-text-3);
  font-weight: 700;
}

.segment-speed-actions {
  display: flex;
  gap: 8px;
  margin-top: 0.85rem;
}

.btn-skip-adjust {
  flex: 0 0 auto;
  padding: 0.7rem 0.95rem;
  border: 2px solid var(--c-border);
  background: var(--c-surface);
  color: var(--c-text-2);
  border-radius: var(--r-full);
  font-size: 0.82rem;
  font-weight: 700;
  cursor: pointer;
}

.segment-speed-error {
  margin-top: 0.65rem;
  margin-bottom: 0;
  color: var(--c-danger);
  font-size: 0.8rem;
}

/* Spinner */
.spinner {
  width: 18px;
  height: 18px;
  border: 2.5px solid rgba(255, 255, 255, 0.3);
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
  transition: all 0.3s var(--ease);
}

.slide-up-enter-from {
  opacity: 0;
  transform: translateY(12px);
}

.slide-up-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s var(--ease);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Responsive */
@media (max-width: 768px) {
  .wizard-progress {
    overflow-x: auto;
    padding: 1rem 1.25rem;
  }
  
  .wizard-content {
    padding: 1.5rem;
  }
  
  .step-label {
    display: none;
  }
  
  .guest-cards {
    grid-template-columns: 1fr;
  }
}
</style>
