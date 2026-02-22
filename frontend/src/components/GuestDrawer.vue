<template>
  <Teleport to="body">
    <!-- Backdrop -->
    <transition name="fade">
      <div v-if="modelValue" class="drawer-overlay" @click="close"></div>
    </transition>

    <!-- Drawer Panel -->
    <transition name="slide">
      <div v-if="modelValue" class="drawer-panel">
        <!-- Header -->
        <div class="drawer-header">
          <div class="header-title-group">
            <h2>嘉宾列表</h2>
            <p class="header-subtitle">管理播客嘉宾</p>
          </div>
          <button class="btn-close" @click="close" title="关闭窗口">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <!-- Body -->
        <div class="drawer-body">
          <div class="guest-list">
            <!-- Host Configuration (Sticky Top) -->
            <div v-if="hostPersona" class="guest-card-wrapper host-section">
              <div class="section-divider"><span>主持人</span></div>
              <div
                class="guest-card host-card"
                :class="{ 'guest-card--expanded': expandedBadge === 'HOST' }"
                @click="expandedBadge = expandedBadge === 'HOST' ? null : 'HOST'"
              >
                <div class="avatar-container">
                  <div class="guest-avatar host-avatar">
                   {{ hostPersona.name.charAt(0) }}
                  </div>
                  <div class="host-badge">HOST</div>
                </div>
                <div class="guest-card-content">
                  <div class="guest-card-header">
                    <span class="guest-name">{{ hostPersona.name }}</span>
                    <div class="expand-chevron">
                      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5">
                        <polyline points="6,9 12,15 18,9"/>
                      </svg>
                    </div>
                  </div>
                  <div class="guest-role">{{ hostPersona.occupation }}</div>
                  <div class="guest-tags">
                    <span class="tag-pill tag-pill--mbti">{{ hostPersona.mbti }}</span>
                    <span class="tag-pill tag-pill--count">{{ hostPersona.gender === 'male' ? '男' : '女' }} · {{ hostPersona.age }}岁</span>
                  </div>
                </div>
              </div>

              <transition name="expand">
                <div v-if="expandedBadge === 'HOST'" class="card-drawer-extension">
                  <div class="action-bar">
                    <button class="btn-icon-label" @click.stop="startEditHost">
                      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                      编辑主持资料
                    </button>
                  </div>
                  <div class="extension-content">
                    <div v-if="editingHost" class="edit-form host-edit-form">
                      <div class="form-body">
                        <div class="form-row">
                          <div class="form-group">
                            <label>名称 *</label>
                            <input v-model="guestForm.name" type="text" />
                          </div>
                          <div class="form-group">
                            <label>MBTI</label>
                            <select v-model="guestForm.mbti">
                              <option value="">请选择 MBTI</option>
                              <option v-for="type in mbtiOptions" :key="type" :value="type">{{ type }}</option>
                            </select>
                          </div>
                        </div>
                        <div class="form-row">
                          <div class="form-group">
                            <label>职业</label>
                            <input v-model="guestForm.occupation" type="text" />
                          </div>
                          <div class="form-group small">
                            <label>性别</label>
                            <select v-model="guestForm.gender">
                              <option value="male">男</option>
                              <option value="female">女</option>
                            </select>
                          </div>
                          <div class="form-group small">
                            <label>年龄</label>
                            <input v-model.number="guestForm.age" type="number" />
                          </div>
                        </div>
                        <div class="form-group">
                          <label class="voice-label">音色ID</label>
                          <div class="form-row">
                            <input v-model="guestForm.voice_id" type="text" />
                            <button class="btn-icon-label" style="flex: 0 0 auto;" @click="showVoicePicker = !showVoicePicker">列表</button>
                          </div>
                          <transition name="expand">
                            <div v-if="showVoicePicker" class="voice-picker">
                              <div class="voice-header">内置音色</div>
                              <div class="voice-options">
                                <button v-for="v in voicesForCurrentGender" :key="v" 
                                  class="voice-option" 
                                  :class="{ 'voice-option--active': guestForm.voice_id === v }"
                                  @click="selectBuiltinVoice(v)">
                                  {{ v }}
                                </button>
                              </div>
                            </div>
                          </transition>
                        </div>
                        <div class="form-group">
                          <label>性格与主持效果描述</label>
                          <textarea v-model="guestForm.personality" rows="5" placeholder="热情、理性的观察者..."></textarea>
                        </div>
                        <div class="form-group">
                          <label>主持/对话风格</label>
                          <textarea v-model="guestForm.speaking_style" rows="5" placeholder="语速、口癖、提问倾向..."></textarea>
                        </div>
                        <div class="form-group">
                          <label>核心背景经历</label>
                          <textarea v-model="guestForm.background" rows="5"></textarea>
                        </div>
                      </div>
                      <div class="form-actions">
                        <button class="btn-cancel" @click="editingHost = false">取消</button>
                        <button class="btn-save" :disabled="savingGuest" @click="saveGuest">保存主持配置</button>
                      </div>
                    </div>
                    <div v-else class="guest-bio-box">
                      <span class="bio-label">主持风格 & 背景</span>
                      <p class="bio-text">{{ hostPersona.personality }}</p>
                    </div>
                  </div>
                </div>
              </transition>
            </div>

            <div class="section-divider"><span>常驻嘉宾</span></div>

            <!-- Guest Profile Cards -->
            <div
              v-for="guest in guests"
              :key="guest.name"
              class="guest-card-wrapper"
            >
              <div
                class="guest-card"
                :class="{
                  'guest-card--expanded': expandedBadge === guest.name
                }"
                @click="toggleExpand(guest.name)"
              >
                <!-- Avatar -->
                <div class="avatar-container">
                  <div class="guest-avatar" :style="{ background: getAvatarGradient(guest.mbti) }">
                    {{ guest.name.charAt(0) }}
                  </div>
                </div>

                <!-- Info Area -->
                <div class="guest-card-content">
                  <div class="guest-card-header">
                    <span class="guest-name">{{ guest.name }}</span>
                    <div class="expand-chevron">
                      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5">
                        <polyline points="6,9 12,15 18,9"/>
                      </svg>
                    </div>
                  </div>
                  <div class="guest-role">{{ guest.occupation || '播客嘉宾' }}</div>
                  <div class="guest-tags">
                    <span v-if="guest.mbti" class="tag-pill tag-pill--mbti">{{ guest.mbti }}</span>
                    <span class="tag-pill tag-pill--count">{{ guest.gender === 'male' ? '男' : '女' }} · {{ guest.age }}岁</span>
                  </div>
                </div>
              </div>

              <!-- Contextual Extension (Actions/Details) -->
              <transition name="expand">
                <div v-if="expandedBadge === guest.name" class="card-drawer-extension">
                  <!-- Management ActionBar -->
                  <div class="action-bar">
                    <button class="btn-icon-label" @click.stop="startEdit(guest)">
                      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                      编辑资料
                    </button>
                    <button class="btn-icon-label danger" @click.stop="askRemoveGuest(guest.name)">
                      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3,6 5,6 21,6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
                      移除嘉宾
                    </button>
                  </div>

                  <!-- Details or Inline Edit -->
                  <div class="extension-content">
                    <!-- Inline Edit Form -->
                    <div v-if="editingGuest === guest.name" class="edit-form">
                      <div class="form-body">
                        <div class="form-row">
                          <div class="form-group">
                            <label>姓名 *</label>
                            <input v-model="guestForm.name" type="text" />
                          </div>
                          <div class="form-group">
                            <label>MBTI</label>
                            <select v-model="guestForm.mbti">
                              <option value="">请选择 MBTI</option>
                              <option v-for="type in mbtiOptions" :key="type" :value="type">{{ type }}</option>
                            </select>
                          </div>
                        </div>
                        <div class="form-row">
                          <div class="form-group">
                            <label>职业</label>
                            <input v-model="guestForm.occupation" type="text" />
                          </div>
                          <div class="form-group small">
                            <label>性别</label>
                            <select v-model="guestForm.gender">
                              <option value="male">男</option>
                              <option value="female">女</option>
                            </select>
                          </div>
                          <div class="form-group small">
                            <label>年龄</label>
                            <input v-model.number="guestForm.age" type="number" />
                          </div>
                        </div>
                        <div class="form-group">
                          <label class="voice-label">音色ID</label>
                          <div class="form-row">
                            <input v-model="guestForm.voice_id" type="text" />
                            <button class="btn-icon-label" style="flex: 0 0 auto;" @click="showVoicePicker = !showVoicePicker">列表</button>
                          </div>
                          <transition name="expand">
                            <div v-if="showVoicePicker" class="voice-picker">
                              <div class="voice-header">内置音色</div>
                              <div class="voice-options">
                                <button v-for="v in voicesForCurrentGender" :key="v" 
                                  class="voice-option" 
                                  :class="{ 'voice-option--active': guestForm.voice_id === v }"
                                  @click="selectBuiltinVoice(v)">
                                  {{ v }}
                                </button>
                              </div>
                            </div>
                          </transition>
                        </div>
                        <div class="form-group">
                          <label>核心描述</label>
                          <textarea v-model="guestForm.personality" rows="6" placeholder="性格特点、背景经历..."></textarea>
                        </div>
                      </div>
                      <div class="form-actions">
                        <button class="btn-cancel" @click="cancelEdit">取消</button>
                        <button class="btn-save" :disabled="savingGuest" @click="saveGuest">
                          <span v-if="savingGuest" class="spinner"></span>
                          {{ savingGuest ? '保存中...' : '保存更改' }}
                        </button>
                      </div>
                    </div>

                    <!-- Read-only Detail View -->
                    <div v-else class="guest-bio-box">
                      <span class="bio-label">性格与特征</span>
                      <p class="bio-text">{{ guest.personality || '暂无详细描述...' }}</p>
                    </div>
                  </div>
                </div>
              </transition>
            </div>

            <!-- Add Guest Entry -->
            <div class="guest-card-wrapper">
              <div class="guest-card guest-card--add" @click="addingGuest = !addingGuest">
                <div class="add-content-grid">
                  <div class="add-circle">
                    <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="3">
                      <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
                    </svg>
                  </div>
                  <span class="add-label">添加新嘉宾</span>
                </div>
              </div>

              <transition name="expand">
                <div v-if="addingGuest" class="card-drawer-extension">
                  <!-- AI Generation Panel -->
                  <div class="ai-gen-container">
                    <div class="ai-gen-badge">✨ AI 智能创作嘉宾</div>
                    <textarea v-model="aiDescription" class="ai-gen-textarea" placeholder="例：一位30岁的女性科幻作家，充满想象力..." rows="4"></textarea>
                    
                    <button class="btn-ai-gen-pill" :disabled="generatingGuest || !aiDescription.trim()" @click="generateGuestFromAI">
                      <span v-if="generatingGuest" class="spinner orange"></span>
                      {{ generatingGuest ? '正在创作中...' : 'AI 辅助补全资料' }}
                    </button>
                    
                    <div class="ai-gen-divider"><span>或手动填写</span></div>
                  </div>

                  <div class="edit-form">
                    <div class="form-body">
                      <div class="form-row">
                        <div class="form-group">
                          <label>姓名 *</label>
                          <input v-model="guestForm.name" type="text" />
                        </div>
                        <div class="form-group">
                          <label>MBTI</label>
                          <input v-model="guestForm.mbti" type="text" placeholder="如 INTJ" />
                        </div>
                      </div>
                      <!-- More fields... -->
                    </div>
                    <div class="form-actions">
                      <button class="btn-cancel" @click="cancelAdd">取消</button>
                      <button class="btn-save" :disabled="savingGuest || !guestForm.name.trim()" @click="saveGuest">
                        <span v-if="savingGuest" class="spinner"></span>
                        创建嘉宾
                      </button>
                    </div>
                  </div>
                </div>
              </transition>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- In-page Confirm Dialog -->
    <transition name="confirm-fade">
      <div v-if="confirmDialog.show" class="confirm-overlay" @click.self="cancelRemove">
        <div class="confirm-box">
          <div class="confirm-icon">
            <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3,6 5,6 21,6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
            </svg>
          </div>
          <h4>移除嘉宾</h4>
          <p>确定移除嘉宾「<strong>{{ confirmDialog.name }}</strong>」吗？此操作无法撤销。</p>
          <div class="confirm-actions">
            <button class="confirm-btn-cancel" @click="cancelRemove">取消</button>
            <button class="confirm-btn-ok" @click="confirmRemove">确认移除</button>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>


<script setup>
import { ref, watch, computed, onMounted } from 'vue'

const props = defineProps({
  modelValue: Boolean,
  guests: { type: Array, default: () => [] },
  selectedGuests: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:modelValue', 'save', 'remove', 'update:selectedGuests'])

const savingGuest = ref(false)
const editingGuest = ref(null)
const editingHost = ref(false)
const addingGuest = ref(false)
const expandedBadge = ref(null)

const hostPersona = ref(null)

// In-page confirm dialog
const confirmDialog = ref({ show: false, name: '' })

const mbtiOptions = [
  'INTJ', 'INTP', 'ENTJ', 'ENTP',
  'INFJ', 'INFP', 'ENFJ', 'ENFP',
  'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
  'ISTP', 'ISFP', 'ESTP', 'ESFP'
]

function askRemoveGuest(name) {
  confirmDialog.value = { show: true, name }
}
function confirmRemove() {
  emit('remove', confirmDialog.value.name)
  confirmDialog.value = { show: false, name: '' }
}
function cancelRemove() {
  confirmDialog.value = { show: false, name: '' }
}

function defaultForm() {
  return {
    name: '',
    gender: 'male',
    age: 30,
    mbti: '',
    personality: '',
    occupation: '',
    speaking_style: '',
    stance_bias: '',
    voice_id: '',
    background: ''
  }
}

const guestForm = ref(defaultForm())

// AI generation
const aiDescription = ref('')
const generatingGuest = ref(false)

// Voice library
const voiceLibrary = ref({ male: [], female: [], official_url: 'https://www.minimaxi.com/audio/voices' })
const showVoicePicker = ref(false)

const voicesForCurrentGender = computed(() =>
  guestForm.value.gender === 'female' ? voiceLibrary.value.female : voiceLibrary.value.male
)

async function fetchVoiceLibrary() {
  try {
    const res = await fetch('/api/voices')
    if (res.ok) voiceLibrary.value = await res.json()
  } catch (e) {
    console.warn('Failed to fetch voice library:', e)
  }
}

async function fetchHost() {
  try {
    const res = await fetch('/api/host')
    if (res.ok) hostPersona.value = await res.json()
  } catch (e) {
    console.warn('Failed to fetch host persona:', e)
  }
}

async function generateGuestFromAI() {
  if (!aiDescription.value.trim()) return
  generatingGuest.value = true
  try {
    const res = await fetch('/api/guests/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description: aiDescription.value.trim() })
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err?.detail || 'AI生成失败')
    }
    const profile = await res.json()
    guestForm.value = {
      name: profile.name || '',
      gender: profile.gender || 'male',
      age: profile.age || 30,
      mbti: profile.mbti || '',
      occupation: profile.occupation || '',
      personality: profile.personality || '',
      speaking_style: profile.speaking_style || '',
      stance_bias: profile.stance_bias || '',
      voice_id: profile.voice_id || '',
      background: profile.background || ''
    }
  } catch (e) {
    alert(e.message || 'AI生成失败，请重试')
  } finally {
    generatingGuest.value = false
  }
}

function selectBuiltinVoice(voiceId) {
  guestForm.value.voice_id = voiceId
  showVoicePicker.value = false
}

onMounted(() => {
  fetchHost()
  fetchVoiceLibrary()
})

watch(() => props.modelValue, (val) => {
  if (val) {
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
    resetState()
  }
})

function resetState() {
  editingGuest.value = null
  addingGuest.value = false
  expandedBadge.value = null
  guestForm.value = defaultForm()
  showVoicePicker.value = false
  aiDescription.value = ''
}

function close() {
  emit('update:modelValue', false)
}

function toggleExpand(name) {
  if (expandedBadge.value === name) {
    expandedBadge.value = null
  } else {
    expandedBadge.value = name
    editingGuest.value = null
  }
}

function startEdit(guest) {
  editingGuest.value = guest.name
  editingHost.value = false
  // expandedBadge.value = null // Fix: don't close the extension when editing
  showVoicePicker.value = false
  guestForm.value = {
    name: guest.name,
    gender: guest.gender,
    age: guest.age,
    mbti: guest.mbti,
    personality: guest.personality,
    occupation: guest.occupation,
    speaking_style: guest.speaking_style,
    stance_bias: guest.stance_bias || '',
    voice_id: guest.voice_id || '',
    background: guest.background
  }
}

function startEditHost() {
  editingHost.value = true
  editingGuest.value = null
  expandedBadge.value = 'HOST'
  showVoicePicker.value = false
  const host = hostPersona.value
  guestForm.value = {
    name: host.name,
    gender: host.gender,
    age: host.age,
    mbti: host.mbti,
    personality: host.personality,
    occupation: host.occupation,
    speaking_style: host.speaking_style,
    stance_bias: host.stance_bias || '',
    voice_id: host.voice_id || '',
    background: host.background
  }
}

function cancelEdit() {
  editingGuest.value = null
  editingHost.value = false
  expandedBadge.value = null
}

function startAdd() {
  resetState()
  addingGuest.value = true
  guestForm.value = defaultForm()
}

function cancelAdd() {
  addingGuest.value = false
}

async function saveGuest() {
  if (!guestForm.value.name.trim()) return
  savingGuest.value = true
  try {
    const payload = {
      ...guestForm.value,
      name: guestForm.value.name.trim(),
      mbti: (guestForm.value.mbti || '').trim().toUpperCase(),
      occupation: (guestForm.value.occupation || '').trim(),
      personality: (guestForm.value.personality || '').trim(),
      speaking_style: (guestForm.value.speaking_style || '').trim(),
      stance_bias: (guestForm.value.stance_bias || '').trim(),
      background: (guestForm.value.background || '').trim(),
      voice_id: (guestForm.value.voice_id || '').trim()
    }

    if (editingHost.value) {
      const res = await fetch('/api/host', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (res.ok) {
        hostPersona.value = await res.json()
      } else {
        throw new Error('保存主持資料失败')
      }
    } else {
      emit('save', {
        ...payload,
        isEdit: !!editingGuest.value,
        originalName: editingGuest.value || undefined
      })
    }
    resetState()
  } catch (e) {
    alert(e.message)
  } finally {
    savingGuest.value = false
  }
}

function removeGuest(name) {
  askRemoveGuest(name)
}

function getMbtiColor(mbti) {
  const colors = {
    'INTJ': '#6366f1', 'INTP': '#3b82f6', 'ENTJ': '#f59e0b', 'ENTP': '#ec4899',
    'INFJ': '#10b981', 'INFP': '#14b8a6', 'ENFJ': '#f97316', 'ENFP': '#f43f5e',
    'ISTJ': '#64748b', 'ISFJ': '#8b5cf6', 'ESTJ': '#0ea5e9', 'ESFJ': '#a855f7',
    'ISTP': '#06b6d4', 'ISFP': '#84cc16', 'ESTP': '#f59e0b', 'ESFP': '#fb923c'
  }
  return colors[mbti] || '#6366f1'
}

function getMbtiBg(mbti) {
  const color = getMbtiColor(mbti)
  return `${color}15`
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
</script>

<style scoped>
/* ─── Guest List Layout ─────────────────────────────── */
.guest-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 0.25rem;
}

.guest-card-wrapper {
  position: relative;
  display: flex;
  flex-direction: column;
}

/* ─── Profile Card ──────────────────────────────────── */
.guest-card {
  width: 100%;
  background: var(--c-surface);
  border-radius: var(--r-xl);
  border: 1.5px solid var(--c-border);
  box-shadow: 0 1px 3px rgba(0,0,0,0.02);
  display: flex;
  padding: 0.85rem 1rem;
  cursor: pointer;
  transition: all var(--dur-normal) var(--ease-bounce);
  position: relative;
  gap: 1rem;
  align-items: center;
}

.guest-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--c-primary-soft);
  background: linear-gradient(to bottom right, var(--c-surface), var(--c-bg));
}

.guest-card--expanded {
  border-bottom-left-radius: 4px;
  border-bottom-right-radius: 4px;
  border-color: var(--c-primary);
  z-index: 10;
}

/* Avatar Area */
.avatar-container {
  position: relative;
  flex-shrink: 0;
}

.guest-avatar {
  width: 52px;
  height: 52px;
  border-radius: 18px; /* Squircle */
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.3rem;
  font-weight: 800;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transition: all var(--dur-normal) var(--ease);
}

.guest-card:hover .guest-avatar {
  transform: scale(1.05);
}

/* Card Content */
.guest-card-content {
  flex: 1;
  min-width: 0;
}

.guest-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.25rem;
}

.guest-name {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--c-text-1);
  letter-spacing: -0.01em;
}

.expand-chevron {
  color: var(--c-text-3);
  opacity: 0.5;
  transition: transform 0.3s var(--ease);
}

.guest-card--expanded .expand-chevron {
  transform: rotate(180deg);
}

.guest-role {
  font-size: 0.78rem;
  color: var(--c-text-2);
  margin-bottom: 0.5rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.guest-tags {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.tag-pill {
  font-size: 0.65rem;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 6px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.tag-pill--mbti {
  background: var(--c-primary-soft);
  color: var(--c-primary);
}

.tag-pill--count {
  background: var(--c-bg);
  color: var(--c-text-3);
  border: 1px solid var(--c-border);
}

/* ─── Detail/Edit Container ─────────────────────────── */
.card-drawer-extension {
  margin-top: -4px;
  background: var(--c-surface);
  border: 1.5px solid var(--c-primary);
  border-top: none;
  border-radius: 0 0 var(--r-xl) var(--r-xl);
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0,0,0,0.05);
  animation: slideInDown 0.3s var(--ease-bounce);
}

@keyframes slideInDown {
  from { transform: translateY(-10px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

/* Management Action Bar */
.action-bar {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--c-border);
  background: var(--c-bg);
}

.btn-icon-label {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px;
  border-radius: var(--r-md);
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--dur-fast) ease;
  border: 1.5px solid var(--c-border);
  background: var(--c-surface);
  color: var(--c-text-2);
}

.btn-icon-label:hover {
  border-color: var(--c-primary-soft);
  color: var(--c-primary);
  background: var(--c-primary-soft);
}

.btn-icon-label.danger:hover {
  background: #FFF1F2;
  border-color: #FECDD3;
  color: #E11D48;
}

/* Detail Stats & Bio */
.extension-content {
  padding: 1.25rem 1rem;
}

.guest-bio-box {
  background: var(--c-bg);
  border-radius: var(--r-md);
  padding: 1rem;
}

.bio-label {
  display: block;
  font-size: 0.7rem;
  font-weight: 800;
  color: var(--c-text-3);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
}

.bio-text {
  font-size: 0.88rem;
  line-height: 1.6;
  color: var(--c-text-1);
}

/* ─── Add Guest Card ────────────────────────────────── */
.guest-card--add {
  border: 2px dashed var(--c-border);
  background: var(--c-bg);
  justify-content: center;
  padding: 1.5rem;
  min-height: 100px;
}

.guest-card--add:hover {
  border-color: var(--c-primary);
  background: var(--c-primary-soft);
  color: var(--c-primary);
}

.add-content-grid {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  color: var(--c-text-3);
}

.guest-card--add:hover .add-content-grid {
  color: var(--c-primary);
}

.add-circle {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: 2px solid currentColor;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s var(--ease-bounce);
}

.guest-card--add:hover .add-circle {
  transform: scale(1.1) rotate(90deg);
}

.add-label {
  font-size: 0.9rem;
  font-weight: 700;
}

/* ─── Edit Form ─────────────────────────────────────── */
.edit-form {
  padding: 1.5rem 1rem;
}

.form-body {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-row {
  display: flex;
  gap: 1rem;
}

.form-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--c-text-2);
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 10px 12px;
  border: 1.5px solid var(--c-border);
  border-radius: var(--r-md);
  font-size: 0.9rem;
  background: var(--c-bg);
  transition: all 0.2s ease;
  width: 100%;
}

.form-group textarea {
  min-height: 80px;
  resize: vertical;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--c-primary);
  background: var(--c-surface);
  box-shadow: 0 0 0 4px rgba(255,107,53,0.1);
}

.form-group.small {
  flex: 0 0 85px;
}

.form-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1.5rem;
}

.btn-save {
  flex: 2;
  background: var(--c-primary);
  color: white;
  border: none;
  border-radius: var(--r-lg);
  padding: 12px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: 0 4px 15px rgba(255,107,53,0.2);
}

.btn-cancel {
  flex: 1;
  background: var(--c-bg);
  border: 1.5px solid var(--c-border);
  border-radius: var(--r-lg);
  padding: 12px;
  font-weight: 600;
  cursor: pointer;
}

/* ─── Confirm Transitions ───────────────────────────── */
.confirm-fade-enter-active, .confirm-fade-leave-active { transition: opacity 0.3s ease; }
.confirm-fade-enter-from, .confirm-fade-leave-to { opacity: 0; }

/* Existing standard components... */
.drawer-overlay {
  position: fixed;
  inset: 0;
  background: rgba(45, 27, 14, 0.4);
  backdrop-filter: blur(4px);
  z-index: 1000;
}

.drawer-panel {
  position: fixed;
  top: 0;
  right: 0;
  width: 100%;
  max-width: 540px;
  height: 100%;
  background: var(--c-bg);
  box-shadow: -10px 0 40px rgba(0,0,0,0.15);
  display: flex;
  flex-direction: column;
  z-index: 1001;
  overscroll-behavior: contain;
}

.drawer-header {
  padding: 1.5rem;
  background: var(--c-surface);
  border-bottom: 2px solid var(--c-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-title-group h2 {
  font-size: 1.4rem;
  font-weight: 800;
  color: var(--c-text-1);
}

.header-subtitle {
  font-size: 0.8rem;
  color: var(--c-text-3);
  margin-top: 2px;
}

.btn-close {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  border: 2px solid var(--c-border);
  background: var(--c-bg);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.btn-close:hover {
  background: var(--c-border);
  color: var(--c-text-1);
  transform: rotate(90deg);
}

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.25rem;
}

/* Transitions */
.slide-enter-active, .slide-leave-active { transition: transform 0.5s cubic-bezier(0.16, 1, 0.3, 1); }
.slide-enter-from, .slide-leave-to { transform: translateX(100%); }

.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.expand-enter-active, .expand-leave-active { transition: all 0.3s ease; }
.expand-enter-from, .expand-leave-to { opacity: 0; transform: translateY(-10px); }

/* ─── AI/Voice styles ─────────────────────────────── */
.ai-gen-container {
  margin: 1.25rem 1rem 0.5rem;
  background: #fffcfb;
  border: 1.5px solid #ffefe8;
  border-radius: 1.25rem;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.ai-gen-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  background: var(--c-primary);
  color: white;
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 800;
  width: fit-content;
}

.ai-gen-textarea {
  border: 1px solid var(--c-border);
  border-radius: 10px;
  padding: 10px;
  font-size: 0.85rem;
  background: white;
  resize: none;
  width: 100%;
}

.ai-gen-textarea:focus {
  outline: none;
  border-color: var(--c-primary-soft);
}

.btn-ai-gen-pill {
  width: 100%;
  padding: 10px;
  background: white;
  border: 1.5px solid var(--c-primary);
  color: var(--c-primary);
  border-radius: 12px;
  font-weight: 700;
  font-size: 0.9rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s;
}

.btn-ai-gen-pill:hover:not(:disabled) {
  background: var(--c-primary-soft);
  transform: translateY(-1px);
}

.btn-ai-gen-pill:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ai-gen-divider {
  display: flex;
  align-items: center;
  text-align: center;
  color: var(--c-text-3);
  font-size: 0.75rem;
  font-weight: 600;
}

.ai-gen-divider::before,
.ai-gen-divider::after {
  content: '';
  flex: 1;
  border-bottom: 1px solid var(--c-border);
}

.ai-gen-divider span {
  padding: 0 10px;
}

/* ─── Section Divider ────────────────────────────────── */
.section-divider {
  display: flex;
  align-items: center;
  margin: 1.5rem 0.5rem 0.5rem;
  color: var(--c-text-3);
  font-size: 0.7rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.section-divider::after {
  content: '';
  flex: 1;
  margin-left: 10px;
  height: 1px;
  background: var(--c-border);
}

/* ─── Host Specific ─────────────────────────────────── */
.host-avatar {
  background: linear-gradient(135deg, #fb923c 0%, #ea580c 100%) !important;
  border: 2px solid white;
}

.host-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: var(--c-primary);
  color: white;
  font-size: 0.55rem;
  font-weight: 900;
  padding: 2px 4px;
  border-radius: 4px;
  border: 2px solid var(--c-surface);
}

.host-card {
  border-style: solid;
  border-width: 2px;
  border-color: #ffefe8;
  background: #fffcfb;
}

.host-card:hover { border-color: var(--c-primary-soft); }

.spinner.orange {
  border: 2px solid rgba(255,107,53, 0.2);
  border-top-color: var(--c-primary);
}

.voice-picker {
  margin-top: 0.75rem;
  background: white;
  border: 1.5px solid var(--c-primary-soft);
  border-radius: var(--r-xl);
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
}

.voice-options {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.75rem;
  max-height: 240px;
  overflow-y: auto;
}

.voice-option {
  padding: 10px 12px;
  background: var(--c-bg);
  border: 1.5px solid var(--c-border);
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 500;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--c-text-2);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.voice-option:hover {
  border-color: var(--c-primary-soft);
  background: white;
  color: var(--c-primary);
}

.voice-option--active {
  background: #fffafa;
  color: var(--c-primary);
  border-color: var(--c-primary);
  font-weight: 700;
  box-shadow: 0 2px 8px rgba(255,107,53,0.1);
}

.voice-header {
  padding: 0.5rem 0.75rem;
  background: var(--c-bg);
  border-bottom: 1px solid var(--c-border);
  font-size: 0.65rem;
  font-weight: 800;
  text-transform: uppercase;
  color: var(--c-text-3);
}

/* Spinner */
.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

</style>
