<script setup lang="ts">
import { watch, onMounted } from 'vue'
import { useWebRTC } from '../../composables/useWebRTC'

const props = defineProps<{
  sessionId?: string
}>()

const emit = defineEmits<{
  (e: 'error', error: string): void
  (e: 'connected'): void
}>()

const { videoRef, connected, error, latestResult, connect, disconnect } = useWebRTC()

watch(error, (newErr) => {
  if (newErr) emit('error', newErr)
})

watch(connected, (isConn) => {
  if (isConn) emit('connected')
})

watch(() => props.sessionId, (newId) => {
  if (newId) {
    connect(newId)
  } else {
    disconnect()
  }
})

onMounted(() => {
  if (props.sessionId) {
    connect(props.sessionId)
  }
})
</script>

<template>
  <div :class="$style.preview">
    <video 
      ref="videoRef" 
      autoplay 
      playsinline 
      muted 
      :class="[$style.video, { [$style.visible]: connected }]"
    ></video>
    
    <div v-if="!sessionId" :class="$style.placeholder">
      No camera selected
    </div>
    <div v-else-if="error" :class="$style.error">
      {{ error }}
    </div>
    <div v-else-if="!connected" :class="$style.loading">
      <div :class="$style.spinner"></div>
      Connecting to stream...
    </div>

    <div v-if="connected && latestResult?.actual_fps" :class="$style.fps">
      {{ latestResult.actual_fps.toFixed(1) }} FPS
    </div>
  </div>
</template>

<style module>
.preview {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  background-color: #000;
  border-radius: 0.5rem;
  overflow: hidden;
  border: 1px solid var(--border);
}

.video {
  width: 100%;
  height: 100%;
  object-fit: contain;
  opacity: 0;
  transition: opacity 0.3s;
}

.video.visible {
  opacity: 1;
}

.placeholder, .error, .loading {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  gap: 1rem;
}

.error {
  color: var(--danger);
  padding: 1rem;
  text-align: center;
}

.spinner {
  width: 2rem;
  height: 2rem;
  border: 3px solid rgba(59, 130, 246, 0.3);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.fps {
  position: absolute;
  bottom: 0.75rem;
  right: 0.75rem;
  background-color: rgba(0, 0, 0, 0.6);
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.7rem;
  font-family: monospace;
  pointer-events: none;
  border: 1px solid rgba(255, 255, 255, 0.1);
}
</style>

