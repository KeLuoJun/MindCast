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
            {{ store.fetchingNews ? '获取中...' : '立即获取资讯' }}
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
            <button class="btn-generate-outline" :disabled="!store.canGenerate || store.generatingScript" @click="store.generateScriptPreview">
              <span v-if="store.generatingScript" class="spinner"></span>
              {{ store.generatingScript ? '生成中...' : '生成文稿预览' }}
            </button>

            <transition name="fade">
              <div v-if="store.hasScriptDraft" class="script-preview">
                <div class="preview-header">
                  <h3>{{ store.scriptDraft.title }}</h3>
                  <p>{{ store.scriptDraft.summary }}</p>
                </div>
                <div class="dialogue-list">
                  <div v-for="(line, idx) in store.scriptDraft.dialogue" :key="idx" class="dialogue-item">
                    <div class="speaker">
                      <span class="avatar" :class="getSpeakerClass(line.speaker)">{{ line.speaker.charAt(0) }}</span>
                      <span class="name">{{ line.speaker }}</span>
                    </div>
                    <textarea v-model="line.text" rows="2" placeholder="编辑对话..."></textarea>
                  </div>
                </div>
                <button class="btn-confirm-synth" :disabled="store.synthesizing" @click="store.confirmScriptSynthesis">
                  <span v-if="store.synthesizing" class="spinner"></span>
                  {{ store.synthesizing ? '合成中...' : '确认并合成语音' }}
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
    <GeneratePanel v-if="store.taskId" :task-id="store.taskId" @completed="store.onGenerateCompleted" />
  </div>
</template>

<script setup>
import { useWorkflowStore } from '../stores/workflow'
import GeneratePanel from './GeneratePanel.vue'

const store = useWorkflowStore()

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

defineExpose({ nextStep, prevStep })
</script>

<style scoped>
.workflow-wizard {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--r-xl);
  overflow: hidden;
}

/* Progress */
.wizard-progress {
  display: flex;
  align-items: center;
  padding: 1.25rem 1.5rem;
  background: var(--c-bg);
  border-bottom: 1px solid var(--c-border);
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
  background: var(--c-bg);
  color: var(--c-text-3);
  border: 2px solid var(--c-border);
  transition: all var(--dur-normal) var(--ease);
  flex-shrink: 0;
}

.progress-step.active .step-indicator {
  background: var(--c-primary);
  border-color: var(--c-primary);
  color: white;
  box-shadow: 0 0 12px rgba(91, 91, 214, 0.35);
}

.progress-step.completed .step-indicator {
  background: var(--c-success);
  border-color: var(--c-success);
  color: white;
}

.step-label {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--c-text-3);
  white-space: nowrap;
}

.progress-step.active .step-label {
  color: var(--c-primary);
}

.progress-step.completed .step-label {
  color: var(--c-success);
}

.step-line {
  flex: 1;
  height: 2px;
  background: var(--c-border);
  margin: 0 12px;
}

.step-line.filled {
  background: var(--c-success);
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
  border-radius: var(--r-md);
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
  background: rgba(16, 185, 129, 0.12);
  color: var(--c-success);
}

.step-icon.generate {
  background: rgba(229, 162, 60, 0.12);
  color: var(--c-accent);
}

.step-header h2 {
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--c-text-1);
}

.step-header p {
  font-size: 0.85rem;
  color: var(--c-text-3);
}

.btn-config {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 1px solid var(--c-border);
  background: var(--c-surface);
  border-radius: var(--r-md);
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--c-text-2);
  cursor: pointer;
  transition: all var(--dur-fast) var(--ease);
}

.btn-config:hover {
  border-color: var(--c-primary);
  color: var(--c-primary);
}

/* Topic Input */
.topic-input-group {
  margin-bottom: 16px;
}

.topic-label {
  display: block;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--c-text-2);
  margin-bottom: 8px;
}

.topic-input {
  width: 100%;
  padding: 12px 16px;
  background: var(--c-bg);
  border: 1px solid var(--c-border);
  border-radius: var(--r-md);
  font-size: 0.95rem;
  color: var(--c-text-1);
  outline: none;
  transition: border-color var(--dur-fast) var(--ease);
  box-sizing: border-box;
}

.topic-input::placeholder {
  color: var(--c-text-3);
}

.topic-input:focus {
  border-color: var(--c-primary);
  box-shadow: var(--shadow-focus);
}

/* Fetch Button */
.btn-fetch {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 14px 24px;
  background: var(--c-primary);
  color: white;
  border: none;
  border-radius: var(--r-md);
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--dur-fast) var(--ease);
}

.btn-fetch:hover:not(:disabled) {
  background: var(--c-primary-hover);
  box-shadow: var(--shadow-md);
}

.btn-fetch:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* News Result */
.news-result {
  background: var(--c-bg);
  border: 1px solid var(--c-border);
  border-radius: var(--r-lg);
  padding: 1.25rem;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--c-success);
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
  border: 1px solid var(--c-border);
  border-radius: var(--r-md);
  background: var(--c-surface);
  cursor: pointer;
  transition: all var(--dur-fast) var(--ease);
}

.news-item:hover {
  border-color: var(--c-primary);
}

.news-item.selected {
  border-color: var(--c-primary);
  background: var(--c-primary-soft);
}

.news-radio {
  flex-shrink: 0;
  padding-top: 2px;
}

.radio-dot {
  width: 18px;
  height: 18px;
  border: 2px solid var(--c-border);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--dur-fast) var(--ease);
}

.radio-dot.active {
  border-color: var(--c-primary);
}

.radio-dot.active::after {
  content: '';
  width: 8px;
  height: 8px;
  background: var(--c-primary);
  border-radius: 50%;
}

.news-content h4 {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--c-text-1);
  margin-bottom: 0.25rem;
  line-height: 1.4;
}

.news-content p {
  font-size: 0.75rem;
  color: var(--c-text-3);
  line-height: 1.5;
}

/* Guest Selection */
.guest-selection {
  margin-bottom: 1rem;
}

.empty-guests {
  text-align: center;
  padding: 2rem;
  background: var(--c-bg);
  border-radius: var(--r-lg);
}

.empty-guests .empty-icon {
  width: 64px;
  height: 64px;
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
  margin-bottom: 1rem;
}

.btn-add {
  padding: 10px 20px;
  background: var(--c-primary);
  color: white;
  border: none;
  border-radius: var(--r-md);
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
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--r-lg);
  cursor: pointer;
  transition: all var(--dur-fast) var(--ease);
  position: relative;
}

.guest-card:hover {
  border-color: var(--c-primary);
  box-shadow: var(--shadow-sm);
}

.guest-card.selected {
  border-color: var(--c-primary);
  background: var(--c-primary-soft);
}

.guest-avatar {
  width: 44px;
  height: 44px;
  border-radius: var(--r-md);
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
  color: var(--c-text-1);
  margin-bottom: 2px;
}

.guest-info .mbti {
  display: inline-block;
  padding: 1px 6px;
  background: rgba(91, 91, 214, 0.1);
  border-radius: 4px;
  font-size: 0.65rem;
  font-weight: 600;
  color: var(--c-primary);
  margin-right: 6px;
}

.guest-info .occupation {
  font-size: 0.75rem;
  color: var(--c-text-3);
}

.selection-check {
  width: 24px;
  height: 24px;
  border: 2px solid var(--c-border);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.guest-card.selected .selection-check {
  background: var(--c-primary);
  border-color: var(--c-primary);
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
  border: 1px solid var(--c-border);
  background: var(--c-surface);
  border-radius: var(--r-md);
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--c-text-2);
  cursor: pointer;
  transition: all var(--dur-fast) var(--ease);
}

.btn-back:hover {
  background: var(--c-bg);
}

.btn-next {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: var(--c-success);
  color: white;
  border: none;
  border-radius: var(--r-md);
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--dur-fast) var(--ease);
}

.btn-next:hover:not(:disabled) {
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
  background: var(--c-bg);
  border: 1px solid var(--c-border);
  border-radius: var(--r-md);
}

.summary-label {
  font-size: 0.75rem;
  color: var(--c-text-3);
  margin-bottom: 0.5rem;
}

.summary-value {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--c-text-1);
}

.guests-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.guest-tag {
  padding: 4px 10px;
  background: var(--c-primary-soft);
  border-radius: var(--r-sm);
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--c-primary);
}

/* Mode Toggle */
.mode-toggle {
  display: flex;
  background: var(--c-bg);
  border-radius: var(--r-md);
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
  color: var(--c-text-3);
  border-radius: var(--r-sm);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--dur-fast) var(--ease);
}

.mode-btn.active {
  background: var(--c-surface);
  color: var(--c-primary);
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
  background: var(--c-accent);
  color: white;
  border: none;
  border-radius: var(--r-md);
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--dur-fast) var(--ease);
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
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--r-md);
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--c-text-1);
  cursor: pointer;
  transition: all var(--dur-fast) var(--ease);
}

.btn-generate-outline:hover:not(:disabled) {
  border-color: var(--c-primary);
  color: var(--c-primary);
}

/* Script Preview */
.script-preview {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--r-lg);
  padding: 1.25rem;
}

.preview-header {
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--c-border);
}

.preview-header h3 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--c-text-1);
}

.preview-header p {
  font-size: 0.85rem;
  color: var(--c-text-2);
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

.avatar.host { background: linear-gradient(135deg, var(--c-primary), var(--c-accent)); }
.avatar.tech { background: linear-gradient(135deg, #3b82f6, #1d4ed8); }
.avatar.pm { background: linear-gradient(135deg, var(--c-accent), #b45309); }
.avatar.ethics { background: linear-gradient(135deg, var(--c-success), #047857); }
.avatar.guest { background: linear-gradient(135deg, #64748b, #475569); }

.speaker .name {
  font-size: 0.65rem;
  color: var(--c-text-3);
}

.dialogue-item textarea {
  flex: 1;
  border: 1px solid var(--c-border);
  border-radius: var(--r-sm);
  padding: 0.5rem;
  font-size: 0.8rem;
  resize: none;
}

.dialogue-item textarea:focus {
  outline: none;
  border-color: var(--c-primary);
}

.btn-confirm-synth {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 12px;
  background: var(--c-success);
  color: white;
  border: none;
  border-radius: var(--r-md);
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--dur-fast) var(--ease);
}

.btn-confirm-synth:hover:not(:disabled) {
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
