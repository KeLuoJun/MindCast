<template>
  <div class="home">
    <!-- Generate button -->
    <div class="generate-section">
      <button
        class="btn-generate"
        :disabled="generating"
        @click="startGenerate"
      >
        {{ generating ? '生成中…' : '🎙️ 生成新一期播客' }}
      </button>
    </div>

    <!-- Generation progress panel -->
    <GeneratePanel
      v-if="taskId"
      :task-id="taskId"
      @completed="onCompleted"
    />

    <!-- Episode list -->
    <section class="episode-list">
      <h2>往期播客</h2>
      <div v-if="episodes.length === 0" class="empty">暂无播客，点击上方按钮生成第一期！</div>
      <div
        v-for="ep in episodes"
        :key="ep.id"
        class="episode-card"
        @click="$router.push(`/episode/${ep.id}`)"
      >
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
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import GeneratePanel from '../components/GeneratePanel.vue'

const episodes = ref([])
const generating = ref(false)
const taskId = ref(null)

async function fetchEpisodes() {
  try {
    const res = await fetch('/api/episodes')
    episodes.value = await res.json()
  } catch (e) {
    console.error('Failed to fetch episodes:', e)
  }
}

async function startGenerate() {
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
  fetchEpisodes()
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

onMounted(fetchEpisodes)
</script>

<style scoped>
.generate-section {
  text-align: center;
  margin-bottom: 2rem;
}

.btn-generate {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 0.8rem 2rem;
  font-size: 1.1rem;
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
}

.btn-generate:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.btn-generate:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.episode-list h2 {
  margin-bottom: 1rem;
  font-size: 1.3rem;
}

.empty {
  text-align: center;
  color: #86868b;
  padding: 3rem 0;
}

.episode-card {
  background: white;
  border-radius: 12px;
  padding: 1.2rem 1.5rem;
  margin-bottom: 1rem;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}

.episode-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.12);
}

.ep-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.85rem;
  color: #86868b;
  margin-bottom: 0.3rem;
}

.episode-card h3 {
  font-size: 1.1rem;
  margin-bottom: 0.4rem;
}

.ep-summary {
  color: #515154;
  font-size: 0.93rem;
  margin-bottom: 0.5rem;
}

.ep-guests {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.guest-tag {
  background: #f0f0f5;
  padding: 0.15rem 0.6rem;
  border-radius: 20px;
  font-size: 0.8rem;
  color: #667eea;
}
</style>
