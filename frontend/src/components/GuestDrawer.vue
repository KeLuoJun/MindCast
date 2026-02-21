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
            <!-- Guest Badges -->
            <div
              v-for="guest in guests"
              :key="guest.name"
              class="badge-section"
            >
              <!-- Lanyard -->
              <div class="lanyard-container">
                <div class="lanyard-ribbon">
                  <div class="lanyard-hole"></div>
                </div>
                <div class="lanyard-clip">
                  <div class="clip-inner"></div>
                </div>
              </div>
              
              <!-- Badge Card -->
              <div 
                class="badge-card" 
                :class="{ 
                  selected: selectedGuests.includes(guest.name),
                  expanded: expandedBadge === guest.name || editingGuest === guest.name
                }"
                @click="toggleExpand(guest.name)"
              >
                <div class="badge-inner">
                  <!-- Avatar with ring -->
                  <div class="avatar-container">
                    <div class="avatar-ring" :style="{ borderColor: getMbtiColor(guest.mbti) }">
                      <div class="badge-avatar" :style="{ background: getAvatarGradient(guest.mbti) }">
                        {{ guest.name.charAt(0) }}
                      </div>
                    </div>
                    <div v-if="selectedGuests.includes(guest.name)" class="selected-badge">
                      <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="3">
                        <polyline points="20,6 9,17 4,12"/>
                      </svg>
                    </div>
                  </div>
                  
                  <!-- Info -->
                  <div class="badge-info">
                    <h3>{{ guest.name }}</h3>
                    <div class="badge-tags">
                      <span class="tag mbti" :style="{ background: getMbtiBg(guest.mbti) }">{{ guest.mbti || 'MBTI' }}</span>
                      <span class="tag occupation">{{ guest.occupation || '职业' }}</span>
                    </div>
                  </div>
                </div>
                
                <!-- Actions (visible when expanded) -->
                <div v-if="expandedBadge === guest.name" class="badge-actions" @click.stop>
                  <button class="btn-action edit" @click="startEdit(guest)">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                      <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                    编辑
                  </button>
                  <button class="btn-action delete" @click="removeGuest(guest.name)">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="3,6 5,6 21,6"/>
                      <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
                    </svg>
                    删除
                  </button>
                </div>
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
                      <label>音色ID</label>
                      <input v-model="guestForm.voice_id" type="text" placeholder="可选" />
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

            <!-- Add New Section -->
            <div class="badge-section" v-if="!addingGuest">
              <div class="lanyard-container">
                <div class="lanyard-ribbon add-ribbon">
                  <div class="lanyard-hole"></div>
                </div>
                <div class="lanyard-clip">
                  <div class="clip-inner"></div>
                </div>
              </div>
              <div class="badge-card add-card" @click="startAdd">
                <div class="add-content">
                  <div class="add-icon">
                    <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
                      <line x1="12" y1="5" x2="12" y2="19"/>
                      <line x1="5" y1="12" x2="19" y2="12"/>
                    </svg>
                  </div>
                  <span>新增嘉宾</span>
                </div>
              </div>
            </div>

            <!-- Add Form -->
            <transition name="expand">
              <div v-if="addingGuest" class="add-form-section">
                <div class="lanyard-container">
                  <div class="lanyard-ribbon">
                    <div class="lanyard-hole"></div>
                  </div>
                  <div class="lanyard-clip">
                    <div class="clip-inner"></div>
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
                      <label>音色ID</label>
                      <input v-model="guestForm.voice_id" type="text" placeholder="可选" />
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
import { ref, watch } from 'vue'

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
  expandedBadge.value = null
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
  gap: 1.5rem;
}

/* Badge Section */
.badge-section {
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* Lanyard - Premium Design */
.lanyard-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: -20px;
  z-index: 10;
}

.lanyard-ribbon {
  width: 60px;
  height: 36px;
  background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
  clip-path: polygon(20% 0%, 80% 0%, 100% 100%, 0% 100%);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 6px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.lanyard-ribbon.add-ribbon {
  background: linear-gradient(180deg, #6366f1 0%, #4f46e5 100%);
}

.lanyard-hole {
  width: 14px;
  height: 14px;
  background: linear-gradient(180deg, #f1f5f9 0%, #cbd5e1 100%);
  border-radius: 50%;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
}

.lanyard-clip {
  width: 24px;
  height: 16px;
  background: linear-gradient(180deg, #fbbf24 0%, #d97706 100%);
  border-radius: 0 0 4px 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.clip-inner {
  width: 10px;
  height: 6px;
  background: linear-gradient(180deg, #fcd34d 0%, #fbbf24 100%);
  border-radius: 2px;
}

/* Badge Card */
.badge-card {
  width: 100%;
  background: white;
  border-radius: 16px;
  padding: 1rem 1.25rem;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 4px 12px rgba(0, 0, 0, 0.03);
  border: 2px solid transparent;
}

.badge-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15), 0 8px 24px rgba(0, 0, 0, 0.08);
}

.badge-card.selected {
  border-color: #6366f1;
  background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
}

.badge-card.expanded {
  border-color: #6366f1;
  border-bottom-left-radius: 4px;
  border-bottom-right-radius: 4px;
}

.badge-inner {
  display: flex;
  align-items: center;
  gap: 1rem;
}

/* Avatar */
.avatar-container {
  position: relative;
}

.avatar-ring {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  border: 3px solid;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
}

.badge-avatar {
  width: 46px;
  height: 46px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.25rem;
  font-weight: 700;
}

.selected-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  width: 20px;
  height: 20px;
  background: #6366f1;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(99, 102, 241, 0.4);
}

/* Info */
.badge-info {
  flex: 1;
  min-width: 0;
}

.badge-info h3 {
  font-size: 1rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 0.35rem;
}

.badge-tags {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tag {
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 0.7rem;
  font-weight: 600;
}

.tag.mbti {
  color: #6366f1;
}

.tag.occupation {
  background: #f1f5f9;
  color: #64748b;
}

/* Actions */
.badge-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.btn-action {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px;
  border-radius: 10px;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-action.edit {
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  color: #475569;
}

.btn-action.edit:hover {
  background: #e2e8f0;
  color: #1e293b;
}

.btn-action.delete {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
}

.btn-action.delete:hover {
  background: #fee2e2;
  color: #b91c1c;
}

/* Add Card */
.add-card {
  border: 2px dashed #cbd5e1;
  background: #f8fafc;
}

.add-card:hover {
  border-color: #6366f1;
  background: #f5f3ff;
}

.add-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  color: #64748b;
}

.add-icon {
  width: 40px;
  height: 40px;
  background: white;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #e2e8f0;
}

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
</style>
