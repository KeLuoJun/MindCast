<template>
  <div class="episode-page" v-if="episode">
    <!-- Back Button -->
    <router-link to="/" class="back-btn">
      <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M19 12H5M12 19l-7-7 7-7"/>
      </svg>
      返回列表
    </router-link>

    <!-- Episode Header -->
    <header class="ep-header">
      <div class="header-gradient"></div>
      <div class="header-content">
        <div class="ep-info">
          <h1>{{ episode.title }}</h1>
          <p class="ep-summary">{{ episode.summary }}</p>
        </div>
        <div class="ep-meta-wrapper">
          <div class="ep-meta">
            <span class="meta-item">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                <line x1="16" y1="2" x2="16" y2="6"/>
                <line x1="8" y1="2" x2="8" y2="6"/>
                <line x1="3" y1="10" x2="21" y2="10"/>
              </svg>
              {{ formatDate(episode.created_at) }}
            </span>
            <span v-if="episode.duration_seconds" class="meta-item">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <polygon points="10 8 16 12 10 16 10 8"/>
              </svg>
              {{ formatDuration(episode.duration_seconds) }}
            </span>
            <span class="meta-item">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
              </svg>
              {{ episode.word_count }} 字
            </span>
          </div>
          <div class="ep-guests">
            <span v-for="g in episode.guests" :key="g" class="guest-tag">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
              </svg>
              {{ g }}
            </span>
          </div>
        </div>
      </div>
    </header>

    <!-- Audio Player -->
    <div class="player-wrapper">
      <PodcastPlayer v-if="episode.has_audio" :episode-id="episode.id" />
    </div>

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
import { ref, onMounted } from 'vue'
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
  padding: 0.75rem 1.25rem;
  background: white;
  color: #6366f1;
  border-radius: 12px;
  font-weight: 600;
  font-size: 0.9rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: all 0.2s;
}

.back-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
}

.ep-header {
  position: relative;
  margin-bottom: 2rem;
  border-radius: 24px;
  overflow: hidden;
  background: white;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.header-gradient {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 200px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
  opacity: 0.1;
}

.header-content {
  position: relative;
  padding: 2.5rem;
}

.ep-info h1 {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 1rem;
  color: #1f2937;
  line-height: 1.3;
}

.ep-summary {
  color: #6b7280;
  font-size: 1.1rem;
  line-height: 1.8;
  margin-bottom: 1.5rem;
}

.ep-meta-wrapper {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.ep-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.9rem;
  color: #6b7280;
}

.ep-guests {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.guest-tag {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 1rem;
  background: linear-gradient(135deg, #e0e7ff 0%, #fae8ff 100%);
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
  color: #6366f1;
}

.player-wrapper {
  margin-bottom: 2.5rem;
}

.transcript-section,
.sources-section {
  margin-top: 3rem;
}

.section-header {
  text-align: center;
  margin-bottom: 2rem;
}

.section-header h2 {
  font-size: 1.6rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  color: #1f2937;
}

.section-desc {
  color: #9ca3af;
  font-size: 0.95rem;
}

.dialogue-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.dialogue-line {
  display: flex;
  gap: 1rem;
  padding: 1.5rem;
  border-radius: 16px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
}

.dialogue-line:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.dialogue-line.host {
  border-left: 4px solid #6366f1;
}

.dialogue-line.guest-a {
  border-left: 4px solid #f59e0b;
}

.dialogue-line.guest-b {
  border-left: 4px solid #10b981;
}

.dialogue-line.guest-c {
  border-left: 4px solid #ef4444;
}

.speaker-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #9ca3af;
}

.dialogue-line.host .speaker-avatar {
  background: linear-gradient(135deg, #e0e7ff 0%, #fae8ff 100%);
  color: #6366f1;
}

.dialogue-line.guest-a .speaker-avatar {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  color: #d97706;
}

.dialogue-line.guest-b .speaker-avatar {
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
  color: #059669;
}

.dialogue-line.guest-c .speaker-avatar {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  color: #dc2626;
}

.dialogue-content {
  flex: 1;
}

.speaker-name {
  font-weight: 600;
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
  color: #6366f1;
}

.line-text {
  font-size: 1rem;
  line-height: 1.8;
  color: #374151;
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
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.2s;
}

.source-link:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.15);
  border-color: #6366f1;
}

.source-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #e0e7ff 0%, #fae8ff 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
;
  color: #6366f1;
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
  font-weight: 600;
  font-size: 0.95rem;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.source-url {
  font-size: 0.8rem;
  color: #9ca3af;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.loading-state {
  text-align: center;
  padding: 5rem 2rem;
  color: #6b7280;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e5e7eb;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
