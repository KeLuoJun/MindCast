<template>
  <Teleport to="body">
    <transition name="fade">
      <div v-if="modelValue" class="settings-backdrop" @click="close"></div>
    </transition>
    <transition name="slide">
      <div v-if="modelValue" class="settings-panel">
        <!-- Header -->
        <div class="settings-header">
          <div class="settings-header-title">
            <div class="settings-icon-wrap">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="3"/>
                <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/>
              </svg>
            </div>
            <div>
              <h2>系统配置</h2>
              <p>API Keys · 模型参数 · 服务地址</p>
            </div>
          </div>
          <button class="close-btn" @click="close">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <!-- Content -->
        <div class="settings-content">
          <div v-if="loading" class="settings-loading">
            <div class="loading-spinner"></div>
            <span>加载配置中…</span>
          </div>

          <template v-else>
            <!-- LLM -->
            <div class="settings-section">
              <div class="section-label">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8m-4-4v4"/></svg>
                LLM 配置（DeepSeek / OpenAI 兼容）
              </div>
              <div class="field-group">
                <div class="field">
                  <label>API Base URL</label>
                  <input v-model="form.llm_base_url" type="text" placeholder="https://api.deepseek.com/v1" />
                </div>
                <div class="field">
                  <label>API Key</label>
                  <div class="key-input-wrap">
                    <input
                      v-model="form.llm_api_key"
                      :type="showKeys.llm ? 'text' : 'password'"
                      placeholder="输入新的 API Key（留空保持不变）"
                      class="key-input"
                      autocomplete="new-password"
                    />
                    <button class="btn-eye" @click="showKeys.llm = !showKeys.llm" title="显示/隐藏">
                      <svg v-if="showKeys.llm" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                      <svg v-else viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                    </button>
                  </div>
                  <span v-if="isMasked(originals.llm_api_key)" class="field-hint">已设置（**** 表示已保存，输入新值可更新）</span>
                </div>
                <div class="field">
                  <label>模型名称</label>
                  <input v-model="form.llm_model" type="text" placeholder="deepseek-chat" />
                </div>
              </div>
            </div>

            <!-- Tavily -->
            <div class="settings-section">
              <div class="section-label">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                Tavily 资讯搜索
              </div>
              <div class="field-group">
                <div class="field">
                  <label>API Key</label>
                  <div class="key-input-wrap">
                    <input
                      v-model="form.tavily_api_key"
                      :type="showKeys.tavily ? 'text' : 'password'"
                      placeholder="输入新的 API Key（留空保持不变）"
                      class="key-input"
                      autocomplete="new-password"
                    />
                    <button class="btn-eye" @click="showKeys.tavily = !showKeys.tavily" title="显示/隐藏">
                      <svg v-if="showKeys.tavily" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                      <svg v-else viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                    </button>
                  </div>
                  <span v-if="isMasked(originals.tavily_api_key)" class="field-hint">已设置（输入新值可更新）</span>
                </div>
              </div>
            </div>

            <!-- MiniMax TTS -->
            <div class="settings-section">
              <div class="section-label">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a3 3 0 00-3 3v7a3 3 0 006 0V5a3 3 0 00-3-3z"/><path d="M19 10v2a7 7 0 01-14 0v-2"/><line x1="12" y1="19" x2="12" y2="22"/></svg>
                MiniMax TTS 语音合成
              </div>
              <div class="field-group">
                <div class="field">
                  <label>API Key</label>
                  <div class="key-input-wrap">
                    <input
                      v-model="form.minimax_api_key"
                      :type="showKeys.minimax ? 'text' : 'password'"
                      placeholder="输入新的 API Key（留空保持不变）"
                      class="key-input"
                      autocomplete="new-password"
                    />
                    <button class="btn-eye" @click="showKeys.minimax = !showKeys.minimax" title="显示/隐藏">
                      <svg v-if="showKeys.minimax" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                      <svg v-else viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                    </button>
                  </div>
                  <span v-if="isMasked(originals.minimax_api_key)" class="field-hint">已设置（输入新值可更新）</span>
                </div>
                <div class="field">
                  <label>TTS 模型</label>
                  <input v-model="form.minimax_tts_model" type="text" placeholder="speech-2.8-hd" />
                </div>
                <div class="field">
                  <label>API Base URL</label>
                  <input v-model="form.minimax_tts_base_url" type="text" placeholder="https://api.minimaxi.com/v1/t2a_v2" />
                </div>
              </div>
            </div>

          </template>
        </div>

        <!-- Footer -->
        <div class="settings-footer">
          <button class="btn-reset" @click="loadSettings" :disabled="loading || saving">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 102.13-9.36L1 10"/></svg>
            重新加载
          </button>
          <div class="footer-actions">
            <button class="btn-cancel" @click="close" :disabled="saving">取消</button>
            <button class="btn-save" @click="saveSettings" :disabled="loading || saving">
              <span v-if="saving" class="spinner"></span>
              <svg v-else viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20,6 9,17 4,12"/></svg>
              {{ saving ? '保存中...' : '保存配置' }}
            </button>
          </div>
        </div>

        <!-- Toast -->
        <transition name="toast-slide">
          <div v-if="toast.show" :class="['settings-toast', `settings-toast--${toast.type}`]">
            <svg v-if="toast.type === 'success'" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20,6 9,17 4,12"/></svg>
            <svg v-else viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            {{ toast.text }}
          </div>
        </transition>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({ modelValue: Boolean })
const emit = defineEmits(['update:modelValue'])

const loading = ref(false)
const saving = ref(false)
const toast = ref({ show: false, type: 'success', text: '' })

const originals = ref({})

const form = ref({
  llm_base_url: '',
  llm_api_key: '',
  llm_model: '',
  tavily_api_key: '',
  minimax_api_key: '',
  minimax_tts_model: '',
  minimax_tts_base_url: '',
})

const showKeys = ref({ llm: false, tavily: false, minimax: false })

function isMasked(val) {
  return val && val.includes('****')
}

function close() {
  emit('update:modelValue', false)
}

function showToast(text, type = 'success') {
  toast.value = { show: true, type, text }
  setTimeout(() => { toast.value.show = false }, 3000)
}

async function loadSettings() {
  loading.value = true
  try {
    const res = await fetch('/api/settings')
    if (!res.ok) throw new Error('加载失败')
    const data = await res.json()
    originals.value = { ...data }
    form.value = {
      llm_base_url: data.llm_base_url || '',
      llm_api_key: data.llm_api_key || '',   // masked value shown as placeholder hint
      llm_model: data.llm_model || '',
      tavily_api_key: data.tavily_api_key || '',
      minimax_api_key: data.minimax_api_key || '',
      minimax_tts_model: data.minimax_tts_model || '',
      minimax_tts_base_url: data.minimax_tts_base_url || '',
    }
    // Clear key fields so user can type new values; masked values are shown via hint
    if (isMasked(form.value.llm_api_key)) form.value.llm_api_key = ''
    if (isMasked(form.value.tavily_api_key)) form.value.tavily_api_key = ''
    if (isMasked(form.value.minimax_api_key)) form.value.minimax_api_key = ''
  } catch (e) {
    showToast('加载配置失败：' + e.message, 'error')
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  try {
    const patch = {}
    if (form.value.llm_base_url) patch.llm_base_url = form.value.llm_base_url
    if (form.value.llm_api_key && !form.value.llm_api_key.includes('****')) patch.llm_api_key = form.value.llm_api_key
    if (form.value.llm_model) patch.llm_model = form.value.llm_model
    if (form.value.tavily_api_key && !form.value.tavily_api_key.includes('****')) patch.tavily_api_key = form.value.tavily_api_key
    if (form.value.minimax_api_key && !form.value.minimax_api_key.includes('****')) patch.minimax_api_key = form.value.minimax_api_key
    if (form.value.minimax_tts_model) patch.minimax_tts_model = form.value.minimax_tts_model
    if (form.value.minimax_tts_base_url) patch.minimax_tts_base_url = form.value.minimax_tts_base_url

    const res = await fetch('/api/settings', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patch),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err?.detail || '保存失败')
    }
    showToast('配置已保存')
    await loadSettings()
  } catch (e) {
    showToast('保存失败：' + e.message, 'error')
  } finally {
    saving.value = false
  }
}

watch(() => props.modelValue, (val) => {
  if (val) {
    showKeys.value = { llm: false, tavily: false, minimax: false }
    loadSettings()
  }
})
</script>

<style scoped>
/* ── Panel ── */
.settings-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(45, 27, 14, 0.35);
  backdrop-filter: blur(6px);
  z-index: 1000;
}

.settings-panel {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  max-width: 440px;
  background: linear-gradient(180deg, var(--c-bg) 0%, var(--c-bg-warm) 100%);
  z-index: 1001;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ── Header ── */
.settings-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  background: var(--c-surface);
  border-bottom: 2px solid var(--c-border);
  box-shadow: 0 1px 4px rgba(45, 27, 14, 0.06);
  flex-shrink: 0;
}

.settings-header-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.settings-icon-wrap {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, var(--c-primary) 0%, var(--c-primary-hover) 100%);
  border-radius: var(--r-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 2px 8px rgba(255, 107, 53, 0.3);
  flex-shrink: 0;
}

.settings-header-title h2 {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--c-text-1);
  margin: 0;
}

.settings-header-title p {
  font-size: 0.72rem;
  color: var(--c-text-3);
  margin: 0;
}

.close-btn {
  width: 36px;
  height: 36px;
  border: 2px solid var(--c-border);
  background: var(--c-surface);
  border-radius: var(--r-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-text-3);
  cursor: pointer;
  transition: all var(--dur-fast) ease;
  flex-shrink: 0;
}

.close-btn:hover {
  background: var(--c-bg);
  border-color: var(--c-primary);
  color: var(--c-primary);
}

/* ── Content ── */
.settings-content {
  flex: 1;
  overflow-y: auto;
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.settings-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 3rem 0;
  color: var(--c-text-3);
  font-size: 0.85rem;
}

.loading-spinner {
  width: 28px;
  height: 28px;
  border: 3px solid var(--c-border);
  border-top-color: var(--c-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* ── Section ── */
.settings-section {
  background: var(--c-surface);
  border-radius: var(--r-lg);
  border: 2px solid var(--c-border);
  overflow: hidden;
  box-shadow: var(--shadow-card);
}

.section-label {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 10px 14px;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--c-text-2);
  background: var(--c-bg);
  border-bottom: 2px solid var(--c-border);
  flex-wrap: wrap;
  row-gap: 4px;
}

.section-label svg {
  color: var(--c-primary);
}

.field-group {
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.field label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--c-text-1);
}

.field input {
  width: 100%;
  height: 38px;
  border: 2px solid var(--c-border);
  border-radius: var(--r-sm);
  padding: 0 10px;
  font-size: 0.82rem;
  font-family: inherit;
  color: var(--c-text-1);
  background: var(--c-surface);
  transition: border-color var(--dur-fast) ease, box-shadow var(--dur-fast) ease;
  box-sizing: border-box;
}

.field input:focus {
  outline: none;
  border-color: var(--c-primary);
  box-shadow: var(--shadow-focus);
  background: var(--c-surface);
}

.key-input-wrap {
  display: flex;
  gap: 6px;
}

.key-input {
  flex: 1;
  font-family: 'Courier New', monospace;
  font-size: 0.8rem !important;
  letter-spacing: 0.05em;
}

.btn-eye {
  width: 38px;
  height: 38px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--c-border);
  border-radius: var(--r-sm);
  background: var(--c-bg);
  color: var(--c-text-3);
  cursor: pointer;
  transition: all var(--dur-fast) ease;
}

.btn-eye:hover {
  border-color: var(--c-primary);
  color: var(--c-primary);
  background: var(--c-primary-soft);
}

.field-hint {
  font-size: 0.7rem;
  color: var(--c-text-3);
  font-style: italic;
}

/* ── Notice ── */
.settings-notice {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  background: var(--c-primary-soft);
  border: 2px solid rgba(255, 107, 53, 0.15);
  border-radius: var(--r-md);
  font-size: 0.75rem;
  color: var(--c-text-2);
  line-height: 1.5;
}

.settings-notice svg {
  flex-shrink: 0;
  margin-top: 1px;
  color: var(--c-primary);
}

.settings-notice code {
  font-family: 'Courier New', monospace;
  background: rgba(255, 107, 53, 0.12);
  padding: 0 4px;
  border-radius: 3px;
  color: var(--c-primary);
  font-weight: 600;
}

/* ── Footer ── */
.settings-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  background: var(--c-surface);
  border-top: 2px solid var(--c-border);
  flex-shrink: 0;
}

.footer-actions {
  display: flex;
  gap: 8px;
}

.btn-reset {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 8px 14px;
  border: 2px solid var(--c-border);
  border-radius: var(--r-full);
  background: var(--c-surface);
  font-size: 0.8rem;
  color: var(--c-text-2);
  cursor: pointer;
  transition: all var(--dur-fast) ease;
}

.btn-reset:hover:not(:disabled) {
  border-color: var(--c-primary);
  color: var(--c-primary);
  background: var(--c-primary-soft);
}

.btn-reset:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-cancel {
  padding: 8px 16px;
  border: 2px solid var(--c-border);
  border-radius: var(--r-full);
  background: var(--c-surface);
  font-size: 0.82rem;
  color: var(--c-text-2);
  cursor: pointer;
  transition: all var(--dur-fast) ease;
}

.btn-cancel:hover:not(:disabled) {
  background: var(--c-bg);
  border-color: var(--c-text-3);
}

.btn-save {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  border: none;
  border-radius: var(--r-full);
  background: linear-gradient(135deg, var(--c-primary) 0%, var(--c-primary-hover) 100%);
  font-size: 0.82rem;
  font-weight: 600;
  color: white;
  cursor: pointer;
  transition: all var(--dur-normal) var(--ease-bounce);
}

.btn-save:hover:not(:disabled) {
  box-shadow: 0 4px 14px rgba(255, 107, 53, 0.35);
  transform: translateY(-1px);
}

.btn-save:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* ── Toast ── */
.settings-toast {
  position: absolute;
  bottom: 72px;
  left: 50%;
  transform: translateX(-50%);
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 9px 16px;
  border-radius: var(--r-full);
  font-size: 0.82rem;
  font-weight: 500;
  white-space: nowrap;
  box-shadow: 0 4px 16px rgba(45, 27, 14, 0.15);
  z-index: 10;
}

.settings-toast--success {
  background: var(--c-success);
  color: white;
}

.settings-toast--error {
  background: #ef4444;
  color: white;
}

.spinner {
  width: 13px;
  height: 13px;
  border: 2px solid rgba(255, 255, 255, 0.35);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* ── Transitions ── */
.fade-enter-active, .fade-leave-active { transition: opacity var(--dur-normal) ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.slide-enter-active, .slide-leave-active { transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.slide-enter-from, .slide-leave-to { transform: translateX(100%); }
.toast-slide-enter-active, .toast-slide-leave-active { transition: all var(--dur-normal) ease; }
.toast-slide-enter-from, .toast-slide-leave-to { opacity: 0; transform: translateX(-50%) translateY(8px); }

@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 500px) {
  .settings-panel { max-width: 100%; }
}
</style>
