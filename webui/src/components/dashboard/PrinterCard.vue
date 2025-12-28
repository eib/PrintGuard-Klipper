<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import LiveFeed from './LiveFeed.vue'
import InferenceTimeline from './InferenceTimeline.vue'
import { usePrintersStore } from '../../store/printers'
import { streamsApi, notificationsApi } from '../../services/api'
import { subscribeUserToPush } from '../../services/notifications'
import IconButton from '../ui/IconButton.vue'
import Button from '../ui/Button.vue'
import Badge from '../ui/Badge.vue'
import { Play, Pause, Square, Settings, Trash2, Zap, ZapOff, Bell, ChevronDown, ChevronUp } from 'lucide-vue-next'
import type { Printer } from '../../types'

const props = defineProps<{
  printer: Printer
}>()

const emit = defineEmits<{
  (e: 'edit', printer: Printer): void
}>()

const store = usePrintersStore()
const prediction = ref<any>(null)
const showTimeline = ref(false)
let pollTimer: any = null

const threshold = computed(() => {
  const sensitivity = props.printer.inference_sensitivity || 1.0
  return 50 / sensitivity
})

async function pollResults() {
  try {
    const response = await streamsApi.result(props.printer.id)
    prediction.value = response.data
    
    if (prediction.value.inference_paused !== undefined && 
        prediction.value.inference_paused !== props.printer.inference_paused) {
      const index = store.printers.findIndex(p => p.id === props.printer.id)
      if (index !== -1) {
        store.printers[index].inference_paused = prediction.value.inference_paused
      }
    }
  } catch (e) {
  }
}

onMounted(() => {
  pollTimer = setInterval(pollResults, 2000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

async function sendCmd(cmd: string) {
  try {
    await store.sendCommand(props.printer.id, cmd)
  } catch (e) {
    alert(`Failed to send ${cmd} command`)
  }
}

async function handleDelete() {
  if (confirm(`Are you sure you want to delete printer "${props.printer.name}"?`)) {
    try {
      await store.remove(props.printer.id)
    } catch (e) {
      alert('Failed to delete printer')
    }
  }
}

async function toggleInference() {
  const action = props.printer.inference_paused ? 'start' : 'stop'
  try {
    await store.toggleInference(props.printer.id, action)
  } catch (e) {
    alert(`Failed to ${action} inference`)
  }
}

async function toggleNotifications() {
  const enabled = !props.printer.notifications_enabled
  try {
    if (enabled) {
      await subscribeUserToPush()
    }
    await store.toggleNotifications(props.printer.id, enabled)
  } catch (e) {
    alert('Failed to toggle notifications')
  }
}

async function sendTestNotification() {
  try {
    await notificationsApi.test(props.printer.id)
  } catch (e) {
    alert('Failed to send test notification')
  }
}
</script>

<template>
  <div :class="$style.card">
    <div :class="$style.header">
      <div :class="$style.titleInfo">
        <div :class="$style.nameRow">
          <h3 :class="$style.name">{{ printer.name }}</h3>
          <IconButton
            :variant="printer.notifications_enabled ? 'primary' : 'ghost'"
            size="sm"
            :class="$style.inlineBell"
            :title="printer.notifications_enabled ? 'Disable notifications' : 'Enable notifications'"
            @click.stop="toggleNotifications"
          >
            <Bell :size="12" />
          </IconButton>
        </div>
        <Badge
          :variant="printer.status === 'printing' ? 'success' : printer.status === 'paused' ? 'warning' : printer.status === 'error' ? 'danger' : 'neutral'"
          size="sm"
        >
          {{ printer.status }}
        </Badge>
      </div>
      <div v-if="prediction" :class="$style.inferenceWrapper">
        <template v-if="prediction.status === 'success'">
          <div :class="[$style.inference, $style[prediction.class_name]]">
            <span :class="$style.icon">{{ prediction.class_name === 'defect' ? '⚠️' : '✅' }}</span>
            <span :class="$style.text">{{ prediction.class_name }}</span>
          </div>
          <div :class="$style.fpsMetric">
            {{ (printer.inference_paused || prediction.inference_paused) ? '-' : (prediction.actual_fps?.toFixed(1) || '0.0') }} det/s
          </div>
        </template>
        <template v-else-if="prediction.status === 'waiting'">
          <div :class="[$style.inference, $style.waiting]">
            <span :class="$style.icon">⏳</span>
            <span :class="$style.text">Waiting...</span>
          </div>
          <div :class="$style.fpsMetric">- det/s</div>
        </template>
      </div>
    </div>

    <div :class="$style.feedWrapper">
      <LiveFeed :printerId="printer.id" :camera="printer.components?.camera" />
      <div v-if="showTimeline" :class="$style.timelineOverlay">
        <InferenceTimeline
          :timelineResults="prediction?.timeline_results"
          :threshold="threshold"
        />
      </div>
    </div>

    <div :class="$style.footer">
      <div :class="$style.controls">
        <IconButton
          variant="default"
          size="sm"
          title="Start"
          :disabled="!printer.has_control || printer.status === 'printing'"
          @click="sendCmd('start')"
        >
          <Play :size="16" />
        </IconButton>
        <IconButton
          variant="default"
          size="sm"
          title="Pause"
          :disabled="!printer.has_control || printer.status !== 'printing'"
          @click="sendCmd('pause')"
        >
          <Pause :size="16" />
        </IconButton>
        <IconButton
          variant="danger"
          size="sm"
          title="Stop"
          :disabled="!printer.has_control || printer.status === 'idle'"
          @click="sendCmd('stop')"
        >
          <Square :size="16" />
        </IconButton>

        <div :class="$style.divider"></div>

        <Button
          :variant="printer.inference_paused ? 'primary' : 'secondary'"
          size="sm"
          @click="toggleInference"
        >
          <Zap v-if="printer.inference_paused" :size="14" />
          <ZapOff v-else :size="14" />
          <span>{{ printer.inference_paused ? 'Start Inference' : 'Stop Inference' }}</span>
        </Button>
      </div>

      <div :class="$style.cardActions">
        <IconButton
          variant="ghost"
          size="sm"
          title="Toggle Timeline"
          @click="showTimeline = !showTimeline"
        >
          <ChevronDown v-if="!showTimeline" :size="16" />
          <ChevronUp v-else :size="16" />
        </IconButton>
        <IconButton
          variant="ghost"
          size="sm"
          title="Edit Printer"
          @click="emit('edit', printer)"
        >
          <Settings :size="16" />
        </IconButton>
        <IconButton
          v-if="printer.notifications_enabled"
          variant="ghost"
          size="sm"
          title="Test Notification"
          @click="sendTestNotification"
        >
          <Bell :size="16" style="color: var(--primary)" />
        </IconButton>
        <IconButton
          variant="danger"
          size="sm"
          title="Delete Printer"
          @click="handleDelete"
        >
          <Trash2 :size="16" />
        </IconButton>
      </div>
    </div>
  </div>
</template>

<style module>
.card {
  background-color: var(--card-bg);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-2xl);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-md);
  transition: all var(--transition-base);
  height: auto;
}

.divider {
  width: 1px;
  height: 24px;
  background-color: var(--border-subtle);
  margin: 0 var(--space-1);
}

.card:hover {
  box-shadow: var(--shadow-lg);
}

.header {
  padding: var(--space-4);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  height: 80px;
}

.titleInfo {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  flex: 1;
  overflow: hidden;
}

.nameRow {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.inlineBell {
  padding: 2px !important;
  height: 20px !important;
  width: 20px !important;
  min-height: 20px !important;
  border-radius: var(--radius-md) !important;
}

.name {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.inferenceWrapper {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--space-1);
}

.inference {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-lg);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-extrabold);
  letter-spacing: var(--letter-spacing-wide);
  text-transform: uppercase;
  flex-shrink: 0;
}

.fpsMetric {
  font-size: 0.65rem;
  color: var(--text-tertiary);
  font-family: monospace;
  font-weight: 600;
}

.inference.normal {
  background-color: var(--success-bg);
  color: var(--success);
}

.inference.waiting {
  background-color: var(--bg-secondary);
  color: var(--text-secondary);
  opacity: 0.8;
}

.inference.defect {
  background-color: var(--danger-bg);
  color: var(--danger);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.7; }
  100% { opacity: 1; }
}

.inference .icon {
  font-size: 1rem;
}

.inference .text {
  font-weight: var(--font-weight-extrabold);
}

.inference .confidence {
  font-weight: var(--font-weight-normal);
  opacity: 0.8;
}

.feedWrapper {
  border-top: 1px solid var(--border-subtle);
  border-bottom: 1px solid var(--border-subtle);
  aspect-ratio: 16 / 9;
  background-color: #000;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.timelineOverlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.9);
  z-index: 10;
  padding: var(--space-4);
}

.footer {
  padding: var(--space-4);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  height: 64px;
}

.controls {
  display: flex;
  gap: var(--space-2);
}

.cardActions {
  display: flex;
  gap: var(--space-2);
}

/* ============================================
   Mobile Responsive Styles
   ============================================ */

@media (max-width: 768px) {
  .header {
    height: auto;
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-3);
  }

  .titleInfo {
    width: 100%;
  }

  .inferenceWrapper {
    width: 100%;
    align-items: flex-start;
  }

  .footer {
    height: auto;
    flex-direction: column;
    align-items: stretch;
    gap: var(--space-4);
  }

  .controls {
    flex-wrap: wrap;
    justify-content: center;
  }

  .cardActions {
    justify-content: center;
  }

  .divider {
    display: none;
  }
}

@media (max-width: 480px) {
  .controls {
    flex-direction: column;
  }

  .controls button,
  .controls .button {
    width: 100%;
    justify-content: center;
  }

  .cardActions {
    flex-wrap: wrap;
    justify-content: center;
  }
}
</style>
