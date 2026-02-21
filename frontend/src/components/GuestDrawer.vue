<template>
  <Teleport to="body">
    <!-- Backdrop -->
    <transition name="fade">
      <div v-if="modelValue" class="drawer-backdrop" @click="close"></div>
    </transition>

    <!-- Drawer -->
    <transition name="slide">
      <div v-if="modelValue" class="drawer-panel">
        <!-- Header -->
        <div class="drawer-header">
          <div class="header-title">
            <div class="header-icon">
              <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 00-3-3.87"/>
                <path d="M16 3.13a4 4 0 010 7.75"/>
              </svg>
            </div>
            <div>
              <h2>嘉宾配置</h2>
              <p>管理播客嘉宾 · 最多选择3位</p>
            </div>
          </div>
          <button class="close-btn" @click="close">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <!-- Content -->
        <div class="drawer-content">
          <div class="badges-list">
            <!-- Guest ID Badges -->
            <div
              v-for="guest in guests"
              :key="guest.name"
              class="id-card-section"
            >
              <!-- Lanyard cord -->
              <div class="badge-lanyard">
                <div class="badge-cord"></div>
                <div class="badge-punch-ring">
                  <div class="badge-punch-hole"></div>
                </div>
              </div>

              <!-- ID Badge -->
              <div
                class="id-badge"
                :class="{
                  'id-badge--selected': selectedGuests.includes(guest.name),
                  'id-badge--expanded': expandedBadge === guest.name || editingGuest === guest.name
                }"
                @click="toggleExpand(guest.name)"
              >
                <!-- Left color accent strip -->
                <div class="id-badge__strip" :style="{ background: getAvatarGradient(guest.mbti) }"></div>

                <!-- Main content area -->
                <div class="id-badge__body">
                  <!-- Header row: org label / selected chip / GUEST type -->
                  <div class="id-badge__header">
                    <span class="id-badge__org">🎙 MindCast</span>
                    <div class="id-badge__header-right">
                      <transition name="chip-pop">
                        <span v-if="selectedGuests.includes(guest.name)" class="id-badge__selected-chip">
                          <svg viewBox="0 0 24 24" width="10" height="10" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20,6 9,17 4,12"/></svg>
                          已选
                        </span>
                      </transition>
                      <span class="id-badge__type">GUEST</span>
                    </div>
                  </div>

                  <div class="id-badge__divider"></div>

                  <!-- Content row: photo + meta -->
                  <div class="id-badge__content">
                    <div class="id-badge__photo" :style="{ background: getAvatarGradient(guest.mbti) }">
                      {{ guest.name.charAt(0) }}
                    </div>
                    <div class="id-badge__meta">
                      <div class="id-badge__name">{{ guest.name }}</div>
                      <div class="id-badge__title">{{ guest.occupation || '播客嘉宾' }}</div>
                      <span
                        class="id-badge__mbti"
                        :style="{ color: getMbtiColor(guest.mbti), background: getMbtiBg(guest.mbti) }"
                      >{{ guest.mbti || '?' }}</span>
                    </div>
                    <!-- Click-to-select area on the right -->
                    <button
                      class="id-badge__select-btn"
                      :class="{ 'id-badge__select-btn--active': selectedGuests.includes(guest.name) }"
                      :style="selectedGuests.includes(guest.name) ? { borderColor: getMbtiColor(guest.mbti), background: getMbtiBg(guest.mbti) } : {}"
                      @click.stop="toggleSelect(guest.name)"
                    >
                      <svg v-if="selectedGuests.includes(guest.name)" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20,6 9,17 4,12"/></svg>
                      <svg v-else viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="4"/></svg>
                    </button>
                  </div>

                  <!-- Footer: barcode decoration -->
                  <div class="id-badge__footer">
                    <div class="id-badge__barcode">
                      <div class="bc-bar" v-for="i in 28" :key="i"></div>
                    </div>
                    <span class="id-badge__serial">#{{ guest.name.charCodeAt(0).toString(16).toUpperCase().padStart(4,'0') }}</span>
                  </div>
                </div>

                <!-- Expand chevron -->
                <div class="id-badge__expand-hint">
                  <svg
                    viewBox="0 0 24 24" width="14" height="14" fill="none"
                    stroke="currentColor" stroke-width="2"
                    :style="{ transform: (expandedBadge === guest.name) ? 'rotate(180deg)' : 'rotate(0)' }"
                  >
                    <polyline points="6,9 12,15 18,9"/>
                  </svg>
                </div>
              </div>

              <!-- Action buttons (shown when expanded) -->
              <div v-if="expandedBadge === guest.name" class="id-badge__actions" @click.stop>
                <button class="btn-action edit" @click="startEdit(guest)">
                  <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                    <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
                  </svg>
                  编辑资料
                </button>
                <button class="btn-action delete" @click="removeGuest(guest.name)">
                  <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3,6 5,6 21,6"/>
                    <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
                  </svg>
                  移除嘉宾
                </button>
              </div>
              
              <!-- Inline Edit Form -->
              <transition name="expand">
                <div v-if="editingGuest === guest.name" class="edit-form">
                  <div class="edit-header">
                    <span class="edit-title">编辑嘉宾</span>
                    <button class="btn-close-form" @click="cancelEdit">
                      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/>
                        <line x1="6" y1="6" x2="18" y2="18"/>
                      </svg>
                    </button>
                  </div>
                  
                  <div class="form-body">
                    <div class="form-row">
                      <div class="form-group">
                        <label>姓名 *</label>
                        <input v-model="guestForm.name" type="text" placeholder="嘉宾姓名" />
                      </div>
                      <div class="form-group">
                        <label>MBTI</label>
                        <input v-model="guestForm.mbti" type="text" placeholder="如 INTJ" />
                      </div>
                    </div>
                    <div class="form-row">
                      <div class="form-group">
                        <label>职业</label>
                        <input v-model="guestForm.occupation" type="text" placeholder="如 AI 算法工程师" />
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
                        <input v-model.number="guestForm.age" type="number" min="18" max="90" />
                      </div>
                    </div>
                    <div class="form-group">
                      <label class="voice-label">
                        音色ID
                        <a href="https://www.minimaxi.com/audio/voices" target="_blank" rel="noopener" class="voice-official-link">
                          <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a3 3 0 00-3 3v4a3 3 0 006 0V5a3 3 0 00-3-3z"/><path d="M19 10v2a7 7 0 01-14 0v-2"/></svg>
                          官方音色库
                        </a>
                      </label>
                      <div class="voice-input-row">
                        <input v-model="guestForm.voice_id" type="text" class="voice-input" placeholder="粘贴自定义音色ID，或从内置列表选择" />
                        <button class="btn-voice-picker" :class="{ 'btn-voice-picker--open': showVoicePicker }" @click.stop="showVoicePicker = !showVoicePicker" title="内置音色列表">
                          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6,9 12,15 18,9"/></svg>
                        </button>
                      </div>
                      <transition name="expand">
                        <div v-if="showVoicePicker" class="voice-picker">
                          <div class="voice-picker-header">内置音色（{{ voicesForCurrentGender.length }} 个 · 按当前性别筛选）</div>
                          <div class="voice-options">
                            <button v-for="v in voicesForCurrentGender" :key="v" class="voice-option" :class="{ 'voice-option--active': guestForm.voice_id === v }" @click="selectBuiltinVoice(v)">
                              <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a3 3 0 00-3 3v4a3 3 0 006 0V5a3 3 0 00-3-3z"/><path d="M19 10v2a7 7 0 01-14 0v-2"/></svg>
                              <span>{{ v }}</span>
                            </button>
                          </div>
                          <a href="https://www.minimaxi.com/audio/voices" target="_blank" rel="noopener" class="voice-more-link">前往官方音色库选更多 →</a>
                        </div>
                      </transition>
                    </div>
                    <div class="form-group">
                      <label>性格特征</label>
                      <textarea v-model="guestForm.personality" rows="2" placeholder="描述嘉宾的性格特点"></textarea>
                    </div>
                    <div class="form-group">
                      <label>说话风格</label>
                      <textarea v-model="guestForm.speaking_style" rows="2" placeholder="描述嘉宾的说话方式"></textarea>
                    </div>
                    <div class="form-group">
                      <label>背景经历</label>
                      <textarea v-model="guestForm.background" rows="2" placeholder="嘉宾的职业背景和经历"></textarea>
                    </div>
                  </div>
                  
                  <div class="form-actions">
                    <button class="btn-cancel" @click="cancelEdit">取消</button>
                    <button class="btn-save" :disabled="savingGuest || !guestForm.name.trim()" @click="saveGuest">
                      <span v-if="savingGuest" class="spinner"></span>
                      {{ savingGuest ? '保存中...' : '保存' }}
                    </button>
                  </div>
                </div>
              </transition>
              
              <!-- Detail View (when expanded but not editing) -->
              <transition name="expand">
                <div v-if="expandedBadge === guest.name && editingGuest !== guest.name" class="detail-view">
                  <div class="detail-stats">
                    <div class="stat">
                      <span class="stat-label">年龄</span>
                      <span class="stat-value">{{ guest.age }}</span>
                    </div>
                    <div class="stat">
                      <span class="stat-label">性别</span>
                      <span class="stat-value">{{ guest.gender === 'male' ? '男' : '女' }}</span>
                    </div>
                    <div class="stat" v-if="guest.voice_id">
                      <span class="stat-label">音色ID</span>
                      <span class="stat-value">{{ guest.voice_id }}</span>
                    </div>
                  </div>
                  <div class="detail-fields" v-if="guest.personality || guest.speaking_style || guest.background">
                    <div class="field" v-if="guest.personality">
                      <span class="field-label">性格特征</span>
                      <p>{{ guest.personality }}</p>
                    </div>
                    <div class="field" v-if="guest.speaking_style">
                      <span class="field-label">说话风格</span>
                      <p>{{ guest.speaking_style }}</p>
                    </div>
                    <div class="field" v-if="guest.background">
                      <span class="field-label">背景经历</span>
                      <p>{{ guest.background }}</p>
                    </div>
                  </div>
                </div>
              </transition>
            </div>

            <!-- Add New Badge -->
            <div class="id-card-section" v-if="!addingGuest">
              <div class="badge-lanyard">
                <div class="badge-cord add-cord"></div>
                <div class="badge-punch-ring add-punch">
                  <div class="badge-punch-hole"></div>
                </div>
              </div>
              <div class="id-badge id-badge--add" @click="startAdd">
                <div class="id-badge__strip add-strip"></div>
                <div class="id-badge__add-content">
                  <div class="id-badge__add-icon">
                    <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8">
                      <line x1="12" y1="5" x2="12" y2="19"/>
                      <line x1="5" y1="12" x2="19" y2="12"/>
                    </svg>
                  </div>
                  <span class="id-badge__add-label">新增嘉宾</span>
                  <span class="id-badge__add-sub">最多可添加 3 位</span>
                </div>
              </div>
            </div>

            <!-- Add Form -->
            <transition name="expand">
              <div v-if="addingGuest" class="add-form-section">
                <div class="badge-lanyard">
                  <div class="badge-cord"></div>
                  <div class="badge-punch-ring">
                    <div class="badge-punch-hole"></div>
                  </div>
                </div>
                <div class="edit-form">
                  <div class="edit-header">
                    <span class="edit-title">新增嘉宾</span>
                    <button class="btn-close-form" @click="cancelAdd">
                      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/>
                        <line x1="6" y1="6" x2="18" y2="18"/>
                      </svg>
                    </button>
                  </div>

                  <!-- AI 智能生成 -->
                  <div class="ai-gen-panel">
                    <div class="ai-gen-header">
                      <div class="ai-gen-badge">
                        <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
                        AI 智能生成
                      </div>
                      <span class="ai-gen-hint">描述你想要的嘉宾，AI 自动填写所有资料</span>
                    </div>
                    <div class="ai-gen-input-row">
                      <textarea
                        v-model="aiDescription"
                        rows="2"
                        class="ai-gen-textarea"
                        placeholder="例如：一位35岁的女性AI产品经理，冷静理性，喜欢用数据说话，对AI商业化有深刻见解"
                      ></textarea>
                      <button
                        class="btn-ai-gen"
                        :disabled="generatingGuest || !aiDescription.trim()"
                        @click="generateGuestFromAI"
                      >
                        <span v-if="generatingGuest" class="spinner"></span>
                        <svg v-else viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="5,12 12,5 19,12"/><polyline points="5,19 12,12 19,19"/></svg>
                        {{ generatingGuest ? '生成中...' : 'AI 生成' }}
                      </button>
                    </div>
                    <div class="ai-gen-divider"><span>或手动填写</span></div>
                  </div>

                  <div class="form-body">
                    <div class="form-row">
                      <div class="form-group">
                        <label>姓名 *</label>
                        <input v-model="guestForm.name" type="text" placeholder="嘉宾姓名" />
                      </div>
                      <div class="form-group">
                        <label>MBTI</label>
                        <input v-model="guestForm.mbti" type="text" placeholder="如 INTJ" />
                      </div>
                    </div>
                    <div class="form-row">
                      <div class="form-group">
                        <label>职业</label>
                        <input v-model="guestForm.occupation" type="text" placeholder="如 AI 算法工程师" />
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
                        <input v-model.number="guestForm.age" type="number" min="18" max="90" />
                      </div>
                    </div>
                    <div class="form-group">
                      <label class="voice-label">
                        音色ID
                        <a href="https://www.minimaxi.com/audio/voices" target="_blank" rel="noopener" class="voice-official-link">
                          <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a3 3 0 00-3 3v4a3 3 0 006 0V5a3 3 0 00-3-3z"/><path d="M19 10v2a7 7 0 01-14 0v-2"/></svg>
                          官方音色库
                        </a>
                      </label>
                      <div class="voice-input-row">
                        <input v-model="guestForm.voice_id" type="text" class="voice-input" placeholder="粘贴自定义音色ID，或从内置列表选择" />
                        <button class="btn-voice-picker" :class="{ 'btn-voice-picker--open': showVoicePicker }" @click.stop="showVoicePicker = !showVoicePicker" title="内置音色列表">
                          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6,9 12,15 18,9"/></svg>
                        </button>
                      </div>
                      <transition name="expand">
                        <div v-if="showVoicePicker" class="voice-picker">
                          <div class="voice-picker-header">内置音色（{{ voicesForCurrentGender.length }} 个 · 按当前性别筛选）</div>
                          <div class="voice-options">
                            <button v-for="v in voicesForCurrentGender" :key="v" class="voice-option" :class="{ 'voice-option--active': guestForm.voice_id === v }" @click="selectBuiltinVoice(v)">
                              <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a3 3 0 00-3 3v4a3 3 0 006 0V5a3 3 0 00-3-3z"/><path d="M19 10v2a7 7 0 01-14 0v-2"/></svg>
                              <span>{{ v }}</span>
                            </button>
                          </div>
                          <a href="https://www.minimaxi.com/audio/voices" target="_blank" rel="noopener" class="voice-more-link">前往官方音色库选更多 →</a>
                        </div>
                      </transition>
                    </div>
                    <div class="form-group">
                      <label>性格特征</label>
                      <textarea v-model="guestForm.personality" rows="2" placeholder="描述嘉宾的性格特点"></textarea>
                    </div>
                    <div class="form-group">
                      <label>说话风格</label>
                      <textarea v-model="guestForm.speaking_style" rows="2" placeholder="描述嘉宾的说话方式"></textarea>
                    </div>
                    <div class="form-group">
                      <label>背景经历</label>
                      <textarea v-model="guestForm.background" rows="2" placeholder="嘉宾的职业背景和经历"></textarea>
                    </div>
                  </div>
                  
                  <div class="form-actions">
                    <button class="btn-cancel" @click="cancelAdd">取消</button>
                    <button class="btn-save" :disabled="savingGuest || !guestForm.name.trim()" @click="saveGuest">
                      <span v-if="savingGuest" class="spinner"></span>
                      {{ savingGuest ? '保存中...' : '添加嘉宾' }}
                    </button>
                  </div>
                </div>
              </div>
            </transition>
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
const addingGuest = ref(false)
const expandedBadge = ref(null)

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

onMounted(() => fetchVoiceLibrary())

watch(() => props.modelValue, (val) => {
  if (!val) {
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

function toggleSelect(name) {
  const current = [...props.selectedGuests]
  const idx = current.indexOf(name)
  if (idx >= 0) {
    current.splice(idx, 1)
  } else {
    if (current.length < 3) {
      current.push(name)
    }
  }
  emit('update:selectedGuests', current)
}

function startEdit(guest) {
  editingGuest.value = guest.name
  expandedBadge.value = null
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

function cancelEdit() {
  editingGuest.value = null
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
    emit('save', { ...payload, isEdit: !!editingGuest.value })
    resetState()
  } finally {
    savingGuest.value = false
  }
}

function removeGuest(name) {
  if (window.confirm(`确定删除嘉宾「${name}」吗？`)) {
    emit('remove', name)
  }
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
/* Base */
.drawer-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  z-index: 1000;
}

.drawer-panel {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  max-width: 480px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  z-index: 1001;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Header */
.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  background: white;
  border-bottom: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 2px 8px rgba(30, 41, 59, 0.3);
}

.header-title h2 {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1e293b;
}

.header-title p {
  font-size: 0.75rem;
  color: #64748b;
}

.close-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: #f1f5f9;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #e2e8f0;
  color: #1e293b;
}

/* Content */
.drawer-content {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

.badges-list {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

/* ─── ID Card Section ─────────────────────────────── */
.id-card-section {
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* Lanyard cord + hole */
.badge-lanyard {
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 2;
  margin-bottom: -10px;
}

.badge-cord {
  width: 2px;
  height: 28px;
  background: linear-gradient(180deg, transparent 0%, #94a3b8 40%, #64748b 100%);
}

.add-cord {
  background: linear-gradient(180deg, transparent 0%, #a5b4fc 40%, #818cf8 100%);
}

.badge-punch-ring {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: linear-gradient(135deg, #cbd5e1 0%, #94a3b8 100%);
  box-shadow: 0 1px 4px rgba(0,0,0,0.25), inset 0 1px 2px rgba(255,255,255,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
}

.add-punch {
  background: linear-gradient(135deg, #c7d2fe 0%, #818cf8 100%);
}

.badge-punch-hole {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #e2e8f0;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
}

/* ─── ID Badge ─────────────────────────────────────── */
.id-badge {
  width: 100%;
  background: #ffffff;
  border-radius: 14px;
  border: 1.5px solid #e2e8f0;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06), 0 0 0 0 transparent;
  display: flex;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.id-badge:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.1);
  border-color: #c7d2fe;
}

.id-badge--selected {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.12), 0 4px 16px rgba(99,102,241,0.15);
  background: linear-gradient(135deg, #ffffff 0%, #f5f3ff 100%);
}

.id-badge--expanded {
  border-color: #6366f1;
  border-bottom-left-radius: 4px;
  border-bottom-right-radius: 4px;
}

/* Left accent strip */
.id-badge__strip {
  width: 6px;
  flex-shrink: 0;
}

/* Badge body */
.id-badge__body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  padding: 0.55rem 0.75rem 0.45rem 0.7rem;
}

/* Header row */
.id-badge__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.3rem;
}

.id-badge__org {
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #475569;
  text-transform: uppercase;
}

.id-badge__header-right {
  display: flex;
  align-items: center;
  gap: 5px;
}

.id-badge__type {
  font-size: 0.58rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  color: #94a3b8;
  text-transform: uppercase;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  padding: 1px 5px;
}

.id-badge__selected-chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 0.6rem;
  font-weight: 700;
  color: #6366f1;
  background: #ede9fe;
  border: 1px solid #c4b5fd;
  border-radius: 4px;
  padding: 1px 5px;
}

/* Divider */
.id-badge__divider {
  height: 1px;
  background: linear-gradient(90deg, #e2e8f0 60%, transparent 100%);
  margin-bottom: 0.4rem;
}

/* Content row */
.id-badge__content {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  flex: 1;
}

.id-badge__photo {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255,255,255,0.95);
  font-size: 1.15rem;
  font-weight: 800;
  letter-spacing: -0.01em;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

.id-badge__meta {
  flex: 1;
  min-width: 0;
}

.id-badge__name {
  font-size: 0.95rem;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.2;
  margin-bottom: 0.15rem;
  letter-spacing: -0.01em;
}

.id-badge__title {
  font-size: 0.72rem;
  color: #475569;
  line-height: 1.3;
  margin-bottom: 0.3rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.id-badge__mbti {
  display: inline-block;
  font-size: 0.65rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  border-radius: 5px;
  padding: 2px 7px;
}

/* Select button */
.id-badge__select-btn {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  border: 1.5px solid #e2e8f0;
  background: #f8fafc;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.2s;
}

.id-badge__select-btn:hover {
  border-color: #818cf8;
  color: #6366f1;
  background: #f5f3ff;
}

.id-badge__select-btn--active {
  color: #6366f1;
}

/* Footer barcode */
.id-badge__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 0.45rem;
  padding-top: 0.35rem;
  border-top: 1px dashed #e2e8f0;
}

.id-badge__barcode {
  display: flex;
  align-items: flex-end;
  gap: 1.5px;
  height: 16px;
}

.bc-bar {
  width: 2px;
  background: #94a3b8;
  border-radius: 1px;
  height: 10px;
}
.bc-bar:nth-child(3n)   { height: 16px; width: 1px; }
.bc-bar:nth-child(5n)   { height: 8px; }
.bc-bar:nth-child(7n)   { height: 14px; }
.bc-bar:nth-child(2n)   { width: 1px; background: #cbd5e1; }
.bc-bar:nth-child(11n)  { height: 12px; width: 3px; }
.bc-bar:nth-child(13n)  { height: 16px; }

.id-badge__serial {
  font-size: 0.58rem;
  font-family: monospace;
  letter-spacing: 0.05em;
  color: #94a3b8;
  font-weight: 600;
}

/* Expand chevron */
.id-badge__expand-hint {
  position: absolute;
  bottom: 6px;
  right: 10px;
  color: #94a3b8;
  transition: transform 0.2s;
  pointer-events: none;
}

/* ─── Action Buttons (below card) ───────────────────── */
.id-badge__actions {
  width: 100%;
  display: flex;
  gap: 0.5rem;
  margin-top: -4px;
  padding: 0.6rem 0.75rem 0.75rem;
  background: white;
  border: 1.5px solid #6366f1;
  border-top: none;
  border-radius: 0 0 12px 12px;
  box-shadow: 0 4px 12px rgba(99,102,241,0.1);
}

.btn-action {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 9px;
  border-radius: 9px;
  font-size: 0.78rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-action.edit {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  color: #475569;
}
.btn-action.edit:hover { background: #e2e8f0; color: #1e293b; }

.btn-action.delete {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
}
.btn-action.delete:hover { background: #fee2e2; color: #b91c1c; }

/* ─── Add Badge ─────────────────────────────────────── */
.id-badge--add {
  border: 2px dashed #c7d2fe;
  background: linear-gradient(135deg, #f8fafc 0%, #f5f3ff 100%);
  min-height: 80px;
}

.id-badge--add:hover {
  border-color: #818cf8;
  background: linear-gradient(135deg, #f0f1fe 0%, #ede9fe 100%);
  transform: translateY(-2px);
}

.add-strip {
  background: linear-gradient(180deg, #818cf8 0%, #6366f1 100%);
  opacity: 0.6;
}

.id-badge__add-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 1rem;
  color: #6366f1;
}

.id-badge__add-icon {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  border: 1.5px dashed #818cf8;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  color: #6366f1;
  transition: all 0.2s;
}

.id-badge--add:hover .id-badge__add-icon {
  background: #6366f1;
  color: white;
  border-color: #6366f1;
}

.id-badge__add-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #6366f1;
}

.id-badge__add-sub {
  font-size: 0.68rem;
  color: #818cf8;
}

/* Add form section wrapper */
/* Add form section wrapper */
.add-form-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}

/* Chip pop animation */
.chip-pop-enter-active { transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1); }
.chip-pop-leave-active { transition: all 0.15s ease; }
.chip-pop-enter-from  { opacity: 0; transform: scale(0.6); }
.chip-pop-leave-to    { opacity: 0; transform: scale(0.8); }

/* Detail View */
.detail-view {
  width: 100%;
  margin-top: -12px;
  padding: 1rem 1.25rem 1.25rem;
  background: white;
  border: 2px solid #6366f1;
  border-top: none;
  border-radius: 0 0 12px 12px;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.1);
}

.detail-stats {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.stat {
  flex: 1;
  background: #f8fafc;
  padding: 0.5rem;
  border-radius: 8px;
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 0.65rem;
  color: #94a3b8;
  margin-bottom: 2px;
}

.stat-value {
  font-size: 0.85rem;
  font-weight: 600;
  color: #1e293b;
}

.detail-fields {
  padding-top: 0.75rem;
  border-top: 1px solid #e2e8f0;
}

.field {
  margin-bottom: 0.5rem;
}

.field-label {
  display: block;
  font-size: 0.7rem;
  font-weight: 500;
  color: #64748b;
  margin-bottom: 0.25rem;
}

.field p {
  font-size: 0.8rem;
  color: #1e293b;
  line-height: 1.4;
  background: #f8fafc;
  padding: 0.5rem;
  border-radius: 6px;
}

/* Edit Form */
.edit-form {
  width: 100%;
  margin-top: -12px;
  padding: 1.25rem;
  background: white;
  border: 2px solid #6366f1;
  border-top: none;
  border-radius: 0 0 12px 12px;
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.15);
}

.edit-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #e2e8f0;
}

.edit-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: #1e293b;
}

.btn-close-form {
  width: 28px;
  height: 28px;
  border: none;
  background: #f1f5f9;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  cursor: pointer;
}

.form-body {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.form-row {
  display: flex;
  gap: 0.75rem;
}

.form-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-group.small {
  flex: 0 0 70px;
}

.form-group label {
  font-size: 0.7rem;
  font-weight: 500;
  color: #64748b;
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 8px 10px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.85rem;
  color: #1e293b;
  background: #f8fafc;
  transition: all 0.2s;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #6366f1;
  background: white;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.form-group textarea {
  resize: none;
}

.form-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.btn-cancel {
  flex: 1;
  padding: 10px;
  border: 1px solid #e2e8f0;
  background: white;
  border-radius: 10px;
  font-size: 0.85rem;
  font-weight: 500;
  color: #64748b;
  cursor: pointer;
}

.btn-cancel:hover {
  background: #f8fafc;
}

.btn-save {
  flex: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px;
  border: none;
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  border-radius: 10px;
  font-size: 0.85rem;
  font-weight: 600;
  color: white;
  cursor: pointer;
}

.btn-save:disabled {
  opacity: 0.6;
}

.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Transitions */
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.slide-enter-active, .slide-leave-active { transition: transform 0.3s; }
.slide-enter-from, .slide-leave-to { transform: translateX(100%); }

.expand-enter-active, .expand-leave-active { transition: all 0.25s ease; }
.expand-enter-from, .expand-leave-to { opacity: 0; transform: translateY(-10px); }

/* Responsive */
@media (max-width: 500px) {
  .drawer-panel { max-width: 100%; }
  .form-row { flex-direction: column; }
  .form-group.small { flex: 1; }
}

/* ─── AI Generation Panel ─────────────────────────────── */
.ai-gen-panel {
  margin: 0 1.25rem 0;
  background: linear-gradient(135deg, rgba(99,102,241,0.06) 0%, rgba(168,85,247,0.06) 100%);
  border: 1px dashed rgba(99,102,241,0.3);
  border-radius: 12px;
  padding: 0.875rem 1rem;
}

.ai-gen-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 0.6rem;
}

.ai-gen-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
  color: white;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 6px;
  white-space: nowrap;
}

.ai-gen-hint {
  font-size: 0.72rem;
  color: #64748b;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ai-gen-input-row {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.ai-gen-textarea {
  flex: 1;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 0.8rem;
  font-family: inherit;
  resize: none;
  background: white;
  transition: border-color 0.2s;
  line-height: 1.5;
  color: #1e293b;
}

.ai-gen-textarea:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.12);
}

.btn-ai-gen {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  white-space: nowrap;
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  align-self: flex-start;
  margin-top: 1px;
}

.btn-ai-gen:hover:not(:disabled) {
  box-shadow: 0 3px 10px rgba(99,102,241,0.35);
  transform: translateY(-1px);
}

.btn-ai-gen:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  transform: none;
}

.ai-gen-divider {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 0.75rem;
  color: #94a3b8;
  font-size: 0.72rem;
}

.ai-gen-divider::before,
.ai-gen-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: rgba(99,102,241,0.2);
}

/* ─── Voice Picker ────────────────────────────────────── */
.voice-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.voice-official-link {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 0.7rem;
  font-weight: 500;
  color: #6366f1;
  text-decoration: none;
  margin-left: auto;
  padding: 1px 6px;
  border-radius: 4px;
  border: 1px solid rgba(99,102,241,0.25);
  transition: all 0.15s;
}

.voice-official-link:hover {
  background: rgba(99,102,241,0.08);
  border-color: #6366f1;
}

.voice-input-row {
  display: flex;
  gap: 6px;
}

.voice-input {
  flex: 1;
}

.btn-voice-picker {
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-voice-picker:hover,
.btn-voice-picker--open {
  border-color: #6366f1;
  color: #6366f1;
  background: rgba(99,102,241,0.06);
}

.btn-voice-picker svg {
  transition: transform 0.2s;
}

.btn-voice-picker--open svg {
  transform: rotate(180deg);
}

.voice-picker {
  margin-top: 6px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: white;
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
  overflow: hidden;
}

.voice-picker-header {
  padding: 8px 12px;
  font-size: 0.7rem;
  font-weight: 600;
  color: #64748b;
  background: #f8fafc;
  border-bottom: 1px solid #f1f5f9;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

.voice-options {
  display: flex;
  flex-direction: column;
  padding: 4px;
  gap: 2px;
  max-height: 180px;
  overflow-y: auto;
}

.voice-option {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 6px 8px;
  border: none;
  background: transparent;
  border-radius: 7px;
  font-size: 0.78rem;
  color: #374151;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s;
}

.voice-option:hover {
  background: #f1f5f9;
  color: #1e293b;
}

.voice-option--active {
  background: rgba(99,102,241,0.1);
  color: #6366f1;
  font-weight: 500;
}

.voice-option span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.voice-more-link {
  display: block;
  padding: 8px 12px;
  font-size: 0.75rem;
  color: #6366f1;
  text-decoration: none;
  border-top: 1px solid #f1f5f9;
  text-align: center;
  font-weight: 500;
  transition: background 0.15s;
}

.voice-more-link:hover {
  background: rgba(99,102,241,0.05);
}
</style>
