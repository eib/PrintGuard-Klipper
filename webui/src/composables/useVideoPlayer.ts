import { ref, onUnmounted } from 'vue'

export function useVideoPlayer() {
  const videoRef = ref<HTMLVideoElement | null>(null)
  const isPlaying = ref(false)
  const error = ref<string | null>(null)

  async function attachStream(stream: MediaStream) {
    if (!videoRef.value) {
      error.value = 'Video element not ready'
      return false
    }
    
    try {
      videoRef.value.srcObject = stream
      videoRef.value.load()
      await videoRef.value.play()
      isPlaying.value = true
      error.value = null
      return true
    } catch (e: any) {
      if (e.name === 'NotAllowedError') {
        console.warn('Autoplay prevented, waiting for user interaction')
        return false
      }
      error.value = e.message || 'Failed to play video'
      return false
    }
  }

  function detachStream() {
    if (videoRef.value) {
      videoRef.value.srcObject = null
    }
    isPlaying.value = false
  }

  onUnmounted(detachStream)

  return {
    videoRef,
    isPlaying,
    error,
    attachStream,
    detachStream
  }
}

