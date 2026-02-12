<template>
  <div class="player" v-if="episodeId">
    <audio ref="audioEl" :src="`/api/episodes/${episodeId}/audio`" preload="metadata" />
    <div class="player-controls">
      <button class="btn-play" @click="togglePlay">
        {{ playing ? '⏸️' : '▶️' }}
      </button>
      <div class="progress-bar" @click="seek">
        <div class="progress-fill" :style="{ width: progress + '%' }"></div>
      </div>
      <span class="time-display">{{ currentTimeStr }} / {{ durationStr }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({ episodeId: String })
const audioEl = ref(null)
const playing = ref(false)
const progress = ref(0)
const currentTimeStr = ref('0:00')
const durationStr = ref('0:00')

let timer = null

function togglePlay() {
  if (!audioEl.value) return
  if (playing.value) {
    audioEl.value.pause()
  } else {
    audioEl.value.play()
  }
  playing.value = !playing.value
}

function seek(e) {
  if (!audioEl.value) return
  const rect = e.currentTarget.getBoundingClientRect()
  const pct = (e.clientX - rect.left) / rect.width
  audioEl.value.currentTime = pct * audioEl.value.duration
}

function formatTime(s) {
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${m}:${sec.toString().padStart(2, '0')}`
}

function updateProgress() {
  if (!audioEl.value) return
  const dur = audioEl.value.duration || 0
  const cur = audioEl.value.currentTime || 0
  progress.value = dur ? (cur / dur) * 100 : 0
  currentTimeStr.value = formatTime(cur)
  durationStr.value = formatTime(dur)
}

onMounted(() => {
  timer = setInterval(updateProgress, 250)
})

onUnmounted(() => {
  clearInterval(timer)
})
</script>

<style scoped>
.player {
  background: white;
  border-radius: 12px;
  padding: 1rem 1.5rem;
  margin: 1rem 0;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.player-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.btn-play {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background: #e5e5ea;
  border-radius: 3px;
  cursor: pointer;
  position: relative;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 3px;
  transition: width 0.2s;
}

.time-display {
  font-size: 0.8rem;
  color: #86868b;
  white-space: nowrap;
}
</style>
