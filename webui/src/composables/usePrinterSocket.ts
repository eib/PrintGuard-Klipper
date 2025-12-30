import { ref, onMounted, onUnmounted } from 'vue'
import { usePrintersStore } from '../store/printers'

interface InferenceEvent {
  class_name: string
  confidence: number
  actual_fps: number
  paused: boolean
  timeline_entry?: {
    timestamp: number
    class_name: string
    confidence: number
    defect_confidence: number
    class_idx?: number
  }
}

interface DefectEvent {
  class_name: string
  confidence: number
  screenshot: string | null
}

interface InferenceStateEvent {
  running: boolean
}

interface WebSocketMessage {
  type: 'inference' | 'defect' | 'inference_state' | 'status' | 'snapshot'
  data:
    | InferenceEvent
    | DefectEvent
    | InferenceStateEvent
    | { status: string }
    | {
        paused: boolean
        prediction: any
        timeline_results: any[]
      }
}

export function usePrinterSocket(printerId: string) {
  const store = usePrintersStore()
  const connected = ref(false)
  const prediction = ref<InferenceEvent | null>(null)
  const timelineResults = ref<any[]>([])
  let ws: WebSocket | null = null
  let reconnectTimeout: ReturnType<typeof setTimeout> | null = null
  let reconnectAttempts = 0
  const maxReconnectAttempts = 10
  const baseReconnectDelay = 1000

  function getWebSocketUrl(): string {
    const token = localStorage.getItem('token')
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${protocol}//${window.location.host}/api/ws/${printerId}?token=${token}`
  }

  function connect() {
    if (ws?.readyState === WebSocket.OPEN) return

    const url = getWebSocketUrl()
    ws = new WebSocket(url)

    ws.onopen = () => {
      connected.value = true
      reconnectAttempts = 0
    }

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data)
        handleMessage(message)
      } catch (e) {
        console.error('WebSocket message parse error:', e)
      }
    }

    ws.onclose = () => {
      connected.value = false
      scheduleReconnect()
    }

    ws.onerror = () => {
      ws?.close()
    }
  }

  function handleMessage(message: WebSocketMessage) {
    switch (message.type) {
      case 'snapshot': {
        const snap = message.data as any
        if (typeof snap.paused === 'boolean') {
          store.setInferencePaused(printerId, snap.paused)
        }
        if (snap.prediction && typeof snap.prediction === 'object') {
          // Best-effort mapping into our lightweight InferenceEvent
          prediction.value = {
            class_name: snap.prediction.class_name,
            confidence: snap.prediction.confidence,
            actual_fps: snap.prediction.actual_fps || 0,
            paused: !!snap.paused
          }
        }
        if (Array.isArray(snap.timeline_results)) {
          timelineResults.value = snap.timeline_results
        }
        break
      }
      case 'inference':
        prediction.value = message.data as InferenceEvent
        store.setInferencePaused(printerId, (message.data as InferenceEvent).paused)
        if ((message.data as InferenceEvent).timeline_entry) {
          timelineResults.value.push((message.data as InferenceEvent).timeline_entry)
          if (timelineResults.value.length > 200) {
            timelineResults.value.splice(0, timelineResults.value.length - 200)
          }
        }
        break

      case 'inference_state':
        const stateData = message.data as InferenceStateEvent
        store.setInferencePaused(printerId, !stateData.running)
        break

      case 'defect':
        break

      case 'status':
        const statusData = message.data as { status: string }
        store.updateStatus(printerId, statusData.status)
        break
    }
  }

  function scheduleReconnect() {
    if (reconnectAttempts >= maxReconnectAttempts) return
    
    const delay = baseReconnectDelay * Math.pow(2, reconnectAttempts)
    reconnectAttempts++
    
    reconnectTimeout = setTimeout(() => {
      connect()
    }, Math.min(delay, 30000))
  }

  function disconnect() {
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout)
      reconnectTimeout = null
    }
    if (ws) {
      ws.close()
      ws = null
    }
    connected.value = false
  }

  onMounted(() => {
    connect()
  })

  onUnmounted(() => {
    disconnect()
  })

  return {
    connected,
    prediction,
    timelineResults,
    reconnect: connect
  }
}

