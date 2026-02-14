<template>
  <div class="home">
    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-content">
        <div class="hero-badge">
          <span class="badge-dot"></span>
          AI 智能播客
        </div>
        <h1 class="hero-title">
          欢迎来到 <span class="brand-text">AI圆桌派</span>
        </h1>
        <p class="hero-desc">
          多智能体协作生成 · 每日为您提供深度、多元的 AI 资讯解读
        </p>
      </div>
      <div class="hero-decoration">
        <div class="decoration-circle circle-1"></div>
        <div class="decoration-circle circle-2"></div>
        <div class="decoration-circle circle-3"></div>
      </div>
    </section>

    <!-- Quick Actions -->
    <section class="actions-grid">
      <!-- Fetch News Card -->
      <div class="action-card fetch-card" :class="{ 'busy': isBusy }">
        <div class="card-header">
          <div class="card-icon fetch-icon">
            <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 6v6l4 2"/>
            </svg>
          </div>
          <div class="card-title">
            <h3>获取今日资讯</h3>
            <p>从 AI 领域获取最新新闻</p>
          </div>
        </div>
        <button
          class="btn-primary"
          :disabled="isBusy"
          @click="fetchNews"
        >
          <span v-if="fetchingNews" class="btn-spinner"></span>
          {{ fetchingNews ? '获取中...' : '立即获取' }}
        </button>
        <transition name="slide">
          <div v-if="newsContent" class="news-preview">
            <div class="news-header">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20,6 9,17 4,12"/>
              </svg>
              已获取 {{ newsContent.count }} 篇资讯
            </div>
            <ul class="news-list">
              <li v-for="(item, idx) in newsContent.items" :key="idx" class="news-item">
                {{ item.title || item.content?.slice(0, 60) + '...' }}
              </li>
            </ul>
          </div>
        </transition>
      </div>

      <!-- Generate Podcast Card -->
      <div class="action-card generate-card" :class="{ 'disabled': !hasNews || isBusy }">
        <div class="card-header">
          <div class="card-icon generate-icon">
            <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2a3 3 0 00-3 3v7a3 3 0 006 0V5a3 3 0 00-3-3z"/>
              <path d="M19 10v2a7 7 0 01-14 0v-2"/>
              <line x1="12" y1="19" x2="12" y2="22"/>
            </svg>
          </div>
          <div class="card-title">
            <h3>生成播客</h3>
            <p>一键生成或分步确认</p>
          </div>
        </div>
        
        <div class="mode-toggle">
          <button
            class="mode-btn"
            :class="{ active: workflowMode === 'one-click' }"
            :disabled="isBusy"
            @click="workflowMode = 'one-click'"
          >
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
              <polygon points="5,3 19,12 5,21"/>
            </svg>
            一键生成
          </button>
          <button
            class="mode-btn"
            :class="{ active: workflowMode === 'step-by-step' }"
            :disabled="isBusy"
            @click="workflowMode = 'step-by-step'"
          >
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="8" y1="6" x2="21" y2="6"/>
              <line x1="8" y1="12" x2="21" y2="12"/>
              <line x1="8" y1="18" x2="21" y2="18"/>
            </svg>
            分步确认
          </button>
        </div>

        <button
          v-if="workflowMode === 'one-click'"
          class="btn-generate"
          :disabled="!hasNews || isBusy"
          @click="startGenerate"
        >
          <span v-if="generating" class="btn-spinner"></span>
          {{ generating ? '生成中...' : '开始生成' }}
        </button>

        <template v-else>
          <button
            class="btn-secondary"
            :disabled="!hasNews || isBusy"
            @click="generateScriptPreview"
          >
            <span v-if="generatingScript" class="btn-spinner"></span>
            {{ generatingScript ? '生成中...' : (hasScriptDraft ? '重新生成' : '生成文稿') }}
          </button>
          <button
            class="btn-confirm"
            :disabled="!hasScriptDraft || isBusy"
            @click="confirmScriptSynthesis"
          >
            <span v-if="synthesizing" class="btn-spinner"></span>
            {{ synthesizing ? '合成中...' : '确认并合成' }}
          </button>
        </template>
      </div>
    </section>

    <!-- Script Editor -->
    <section v-if="workflowMode === 'step-by-step' && hasScriptDraft" class="script-section">
      <div class="section-header">
        <div class="section-icon">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
        </div>
        <div>
          <h2>文稿预览</h2>
          <p>可编辑对话内容后进行语音合成</p>
        </div>
      </div>
      <div class="script-card">
        <div class="script-header">
          <h3>{{ scriptDraft.title || scriptDraft.topic }}</h3>
          <p>{{ scriptDraft.summary }}</p>
        </div>
        <div class="dialogue-list">
          <div
            v-for="(line, idx) in scriptDraft.dialogue"
            :key="idx"
            class="dialogue-item"
          >
            <div class="speaker-info">
              <span class="speaker-avatar" :class="getSpeakerClass(line.speaker)">
                {{ line.speaker.charAt(0) }}
              </span>
              <span class="speaker-name">{{ line.speaker }}</span>
            </div>
            <textarea v-model="line.text" rows="2" placeholder="编辑对话..."></textarea>
          </div>
        </div>
      </div>
    </section>

    <!-- Generation Panel -->
    <GeneratePanel v-if="taskId" :task-id="taskId" @completed="onCompleted" />

    <!-- Episodes Section -->
    <section class="episodes-section">
      <div class="section-header">
        <div class="section-icon">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <polygon points="10,8 16,12 10,16"/>
          </svg>
        </div>
        <div>
          <h2>往期节目</h2>
          <p>点击播放往期精彩内容</p>
        </div>
      </div>
      
      <div v-if="episodes.length === 0" class="empty-state">
        <div class="empty-icon">
          <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M12 2a3 3 0 00-3 3v7a3 3 0 006 0V5a3 3 0 00-3-3z"/>
            <path d="M19 10v2a7 7 0 01-14 0v-2"/>
            <line x1="12" y1="19" x2="12" y2="22"/>
          </svg>
        </div>
        <p>暂无节目，点击上方按钮生成第一期播客</p>
      </div>
      
      <div v-else class="episodes-grid">
        <div
          v-for="(ep, idx) in episodes"
          :key="ep.id"
          class="episode-card"
          @click="$router.push(`/episode/${ep.id}`)"
        >
          <div class="episode-cover">
            <div class="cover-play">
              <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
                <path d="M8 5v14l11-7z"/>
              </svg>
            </div>
            <span v-if="ep.duration_seconds" class="duration">{{ formatDuration(ep.duration_seconds) }}</span>
          </div>
          <div class="episode-body">
            <span class="episode-date">{{ formatDate(ep.created_at) }}</span>
            <h3>{{ ep.title }}</h3>
            <p>{{ ep.summary }}</p>
            <div class="episode-guests">
              <span v-for="g in ep.guests" :key="g" class="guest">{{ g }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import GeneratePanel from '../components/GeneratePanel.vue'

const episodes = ref([])
const generating = ref(false)
const fetchingNews = ref(false)
const generatingScript = ref(false)
const synthesizing = ref(false)
const taskId = ref(null)
const newsContent = ref(null)
const workflowMode = ref('one-click')
const scriptDraft = ref(null)

const hasNews = computed(() => newsContent.value !== null)
const hasScriptDraft = computed(() => scriptDraft.value && scriptDraft.value.dialogue?.length > 0)
const isBusy = computed(() => fetchingNews.value || generating.value || generatingScript.value || synthesizing.value)

async function fetchEpisodes() {
  try {
    const res = await fetch('/api/episodes')
    episodes.value = await res.json()
  } catch (e) {
    console.error('Failed to fetch episodes:', e)
  }
}

async function fetchNews() {
  fetchingNews.value = true
  try {
    const res = await fetch('/api/debug/news?max_results=10')
    const data = await res.json()
    newsContent.value = {
      count: data.count || 0,
      items: data.items || [],
      summary: data.items?.[0]?.title || data.items?.[0]?.content || '已加载最新 AI 资讯'
    }
    scriptDraft.value = null
  } catch (e) {
    console.error('Failed to fetch news:', e)
  } finally {
    fetchingNews.value = false
  }
}

async function startGenerate() {
  if (!hasNews.value) return
  generating.value = true
  try {
    const res = await fetch('/api/generate', { method: 'POST' })
    const data = await res.json()
    taskId.value = data.task_id
  } catch (e) {
    console.error('Failed to start generation:', e)
    generating.value = false
  }
}

async function generateScriptPreview() {
  if (!hasNews.value) return
  generatingScript.value = true
  try {
    const res = await fetch('/api/script/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
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

function onCompleted() {
  generating.value = false
  synthesizing.value = false
  taskId.value = null
  newsContent.value = null
  scriptDraft.value = null
  fetchEpisodes()
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' })
}

function formatDuration(seconds) {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function getSpeakerClass(speaker) {
  if (speaker.includes('主持')) return 'host'
  if (speaker.includes('技术') || speaker.includes('明远')) return 'tech'
  if (speaker.includes('创业') || speaker.includes('婉清')) return 'pm'
  if (speaker.includes('伦理') || speaker.includes('志恒')) return 'ethics'
  return 'guest'
}

onMounted(fetchEpisodes)
</script>

<style scoped>
.home {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* Hero Section */
.hero {
  position: relative;
  background: white;
  border-radius: var(--radius-xl);
  padding: 2.5rem;
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.hero-content {
  position: relative;
  z-index: 1;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
  border: 1px solid rgba(99, 102, 241, 0.2);
  padding: 6px 14px;
  border-radius: var(--radius-full);
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-primary);
  margin-bottom: 1rem;
}

.badge-dot {
  width: 6px;
  height: 6px;
  background: var(--color-primary);
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.hero-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 0.5rem;
}

.brand-text {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-desc {
  color: var(--color-text-secondary);
  font-size: 1rem;
}

.hero-decoration {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 40%;
  pointer-events: none;
}

.decoration-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.5;
}

.circle-1 {
  width: 200px;
  height: 200px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.1) 100%);
  top: -50px;
  right: 20px;
}

.circle-2 {
  width: 120px;
  height: 120px;
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(245, 158, 11, 0.1) 100%);
  bottom: 20px;
  right: 150px;
}

.circle-3 {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(16, 185, 129, 0.1) 100%);
  bottom: 40px;
  right: 40px;
}

/* Actions Grid */
.actions-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.25rem;
}

.action-card {
  background: white;
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: column;
  gap: 1rem;
  transition: all var(--transition-normal);
}

.action-card:hover {
  box-shadow: var(--shadow-md);
}

.action-card.disabled {
  opacity: 0.5;
  pointer-events: none;
}

.action-card.busy {
  opacity: 0.7;
}

.card-header {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.card-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.fetch-icon {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(99, 102, 241, 0.08) 100%);
  color: var(--color-primary);
}

.generate-icon {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(245, 158, 11, 0.08) 100%);
  color: var(--color-accent-warm);
}

.card-title h3 {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 0.25rem;
}

.card-title p {
  font-size: 0.85rem;
  color: var(--color-text-muted);
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
  gap: 6px;
  padding: 10px;
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.mode-btn:hover {
  color: var(--color-text);
}

.mode-btn.active {
  background: white;
  color: var(--color-primary);
  box-shadow: var(--shadow-sm);
}

/* Buttons */
.btn-primary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 20px;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-generate {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 20px;
  background: linear-gradient(135deg, var(--color-accent-warm) 0%, #d97706 100%);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-generate:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.btn-generate:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  background: var(--color-border-light);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--color-border);
}

.btn-confirm {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  background: linear-gradient(135deg, var(--color-success) 0%, #059669 100%);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-confirm:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.btn-confirm:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.news-preview {
  padding: 12px;
  background: rgba(16, 185, 129, 0.08);
  border: 1px solid rgba(16, 185, 129, 0.2);
  border-radius: var(--radius-md);
}

.news-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-success);
  margin-bottom: 8px;
}

.news-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.news-item {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
  line-height: 1.4;
  padding-left: 12px;
  position: relative;
}

.news-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 6px;
  width: 4px;
  height: 4px;
  background: var(--color-primary);
  border-radius: 50%;
}

/* Section Header */
.section-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.section-icon {
  width: 44px;
  height: 44px;
  background: white;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary);
  box-shadow: var(--shadow-sm);
}

.section-header h2 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text);
}

.section-header p {
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

/* Script Section */
.script-section {
  background: white;
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  box-shadow: var(--shadow-card);
}

.script-card {
  background: var(--color-border-light);
  border-radius: var(--radius-md);
  padding: 1.25rem;
}

.script-header {
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--color-border);
}

.script-header h3 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 0.25rem;
}

.script-header p {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
}

.dialogue-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.dialogue-item {
  background: white;
  border-radius: var(--radius-md);
  padding: 0.875rem;
}

.speaker-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 0.5rem;
}

.speaker-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
  color: white;
}

.speaker-avatar.host { background: linear-gradient(135deg, var(--color-primary), var(--color-accent)); }
.speaker-avatar.tech { background: linear-gradient(135deg, #3b82f6, #1d4ed8); }
.speaker-avatar.pm { background: linear-gradient(135deg, var(--color-accent-warm), #b45309); }
.speaker-avatar.ethics { background: linear-gradient(135deg, var(--color-success), #047857); }
.speaker-avatar.guest { background: linear-gradient(135deg, #64748b, #475569); }

.speaker-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text);
}

.dialogue-item textarea {
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 0.625rem;
  font-size: 0.85rem;
  font-family: inherit;
  resize: none;
  transition: border-color var(--transition-fast);
}

.dialogue-item textarea:focus {
  outline: none;
  border-color: var(--color-primary);
}

/* Episodes Section */
.episodes-section {
  margin-top: 0.5rem;
}

.empty-state {
  background: white;
  border-radius: var(--radius-lg);
  padding: 3rem;
  text-align: center;
  box-shadow: var(--shadow-card);
}

.empty-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 1rem;
  background: var(--color-border-light);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
}

.empty-state p {
  color: var(--color-text-muted);
  font-size: 0.95rem;
}

.episodes-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.25rem;
}

.episode-card {
  background: white;
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-card);
  cursor: pointer;
  transition: all var(--transition-normal);
}

.episode-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
}

.episode-cover {
  position: relative;
  height: 100px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover-play {
  width: 44px;
  height: 44px;
  background: rgba(255,255,255,0.25);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  transition: all var(--transition-fast);
}

.episode-card:hover .cover-play {
  background: white;
  color: var(--color-primary);
  transform: scale(1.1);
}

.duration {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0,0,0,0.5);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: 0.7rem;
  color: white;
}

.episode-body {
  padding: 1rem;
}

.episode-date {
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.episode-body h3 {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0.375rem 0;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.episode-body p {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.episode-guests {
  display: flex;
  gap: 0.375rem;
  flex-wrap: wrap;
  margin-top: 0.75rem;
}

.guest {
  padding: 3px 8px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
  border-radius: var(--radius-full);
  font-size: 0.7rem;
  color: var(--color-primary);
  font-weight: 500;
}

/* Transitions */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* Responsive */
@media (max-width: 900px) {
  .actions-grid {
    grid-template-columns: 1fr;
  }
  
  .episodes-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .hero {
    padding: 1.75rem;
  }
  
  .hero-title {
    font-size: 1.4rem;
  }
  
  .episodes-grid {
    grid-template-columns: 1fr;
  }
}
</style>
