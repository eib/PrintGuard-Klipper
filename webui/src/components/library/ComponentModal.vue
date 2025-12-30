<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import BaseModal from '../shared/BaseModal.vue'
import ProviderForm from '../shared/ProviderForm.vue'
import Button from '../ui/Button.vue'
import Input from '../ui/Input.vue'
import Select from '../ui/Select.vue'
import Badge from '../ui/Badge.vue'
import { useComponentsStore } from '../../store/components'
import { useConnectionsStore } from '../../store/connections'
import { connectionsApi } from '../../services/api'
import type { Component, ComponentCreate } from '../../types'

const props = defineProps<{
  show: boolean
  initialType?: 'camera' | 'control' | 'status'
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'created', component: Component): void
}>()

const router = useRouter()
const store = useComponentsStore()
const connStore = useConnectionsStore()
const loading = ref(false)
const error = ref<string | null>(null)
const step = ref(1)
const entityDetails = ref<any>(null)
const connectionEntities = ref<any[]>([])
const loadingEntities = ref(false)

const formData = ref<ComponentCreate>({
  name: '',
  type: 'camera',
  provider: 'homeassistant',
  connection_id: undefined,
  entity_config: {}
})

const selectedConnection = computed(() =>
  connStore.connections.find(c => c.id === formData.value.connection_id)
)

const showStandaloneOptions = computed(() => formData.value.type === 'camera')

const connectionLabel = computed(() => 
  showStandaloneOptions.value 
    ? 'Select a connection or choose standalone' 
    : 'Select a connection'
)

const hasConnections = computed(() => connStore.connections.length > 0)

function goToConnections() {
  emit('close')
  router.push('/connections')
}

async function fetchEntityDetails() {
  const entityId = formData.value.entity_config?.entity_id
  const connectionId = formData.value.connection_id
  if (entityId && connectionId) {
    try {
      const response = await connectionsApi.entityDetails(connectionId, entityId)
      entityDetails.value = response.data

      // Auto-fill common enum mappings for HA status sensors
      if (formData.value.provider === 'homeassistant' && formData.value.type === 'status') {
        const opts = entityDetails.value?.attributes?.options
        if (Array.isArray(opts)) {
          const lower = opts.map((o: any) => String(o).toLowerCase())
          const updates = { ...(formData.value.entity_config || {}) }
          const pick = (key: 'printing_state' | 'paused_state' | 'error_state', val: string) => {
            if (!updates[key] && lower.includes(val)) updates[key] = val
          }
          pick('printing_state', 'printing')
          pick('paused_state', 'paused')
          pick('error_state', 'error')
          formData.value.entity_config = updates
        }
      }
    } catch (e) {
      console.warn('Failed to fetch entity details:', e)
      entityDetails.value = null
    }
  } else {
    entityDetails.value = null
  }
}

async function fetchConnectionEntities() {
  if (!formData.value.connection_id) {
    connectionEntities.value = []
    return
  }
  loadingEntities.value = true
  try {
    const response = await connectionsApi.entities(formData.value.connection_id, formData.value.type)
    connectionEntities.value = response.data
  } catch (e) {
    console.error('Failed to fetch connection entities:', e)
    connectionEntities.value = []
  } finally {
    loadingEntities.value = false
  }
}

watch(() => props.show, async (show) => {
  if (!show) return
  
  formData.value = {
    name: '',
    type: props.initialType || 'camera',
    provider: 'homeassistant',
    connection_id: undefined,
    entity_config: {}
  }
  entityDetails.value = null
  connectionEntities.value = []
  step.value = 1
})

async function nextStep() {
  if (step.value === 1) {
    step.value = 2
  } else if (step.value === 2) {
    if (formData.value.connection_id) {
      await fetchConnectionEntities()
    }
    step.value = 3
  }
}

async function handleSave() {
  loading.value = true
  error.value = null
  
  // Validation
  if (formData.value.type === 'control') {
    error.value = 'Please select a control action'
    loading.value = false
    return
  }

  if (formData.value.connection_id && !formData.value.entity_config?.entity_id) {
    error.value = 'Please select an entity'
    loading.value = false
    return
  }

  if (formData.value.provider === 'homeassistant' && formData.value.type === 'status') {
    const config = formData.value.entity_config || {}
    if (!config.printing_state || !config.paused_state || !config.error_state) {
      error.value = 'Please provide all required state labels (Printing, Paused, Error)'
      loading.value = false
      return
    }
  }

  try {
    const data = {
      ...formData.value,
      entity_config: formData.value.entity_config || {}
    }

    const created = await store.create(data)
    emit('created', created)
    emit('close')
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Failed to save component'
  } finally {
    loading.value = false
  }
}

async function onEntityIdChange(value: string | number) {
  const entityId = String(value)
  const entity = connectionEntities.value.find(e => e.id === entityId)
  if (entity) {
    formData.value.name = formData.value.name || entity.name
  }
  formData.value.entity_config.entity_id = entityId
  await fetchEntityDetails()
}
</script>

<template>
  <BaseModal
    :show="show"
    title="Add Component"
    @close="emit('close')"
  >
    <div :class="$style.steps">
      <div :class="[$style.step, { [$style.stepActive]: step === 1 }]">1. Type</div>
      <div :class="[$style.step, { [$style.stepActive]: step === 2 }]">2. Connection</div>
      <div :class="[$style.step, { [$style.stepActive]: step === 3 }]">3. Config</div>
    </div>

    <div v-if="step === 1" :class="$style.form">
      <label>What type of component are you adding?</label>
      <div :class="$style.typeGrid">
        <button
          v-for="t in ['camera', 'control', 'status']"
          :key="t"
          :class="[$style.typeBtn, { [$style.typeActive]: formData.type === t || (t === 'control' && formData.type.startsWith('control:')) }]"
          @click="formData.type = t as any; if (t !== 'control') nextStep()"
        >
          <span :class="$style.typeIcon">{{ t === 'camera' ? '📷' : t === 'control' ? '🎮' : '📊' }}</span>
          <span :class="$style.typeName">{{ t }}</span>
        </button>
      </div>

      <div v-if="formData.type === 'control' || formData.type.startsWith('control:')" :class="$style.subtypeSelector">
        <label>Control Action*</label>
        <Select
          :modelValue="formData.type.includes(':') ? formData.type : ''"
          :options="[
            { value: 'control:start', label: 'Start Button' },
            { value: 'control:pause', label: 'Pause Button' },
            { value: 'control:resume', label: 'Resume Button' },
            { value: 'control:stop', label: 'Stop Button' }
          ]"
          @update:modelValue="(val) => { formData.type = val as any; if (val) nextStep(); }"
          placeholder="Select an action..."
          fullWidth
        />
        <small :class="$style.helpText">Specify which action this component handles.</small>
      </div>
    </div>

    <div v-else-if="step === 2" :class="$style.form">
      <label>{{ connectionLabel }}</label>
      
      <div v-if="!hasConnections && !showStandaloneOptions" :class="$style.emptyState">
        <p>No connections found. You need to add a connection (like Home Assistant) before you can add this component.</p>
        <Button variant="secondary" @click="goToConnections">Go to Connections</Button>
      </div>

      <div v-else :class="$style.connList">
        <button
          v-for="c in connStore.connections"
          :key="c.id"
          :class="[$style.connItem, { [$style.connActive]: formData.connection_id === c.id }]"
          @click="formData.connection_id = c.id; formData.provider = c.provider; nextStep()"
        >
          <strong>{{ c.name }}</strong>
          <Badge variant="neutral" size="sm">{{ c.provider }}</Badge>
        </button>

        <template v-if="showStandaloneOptions">
          <div v-if="hasConnections" :class="$style.divider">OR</div>

          <button
            :class="[$style.connItem, { [$style.connActive]: !formData.connection_id && formData.provider === 'webcam' }]"
            @click="formData.connection_id = undefined; formData.provider = 'webcam'; nextStep()"
          >
            <strong>Standalone Webcam</strong>
            <span>Browser or RTSP</span>
          </button>
        </template>
      </div>
    </div>

    <div v-else-if="step === 3" class="base-form">
      <div class="form-field">
        <label for="component-name">Component Name*</label>
        <Input
          id="component-name"
          v-model="formData.name"
          placeholder="e.g. Front Camera"
          required
          :error="!!error"
        />
      </div>

      <div v-if="formData.connection_id" class="form-field">
        <label>Select Entity from {{ selectedConnection?.name }}</label>
        <Select 
          :modelValue="formData.entity_config.entity_id"
          :options="connectionEntities.map(e => ({ value: e.id, label: e.name }))"
          @update:modelValue="onEntityIdChange"
          :disabled="loadingEntities"
          placeholder="Select an entity..."
          fullWidth
        />
      </div>

      <div v-if="formData.provider" :class="$style.configForm">
        <ProviderForm
          :provider="formData.provider"
          v-model="formData.entity_config"
          :entityDetails="entityDetails"
          :type="formData.type"
          :hiddenFields="formData.connection_id ? ['entity_id'] : []"
          mode="entity"
        />
      </div>

      <div v-if="error" class="form-error">{{ error }}</div>
    </div>

    <template #footer>
      <Button variant="ghost" @click="emit('close')">Cancel</Button>
      <Button v-if="step > 1" variant="secondary" @click="step--">Back</Button>
      <Button
        v-if="step === 3"
        variant="primary"
        @click="handleSave"
        :loading="loading"
      >
        {{ loading ? 'Saving...' : 'Save Component' }}
      </Button>
    </template>
  </BaseModal>
</template>

<style module>
.steps {
  display: flex;
  gap: var(--space-4);
  margin-bottom: var(--space-8);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--border-subtle);
}

.step {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--text-tertiary);
}

.stepActive {
  color: var(--primary);
}

.form {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.form label {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

.emptyState {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-6);
  padding: var(--space-8);
  text-align: center;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-xl);
  border: 1px dashed var(--border-default);
}

.emptyState p {
  color: var(--text-tertiary);
  font-size: var(--font-size-sm);
  line-height: var(--line-height-relaxed);
  max-width: 300px;
}

.typeGrid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-4);
}

.typeBtn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-6);
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  transition: all var(--transition-fast);
  cursor: pointer;
}

.typeBtn:hover {
  border-color: var(--border-strong);
  background-color: var(--bg-tertiary);
}

.typeActive {
  border-color: var(--primary);
  background-color: var(--primary-50);
}

.typeIcon {
  font-size: 2rem;
}

.typeName {
  font-weight: var(--font-weight-semibold);
  text-transform: capitalize;
  color: var(--text-primary);
}

.subtypeSelector {
  margin-top: var(--space-4);
  padding: var(--space-4);
  background: var(--bg-tertiary);
  border-radius: var(--radius-lg);
}

.helpText {
  display: block;
  margin-top: var(--space-2);
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

.configForm {
  margin-top: var(--space-6);
  padding-top: var(--space-6);
  border-top: 1px solid var(--border-subtle);
}

.connList {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.connItem {
  padding: var(--space-4);
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all var(--transition-fast);
  cursor: pointer;
}

.connItem:hover {
  border-color: var(--border-strong);
  background-color: var(--bg-tertiary);
}

.connItem strong {
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

.connItem span {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

.connActive {
  border-color: var(--primary);
  background-color: var(--primary-50);
}

.divider {
  text-align: center;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
  color: var(--text-tertiary);
  margin: var(--space-2) 0;
  letter-spacing: var(--letter-spacing-wide);
}
</style>
