<template>
  <div class="episode-page" v-if="episode">
    <router-link to="/" class="back">&larr; 返回列表</router-link>

    <header class="ep-header">
      <h2>{{ episode.title }}</h2>
      <p class="ep-summary">{{ episode.summary }}</p>
      <div class="ep-meta">
        <span>{{ formatDate(episode.created_at) }}</span>
        <span v-if="episode.duration_seconds">时长: {{ formatDuration(episode.duration_seconds) }}</span>
        <span>{{ episode.word_count }} 字</span>
      </div>
      <div class="ep-guests">
        <span v-for="g in episode.guests" :key="g" class="guest-tag">{{ g }}</span>
      </div>
    </header>

    <!-- Audio Player -->
    <PodcastPlayer v-if="episode.has_audio" :episode-id="episode.id" />

    <!-- Dialogue transcript -->
    <section class="transcript">
      <h3>对话文稿</h3>
      <div
        v-for="(line, idx) in episode.dialogue"
        :key="idx"
        class="dialogue-line"
        :class="getSpeakerClass(line.speaker)"
      >
        <div class="speaker-name">{{ line.speaker }}</div>
        <div class="line-text">{{ line.text }}</div>
      </div>
    </section>

    <!-- Sources -->
    <section v-if="episode.news_sources?.length" class="sources">
      <h3>参考来源</h3>
      <ul>
        <li v-for="(src, idx) in episode.news_sources" :key="idx">
          <a :href="src.url" target="_blank">{{ src.title }}</a>
        </li>
      </ul>
    </section>
  </div>
  <div v-else class="loading">加载中…</div>
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
.back {
  display: inline-block;
  margin-bottom: 1rem;
  color: #667eea;
}

.ep-header {
  margin-bottom: 1.5rem;
}

.ep-header h2 {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.ep-summary {
  color: #515154;
  margin-bottom: 0.5rem;
}

.ep-meta {
  display: flex;
  gap: 1.5rem;
  color: #86868b;
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
}

.ep-guests {
  display: flex;
  gap: 0.5rem;
}

.guest-tag {
  background: #f0f0f5;
  padding: 0.15rem 0.6rem;
  border-radius: 20px;
  font-size: 0.8rem;
  color: #667eea;
}

.transcript {
  margin-top: 2rem;
}

.transcript h3 {
  margin-bottom: 1rem;
}

.dialogue-line {
  padding: 0.8rem 1rem;
  margin-bottom: 0.5rem;
  border-radius: 10px;
  background: white;
  box-shadow: 0 1px 2px rgba(0,0,0,0.06);
}

.dialogue-line.host {
  border-left: 4px solid #667eea;
}

.dialogue-line.guest-a {
  border-left: 4px solid #f093fb;
}

.dialogue-line.guest-b {
  border-left: 4px solid #4facfe;
}

.dialogue-line.guest-c {
  border-left: 4px solid #43e97b;
}

.speaker-name {
  font-weight: 600;
  font-size: 0.85rem;
  margin-bottom: 0.2rem;
  color: #667eea;
}

.line-text {
  font-size: 0.95rem;
  line-height: 1.7;
}

.sources {
  margin-top: 2rem;
}

.sources h3 {
  margin-bottom: 0.5rem;
}

.sources ul {
  list-style: none;
  padding: 0;
}

.sources li {
  padding: 0.3rem 0;
}

.sources a {
  color: #667eea;
}

.loading {
  text-align: center;
  padding: 3rem;
  color: #86868b;
}
</style>
