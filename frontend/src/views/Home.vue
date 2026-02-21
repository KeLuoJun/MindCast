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
        <h2>往期节目</h2>
        <span class="section-count" v-if="episodes.length">{{ episodes.length }}期</span>
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
          @click="$router.push(`/episode/${ep.id}`)"
        >
          <div class="ep-card-top">
            <span class="ep-num">#{{ episodes.length - idx }}</span>
            <span class="ep-date">{{ formatDate(ep.created_at) }}</span>
          </div>
          <h3 class="ep-title">{{ ep.title }}</h3>
          <p class="ep-desc">{{ ep.summary }}</p>
          <div class="ep-card-bottom">
            <div class="ep-tags">
              <span v-for="g in ep.guests" :key="g" class="ep-tag">{{ g }}</span>
            </div>
            <div class="ep-info">
              <span v-if="ep.word_count">{{ ep.word_count }}字</span>
              <span v-if="ep.duration_seconds">{{ formatDuration(ep.duration_seconds) }}</span>
            </div>
          </div>
          <div class="ep-play-hint">
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
  </div>
</template>

<script setup>
/**
 * Home.vue — keeps its name so <keep-alive include="Home"> works.
 */
defineOptions({ name: 'Home' })

import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkflowStore } from '../stores/workflow'
import WorkflowWizard from '../components/WorkflowWizard.vue'
import GuestDrawer from '../components/GuestDrawer.vue'

const store = useWorkflowStore()
const router = useRouter()
const workflowRef = ref(null)
const episodes = ref([])
const newEpisode = ref(null)

// ── Fetch episodes ──
async function fetchEpisodes() {
  try {
    const res = await fetch('/api/episodes')
    episodes.value = await res.json()
  } catch (e) {
    console.error('Failed to fetch episodes:', e)
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
  gap: 2rem;
  background: linear-gradient(135deg, var(--c-primary-soft) 0%, #f0e7ff 60%, #fef3e0 100%);
  border: 1px solid var(--c-border);
  border-radius: var(--r-xl);
  padding: 2.5rem 3rem;
  overflow: hidden;
}
.showcase-inner { position: relative; z-index: 1; flex: 1; min-width: 0; }
.showcase-badge {
  display: inline-flex; align-items: center; gap: 6px;
  background: var(--c-primary); color: #fff;
  padding: 5px 14px; border-radius: var(--r-full);
  font-size: 0.78rem; font-weight: 600; margin-bottom: 1rem;
}
.badge-dot { width: 6px; height: 6px; background: #fff; border-radius: 50%; animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
.showcase-title { font-size: 1.5rem; font-weight: 700; color: var(--c-text-1); margin-bottom: .5rem; }
.showcase-summary {
  color: var(--c-text-2); font-size: .95rem; line-height: 1.6;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
  margin-bottom: 1rem;
}
.showcase-meta { display: flex; flex-wrap: wrap; gap: .5rem; margin-bottom: 1.5rem; }
.meta-tag {
  padding: 3px 10px; border-radius: var(--r-full);
  background: rgba(91,91,214,.1); color: var(--c-primary);
  font-size: .75rem; font-weight: 600;
}
.meta-info { font-size: .75rem; color: var(--c-text-3); padding: 3px 0; }
.showcase-actions { display: flex; gap: .75rem; }
.btn-primary {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 10px 24px; border-radius: var(--r-md);
  background: var(--c-primary); color: #fff;
  font-weight: 600; font-size: .88rem; border: none; cursor: pointer;
  transition: background var(--dur-fast) var(--ease);
}
.btn-primary:hover { background: var(--c-primary-hover); }
.btn-ghost {
  padding: 10px 20px; border-radius: var(--r-md);
  background: transparent; color: var(--c-text-2);
  font-weight: 500; font-size: .88rem; border: 1px solid var(--c-border); cursor: pointer;
  transition: all var(--dur-fast) var(--ease);
}
.btn-ghost:hover { border-color: var(--c-text-3); color: var(--c-text-1); }

/* Visual decoration */
.showcase-visual {
  position: relative; width: 160px; height: 160px; flex-shrink: 0;
}
.visual-ring {
  position: absolute; border-radius: 50%;
  border: 1.5px solid rgba(91,91,214,.15);
  inset: 0; animation: ring-pulse 3s ease-in-out infinite;
}
.ring-1 { inset: 0; animation-delay: 0s; }
.ring-2 { inset: 15px; animation-delay: .5s; }
.ring-3 { inset: 30px; animation-delay: 1s; }
@keyframes ring-pulse { 0%,100%{transform:scale(1);opacity:.4} 50%{transform:scale(1.06);opacity:.9} }
.visual-mic {
  position: absolute; inset: 45px;
  display: flex; align-items: center; justify-content: center;
  background: var(--c-primary); border-radius: 50%; color: #fff;
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
  grid-template-columns: 1fr 240px;
  gap: 1.5rem;
  align-items: start;
}
.workspace-main { min-width: 0; }
.workspace-side {
  display: flex; flex-direction: column; gap: 1rem;
  position: sticky; top: 5.5rem;
}

/* Side card — guest library entry */
.side-card {
  display: flex; align-items: center; gap: .85rem;
  background: var(--c-surface); border: 1px solid var(--c-border);
  border-radius: var(--r-lg); padding: 1rem 1.15rem;
  cursor: pointer; transition: all var(--dur-fast) var(--ease);
}
.side-card:hover { border-color: var(--c-primary); box-shadow: var(--shadow-sm); }
.side-card-icon {
  width: 42px; height: 42px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: var(--c-primary-soft); border-radius: var(--r-md); color: var(--c-primary);
}
.side-card-body { flex: 1; min-width: 0; }
.side-card-body h3 { font-size: .92rem; font-weight: 600; color: var(--c-text-1); margin-bottom: 4px; }
.side-hint { font-size: .78rem; color: var(--c-text-3); }
.side-arrow { color: var(--c-text-3); flex-shrink: 0; }
.guest-avatars { display: flex; align-items: center; gap: 0; }
.mini-avatar {
  width: 26px; height: 26px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: .68rem; font-weight: 600;
  border: 2px solid var(--c-surface); margin-left: -6px;
}
.mini-avatar:first-child { margin-left: 0; }
.avatar-count { font-size: .72rem; color: var(--c-text-3); margin-left: 4px; }

/* Side stats */
.side-stats {
  display: flex; align-items: center; justify-content: center; gap: 1.5rem;
  background: var(--c-surface); border: 1px solid var(--c-border);
  border-radius: var(--r-lg); padding: 1rem;
}
.stat-block { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.stat-num { font-size: 1.4rem; font-weight: 700; color: var(--c-primary); }
.stat-lbl { font-size: .72rem; color: var(--c-text-3); }
.stat-sep { width: 1px; height: 32px; background: var(--c-border); }

/* ────────── Episodes Section ────────── */
.episodes { margin-top: .5rem; }
.section-title {
  display: flex; align-items: baseline; gap: .75rem; margin-bottom: 1.25rem;
}
.section-title h2 { font-size: 1.15rem; font-weight: 600; color: var(--c-text-1); }
.section-count {
  font-size: .78rem; color: var(--c-text-3);
  background: var(--c-primary-soft); padding: 2px 10px; border-radius: var(--r-full);
}

.empty-block {
  text-align: center; padding: 3rem 1rem;
  background: var(--c-surface); border: 1px dashed var(--c-border); border-radius: var(--r-lg);
}
.empty-icon { color: var(--c-text-3); margin-bottom: .75rem; }
.empty-block p { color: var(--c-text-3); font-size: .9rem; }

/* Episode grid */
.episode-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}
.ep-card {
  position: relative;
  background: var(--c-surface); border: 1px solid var(--c-border);
  border-radius: var(--r-lg); padding: 1.25rem;
  cursor: pointer; transition: all var(--dur-fast) var(--ease);
  overflow: hidden;
}
.ep-card:hover {
  border-color: var(--c-primary); box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}
.ep-card:hover .ep-play-hint { opacity: 1; }
.ep-card-top {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: .6rem;
}
.ep-num { font-size: .72rem; font-weight: 700; color: var(--c-primary); }
.ep-date { font-size: .7rem; color: var(--c-text-3); }
.ep-title {
  font-size: .95rem; font-weight: 600; color: var(--c-text-1); margin-bottom: .35rem;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
  line-height: 1.45;
}
.ep-desc {
  font-size: .8rem; color: var(--c-text-2); line-height: 1.5;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
  margin-bottom: .75rem;
}
.ep-card-bottom {
  display: flex; justify-content: space-between; align-items: flex-end;
}
.ep-tags { display: flex; flex-wrap: wrap; gap: .35rem; }
.ep-tag {
  padding: 2px 8px; border-radius: var(--r-sm);
  background: var(--c-primary-soft); color: var(--c-primary);
  font-size: .68rem; font-weight: 600;
}
.ep-info { display: flex; gap: .6rem; font-size: .7rem; color: var(--c-text-3); }
.ep-play-hint {
  position: absolute; top: 1rem; right: 1rem;
  width: 32px; height: 32px; border-radius: 50%;
  background: var(--c-primary); color: #fff;
  display: flex; align-items: center; justify-content: center;
  opacity: 0; transition: opacity var(--dur-fast) var(--ease);
}

/* ────────── Responsive ────────── */
@media (max-width: 900px) {
  .workspace-grid { grid-template-columns: 1fr; }
  .workspace-side { flex-direction: row; position: static; }
  .side-card { flex: 1; }
  .side-stats { flex: 0 0 auto; }
  .showcase { flex-direction: column; text-align: center; padding: 2rem; }
  .showcase-actions { justify-content: center; }
  .showcase-visual { width: 120px; height: 120px; }
  .visual-mic { inset: 35px; }
}

@media (max-width: 600px) {
  .workspace-side { flex-direction: column; }
  .episode-grid { grid-template-columns: 1fr; }
  .showcase { padding: 1.5rem; }
  .showcase-title { font-size: 1.2rem; }
}
</style>
