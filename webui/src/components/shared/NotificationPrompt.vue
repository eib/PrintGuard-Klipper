<script setup lang="ts">
import { ref } from 'vue'
import BaseModal from './BaseModal.vue'
import Button from '../ui/Button.vue'
import { subscribeUserToPush } from '../../services/notifications'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  (e: 'success'): void
}>()

const loading = ref(false)
const error = ref<string | null>(null)
const permissionDenied = ref(false)

async function handleEnable() {
  loading.value = true
  error.value = null
  permissionDenied.value = false
  
  try {
    await subscribeUserToPush()
    emit('success')
  } catch (e: any) {
    if (e.message === 'PERMISSION_DENIED') {
      permissionDenied.value = true
    } else if (e.message === 'VAPID_MISSING') {
      error.value = 'Notifications are not configured on the server. Please contact an administrator.'
    } else {
      error.value = e.message || 'Failed to enable notifications. Please try again.'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <BaseModal
    :show="show"
    title="Notifications Required"
    size="sm"
    @close="() => {}" 
  >
    <div :class="$style.content">
      <div :class="$style.icon">🔔</div>
      <p :class="$style.description">
        PrintGuard requires browser notifications to alert you of print defects in real-time.
      </p>

      <div v-if="permissionDenied" :class="$style.errorBox">
        <strong>Permission Denied</strong>
        <p>You have blocked notifications for this site. To continue, please reset the notification permission in your browser settings and click "Try Again".</p>
      </div>

      <div v-else-if="error" :class="$style.errorBox">
        {{ error }}
      </div>

      <div :class="$style.actions">
        <Button
          variant="primary"
          @click="handleEnable"
          :loading="loading"
          full-width
        >
          {{ permissionDenied ? 'Try Again' : 'Enable Notifications' }}
        </Button>
      </div>
    </div>
  </BaseModal>
</template>

<style module>
.content {
  text-align: center;
  padding: var(--space-2) 0;
}

.icon {
  font-size: 3rem;
  margin-bottom: var(--space-4);
}

.description {
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: var(--space-6);
}

.errorBox {
  background-color: var(--danger-bg);
  border: 1px solid var(--danger-subtle);
  color: var(--danger-text);
  padding: var(--space-4);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-6);
  text-align: left;
  font-size: var(--font-size-sm);
}

.errorBox strong {
  display: block;
  margin-bottom: var(--space-1);
}

.errorBox p {
  margin: 0;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
</style>

