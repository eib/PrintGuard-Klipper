<script setup lang="ts">
import { ref, watch } from 'vue'
import BaseModal from '../shared/BaseModal.vue'
import ComponentSelector from '../shared/ComponentSelector.vue'
import ComponentModal from '../library/ComponentModal.vue'
import Button from '../ui/Button.vue'
import Input from '../ui/Input.vue'
import { usePrintersStore } from '../../store/printers'
import { useComponentsStore } from '../../store/components'
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
  inference_target_fps: 2.0
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
        inference_target_fps: printer.inference_target_fps ?? 2.0
      }
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
        inference_target_fps: 2.0
      }
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
    if (props.printer) {
      await store.update(props.printer.id, formData.value)
    } else {
      await store.create(formData.value)
    }
    emit('close')
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Failed to save printer'
  } finally {
    loading.value = false
  }
}
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
</style>
