/**
 * Workflow store — persists state across route navigation.
 * Covers: news fetching, topic selection, guest selection,
 *         generation progress, and the newly-generated episode.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useWorkflowStore = defineStore('workflow', () => {
  // ── Step / wizard ──
  const currentStep = ref(0)

  // ── News ──
  const topicQuery = ref('')
  const newsContent = ref(null)          // { count, items }
  const selectedTopic = ref('')
  const customTopic = ref('')
  const fetchingNews = ref(false)

  // ── Guests ──
  const guests = ref([])
  const selectedGuests = ref([])
  const maxGuests = 3

  // ── Generate ──
  const workflowMode = ref('one-click')  // 'one-click' | 'step-by-step'
  const generating = ref(false)
  const generatingScript = ref(false)
  const synthesizing = ref(false)
  const taskId = ref(null)
  const scriptDraft = ref(null)
  const audioAdjustEpisodeId = ref(null)
  const audioAdjustLines = ref([])
  const applyingSegmentSpeeds = ref(false)
  const pendingAudioRetime = ref(false)

  // ── Preview task (step-by-step mode SSE) ──
  const previewStage = ref('')
  const previewStageDetail = ref('')
  const previewTaskId = ref(null)
  let _previewEventSource = null

  // ── Newly generated episode (for auto-display) ──
  const newEpisodeId = ref(null)
  const showNewEpisode = ref(false)

  // ── GuestDrawer open state ──
  const guestDrawerOpen = ref(false)

  // ── Computed ──
  const hasNews = computed(() => newsContent.value !== null)
  const effectiveTopic = computed(() => customTopic.value || selectedTopic.value || '')
  const hasScriptDraft = computed(() => scriptDraft.value && scriptDraft.value.dialogue?.length > 0)
  const hasAudioAdjustDraft = computed(() => audioAdjustEpisodeId.value && audioAdjustLines.value.length > 0)
  const canGenerate = computed(
    () => hasNews.value && !!effectiveTopic.value && selectedGuests.value.length > 0
  )

  // ── Actions ──
  async function fetchNews() {
    fetchingNews.value = true
    try {
      const params = new URLSearchParams({ max_results: '10' })
      if (topicQuery.value.trim()) {
        params.set('topic', topicQuery.value.trim())
      }
      const res = await fetch(`/api/debug/news?${params}`)
      const data = await res.json()
      newsContent.value = {
        count: data.count || 0,
        items: data.items || []
      }
      if (newsContent.value.items.length > 0) {
        selectedTopic.value = newsContent.value.items[0].title
      }
      customTopic.value = ''
    } catch (e) {
      console.error('Failed to fetch news:', e)
    } finally {
      fetchingNews.value = false
    }
  }

  async function loadGuests() {
    try {
      const res = await fetch('/api/guests')
      const data = await res.json()
      guests.value = Array.isArray(data) ? data : []
      if (!selectedGuests.value.length && guests.value.length) {
        selectedGuests.value = [guests.value[0].name]
      }
    } catch (e) {
      console.error('Failed to load guests:', e)
    }
  }

  async function saveGuest({ isEdit, ...payload }) {
    try {
      const method = isEdit ? 'PUT' : 'POST'
      const url = isEdit
        ? `/api/guests/${encodeURIComponent(payload.name)}`
        : '/api/guests'
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data?.detail || '操作失败')
      }
      const data = await res.json()
      guests.value = data
      if (!selectedGuests.value.includes(payload.name) && selectedGuests.value.length < maxGuests) {
        selectedGuests.value = [...selectedGuests.value, payload.name]
      }
    } catch (e) {
      console.error('Failed to save guest:', e)
      throw e
    }
  }

  async function removeGuest(name) {
    try {
      const res = await fetch(`/api/guests/${encodeURIComponent(name)}`, { method: 'DELETE' })
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data?.detail || '删除失败')
      }
      guests.value = data
      selectedGuests.value = selectedGuests.value.filter(item => item !== name)
    } catch (e) {
      console.error('Failed to delete guest:', e)
      throw e
    }
  }

  function selectTopic(title) {
    selectedTopic.value = title
    customTopic.value = ''
  }

  function toggleGuest(name) {
    const current = [...selectedGuests.value]
    const idx = current.indexOf(name)
    if (idx >= 0) {
      current.splice(idx, 1)
    } else if (current.length < maxGuests) {
      current.push(name)
    }
    selectedGuests.value = current
  }

  async function startGenerate() {
    if (!canGenerate.value) return
    generating.value = true
    audioAdjustEpisodeId.value = null
    audioAdjustLines.value = []
    pendingAudioRetime.value = false
    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: effectiveTopic.value,
          selected_guests: selectedGuests.value
        })
      })
      const data = await res.json()
      taskId.value = data.task_id
    } catch (e) {
      console.error('Failed to start generation:', e)
      generating.value = false
    }
  }

  async function generateScriptPreview() {
    if (!canGenerate.value) return
    generatingScript.value = true
    previewStage.value = 'news'
    previewStageDetail.value = '正在获取资讯...'
    previewTaskId.value = null
    scriptDraft.value = null
    audioAdjustEpisodeId.value = null
    audioAdjustLines.value = []
    pendingAudioRetime.value = false

    // Tear down any existing SSE connection
    if (_previewEventSource) {
      _previewEventSource.close()
      _previewEventSource = null
    }

    try {
      const res = await fetch('/api/script/preview/task', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: effectiveTopic.value,
          selected_guests: selectedGuests.value
        })
      })
      const data = await res.json()
      const taskId = data.task_id
      previewTaskId.value = taskId

      // Subscribe to SSE progress
      _previewEventSource = new EventSource(`/api/status/${taskId}`)
      _previewEventSource.onmessage = (event) => {
        try {
          const evt = JSON.parse(event.data)
          previewStage.value = evt.stage || ''
          previewStageDetail.value = evt.detail || ''
          if (evt.status === 'completed' && evt.result) {
            scriptDraft.value = {
              title: evt.result.title || '',
              topic: evt.result.topic || '',
              summary: evt.result.summary || '',
              guests: evt.result.guests || [],
              dialogue: (evt.result.dialogue || []).map(line => ({
                speaker: line.speaker,
                text: line.text,
                emotion: line.emotion || 'neutral'
              }))
            }
            generatingScript.value = false
            previewTaskId.value = null
            _previewEventSource.close()
            _previewEventSource = null
          }
          if (evt.status === 'failed' || evt.status === 'cancelled') {
            generatingScript.value = false
            if (evt.status === 'cancelled') {
              previewStage.value = 'cancelled'
              previewStageDetail.value = evt.detail || '任务已终止'
            }
            previewTaskId.value = null
            _previewEventSource.close()
            _previewEventSource = null
          }
        } catch (e) {
          console.error('SSE parse error:', e)
        }
      }
      _previewEventSource.onerror = () => {
        generatingScript.value = false
        previewTaskId.value = null
        if (_previewEventSource) {
          _previewEventSource.close()
          _previewEventSource = null
        }
      }
    } catch (e) {
      console.error('Failed to start script preview task:', e)
      generatingScript.value = false
      previewTaskId.value = null
    }
  }

  async function cancelScriptPreview() {
    if (!previewTaskId.value) return
    const currentTaskId = previewTaskId.value
    try {
      await fetch(`/api/tasks/${currentTaskId}/cancel`, { method: 'POST' })
    } catch (e) {
      console.error('Failed to cancel script preview:', e)
    } finally {
      generatingScript.value = false
      previewStage.value = 'cancelled'
      previewStageDetail.value = '任务已终止'
      previewTaskId.value = null
      if (_previewEventSource) {
        _previewEventSource.close()
        _previewEventSource = null
      }
    }
  }

  async function confirmScriptSynthesis() {
    if (!hasScriptDraft.value) return
    synthesizing.value = true
    audioAdjustEpisodeId.value = null
    audioAdjustLines.value = []
    try {
      const payload = {
        title: scriptDraft.value.title,
        topic: scriptDraft.value.topic,
        summary: scriptDraft.value.summary,
        guests: scriptDraft.value.guests,
        dialogue: scriptDraft.value.dialogue
          .map(line => ({ speaker: line.speaker, text: line.text?.trim(), emotion: line.emotion }))
          .filter(line => line.text)
      }
      const res = await fetch('/api/script/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      const data = await res.json()
      pendingAudioRetime.value = false
      taskId.value = data.task_id
    } catch (e) {
      console.error('Failed to start synthesis:', e)
      synthesizing.value = false
    }
  }

  async function prepareAudioAdjustment(episodeId) {
    if (!episodeId) return
    try {
      const res = await fetch(`/api/episodes/${episodeId}`)
      if (!res.ok) throw new Error('加载节目失败')
      const data = await res.json()
      audioAdjustEpisodeId.value = episodeId
      audioAdjustLines.value = (data.dialogue || []).map(line => ({
        speaker: line.speaker,
        text: line.text,
        speech_rate: Number(line.speech_rate ?? 1) || 1
      }))
      if (!audioAdjustLines.value.length && scriptDraft.value?.dialogue?.length) {
        audioAdjustLines.value = scriptDraft.value.dialogue.map(line => ({
          speaker: line.speaker,
          text: line.text,
          speech_rate: 1
        }))
      }
    } catch (e) {
      console.error('Failed to prepare segment speed adjust:', e)
      newEpisodeId.value = episodeId
      showNewEpisode.value = true
    }
  }

  async function applySegmentSpeeds() {
    if (!audioAdjustEpisodeId.value || !audioAdjustLines.value.length || applyingSegmentSpeeds.value) return
    applyingSegmentSpeeds.value = true
    try {
      const res = await fetch(`/api/episodes/${audioAdjustEpisodeId.value}/audio/retime`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          line_speeds: audioAdjustLines.value.map(line => {
            const speed = Number(line.speech_rate)
            if (!Number.isFinite(speed)) return 1
            return Math.max(0.5, Math.min(2, speed))
          })
        })
      })
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data?.detail || '段级倍速处理失败')
      }
      pendingAudioRetime.value = true
      taskId.value = data.task_id
    } catch (e) {
      console.error('Failed to apply segment speeds:', e)
      throw e
    } finally {
      applyingSegmentSpeeds.value = false
    }
  }

  async function cleanupEpisodeSegments(episodeId) {
    if (!episodeId) return
    try {
      await fetch(`/api/episodes/${episodeId}/segments/cleanup`, { method: 'POST' })
    } catch (e) {
      console.error('Failed to cleanup segment audio files:', e)
    }
  }

  async function skipSegmentSpeedAdjust() {
    if (!audioAdjustEpisodeId.value) return
    const episodeId = audioAdjustEpisodeId.value
    await cleanupEpisodeSegments(episodeId)
    audioAdjustEpisodeId.value = null
    audioAdjustLines.value = []
    pendingAudioRetime.value = false
    onGenerateCompleted(episodeId)
  }

  async function onGenerateCompleted(episodeId) {
    generating.value = false
    synthesizing.value = false
    taskId.value = null
    if (episodeId && pendingAudioRetime.value) {
      await cleanupEpisodeSegments(episodeId)
      pendingAudioRetime.value = false
      newEpisodeId.value = episodeId
      showNewEpisode.value = true
      audioAdjustEpisodeId.value = null
      audioAdjustLines.value = []
      return
    }
    if (episodeId && workflowMode.value === 'step-by-step' && hasScriptDraft.value) {
      prepareAudioAdjustment(episodeId)
      return
    }
    if (episodeId) {
      newEpisodeId.value = episodeId
      showNewEpisode.value = true
    }
  }

  function dismissNewEpisode() {
    showNewEpisode.value = false
    newEpisodeId.value = null
  }

  /** Reset wizard to initial state for a fresh generation run. */
  function resetWizard() {
    currentStep.value = 0
    topicQuery.value = ''
    newsContent.value = null
    selectedTopic.value = ''
    customTopic.value = ''
    taskId.value = null
    scriptDraft.value = null
    generating.value = false
    generatingScript.value = false
    synthesizing.value = false
    showNewEpisode.value = false
    newEpisodeId.value = null
    audioAdjustEpisodeId.value = null
    audioAdjustLines.value = []
    applyingSegmentSpeeds.value = false
    pendingAudioRetime.value = false
    previewStage.value = ''
    previewStageDetail.value = ''
    previewTaskId.value = null
    if (_previewEventSource) {
      _previewEventSource.close()
      _previewEventSource = null
    }
  }

  return {
    // State
    currentStep,
    topicQuery,
    newsContent,
    selectedTopic,
    customTopic,
    fetchingNews,
    guests,
    selectedGuests,
    maxGuests,
    workflowMode,
    generating,
    generatingScript,
    synthesizing,
    taskId,
    scriptDraft,
    audioAdjustEpisodeId,
    audioAdjustLines,
    applyingSegmentSpeeds,
    newEpisodeId,
    showNewEpisode,
    guestDrawerOpen,

    // Computed
    hasNews,
    effectiveTopic,
    hasScriptDraft,
    hasAudioAdjustDraft,
    canGenerate,

    // Preview SSE state
    previewStage,
    previewStageDetail,
    previewTaskId,

    // Actions
    fetchNews,
    loadGuests,
    saveGuest,
    removeGuest,
    selectTopic,
    toggleGuest,
    startGenerate,
    generateScriptPreview,
    cancelScriptPreview,
    confirmScriptSynthesis,
    prepareAudioAdjustment,
    applySegmentSpeeds,
    skipSegmentSpeedAdjust,
    onGenerateCompleted,
    dismissNewEpisode,
    resetWizard,
  }
})
