import { ref, onUnmounted } from 'vue'
import { streamsApi } from '../services/api'
import type { PredictionResult } from '../types'

export function useWebRTC() {
  const videoRef = ref<HTMLVideoElement | null>(null)
  const connected = ref(false)
  const error = ref<string | null>(null)
  const pc = ref<RTCPeerConnection | null>(null)
  const latestResult = ref<PredictionResult | null>(null)
  const reconnecting = ref(false)
  let lastSessionId: string | null = null
  let reconnectAttempts = 0
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null

  function clearReconnectTimer() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  function scheduleReconnect(reason: string) {
    if (!lastSessionId) return
    if (reconnectTimer) return

    const delay = Math.min(10000, 750 * Math.pow(2, reconnectAttempts))
    reconnectAttempts = Math.min(reconnectAttempts + 1, 6)
    reconnecting.value = true
    console.warn(`WebRTC: scheduling reconnect in ${delay}ms (${reason})`)

    reconnectTimer = setTimeout(() => {
      reconnectTimer = null
      if (lastSessionId) connect(lastSessionId)
    }, delay)
  }

  function setupDataChannel(channel: RTCDataChannel) {
    channel.onmessage = (event) => {
      try {
        latestResult.value = JSON.parse(event.data)
      } catch (e) {
        console.error('Failed to parse WebRTC message:', e)
      }
    }
  }

  async function connect(sessionId: string) {
    lastSessionId = sessionId
    clearReconnectTimer()

    if (pc.value) {
      pc.value.close()
    }

    try {
      connected.value = false
      error.value = null
      reconnecting.value = false

      pc.value = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
      })

      pc.value.ontrack = async (event) => {
        if (videoRef.value) {
          const el = videoRef.value
          el.srcObject = event.streams[0]
          
          try {
            el.load()
            await el.play()
          } catch (e) {
            console.warn('WebRTC autoplay prevented, will retry on interaction', e)
          }
        }
      }

      pc.value.onconnectionstatechange = () => {
        const state = pc.value?.connectionState
        if (state === 'connected') {
          connected.value = true
          reconnectAttempts = 0
        } else if (state === 'disconnected' || state === 'failed') {
          error.value = `WebRTC ${state}`
          scheduleReconnect(state)
        } else if (state === 'closed') {
          connected.value = false
        }
      }

      pc.value.oniceconnectionstatechange = () => {
        const ice = pc.value?.iceConnectionState
        if (ice === 'failed' || ice === 'disconnected') {
          scheduleReconnect(`ice:${ice}`)
        }
      }

      pc.value.ondatachannel = (event) => {
        setupDataChannel(event.channel)
      }

      pc.value.addTransceiver('video', { direction: 'recvonly' })

      const offer = await pc.value.createOffer()
      await pc.value.setLocalDescription(offer)

      await new Promise<void>((resolve) => {
        if (pc.value?.iceGatheringState === 'complete') {
          resolve()
        } else {
          const checkState = () => {
            if (pc.value?.iceGatheringState === 'complete') {
              pc.value.removeEventListener('icegatheringstatechange', checkState)
              resolve()
            }
          }
          pc.value?.addEventListener('icegatheringstatechange', checkState)
        }
      })

      const response = await streamsApi.view(sessionId, {
        sdp: pc.value?.localDescription?.sdp,
        type: pc.value?.localDescription?.type,
        session_id: `view-${Math.random().toString(36).slice(2, 9)}`
      })

      await pc.value.setRemoteDescription(new RTCSessionDescription(response.data))
    } catch (e: any) {
      error.value = e.message || 'Failed to connect'
      console.error('WebRTC error:', e)
      scheduleReconnect('exception')
    }
  }

  function disconnect() {
    clearReconnectTimer()
    lastSessionId = null
    reconnectAttempts = 0
    reconnecting.value = false
    if (pc.value) {
      pc.value.close()
      pc.value = null
    }
    if (videoRef.value) {
      videoRef.value.srcObject = null
    }
    connected.value = false
  }

  onUnmounted(disconnect)

  async function push(sessionId: string, stream: MediaStream, deviceName = 'Webcam', printerId?: string) {
    if (pc.value) {
      pc.value.close()
    }

    try {
      connected.value = false
      error.value = null

      pc.value = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
      })

      stream.getTracks().forEach(track => {
        pc.value?.addTrack(track, stream)
      })

      const dc = pc.value.createDataChannel('results')
      setupDataChannel(dc)

      pc.value.onconnectionstatechange = () => {
        if (pc.value?.connectionState === 'connected') {
          connected.value = true
        } else if (pc.value?.connectionState === 'failed') {
          error.value = 'WebRTC push failed'
        }
      }

      const offer = await pc.value.createOffer()
      await pc.value.setLocalDescription(offer)

      await new Promise<void>((resolve) => {
        if (pc.value?.iceGatheringState === 'complete') {
          resolve()
        } else {
          const checkState = () => {
            if (pc.value?.iceGatheringState === 'complete') {
              pc.value.removeEventListener('icegatheringstatechange', checkState)
              resolve()
            }
          }
          pc.value?.addEventListener('icegatheringstatechange', checkState)
        }
      })

      const response = await streamsApi.offer({
        sdp: pc.value?.localDescription?.sdp,
        type: pc.value?.localDescription?.type,
        session_id: sessionId,
        device_name: deviceName,
        printer_id: printerId
      })

      await pc.value.setRemoteDescription(new RTCSessionDescription(response.data))
    } catch (e: any) {
      error.value = e.message || 'Failed to push stream'
      console.error('WebRTC push error:', e)
    }
  }

  return {
    videoRef,
    connected,
    reconnecting,
    error,
    latestResult,
    connect,
    push,
    disconnect
  }
}

