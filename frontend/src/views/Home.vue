<template>
  <div class="home">
    <!-- ────────── New Episode Showcase (auto-display) ────────── -->
    <transition name="showcase">
      <section v-if="store.showNewEpisode && newEpisode" class="showcase">
        <div class="showcase-inner">
          <div class="showcase-badge">
            <span class="badge-dot"></span>
            新节目已生成
          </div>
          <h2 class="showcase-title">{{ newEpisode.title }}</h2>
          <p class="showcase-summary">{{ newEpisode.summary }}</p>
          <div class="showcase-meta">
            <span v-for="g in newEpisode.guests" :key="g" class="meta-tag">{{ g }}</span>
            <span v-if="newEpisode.word_count" class="meta-info">{{ newEpisode.word_count }}字</span>
            <span v-if="newEpisode.duration_seconds" class="meta-info">{{ formatDuration(newEpisode.duration_seconds) }}</span>
          </div>
          <div class="showcase-actions">
            <button class="btn-primary" @click="goToNewEpisode">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
              查看并播放
            </button>
            <button class="btn-ghost" @click="dismissShowcase">继续生成新节目</button>
          </div>
        </div>
        <div class="showcase-visual">
          <div class="visual-ring ring-1"></div>
          <div class="visual-ring ring-2"></div>
          <div class="visual-ring ring-3"></div>
          <div class="visual-mic">
            <svg viewBox="0 0 24 24" width="40" height="40" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 2a3 3 0 00-3 3v7a3 3 0 006 0V5a3 3 0 00-3-3z"/>
              <path d="M19 10v2a7 7 0 01-14 0v-2"/>
              <line x1="12" y1="19" x2="12" y2="22"/>
            </svg>
          </div>
        </div>
      </section>
    </transition>

    <!-- ────────── Workflow ────────── -->
    <section class="workspace" v-show="!store.showNewEpisode">
      <div class="workspace-grid">
        <!-- Left: Wizard -->
        <div class="workspace-main">
          <WorkflowWizard ref="workflowRef" />
        </div>

        <!-- Right: Sidebar -->
        <aside class="workspace-side">
          <div class="side-card side-guests" @click="store.guestDrawerOpen = true">
            <div class="side-card-icon">
              <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8">
                <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 00-3-3.87"/>
                <path d="M16 3.13a4 4 0 010 7.75"/>
              </svg>
            </div>
            <div class="side-card-body">
              <h3>嘉宾库</h3>
              <div class="guest-avatars" v-if="store.guests.length > 0">
                <div
                  v-for="(guest, idx) in store.guests.slice(0, 4)"
                  :key="guest.name"
                  class="mini-avatar"
                  :style="{ background: getAvatarGradient(guest.mbti), zIndex: 4 - idx }"
                >{{ guest.name.charAt(0) }}</div>
                <span class="avatar-count" v-if="store.guests.length > 4">+{{ store.guests.length - 4 }}</span>
              </div>
              <span class="side-hint" v-else>点击管理嘉宾</span>
            </div>
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" class="side-arrow">
              <polyline points="9,18 15,12 9,6"/>
            </svg>
          </div>

          <div class="side-stats">
            <div class="stat-block">
              <span class="stat-num">{{ episodes.length }}</span>
              <span class="stat-lbl">节目</span>
            </div>
            <div class="stat-sep"></div>
            <div class="stat-block">
              <span class="stat-num">{{ store.guests.length }}</span>
              <span class="stat-lbl">嘉宾</span>
            </div>
          </div>
        </aside>
      </div>
    </section>

    <!-- ────────── Episodes ────────── -->
    <section class="episodes" v-show="!store.showNewEpisode">
      <div class="section-title">
        <div class="section-title-main">
          <h2>往期节目</h2>
          <span class="section-count" v-if="episodes.length">{{ episodes.length }}期</span>
        </div>
        <div v-if="episodes.length" class="section-actions">
          <button class="btn-manage" @click="toggleManageMode">
            {{ manageMode ? '完成管理' : '管理节目' }}
          </button>
          <template v-if="manageMode">
            <button class="btn-subtle" @click="toggleSelectAll">
              {{ allSelected ? '取消全选' : '全选' }}
            </button>
            <button class="btn-danger" :disabled="!selectedEpisodeIds.length || deleting" @click="openConfirmDelete('batch', selectedEpisodeIds.length)">
              {{ deleting ? '删除中...' : `删除所选 (${selectedEpisodeIds.length})` }}
            </button>
          </template>
        </div>
      </div>
      
      <div v-if="episodes.length === 0" class="empty-block">
        <svg viewBox="0 0 24 24" width="36" height="36" fill="none" stroke="currentColor" stroke-width="1.5" class="empty-icon">
          <path d="M12 2a3 3 0 00-3 3v7a3 3 0 006 0V5a3 3 0 00-3-3z"/>
          <path d="M19 10v2a7 7 0 01-14 0v-2"/>
          <line x1="12" y1="19" x2="12" y2="22"/>
        </svg>
        <p>尚无节目，在上方开始生成第一期播客</p>
      </div>
      
      <div v-else class="episode-grid">
        <div
          v-for="(ep, idx) in episodes"
          :key="ep.id"
          class="ep-card"
          :class="{ 'is-managing': manageMode, 'is-selected': isEpisodeSelected(ep.id) }"
          @click="handleEpisodeClick(ep.id)"
        >
          <div class="ep-card-top">
            <div class="ep-card-top-left">
              <span
                v-if="manageMode"
                class="ep-checkbox"
                :class="{ checked: isEpisodeSelected(ep.id) }"
                @click.stop="toggleEpisodeSelection(ep.id)"
              >
                <svg v-if="isEpisodeSelected(ep.id)" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="3">
                  <polyline points="20,6 9,17 4,12"/>
                </svg>
              </span>
              <span class="ep-num">#{{ episodes.length - idx }}</span>
            </div>
            <span class="ep-date">{{ formatDate(ep.created_at) }}</span>
          </div>
          <h3 class="ep-title">{{ ep.title }}</h3>
          <p class="ep-desc">{{ ep.summary }}</p>
          <div class="ep-card-bottom">
            <div class="ep-tags">
              <span v-for="g in ep.guests" :key="g" class="ep-tag">{{ g }}</span>
            </div>
            <div class="ep-bottom-right">
              <template v-if="!manageMode">
                <div class="ep-info">
                  <span v-if="ep.word_count">{{ ep.word_count }}字</span>
                  <span v-if="ep.duration_seconds">{{ formatDuration(ep.duration_seconds) }}</span>
                </div>
              </template>
              <button
                v-if="manageMode"
                class="ep-delete-btn"
                :disabled="deleting"
                @click.stop="openConfirmDelete('single', ep.id)"
              >
                删除
              </button>
            </div>
          </div>
          <div v-if="!manageMode" class="ep-play-hint">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
          </div>
        </div>
      </div>
    </section>

    <!-- ────────── Guest Drawer ────────── -->
    <GuestDrawer
      v-model="store.guestDrawerOpen"
      :guests="store.guests"
      :selected-guests="store.selectedGuests"
      @update:selected-guests="store.selectedGuests = $event"
      @save="handleSaveGuest"
      @remove="handleRemoveGuest"
    />

    <!-- ────────── Confirm Delete Dialog ────────── -->
    <Teleport to="body">
      <transition name="dialog-fade">
        <div v-if="confirmDialog.show" class="dialog-overlay" @click.self="closeConfirmDialog">
          <div class="dialog-content">
            <div class="dialog-icon">
              <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2.5">
                <polyline points="3,6 5,6 21,6"/>
                <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
              </svg>
            </div>
            <h4 class="dialog-title">{{ confirmDialog.mode === 'single' ? '删除节目' : '批量删除' }}</h4>
            <p v-if="confirmDialog.mode === 'single'" class="dialog-body">
              确认删除该期节目吗？操作后数据将从服务器彻底移除，且<strong>不可恢复</strong>。
            </p>
            <p v-else class="dialog-body">
              确定移除选中的 <strong>{{ confirmDialog.count }}</strong> 期节目吗？此操作将永久删除相关文件且<strong>无法撤销</strong>。
            </p>
            <div class="dialog-actions">
              <button class="dialog-btn cancel" @click="closeConfirmDialog">取消</button>
              <button class="dialog-btn confirm" @click="handleConfirmDelete">确认删除</button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup>
/**
 * Home.vue — keeps its name so <keep-alive include="Home"> works.
 */
defineOptions({ name: 'Home' })

import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkflowStore } from '../stores/workflow'
import WorkflowWizard from '../components/WorkflowWizard.vue'
import GuestDrawer from '../components/GuestDrawer.vue'

const store = useWorkflowStore()
const router = useRouter()
const workflowRef = ref(null)
const episodes = ref([])
const newEpisode = ref(null)
const manageMode = ref(false)
const selectedEpisodeIds = ref([])
const deleting = ref(false)
const confirmDialog = ref({ show: false, mode: 'single', episodeId: null, count: 0 })

const allSelected = computed(
  () => episodes.value.length > 0 && selectedEpisodeIds.value.length === episodes.value.length
)

// ── Fetch episodes ──
async function fetchEpisodes() {
  try {
    const res = await fetch('/api/episodes')
    episodes.value = await res.json()
    const validIds = new Set(episodes.value.map(ep => ep.id))
    selectedEpisodeIds.value = selectedEpisodeIds.value.filter(id => validIds.has(id))
    if (episodes.value.length === 0) {
      manageMode.value = false
    }
  } catch (e) {
    console.error('Failed to fetch episodes:', e)
  }
}

function toggleManageMode() {
  manageMode.value = !manageMode.value
  if (!manageMode.value) {
    selectedEpisodeIds.value = []
  }
}

function handleEpisodeClick(episodeId) {
  if (manageMode.value) {
    toggleEpisodeSelection(episodeId)
    return
  }
  router.push(`/episode/${episodeId}`)
}

function isEpisodeSelected(episodeId) {
  return selectedEpisodeIds.value.includes(episodeId)
}

function toggleEpisodeSelection(episodeId) {
  if (!manageMode.value) return
  if (isEpisodeSelected(episodeId)) {
    selectedEpisodeIds.value = selectedEpisodeIds.value.filter(id => id !== episodeId)
    return
  }
  selectedEpisodeIds.value = [...selectedEpisodeIds.value, episodeId]
}

function toggleSelectAll() {
  if (allSelected.value) {
    selectedEpisodeIds.value = []
    return
  }
  selectedEpisodeIds.value = episodes.value.map(ep => ep.id)
}

function openConfirmDelete(mode, idOrCount) {
  if (mode === 'single') {
    confirmDialog.value = { show: true, mode: 'single', episodeId: idOrCount, count: 1 }
  } else {
    confirmDialog.value = { show: true, mode: 'batch', episodeId: null, count: idOrCount }
  }
}

function closeConfirmDialog() {
  confirmDialog.value.show = false
}

async function handleConfirmDelete() {
  const { mode, episodeId } = confirmDialog.value
  closeConfirmDialog()
  
  if (mode === 'single') {
    await executeDeleteSingle(episodeId)
  } else {
    await executeDeleteBatch()
  }
}

async function executeDeleteSingle(episodeId) {
  if (deleting.value) return
  deleting.value = true
  try {
    const res = await fetch(`/api/episodes/${episodeId}`, { method: 'DELETE' })
    if (!res.ok) {
      const data = await res.json().catch(() => ({}))
      throw new Error(data?.detail || data?.message || '删除失败')
    }
    await fetchEpisodes()
  } catch (e) {
    alert(e.message || '删除节目失败')
  } finally {
    deleting.value = false
  }
}

async function executeDeleteBatch() {
  if (!selectedEpisodeIds.value.length || deleting.value) return
  deleting.value = true
  const ids = [...selectedEpisodeIds.value]
  try {
    for (const id of ids) {
      const res = await fetch(`/api/episodes/${id}`, { method: 'DELETE' })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data?.detail || data?.message || `删除节目 ${id} 失败`)
      }
    }
    selectedEpisodeIds.value = []
    manageMode.value = false
    await fetchEpisodes()
  } catch (e) {
    alert(e.message || '批量删除失败')
  } finally {
    deleting.value = false
  }
}

// ── Watch for new episode to display ──
watch(() => store.newEpisodeId, async (id) => {
  if (!id) { newEpisode.value = null; return }
  try {
    const res = await fetch(`/api/episodes/${id}`)
    newEpisode.value = await res.json()
    await fetchEpisodes()   // refresh list too
  } catch (e) {
    console.error('Failed to fetch new episode:', e)
  }
})

function goToNewEpisode() {
  const id = store.newEpisodeId
  store.dismissNewEpisode()
  if (id) router.push(`/episode/${id}`)
}

function dismissShowcase() {
  store.dismissNewEpisode()
  store.resetWizard()
}

// ── Guest CRUD wrappers ──
async function handleSaveGuest(payload) {
  try {
    await store.saveGuest(payload)
  } catch (e) {
    alert(e.message || '保存嘉宾失败')
  }
}

async function handleRemoveGuest(name) {
  try {
    await store.removeGuest(name)
  } catch (e) {
    alert(e.message || '删除嘉宾失败')
  }
}

// ── Helpers ──
function getAvatarGradient(mbti) {
  const map = {
    'INTJ': '#6366f1', 'INTP': '#3b82f6', 'ENTJ': '#f59e0b', 'ENTP': '#ec4899',
    'INFJ': '#10b981', 'INFP': '#14b8a6', 'ENFJ': '#f97316', 'ENFP': '#f43f5e',
    'ISTJ': '#64748b', 'ISFJ': '#8b5cf6', 'ESTJ': '#0ea5e9', 'ESFJ': '#a855f7',
    'ISTP': '#06b6d4', 'ISFP': '#84cc16', 'ESTP': '#f59e0b', 'ESFP': '#fb923c'
  }
  return map[mbti] || '#5b5bd6'
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

function formatDuration(seconds) {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

onMounted(async () => {
  await Promise.all([fetchEpisodes(), store.loadGuests()])
})
</script>

<style scoped>
/* ────────── Layout ────────── */
.home {
  display: flex;
  flex-direction: column;
  gap: 2.5rem;
}

/* ────────── Showcase (new episode auto-display) ────────── */
.showcase {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 2.5rem;
  background: linear-gradient(135deg, #FFF5ED 0%, #FFE4CC 40%, #FFDAB9 100%);
  border: 2px solid var(--c-primary-muted);
  border-radius: var(--r-2xl);
  padding: 3rem 3.5rem;
  overflow: hidden;
}
.showcase::before {
  content: '';
  position: absolute;
  top: -60px;
  right: -40px;
  width: 200px;
  height: 200px;
  background: var(--c-primary);
  opacity: 0.06;
  border-radius: 50%;
}
.showcase-inner { position: relative; z-index: 1; flex: 1; min-width: 0; }
.showcase-badge {
  display: inline-flex; align-items: center; gap: 8px;
  background: var(--c-primary); color: #fff;
  padding: 6px 18px; border-radius: var(--r-full);
  font-size: .8rem; font-weight: 700; margin-bottom: 1.25rem;
  box-shadow: 0 3px 10px rgba(255, 107, 53, 0.3);
}
.badge-dot { width: 7px; height: 7px; background: #fff; border-radius: 50%; animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
.showcase-title {
  font-size: 1.8rem; font-weight: 800; color: var(--c-text-1);
  margin-bottom: .6rem; letter-spacing: -0.02em;
}
.showcase-summary {
  color: var(--c-text-2); font-size: 1rem; line-height: 1.7;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
  margin-bottom: 1.25rem;
}
.showcase-meta { display: flex; flex-wrap: wrap; gap: .6rem; margin-bottom: 1.75rem; }
.meta-tag {
  padding: 5px 14px; border-radius: var(--r-full);
  background: var(--c-accent-soft); color: var(--c-accent);
  font-size: .78rem; font-weight: 700;
  border: 1px solid rgba(64, 70, 227, 0.12);
}
.meta-info { font-size: .78rem; color: var(--c-text-3); padding: 5px 0; }
.showcase-actions { display: flex; gap: 1rem; }
.btn-primary {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 12px 28px; border-radius: var(--r-full);
  background: var(--c-primary); color: #fff;
  font-weight: 700; font-size: .9rem; border: none; cursor: pointer;
  box-shadow: 0 4px 14px rgba(255, 107, 53, 0.3);
  transition: all var(--dur-normal) var(--ease-bounce);
}
.btn-primary:hover { background: var(--c-primary-hover); transform: translateY(-2px); box-shadow: 0 6px 20px rgba(255, 107, 53, 0.35); }
.btn-ghost {
  padding: 12px 24px; border-radius: var(--r-full);
  background: var(--c-surface); color: var(--c-text-2);
  font-weight: 600; font-size: .9rem; border: 2px solid var(--c-border); cursor: pointer;
  transition: all var(--dur-fast) var(--ease);
}
.btn-ghost:hover { border-color: var(--c-primary); color: var(--c-primary); }

/* Visual decoration */
.showcase-visual {
  position: relative; width: 180px; height: 180px; flex-shrink: 0;
}
.visual-ring {
  position: absolute; border-radius: 50%;
  border: 2px solid rgba(255, 107, 53, 0.12);
  inset: 0; animation: ring-pulse 3s ease-in-out infinite;
}
.ring-1 { inset: 0; animation-delay: 0s; }
.ring-2 { inset: 18px; animation-delay: .5s; border-color: rgba(64, 70, 227, 0.1); }
.ring-3 { inset: 36px; animation-delay: 1s; border-color: rgba(241, 198, 68, 0.15); }
@keyframes ring-pulse { 0%,100%{transform:scale(1);opacity:.3} 50%{transform:scale(1.08);opacity:1} }
.visual-mic {
  position: absolute; inset: 50px;
  display: flex; align-items: center; justify-content: center;
  background: var(--c-primary); border-radius: 50%; color: #fff;
  box-shadow: 0 6px 24px rgba(255, 107, 53, 0.35);
}

.showcase-enter-active { animation: fade-slide-up .45s var(--ease); }
.showcase-leave-active { animation: fade-slide-up .3s var(--ease) reverse; }
@keyframes fade-slide-up {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ────────── Workspace ────────── */
.workspace-grid {
  display: grid;
  grid-template-columns: 1fr 260px;
  gap: 1.75rem;
  align-items: start;
}
.workspace-main { min-width: 0; }
.workspace-side {
  display: flex; flex-direction: column; gap: 1.25rem;
  position: sticky; top: 5.5rem;
}

/* Side card — guest library entry */
.side-card {
  display: flex; align-items: center; gap: 1rem;
  background: var(--c-surface); border: 2px solid var(--c-border);
  border-radius: var(--r-xl); padding: 1.25rem;
  cursor: pointer; transition: all var(--dur-normal) var(--ease);
}
.side-card:hover {
  border-color: var(--c-primary); box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}
.side-card-icon {
  width: 48px; height: 48px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: var(--c-yellow-soft); border-radius: var(--r-lg); color: #D4A017;
}
.side-card-body { flex: 1; min-width: 0; }
.side-card-body h3 { font-size: .95rem; font-weight: 700; color: var(--c-text-1); margin-bottom: 4px; }
.side-hint { font-size: .8rem; color: var(--c-text-3); }
.side-arrow { color: var(--c-text-3); flex-shrink: 0; transition: transform var(--dur-fast) var(--ease); }
.side-card:hover .side-arrow { transform: translateX(3px); color: var(--c-primary); }
.guest-avatars { display: flex; align-items: center; gap: 0; }
.mini-avatar {
  width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: .7rem; font-weight: 700;
  border: 2px solid var(--c-surface); margin-left: -6px;
}
.mini-avatar:first-child { margin-left: 0; }
.avatar-count { font-size: .75rem; color: var(--c-text-3); margin-left: 6px; font-weight: 600; }

/* Side stats */
.side-stats {
  display: flex; align-items: center; justify-content: center; gap: 2rem;
  background: var(--c-surface); border: 2px solid var(--c-border);
  border-radius: var(--r-xl); padding: 1.25rem;
}
.stat-block { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.stat-num { font-size: 1.6rem; font-weight: 800; color: var(--c-primary); }
.stat-lbl { font-size: .75rem; color: var(--c-text-3); font-weight: 600; }
.stat-sep { width: 2px; height: 36px; background: var(--c-border); border-radius: 1px; }

/* ────────── Episodes Section ────────── */
.episodes { margin-top: .5rem; }
.section-title {
  display: flex; align-items: center; justify-content: space-between; gap: .75rem; margin-bottom: 1.5rem;
}
.section-title-main {
  display: flex; align-items: baseline; gap: .75rem;
}
.section-title h2 {
  font-size: 1.35rem; font-weight: 800; color: var(--c-text-1);
  letter-spacing: -0.01em;
}
.section-count {
  font-size: .8rem; color: var(--c-primary); font-weight: 700;
  background: var(--c-primary-soft); padding: 3px 14px; border-radius: var(--r-full);
}

.section-actions {
  display: flex;
  align-items: center;
  gap: .6rem;
}

.btn-manage,
.btn-subtle,
.btn-danger {
  border-radius: var(--r-full);
  font-size: .78rem;
  font-weight: 700;
  padding: 7px 14px;
  cursor: pointer;
  border: 2px solid var(--c-border);
  background: var(--c-surface);
  color: var(--c-text-2);
  transition: all var(--dur-fast) var(--ease);
}

.btn-manage:hover,
.btn-subtle:hover {
  color: var(--c-primary);
  border-color: var(--c-primary);
}

.btn-danger {
  border-color: rgba(255, 107, 53, 0.35);
  color: var(--c-primary);
}

.btn-danger:disabled {
  opacity: .55;
  cursor: not-allowed;
}

.empty-block {
  text-align: center; padding: 4rem 2rem;
  background: var(--c-surface); border: 2px dashed var(--c-border); border-radius: var(--r-xl);
}
.empty-icon { color: var(--c-text-3); margin-bottom: 1rem; }
.empty-block p { color: var(--c-text-3); font-size: .95rem; }

/* Episode grid */
.episode-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.25rem;
}
.ep-card {
  position: relative;
  background: var(--c-surface); border: 2px solid var(--c-border);
  border-radius: var(--r-xl); padding: 1.5rem;
  cursor: pointer; transition: all var(--dur-normal) var(--ease);
  overflow: hidden;
}
.ep-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--c-primary), var(--c-yellow), var(--c-blue));
  opacity: 0;
  transition: opacity var(--dur-fast) var(--ease);
}
.ep-card:hover {
  border-color: transparent; box-shadow: var(--shadow-lg);
  transform: translateY(-4px);
}
.ep-card.is-managing {
  cursor: default;
}
.ep-card.is-managing:hover {
  transform: translateY(0);
}
.ep-card.is-managing.is-selected {
  border-color: var(--c-primary);
  box-shadow: 0 0 0 2px rgba(255, 107, 53, 0.14);
}
.ep-card:hover::before { opacity: 1; }
.ep-card:hover .ep-play-hint { opacity: 1; transform: scale(1); }

.ep-checkbox {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  border-radius: 50%;
  border: 2px solid var(--c-border);
  background: var(--c-surface);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--dur-fast) var(--ease);
}

.ep-checkbox:hover {
  border-color: var(--c-primary);
}

.ep-checkbox.checked {
  border-color: var(--c-primary);
  background: var(--c-primary);
}
.ep-card-top {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: .75rem;
}
.ep-card-top-left {
  display: flex; align-items: center; gap: .5rem;
}
.ep-num {
  font-size: .78rem; font-weight: 800; color: var(--c-primary);
  background: var(--c-primary-soft); padding: 2px 10px; border-radius: var(--r-full);
}
.ep-date { font-size: .75rem; color: var(--c-text-3); font-weight: 500; }
.ep-title {
  font-size: 1.05rem; font-weight: 700; color: var(--c-text-1); margin-bottom: .4rem;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
  line-height: 1.5;
}
.ep-desc {
  font-size: .85rem; color: var(--c-text-2); line-height: 1.6;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
  margin-bottom: 1rem;
}
.ep-card-bottom {
  display: flex; justify-content: space-between; align-items: flex-end; gap: .5rem;
}
.ep-tags { display: flex; flex-wrap: wrap; gap: .4rem; flex: 1; min-width: 0; }
.ep-bottom-right { display: flex; align-items: center; flex-shrink: 0; }
.ep-tag {
  padding: 3px 10px; border-radius: var(--r-full);
  background: var(--c-accent-soft); color: var(--c-accent);
  font-size: .72rem; font-weight: 700;
}
.ep-tag:nth-child(2) { background: var(--c-blue-soft); color: #0099CC; }
.ep-tag:nth-child(3) { background: var(--c-green-soft); color: var(--c-green); }
.ep-info { display: flex; gap: .6rem; font-size: .75rem; color: var(--c-text-3); font-weight: 500; }
.ep-play-hint {
  position: absolute; top: 1.25rem; right: 1.25rem;
  width: 36px; height: 36px; border-radius: 50%;
  background: var(--c-primary); color: #fff;
  display: flex; align-items: center; justify-content: center;
  opacity: 0; transform: scale(0.8);
  transition: all var(--dur-normal) var(--ease-bounce);
  box-shadow: 0 3px 10px rgba(255, 107, 53, 0.3);
}

.ep-delete-btn {
  border: none;
  border-radius: var(--r-full);
  background: rgba(255, 107, 53, 0.1);
  color: var(--c-primary);
  font-size: .72rem;
  font-weight: 700;
  padding: 5px 14px;
  cursor: pointer;
  transition: all var(--dur-fast) var(--ease);
  white-space: nowrap;
}

.ep-delete-btn:hover {
  background: var(--c-primary);
  color: #fff;
}

.ep-delete-btn:disabled {
  opacity: .55;
  cursor: not-allowed;
}

/* ────────── Delete Confirmation Dialog ────────── */
.dialog-overlay {
  position: fixed; inset: 0;
  background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(12px);
  z-index: 9999;
  display: flex; align-items: center; justify-content: center;
  padding: 20px;
}
.dialog-content {
  background: #FFFFFF; border-radius: 28px;
  width: 100%; max-width: 420px;
  padding: 40px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.15), 0 0 0 1px rgba(0, 0, 0, 0.05);
  text-align: center;
  animation: dialog-pop .3s var(--ease-bounce);
}
@keyframes dialog-pop {
  from { opacity: 0; transform: scale(0.9) translateY(10px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
.dialog-icon {
  width: 72px; height: 72px;
  background: rgba(255, 107, 53, 0.1);
  color: #FF6B35;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 28px; font-size: 36px;
}
.dialog-title {
  font-size: 1.3rem; font-weight: 800;
  color: var(--c-text-1); margin-bottom: 12px;
}
.dialog-body {
  font-size: 1rem; color: var(--c-text-2);
  line-height: 1.6; margin-bottom: 36px;
}
.dialog-actions {
  display: grid; grid-template-columns: 1fr 1fr; gap: 14px;
}
.dialog-btn {
  padding: 14px; border-radius: 16px;
  font-size: 1rem; font-weight: 700;
  cursor: pointer; transition: all .2s var(--ease);
  border: none;
}
.dialog-btn.cancel {
  background: var(--c-surface); color: var(--c-text-1);
  box-shadow: 0 0 0 1px var(--c-border);
}
.dialog-btn.cancel:hover { background: #f8fafc; color: var(--c-primary); }
.dialog-btn.confirm {
  background: #FF6B35; color: #FFFFFF;
}
.dialog-btn.confirm:hover { background: #E85A2A; transform: translateY(-2px); box-shadow: 0 4px 14px rgba(255, 107, 53, 0.3); }

/* Dialog Transitions */
.dialog-fade-enter-active, .dialog-fade-leave-active {
  transition: opacity .3s var(--ease);
}
.dialog-fade-enter-from, .dialog-fade-leave-to {
  opacity: 0;
}
.dialog-fade-enter-active .dialog-content {
  animation: dialog-pop .35s var(--ease-bounce);
}
.dialog-fade-leave-active .dialog-content {
  animation: dialog-pop .2s var(--ease) reverse;
}

/* ────────── Responsive ────────── */
@media (max-width: 900px) {
  .workspace-grid { grid-template-columns: 1fr; }
  .workspace-side { flex-direction: row; position: static; }
  .side-card { flex: 1; }
  .side-stats { flex: 0 0 auto; }
  .showcase { flex-direction: column; text-align: center; padding: 2.5rem; }
  .showcase-actions { justify-content: center; }
  .showcase-visual { width: 140px; height: 140px; }
  .visual-mic { inset: 40px; }
}

@media (max-width: 600px) {
  .workspace-side { flex-direction: column; }
  .episode-grid { grid-template-columns: 1fr; }
  .showcase { padding: 2rem; }
  .showcase-title { font-size: 1.4rem; }
  .section-title { align-items: flex-start; flex-direction: column; }
  .section-actions { width: 100%; flex-wrap: wrap; }
}
</style>
