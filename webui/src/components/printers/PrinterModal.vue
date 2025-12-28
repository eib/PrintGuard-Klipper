<script setup lang="ts">
import { ref, watch } from 'vue'
import BaseModal from '../shared/BaseModal.vue'
import ComponentSelector from '../shared/ComponentSelector.vue'
import ComponentModal from '../library/ComponentModal.vue'
import Button from '../ui/Button.vue'
import Input from '../ui/Input.vue'
import Select from '../ui/Select.vue'
import { usePrintersStore } from '../../store/printers'
import { useComponentsStore } from '../../store/components'
import { subscribeUserToPush } from '../../services/notifications'
import type { Printer, PrinterCreate } from '../../types'

const props = defineProps<{
  show: boolean
  printer?: Printer | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const store = usePrintersStore()
const compStore = useComponentsStore()
const loading = ref(false)
const error = ref<string | null>(null)
const notificationsEnabled = ref(false)

const showCompModal = ref(false)
const activeCompType = ref<'camera' | 'control' | 'status'>('camera')

const formData = ref<PrinterCreate>({
  name: '',
  components: {
    camera: '',
    status: null,
    control: null
  },
  inference_sensitivity: 1.0,
  inference_majority_voting: 1,
  inference_target_fps: 2.0,
  detection_action: 'none'
})

watch([() => props.show, () => props.printer], ([show, printer]) => {
  if (show) {
    compStore.fetchAll(undefined, true)

    if (printer) {
      const comps = printer.components || {}
      formData.value = {
        name: printer.name,
        components: {
          camera: comps.camera?.id || '',
          status: comps.status?.id || null,
          control: comps.control?.id || null
        },
        inference_sensitivity: printer.inference_sensitivity ?? 1.0,
        inference_majority_voting: printer.inference_majority_voting ?? 1,
        inference_target_fps: printer.inference_target_fps ?? 2.0,
        detection_action: printer.detection_action ?? 'none'
      }
      notificationsEnabled.value = printer.notifications_enabled || false
    } else {
      formData.value = {
        name: '',
        components: {
          camera: '',
          status: null,
          control: null
        },
        inference_sensitivity: 1.0,
        inference_majority_voting: 1,
        inference_target_fps: 2.0,
        detection_action: 'none'
      }
      notificationsEnabled.value = false
    }
  }
}, { immediate: true })

function openAddNew(type: 'camera' | 'control' | 'status') {
  activeCompType.value = type
  showCompModal.value = true
}

function onComponentCreated(comp: any) {
  if (comp.type === 'camera') formData.value.components.camera = comp.id
  else if (comp.type === 'status') formData.value.components.status = comp.id
  else if (comp.type === 'control') formData.value.components.control = comp.id

  showCompModal.value = false
}

async function handleSave() {
  if (!formData.value.components.camera) {
    error.value = 'Camera is required'
    return
  }

  loading.value = true
  error.value = null
  try {
    let savedPrinter
    if (props.printer) {
      savedPrinter = await store.update(props.printer.id, formData.value)
    } else {
      savedPrinter = await store.create(formData.value)
    }

    if (notificationsEnabled.value) {
      await subscribeUserToPush()
    }
    await store.toggleNotifications(savedPrinter.id, notificationsEnabled.value)

    emit('close')
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Failed to save printer'
  } finally {
    loading.value = false
  }
}

watch(() => formData.value.components.control, (newControl) => {
  if (!newControl) {
    formData.value.detection_action = 'none'
  }
})
</script>

<template>
  <BaseModal
    :show="show"
    :title="printer ? 'Edit Printer' : 'Add Printer'"
    @close="emit('close')"
  >
    <form @submit.prevent="handleSave" class="base-form">
      <div class="form-field">
        <label for="printer-name">Printer Name*</label>
        <Input
          id="printer-name"
          v-model="formData.name"
          placeholder="e.g. Ender 3 V2"
          required
          :error="!!error"
        />
      </div>

      <div class="form-field">
        <label>Camera Source* (Required)</label>
        <ComponentSelector
          type="camera"
          v-model="formData.components.camera"
          :printerId="printer?.id"
          required
          @add-new="openAddNew('camera')"
        />
      </div>

      <div class="form-field">
        <label>Status Source (Optional)</label>
        <ComponentSelector
          type="status"
          v-model="formData.components.status"
          @add-new="openAddNew('status')"
          placeholder="No status source selected"
        />
      </div>

      <div class="form-field">
        <label>Control Source (Optional)</label>
        <ComponentSelector
          type="control"
          v-model="formData.components.control"
          @add-new="openAddNew('control')"
          placeholder="No control source selected"
        />
      </div>

      <div class="form-section-title">Inference Settings</div>
      
      <div class="form-row">
        <div class="form-field">
          <label for="sensitivity">Sensitivity</label>
          <Input
            id="sensitivity"
            type="number"
            step="0.1"
            v-model.number="formData.inference_sensitivity"
            placeholder="1.0"
          />
          <small class="field-help">Higher = more likely to detect defects (defaults to 1.0)</small>
        </div>

        <div class="form-field">
          <label for="majority_voting">Majority Voting</label>
          <Input
            id="majority_voting"
            type="number"
            v-model.number="formData.inference_majority_voting"
            placeholder="1"
          />
          <small class="field-help">Number of inferences to average</small>
        </div>
      </div>

      <div class="form-field">
        <label for="target_fps">Target Detections Per Second</label>
        <Input
          id="target_fps"
          type="number"
          step="0.1"
          v-model.number="formData.inference_target_fps"
          placeholder="5.0"
        />
        <small class="field-help">Limit the number of inferences per second</small>
      </div>

      <div class="form-field">
        <label for="detection-action">Action on Defect</label>
        <Select
          id="detection-action"
          v-model="formData.detection_action"
          :disabled="!formData.components.control"
          :options="[
            { value: 'none', label: 'None (Notification Only)' },
            { value: 'pause', label: 'Pause Print' },
            { value: 'stop', label: 'Stop Print' }
          ]"
          full-width
        />
        <small class="field-help" v-if="!formData.components.control">
          Requires a Control Source to be configured.
        </small>
        <small class="field-help" v-else>
          Choose what happens automatically when a defect is detected.
        </small>
      </div>

      <div class="form-section-title">Notification Settings</div>
      <div class="form-field">
        <label :class="$style.checkboxLabel">
          <input type="checkbox" v-model="notificationsEnabled" />
          Notify me of defects on this printer
        </label>
        <small class="field-help">Requires browser notification permission.</small>
      </div>

      <div v-if="error" class="form-error">{{ error }}</div>
    </form>

    <template #footer>
      <Button variant="ghost" @click="emit('close')">Cancel</Button>
      <Button
        variant="primary"
        @click="handleSave"
        :loading="loading"
      >
        {{ loading ? 'Saving...' : 'Save Printer' }}
      </Button>
    </template>

    <ComponentModal
      :show="showCompModal"
      :initialType="activeCompType"
      @close="showCompModal = false"
      @created="onComponentCreated"
    />
  </BaseModal>
</template>

<style module>
.form-section-title {
  font-size: 0.9rem;
  font-weight: 600;
  margin: 1.5rem 0 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.field-help {
  display: block;
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-top: 0.25rem;
}

.checkboxLabel {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  cursor: pointer;
  color: var(--text-primary);
}

.checkboxLabel input {
  width: 1rem;
  height: 1rem;
}

/* ============================================
   Mobile Responsive Styles
   ============================================ */

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
    gap: var(--space-3);
  }

  .form-section-title {
    font-size: var(--font-size-sm);
    margin: var(--space-4) 0 var(--space-3);
  }

  .field-help {
    font-size: var(--font-size-xs);
  }

  .checkboxLabel {
    font-size: var(--font-size-sm);
  }
}

@media (max-width: 480px) {
  .form-row {
    gap: var(--space-2);
  }

  .form-section-title {
    margin: var(--space-3) 0 var(--space-2);
  }
}
</style>
