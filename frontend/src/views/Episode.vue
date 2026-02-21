<template>
  <div class="episode-page" v-if="episode">
    <!-- Back Button -->
    <router-link to="/" class="back-btn">
      <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M19 12H5M12 19l-7-7 7-7"/>
      </svg>
      返回列表
    </router-link>

    <!-- Episode Header Card (Unified) -->
    <header class="ep-header">
      <div class="header-gradient"></div>
      <div class="header-content-grid">
        <!-- Left Column: Content -->
        <div class="header-left">
          <div class="ep-badge">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 14.5c-2.49 0-4.5-2.01-4.5-4.5S9.51 7.5 12 7.5s4.5 2.01 4.5 4.5-2.01 4.5-4.5 4.5z"/>
            </svg>
            AI 深度探讨 · 圆桌派
          </div>
          <h1 class="ep-title">{{ episode.title }}</h1>
          <p class="ep-summary">{{ episode.summary }}</p>
        </div>

        <!-- Right Column: Meta Info Card -->
        <aside class="header-right">
          <section class="meta-card">
            <div class="meta-card-item">
              <span class="meta-label">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
                </svg>
              </span>
              {{ formatDate(episode.created_at) }}
            </div>
            <div v-if="episode.duration_seconds" class="meta-card-item">
              <span class="meta-label">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5">
                  <circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/>
                </svg>
              </span>
              {{ formatDuration(episode.duration_seconds) }}
            </div>
            <div v-if="episode.word_count" class="meta-card-item">
              <span class="meta-label">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5">
                  <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                </svg>
              </span>
              {{ episode.word_count }} 字
            </div>
            <div class="meta-card-guests">
              <span v-for="g in episode.guests" :key="g" class="mini-guest-tag">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                  <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                </svg>
                {{ g }}
              </span>
            </div>
          </section>
        </aside>

        <!-- Player Controls (Middle Row) -->
        <div class="header-player" v-if="episode.has_audio">
          <PodcastPlayer :episode-id="episode.id" minimal />
        </div>
      </div>
    </header>

    <!-- Deep-read article -->
    <section v-if="episode.article" class="article-section">
      <div class="section-header">
        <h2>深度阅读</h2>
        <p class="section-desc">编辑精选延伸阅读，适合细读与深思</p>
      </div>
      <div class="article-card">
        <div class="article-body" v-html="articleHtml"></div>
      </div>
    </section>

    <!-- Dialogue transcript -->
    <section class="transcript-section">
      <div class="section-header">
        <h2>对话文稿</h2>
        <p class="section-desc">AI 嘉宾的精彩讨论</p>
      </div>
      <div class="dialogue-container">
        <div
          v-for="(line, idx) in episode.dialogue"
          :key="idx"
          class="dialogue-line"
          :class="getSpeakerClass(line.speaker)"
        >
          <div class="speaker-avatar">
            <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
            </svg>
          </div>
          <div class="dialogue-content">
            <div class="speaker-name">{{ line.speaker }}</div>
            <div class="line-text">{{ line.text }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Sources -->
    <section v-if="episode.news_sources?.length" class="sources-section">
      <div class="section-header">
        <h2>参考来源</h2>
        <p class="section-desc">了解更多详情</p>
      </div>
      <div class="sources-list">
        <a
          v-for="(src, idx) in episode.news_sources"
          :key="idx"
          :href="src.url"
          target="_blank"
          class="source-link"
        >
          <div class="source-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"/>
              <path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/>
            </svg>
          </div>
          <div class="source-info">
            <span class="source-title">{{ src.title }}</span>
            <span class="source-url">{{ src.url }}</span>
          </div>
        </a>
      </div>
    </section>
  </div>
  <div v-else class="loading-state">
    <div class="loading-spinner"></div>
    <p>加载中…</p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import PodcastPlayer from '../components/PodcastPlayer.vue'

const props = defineProps({ id: String })
const episode = ref(null)

async function fetchEpisode() {
  try {
    const res = await fetch(`/api/episodes/${props.id}`)
    episode.value = await res.json()
  } catch (e) {
    console.error('Failed to fetch episode:', e)
  }
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('zh-CN', {
    year: 'numeric', month: 'long', day: 'numeric'
  })
}

function formatDuration(seconds) {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

const speakerColors = {}
let colorIdx = 0
const colors = ['host', 'guest-a', 'guest-b', 'guest-c']

function getSpeakerClass(speaker) {
  if (!(speaker in speakerColors)) {
    speakerColors[speaker] = colors[colorIdx % colors.length]
    colorIdx++
  }
  return speakerColors[speaker]
}

/** Convert the article plain-text (with basic Markdown) to safe HTML. */
const articleHtml = computed(() => {
  const text = episode.value?.article || ''
  if (!text) return ''

  const escape = (s) =>
    s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

  const inlineFormat = (s) =>
    escape(s)
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/`(.+?)`/g, '<code>$1</code>')

  const blocks = text.split(/\n{2,}/)
  return blocks
    .map((block) => {
      const trimmed = block.trim()
      if (!trimmed) return ''
      if (trimmed.startsWith('#### ')) return `<h4>${inlineFormat(trimmed.slice(5))}</h4>`
      if (trimmed.startsWith('### '))  return `<h3>${inlineFormat(trimmed.slice(4))}</h3>`
      if (trimmed.startsWith('## '))   return `<h2>${inlineFormat(trimmed.slice(3))}</h2>`
      if (trimmed.startsWith('# '))    return `<h1>${inlineFormat(trimmed.slice(2))}</h1>`
      // multi-line inside a block → join with <br>
      const lines = trimmed.split('\n').map(inlineFormat).join('<br>')
      return `<p>${lines}</p>`
    })
    .join('')
})

onMounted(fetchEpisode)
</script>

<style scoped>
.episode-page {
  padding-bottom: 3rem;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1rem;
  background: white;
  color: var(--c-text-2);
  border: 1px solid var(--c-border);
  border-radius: var(--r-lg);
  font-weight: 700;
  font-size: 0.85rem;
  margin-bottom: 2rem;
  box-shadow: 0 4px 10px rgba(0,0,0,0.03);
  transition: all var(--dur-normal) var(--ease-bounce);
}

.back-btn:hover {
  transform: translateX(-4px);
  color: var(--c-primary);
  border-color: var(--c-primary-soft);
}

.ep-header {
  position: relative;
  margin-bottom: 3.5rem;
  border-radius: var(--r-2xl);
  background: white;
  border: 1px solid var(--c-border);
  box-shadow: 0 10px 40px rgba(0,0,0,0.02);
}

.header-gradient {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: var(--r-2xl);
  background: radial-gradient(circle at top right, rgba(255, 107, 53, 0.1), transparent 600px),
              radial-gradient(circle at bottom left, rgba(64, 70, 227, 0.06), transparent 600px);
  pointer-events: none;
}

.header-content-grid {
  position: relative;
  z-index: 1;
  padding: 0; /* padding handled inside grid cells */
  display: grid;
  grid-template-columns: 1fr 300px;
  grid-template-areas: 
    "left right"
    "player player";
  align-items: stretch;
}

.header-left {
  grid-area: left;
  min-width: 0;
  padding: 3rem 2.5rem 2.5rem 3.5rem;
}

.header-right {
  grid-area: right;
  padding: 3rem 3.5rem 2.5rem 0;
}

.header-player {
  grid-area: player;
  background: white;
  padding: 2.5rem 4rem;
  border-top: 1px solid var(--c-border);
  border-radius: 0 0 var(--r-2xl) var(--r-2xl);
  display: flex;
  justify-content: center;
}

.header-player > * {
  width: 100%;
  max-width: 1000px;
}

.ep-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: white;
  color: var(--c-primary);
  font-size: 0.75rem;
  font-weight: 800;
  padding: 6px 14px;
  border-radius: var(--r-lg);
  margin-bottom: 2rem;
  width: fit-content;
  box-shadow: 0 4px 10px rgba(0,0,0,0.02);
  border: 1px solid var(--c-border);
}

.ep-title {
  font-size: 2.2rem;
  font-weight: 900;
  color: var(--c-text-1);
  line-height: 1.15;
  letter-spacing: -0.04em;
  margin: 0 0 1.5rem;
}

.ep-summary {
  color: var(--c-text-2);
  font-size: 1.1rem;
  line-height: 1.8;
  margin: 0;
  opacity: 0.9;
  font-weight: 500;
  max-width: 800px;
}

.meta-card {
  background: white;
  border: 1px solid var(--c-border);
  border-radius: var(--r-xl);
  padding: 1.75rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  box-shadow: 0 10px 30px rgba(0,0,0,0.03);
}

.meta-card-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 0.95rem;
  color: var(--c-text-1);
  font-weight: 700;
}

.meta-label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  width: 16px;
  opacity: 0.4;
}

.meta-card-guests {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  margin-top: 0.5rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--c-border-light);
}

.mini-guest-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--c-primary-soft);
  color: var(--c-primary);
  border-radius: var(--r-md);
  font-size: 0.82rem;
  font-weight: 800;
  transition: all var(--dur-normal) var(--ease);
}

.mini-guest-tag:nth-child(2n) {
  background: var(--c-accent-soft);
  color: var(--c-accent);
}

.mini-guest-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 10px rgba(0,0,0,0.05);
}

.mini-guest-tag svg {
  opacity: 0.8;
}

@media (max-width: 1000px) {
  .header-content-grid {
    grid-template-columns: 1fr;
    grid-template-areas: 
      "left"
      "right"
      "player";
  }
  .header-left { padding: 3rem 2.5rem 1rem; }
  .header-right { padding: 1rem 2.5rem 3rem; }
  .header-player { padding: 2rem; }
}

/* ── Article section ── */
.article-section {
  margin-top: 3rem;
}

.article-card {
  background: var(--c-surface);
  border-radius: var(--r-2xl);
  border: 2px solid var(--c-border);
  box-shadow: var(--shadow-card);
  padding: 2.5rem 3rem;
  border-top: 4px solid var(--c-primary);
}

.article-body {
  color: var(--c-text-1);
  font-size: 1.05rem;
  line-height: 2;
  font-family: 'Georgia', 'Noto Serif SC', serif;
}

.article-body :deep(h1) {
  font-size: 1.7rem;
  font-weight: 800;
  color: var(--c-text-1);
  margin: 0 0 1.25rem;
  line-height: 1.35;
  letter-spacing: -0.02em;
}

.article-body :deep(h2) {
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--c-text-1);
  margin: 2.5rem 0 1rem;
  padding-left: 0.8rem;
  border-left: 4px solid var(--c-primary);
}

.article-body :deep(h3) {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--c-text-2);
  margin: 2rem 0 0.75rem;
}

.article-body :deep(h4) {
  font-size: 1rem;
  font-weight: 700;
  color: var(--c-text-2);
  margin: 1.5rem 0 0.5rem;
}

.article-body :deep(p) {
  margin: 0 0 1.4em;
  text-align: justify;
  text-indent: 2em;
}

.article-body :deep(strong) {
  color: var(--c-text-1);
  font-weight: 700;
}

.article-body :deep(em) {
  font-style: italic;
  color: var(--c-text-2);
}

.article-body :deep(code) {
  background: var(--c-bg);
  padding: 0.15em 0.4em;
  border-radius: var(--r-sm);
  font-size: 0.9em;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  color: var(--c-primary);
}

.transcript-section,
.sources-section {
  margin-top: 3rem;
}

.section-header {
  text-align: center;
  margin-bottom: 2.5rem;
  padding: 0 1rem;
}

.section-header h2 {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 2rem;
  font-weight: 900;
  margin-bottom: 0.75rem;
  color: var(--c-text-1);
  letter-spacing: -0.04em;
}

.section-header h2::before,
.section-header h2::after {
  content: '';
  width: 40px;
  height: 2px;
  background: var(--c-primary-soft);
  border-radius: 2px;
}

.section-desc {
  color: var(--c-text-2);
  font-size: 1rem;
  font-weight: 500;
  opacity: 0.7;
}

.article-card {
  background: white;
  border-radius: var(--r-2xl);
  border: 1px solid var(--c-border);
  box-shadow: 0 10px 40px rgba(0,0,0,0.02);
  padding: 4rem 5rem;
  max-width: 1000px;
  margin: 0 auto;
  position: relative;
  overflow: hidden;
}

.article-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 6px;
  background: linear-gradient(90deg, var(--c-primary), var(--c-yellow), var(--c-blue));
}

.dialogue-container {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.dialogue-line {
  display: flex;
  gap: 1.5rem;
  padding: 1.75rem 2rem;
  border-radius: var(--r-xl);
  background: white;
  border: 1px solid var(--c-border);
  border-left: 5px solid transparent;
  transition: all var(--dur-normal) var(--ease);
}

.dialogue-line:hover {
  box-shadow: 0 10px 25px rgba(0,0,0,0.03);
  transform: scale(1.01);
}

.dialogue-line.host {
  border-left-color: var(--c-primary);
}

.dialogue-line.guest-a {
  border-left-color: var(--c-yellow);
}

.dialogue-line.guest-b {
  border-left-color: var(--c-success);
}

.dialogue-line.guest-c {
  border-left-color: var(--c-blue);
}

.speaker-avatar {
  width: 48px;
  height: 48px;
  border-radius: var(--r-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: #FAFBFC;
  color: var(--c-text-3);
  box-shadow: inset 0 2px 5px rgba(0,0,0,0.02);
}

.dialogue-line.host .speaker-avatar {
  background: var(--c-primary-soft);
  color: var(--c-primary);
}

.dialogue-line.guest-a .speaker-avatar {
  background: var(--c-yellow-soft);
  color: #C4920D;
}

.dialogue-line.guest-b .speaker-avatar {
  background: rgba(46, 204, 113, 0.12);
  color: var(--c-success);
}

.dialogue-line.guest-c .speaker-avatar {
  background: var(--c-blue-soft);
  color: var(--c-blue);
}

.dialogue-content {
  flex: 1;
}

.speaker-name {
  font-weight: 700;
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
  color: var(--c-primary);
}

.dialogue-line.guest-a .speaker-name { color: #C4920D; }
.dialogue-line.guest-b .speaker-name { color: var(--c-success); }
.dialogue-line.guest-c .speaker-name { color: var(--c-blue); }

.line-text {
  font-size: 1rem;
  line-height: 1.8;
  color: var(--c-text-2);
}

.sources-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.source-link {
  display: flex;
  gap: 1rem;
  padding: 1.25rem;
  background: var(--c-surface);
  border: 2px solid var(--c-border);
  border-radius: var(--r-xl);
  transition: all var(--dur-normal) var(--ease);
}

.source-link:hover {
  transform: translateY(-2px);
  border-color: var(--c-primary);
  box-shadow: 0 4px 16px rgba(255, 107, 53, 0.12);
}

.source-icon {
  width: 44px;
  height: 44px;
  background: var(--c-primary-soft);
  border-radius: var(--r-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-primary);
  flex-shrink: 0;
}

.source-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  overflow: hidden;
}

.source-title {
  font-weight: 700;
  font-size: 0.95rem;
  color: var(--c-text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.source-url {
  font-size: 0.78rem;
  color: var(--c-text-3);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.loading-state {
  text-align: center;
  padding: 5rem 2rem;
  color: var(--c-text-3);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--c-border);
  border-top-color: var(--c-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 700px) {
  .header-content {
    padding: 1.5rem 1.5rem 2rem;
  }

  .ep-title {
    font-size: 1.5rem;
  }

  .ep-summary {
    font-size: 0.95rem;
  }

  .ep-meta {
    gap: 0.7rem 1.2rem;
  }
}
</style>
