<template>
  <div class="home">
    <!-- Welcome Section -->
    <section class="welcome-section">
      <div class="welcome-content">
        <h2>欢迎来到 AI圆桌派</h2>
        <p class="welcome-desc">
          由多智能体协作生成的 AI 资讯播客，每日为您提供深度、多元的科技解读。
          下方选择内容源，开启今天的播客之旅。
        </p>
      </div>
    </section>

    <!-- Actions Section -->
    <section class="actions-section">
      <div class="action-card">
        <div class="action-icon">
          <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
          </svg>
        </div>
        <h3>获取今日资讯</h3>
        <p>从 AI 领域获取最新新闻和话题</p>
        <button
          class="btn-action btn-primary"
          :disabled="fetchingNews || generating"
          @click="fetchNews"
        >
          <span v-if="fetchingNews" class="spinner"></span>
          {{ fetchingNews ? '获取中...' : '获取内容' }}
        </button>
        <div v-if="newsContent" class="news-preview">
          <h4>已获取内容</h4>
          <p>{{ newsContent.summary }}</p>
          <p class="news-count">{{ newsContent.count }} 篇资讯</p>
        </div>
      </div>

      <div class="action-card" :class="{ 'disabled': !hasNews }">
        <div class="action-icon action-icon-generate">
          <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"/>
          </svg>
        </div>
        <h3>生成播客</h3>
        <p>基于获取的内容，AI 嘉宾进行深度讨论</p>
        <button
          class="btn-action btn-secondary"
          :disabled="!hasNews || generating"
          @click="startGenerate"
        >
          {{ generating ? '生成中…' : '开始生成' }}
        </button>
      </div>
    </section>

    <!-- Generation progress panel -->
    <GeneratePanel
      v-if="taskId"
      :task-id="taskId"
      @completed="onCompleted"
    />

    <!-- Episode list -->
    <section class="episode-section">
      <div class="section-header">
        <h2>往期播客</h2>
        <p class="section-subtitle">回顾精彩内容</p>
      </div>
      <div v-if="episodes.length === 0" class="empty-state">
        <svg viewBox="0 0 24 24" width="64" height="64" fill="none" stroke="currentColor" stroke-width="1">
          <circle cx="12" cy="12" r="10"/>
          <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3"/>
          <path d="M12 17h.01"/>
        </svg>
        <p>暂无播客，获取内容后即可开始生成第一期！</p>
      </div>
      <div class="episode-grid">
        <div
          v-for="ep in episodes"
          :key="ep.id"
          class="episode-card"
          @click="$router.push(`/episode/${ep.id}`)"
        >
          <div class="episode-cover">
            <div class="play-icon">
              <svg viewBox="0 0 24 24" width="32" height="32" fill="currentColor">
                <path d="M8 5v14l11-7z"/>
              </svg>
            </div>
          </div>
          <div class="episode-content">
            <div class="ep-meta">
              <span class="ep-date">{{ formatDate(ep.created_at) }}</span>
              <span v-if="ep.duration_seconds" class="ep-duration">
                {{ formatDuration(ep.duration_seconds) }}
              </span>
            </div>
            <h3>{{ ep.title }}</h3>
            <p class="ep-summary">{{ ep.summary }}</p>
            <div class="ep-guests">
              <span v-for="g in ep.guests" :key="g" class="guest-tag">{{ g }}</span>
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
const taskId = ref(null)
const newsContent = ref(null)

const hasNews = computed(() => newsContent.value !== null)

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
    const res = await fetch('/api/debug/news?max_results=5')
    const data = await res.json()
    newsContent.value = {
      count: data.news?.length || data.length || 0,
      summary: data.news?.[0]?.title || '获取成功，已加载最新 AI 资讯'
    }
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

function onCompleted() {
  generating.value = false
  taskId.value = null
  newsContent.value = null
  fetchEpisodes()
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('zh-CN', {
    year: 'numeric', 'month': 'long', 'day': 'numeric'
  })
}

function formatDuration(seconds) {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

onMounted(fetchEpisodes)
</script>

<style scoped>
.home {
  padding-bottom: 3rem;
}

.welcome-section {
  text-align: center;
  margin-bottom: 3rem;
  padding: 2rem 0;
}

.welcome-content h2 {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 1rem;
  background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.welcome-desc {
  color: #6b7280;
  font-size: 1.1rem;
  max-width: 700px;
  margin: 0 auto;
  line-height: 1.8;
}

.actions-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.5rem;
  margin-bottom: 3rem;
}

.action-card {
  background: white;
  border-radius: 20px;
  padding: 2rem;
  text-align: center;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.action-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #6366f1, #8b5cf6, #a855f7);
}

.action-card.disabled {
  opacity: 0.6;
}

.action-card:not(.disabled):hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(99, 102, 241, 0.2);
}

.action-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 1.5rem;
  background: linear-gradient(135deg, #e0e7ff 0%, #fae8ff 100%);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6366f1;
}

.action-icon-generate {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  color: #92400e;
}

.action-card h3 {
  font-size: 1.4rem;
  margin-bottom: 0.75rem;
  color: #1f2937;
}

.action-card p {
  color: #6b7280;
  font-size: 0.95rem;
  margin-bottom: 1.5rem;
  line-height: 1.6;
}

.btn-action {
  padding: 0.875rem 2rem;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-primary {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
}

.btn-secondary {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 15px rgba(245, 158, 11, 0.4);
}

.btn-action:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

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

.news-preview {
  margin-top: 1.5rem;
  padding: 1rem;
  background: #f0fdf4;
  border-radius: 12px;
  border: 1px solid #bbf7d0;
}

.news-preview h4 {
  font-size: 0.9rem;
  color: #16a34a;
  margin-bottom: 0.5rem;
}

.news-preview p {
  font-size: 0.85rem;
  color: #166534;
  margin-bottom: 0.25rem;
}

.news-count {
  font-weight: 600;
}

.episode-section {
  margin-top: 4rem;
}

.section-header {
  text-align: center;
  margin-bottom: 2rem;
}

.section-header h2 {
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  color: #1f2937;
}

.section-subtitle {
  color: #6b7280;
  font-size: 0.95rem;
;
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  color: #9ca3af;
}

.empty-state svg {
  color: #d1d5db;
  margin-bottom: 1.5rem;
}

.empty-state p {
  font-size: 1.1rem;
}

.episode-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.episode-card {
  background: white;
  border-radius: 16px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
}

.episode-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
}

.episode-cover {
  height: 140px;
  background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.play-icon {
  width: 60px;
  height: 60px;
  background: rgba(255, 255, 255, 0.25);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
  transition: all 0.3s;
}

.episode-card:hover .play-icon {
  background: rgba(255, 255, 255, 0.35);
  transform: scale(1.1);
}

.play-icon svg {
  color: white;
  margin-left: 4px;
}

.episode-content {
  padding: 1.5rem;
}

.ep-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.8rem;
  color: #9ca3af;
  margin-bottom: 0.75rem;
}

.episode-card h3 {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 0.6rem;
  color: #1f2937;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.ep-summary {
  color: #6b7280;
  font-size: 0.9rem;
  margin-bottom: 1rem;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.ep-guests {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.guest-tag {
  background: linear-gradient(135deg, #e0e7ff 0%, #fae8ff 100%);
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  color: #6366f1;
  font-weight: 500;
}
</style>
