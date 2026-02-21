<template>
  <div class="home">
    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-content">
        <div class="hero-badge">
          <span class="badge-dot"></span>
          智能播客
        </div>
        <h1 class="hero-title">
          欢迎来到 <span class="brand-text">圆桌派</span>
        </h1>
        <p class="hero-desc">
          多智能体协作生成 · 输入任何话题，为您生成深度、多元的播客节目
        </p>
      </div>
      <div class="hero-decoration">
        <div class="decoration-circle circle-1"></div>
        <div class="decoration-circle circle-2"></div>
        <div class="decoration-circle circle-3"></div>
      </div>
    </section>

    <!-- Main Content: Workflow + Guest Config -->
    <section class="main-content">
      <!-- Left: Workflow Wizard -->
      <div class="workflow-section">
        <WorkflowWizard
          ref="workflowRef"
          :guests="guests"
          :selected-guests="selectedGuests"
          @update:selected-guests="selectedGuests = $event"
          @open-guest-drawer="guestDrawerOpen = true"
          @completed="onWorkflowCompleted"
        />
      </div>

      <!-- Right: Guest Config Entry -->
      <div class="guest-config-section">
        <div class="config-card" @click="guestDrawerOpen = true">
          <div class="config-icon">
            <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 00-3-3.87"/>
              <path d="M16 3.13a4 4 0 010 7.75"/>
            </svg>
          </div>
          <h3>嘉宾配置</h3>
          <p>管理播客嘉宾库</p>
          <div class="guest-preview" v-if="guests.length > 0">
            <div class="preview-avatars">
              <div
                v-for="(guest, idx) in guests.slice(0, 3)"
                :key="guest.name"
                class="preview-avatar"
                :style="{ background: getAvatarGradient(guest.mbti), zIndex: 3 - idx }"
              >
                {{ guest.name.charAt(0) }}
              </div>
              <div v-if="guests.length > 3" class="preview-more">
                +{{ guests.length - 3 }}
              </div>
            </div>
            <span class="guest-count">{{ guests.length }} 位嘉宾</span>
          </div>
          <div v-else class="empty-hint">
            暂无嘉宾，点击创建
          </div>
        </div>

        <!-- Quick Stats -->
        <div class="stats-card">
          <div class="stat-item">
            <span class="stat-value">{{ episodes.length }}</span>
            <span class="stat-label">往期节目</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-value">{{ guests.length }}</span>
            <span class="stat-label">嘉宾总数</span>
          </div>
        </div>
      </div>
    </section>

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
      
      <div v-else class="episodes-list">
        <div
          v-for="(ep, idx) in episodes"
          :key="ep.id"
          class="episode-item"
          @click="$router.push(`/episode/${ep.id}`)"
        >
          <div class="episode-icon">
            <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 2a3 3 0 00-3 3v7a3 3 0 006 0V5a3 3 0 00-3-3z"/>
              <path d="M19 10v2a7 7 0 01-14 0v-2"/>
              <line x1="12" y1="19" x2="12" y2="22"/>
            </svg>
          </div>
          <div class="episode-info">
            <div class="episode-header">
              <span class="episode-badge">第{{ idx + 1 }}期</span>
              <h3>{{ ep.title }}</h3>
              <span class="episode-date">{{ formatDate(ep.created_at) }}</span>
            </div>
            <p class="episode-summary">{{ ep.summary }}</p>
            <div class="episode-meta">
              <div class="episode-guests">
                <span v-for="g in ep.guests" :key="g" class="guest">
                  <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
                    <circle cx="12" cy="7" r="4"/>
                  </svg>
                  {{ g }}
                </span>
              </div>
              <div class="episode-stats">
                <span v-if="ep.word_count" class="stat">
                  <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                    <polyline points="14,2 14,8 20,8"/>
                  </svg>
                  {{ ep.word_count }}字
                </span>
                <span v-if="ep.duration_seconds" class="stat">
                  <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <polyline points="12,6 12,12 16,14"/>
                  </svg>
                  {{ formatDuration(ep.duration_seconds) }}
                </span>
              </div>
            </div>
          </div>
          <div class="episode-action">
            <div class="play-button">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M8 5v14l11-7z"/>
              </svg>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Guest Drawer -->
    <GuestDrawer
      v-model="guestDrawerOpen"
      :guests="guests"
      :selected-guests="selectedGuests"
      @update:selected-guests="selectedGuests = $event"
      @save="saveGuest"
      @remove="removeGuest"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import WorkflowWizard from '../components/WorkflowWizard.vue'
import GuestDrawer from '../components/GuestDrawer.vue'

const workflowRef = ref(null)
const episodes = ref([])
const guests = ref([])
const selectedGuests = ref([])
const guestDrawerOpen = ref(false)
const maxGuests = 3

async function fetchEpisodes() {
  try {
    const res = await fetch('/api/episodes')
    episodes.value = await res.json()
  } catch (e) {
    console.error('Failed to fetch episodes:', e)
  }
}

async function loadGuests() {
  try {
    const res = await fetch('/api/guests')
    const data = await res.json()
    guests.value = Array.isArray(data) ? data : []
    if (!selectedGuests.value.length && guests.value.length) {
      selectedGuests.value = [guests.value[0].name]
    }
  } catch (e) {
    console.error('Failed to load guests:', e)
  }
}

async function saveGuest({ isEdit, ...payload }) {
  try {
    const method = isEdit ? 'PUT' : 'POST'
    const url = isEdit
      ? `/api/guests/${encodeURIComponent(payload.name)}`
      : '/api/guests'
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    if (!res.ok) {
      const data = await res.json()
      throw new Error(data?.detail || '操作失败')
    }
    const data = await res.json()
    guests.value = data
    if (!selectedGuests.value.includes(payload.name) && selectedGuests.value.length < maxGuests) {
      selectedGuests.value = [...selectedGuests.value, payload.name]
    }
  } catch (e) {
    console.error('Failed to save guest:', e)
    alert(e.message || '保存嘉宾失败')
  }
}

async function removeGuest(name) {
  try {
    const res = await fetch(`/api/guests/${encodeURIComponent(name)}`, { method: 'DELETE' })
    const data = await res.json()
    if (!res.ok) {
      throw new Error(data?.detail || '删除失败')
    }
    guests.value = data
    selectedGuests.value = selectedGuests.value.filter(item => item !== name)
  } catch (e) {
    console.error('Failed to delete guest:', e)
    alert(e.message || '删除嘉宾失败')
  }
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

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' })
}

function formatDuration(seconds) {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function onWorkflowCompleted() {
  fetchEpisodes()
}

onMounted(async () => {
  await Promise.all([fetchEpisodes(), loadGuests()])
})
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
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-xl);
  padding: 2.5rem;
  box-shadow: var(--glass-shadow);
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

/* Main Content */
.main-content {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 1.25rem;
}

.workflow-section {
  min-width: 0;
}

.guest-config-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Guest Config Card */
.config-card {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-xl);
  padding: 1.5rem;
  cursor: pointer;
  transition: all var(--transition-normal);
}

.config-card:hover {
  border-color: var(--color-primary-light);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.config-icon {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary);
  margin-bottom: 1rem;
}

.config-card h3 {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 0.25rem;
}

.config-card > p {
  font-size: 0.85rem;
  color: var(--color-text-muted);
  margin-bottom: 1rem;
}

.guest-preview {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border-light);
}

.preview-avatars {
  display: flex;
}

.preview-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 0.75rem;
  font-weight: 600;
  border: 2px solid white;
  margin-left: -8px;
}

.preview-avatar:first-child {
  margin-left: 0;
}

.preview-more {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-border-light);
  color: var(--color-text-secondary);
  font-size: 0.7rem;
  font-weight: 600;
  border: 2px solid white;
  margin-left: -8px;
}

.guest-count {
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.empty-hint {
  padding-top: 1rem;
  border-top: 1px solid var(--color-border-light);
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

/* Stats Card */
.stats-card {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-xl);
  padding: 1.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-primary);
}

.stat-label {
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: var(--color-border-light);
}

/* Episodes Section */
.episodes-section {
  margin-top: 0.5rem;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.section-icon {
  width: 44px;
  height: 44px;
  background: var(--glass-bg-strong);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary);
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

.empty-state {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-xl);
  padding: 3rem;
  text-align: center;
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

.episodes-list {
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
}

.episode-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  padding: 1rem 1.25rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.episode-item:hover {
  border-color: var(--color-primary-light);
  box-shadow: var(--shadow-md);
}

.episode-item:hover .episode-icon {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  color: white;
}

.episode-item:hover .play-button {
  background: var(--color-primary);
  color: white;
}

.episode-icon {
  width: 48px;
  height: 48px;
  background: var(--color-border-light);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-secondary);
  flex-shrink: 0;
  transition: all var(--transition-fast);
}

.episode-info {
  flex: 1;
  min-width: 0;
}

.episode-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.25rem;
}

.episode-badge {
  flex-shrink: 0;
  padding: 2px 8px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: var(--radius-sm);
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--color-primary);
}

.episode-info h3 {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--color-text);
  line-height: 1.4;
  flex: 1;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.episode-date {
  font-size: 0.7rem;
  color: var(--color-text-muted);
  white-space: nowrap;
}

.episode-summary {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 0.375rem;
}

.episode-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.episode-guests {
  display: flex;
  gap: 0.375rem;
}

.guest {
  display: flex;
  align-items: center;
  gap: 3px;
  padding: 2px 8px;
  background: var(--color-border-light);
  border-radius: var(--radius-sm);
  font-size: 0.65rem;
  color: var(--color-text-secondary);
}

.episode-stats {
  display: flex;
  gap: 0.75rem;
}

.stat {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 0.65rem;
  color: var(--color-text-muted);
}

.episode-action {
  flex-shrink: 0;
}

.play-button {
  width: 40px;
  height: 40px;
  background: var(--color-border-light);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-secondary);
  transition: all var(--transition-fast);
}

/* Responsive */
@media (max-width: 900px) {
  .main-content {
    grid-template-columns: 1fr;
  }
  
  .guest-config-section {
    flex-direction: row;
  }
  
  .config-card {
    flex: 1;
  }
  
  .stats-card {
    flex: 0 0 auto;
  }
}

@media (max-width: 600px) {
  .hero {
    padding: 1.75rem;
  }
  
  .hero-title {
    font-size: 1.4rem;
  }
  
  .guest-config-section {
    flex-direction: column;
  }
  
  .episode-item {
    flex-wrap: wrap;
    gap: 0.75rem;
    padding: 0.875rem 1rem;
  }
  
  .episode-icon {
    width: 40px;
    height: 40px;
  }
  
  .episode-info {
    order: 3;
    width: 100%;
  }
  
  .episode-header {
    flex-wrap: wrap;
  }
  
  .episode-badge {
    display: none;
  }
  
  .episode-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.375rem;
  }
  
  .episode-stats {
    display: none;
  }
  
  .play-button {
    width: 36px;
    height: 36px;
  }
}
</style>
