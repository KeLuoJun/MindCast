<template>
  <div class="player" :class="{ 'is-minimal': minimal }" v-if="episodeId">
    <audio ref="audioEl" :src="`/api/episodes/${episodeId}/audio`" preload="metadata" />
    <div class="player-wrapper">
      <div class="player-main">
        <button class="btn-control btn-prev">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/>
          </svg>
        </button>

        <button class="btn-control btn-play" @click="togglePlay">
          <svg v-if="!playing" viewBox="0 0 24 24" width="28" height="28" fill="currentColor">
            <path d="M8 5v14l11-7z"/>
          </svg>
          <svg v-else viewBox="0 0 24 24" width="28" height="28" fill="currentColor">
            <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
          </svg>
        </button>

        <button class="btn-control btn-next">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/>
          </svg>
        </button>
      </div>

      <div class="progress-container">
        <span class="time-display">{{ currentTimeStr }}</span>
        <div class="progress-bar" @click="seek">
          <div class="progress-track"></div>
          <div class="progress-fill" :style="{ width: progress + '%' }">
            <div class="progress-thumb"></div>
          </div>
        </div>
        <span class="time-display">{{ durationStr }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  episodeId: String,
  minimal: { type: Boolean, default: false }
})
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
.player.is-minimal {
  background: transparent;
  border: none;
  box-shadow: none;
  padding: 0;
  margin: 0;
}

.player.is-minimal .btn-control {
  width: 42px;
  height: 42px;
}

.player.is-minimal .btn-control svg {
  width: 18px;
  height: 18px;
}

.player.is-minimal .btn-play {
  width: 56px;
  height: 56px;
}

.player.is-minimal .btn-play svg {
  width: 24px;
  height: 24px;
}

.player.is-minimal .player-wrapper {
  gap: 0.8rem;
}

.player.is-minimal .progress-container {
  margin-top: 0.2rem;
}

.player-wrapper {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.player-main {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
}

.btn-control {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--c-bg);
  border: 2px solid var(--c-border);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-text-3);
  transition: all var(--dur-normal) var(--ease);
}

.btn-control:hover {
  background: var(--c-primary-soft);
  border-color: var(--c-primary);
  color: var(--c-primary);
  transform: scale(1.05);
}

.btn-control:active {
  transform: scale(0.95);
}

.btn-play {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, var(--c-primary) 0%, #FF8F5F 100%);
  border: none;
  color: white;
  box-shadow: 0 6px 20px rgba(255, 107, 53, 0.35);
}

.btn-play:hover {
  background: linear-gradient(135deg, var(--c-primary-hover) 0%, var(--c-primary) 100%);
  box-shadow: 0 8px 28px rgba(255, 107, 53, 0.45);
  border: none;
  color: white;
  transform: scale(1.08);
}

.progress-container {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.time-display {
  font-size: 0.82rem;
  color: var(--c-text-3);
  font-weight: 600;
  min-width: 45px;
  text-align: center;
  font-variant-numeric: tabular-nums;
}

.progress-bar {
  flex: 1;
  height: 8px;
  cursor: pointer;
  position: relative;
  display: flex;
  align-items: center;
}

.progress-track {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 100%;
  background: var(--c-border);
  border-radius: var(--r-full);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--c-primary) 0%, var(--c-yellow) 100%);
  border-radius: var(--r-full);
  transition: width 0.1s;
  position: relative;
  min-width: 8px;
}

.progress-thumb {
  position: absolute;
  right: -6px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  background: white;
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  border: 3px solid var(--c-primary);
  transition: transform var(--dur-fast) var(--ease);
}

.progress-bar:hover .progress-thumb {
  transform: translateY(-50%) scale(1.25);
}
</style>
