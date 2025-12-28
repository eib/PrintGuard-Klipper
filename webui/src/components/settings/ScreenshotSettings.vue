<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminApi } from '../../services/api'
import Button from '../ui/Button.vue'
import Input from '../ui/Input.vue'

const loading = ref(false)
const saving = ref(false)
const settings = ref({
  screenshot_retention_hours: 24,
  screenshot_max_count: 100,
  screenshot_cleanup_interval_minutes: 60
})

async function fetchSettings() {
  loading.value = true
  try {
    const res = await adminApi.getSettings()
    settings.value = res.data
  } catch (e) {
    console.error('Failed to fetch screenshot settings', e)
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  try {
    await adminApi.updateSettings(settings.value)
    alert('Screenshot settings updated successfully')
  } catch (e: any) {
    alert(`Failed to update settings: ${e.response?.data?.detail || e.message}`)
  } finally {
    saving.value = false
  }
}

onMounted(fetchSettings)
</script>

<template>
  <div :class="$style.container">
    <div v-if="loading" :class="$style.loading">Loading settings...</div>
    <form v-else @submit.prevent="saveSettings" :class="$style.form">
      <div class="form-field">
        <label>Retention Period (Hours)</label>
        <Input 
          v-model.number="settings.screenshot_retention_hours" 
          type="number" 
          min="1" 
          required 
        />
        <p :class="$style.helpText">
          Screenshots older than this will be automatically deleted.
        </p>
      </div>

      <div class="form-field">
        <label>Maximum Screenshot Count</label>
        <Input 
          v-model.number="settings.screenshot_max_count" 
          type="number" 
          min="1" 
          required 
        />
        <p :class="$style.helpText">
          The oldest screenshots will be removed if this limit is exceeded.
        </p>
      </div>

      <div class="form-field">
        <label>Cleanup Interval (Minutes)</label>
        <Input 
          v-model.number="settings.screenshot_cleanup_interval_minutes" 
          type="number" 
          min="1" 
          required 
        />
        <p :class="$style.helpText">
          How often the server checks for expired or excess screenshots.
        </p>
      </div>

      <div :class="$style.actions">
        <Button variant="primary" type="submit" :loading="saving">
          Save Settings
        </Button>
      </div>
    </form>
  </div>
</template>

<style module>
.container {
  background-color: var(--card-bg);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  box-shadow: var(--shadow-sm);
  max-width: 600px;
}

.form {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.helpText {
  margin-top: var(--space-2);
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

.actions {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--space-2);
}

.loading {
  padding: var(--space-8);
  text-align: center;
  color: var(--text-tertiary);
}

/* ============================================
   Mobile Responsive Styles
   ============================================ */

@media (max-width: 768px) {
  .container {
    padding: var(--space-4);
  }

  .form {
    gap: var(--space-4);
  }

  .helpText {
    font-size: var(--font-size-xs);
  }
}

@media (max-width: 480px) {
  .container {
    padding: var(--space-3);
  }

  .form {
    gap: var(--space-3);
  }
}
</style>

