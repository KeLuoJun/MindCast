<template>
  <div class="home">
    <section class="test-section">
      <h2>接口测试面板</h2>
      <div class="test-actions">
        <button class="btn-test" @click="runHealthCheck">测试健康检查</button>
        <button class="btn-test" @click="fetchEpisodes">测试播客列表</button>
        <button class="btn-test" @click="runNewsDebug">测试内容获取</button>
        <button class="btn-test" @click="runScriptDebug">测试文本生成</button>
      </div>
      <div class="task-tools">
        <input
          v-model="debugTaskId"
          class="task-input"
          placeholder="输入 task_id 查询状态"
        />
        <button class="btn-test" @click="checkTaskStatus">查询任务状态</button>
      </div>
      <pre class="test-output">{{ testOutput }}</pre>
    </section>

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
const debugTaskId = ref('')
const testOutput = ref('等待测试...')

function pretty(data) {
  if (typeof data === 'string') return data
  return JSON.stringify(data, null, 2)
}

async function runHealthCheck() {
  try {
    const res = await fetch('/')
    const data = await res.json()
    testOutput.value = pretty(data)
  } catch (e) {
    testOutput.value = `健康检查失败: ${e.message}`
  }
}

async function fetchEpisodes() {
  try {
    const res = await fetch('/api/episodes')
    episodes.value = await res.json()
    testOutput.value = pretty(episodes.value)
  } catch (e) {
    console.error('Failed to fetch episodes:', e)
    testOutput.value = `获取播客列表失败: ${e.message}`
  }
}

async function runNewsDebug() {
  try {
    const res = await fetch('/api/debug/news?max_results=5')
    const data = await res.json()
    testOutput.value = pretty(data)
  } catch (e) {
    testOutput.value = `内容获取测试失败: ${e.message}`
  }
}

async function runScriptDebug() {
  try {
    const res = await fetch('/api/debug/script', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ max_news_results: 6, max_search_queries: 3 }),
    })
    const data = await res.json()
    testOutput.value = pretty(data)
  } catch (e) {
    testOutput.value = `文本生成测试失败: ${e.message}`
  }
}

async function checkTaskStatus() {
  if (!debugTaskId.value.trim()) {
    testOutput.value = '请先输入 task_id'
    return
  }
  try {
    const res = await fetch(`/api/status/${debugTaskId.value.trim()}`)
    const raw = await res.text()
    const lines = raw
      .split('\n')
      .filter(line => line.startsWith('data:'))
    const latest = lines.length ? lines[lines.length - 1].slice(5).trim() : '{}'
    testOutput.value = pretty(JSON.parse(latest))
  } catch (e) {
    testOutput.value = `任务状态查询失败: ${e.message}`
  }
}

async function startGenerate() {
  generating.value = true
  try {
    const res = await fetch('/api/generate', { method: 'POST' })
    const data = await res.json()
    taskId.value = data.task_id
    debugTaskId.value = data.task_id
    testOutput.value = pretty(data)
  } catch (e) {
    console.error('Failed to start generation:', e)
    testOutput.value = `创建任务失败: ${e.message}`
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
.test-section {
  background: white;
  border-radius: 12px;
  padding: 1rem;
  margin-bottom: 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.test-section h2 {
  margin-bottom: 0.6rem;
  font-size: 1.05rem;
}

.test-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.task-tools {
  margin-top: 0.6rem;
  display: flex;
  gap: 0.5rem;
}

.task-input {
  flex: 1;
  border: 1px solid #d2d2d7;
  border-radius: 8px;
  padding: 0.45rem 0.6rem;
}

.btn-test {
  border: 1px solid #d2d2d7;
  background: #fff;
  border-radius: 8px;
  padding: 0.4rem 0.7rem;
  cursor: pointer;
}

.test-output {
  margin-top: 0.7rem;
  background: #f5f5f7;
  border-radius: 8px;
  padding: 0.7rem;
  max-height: 240px;
  overflow: auto;
  font-size: 0.8rem;
  white-space: pre-wrap;
  word-break: break-word;
}

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
