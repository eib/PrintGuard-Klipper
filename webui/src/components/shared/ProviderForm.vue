<script setup lang="ts">
import { ref, onMounted, watch, computed, nextTick } from 'vue'
import { printersApi } from '../../services/api'
import { useDevices } from '../../composables/useDevices'
import Select from '../ui/Select.vue'
import Input from '../ui/Input.vue'
import type { ProviderSchema, ProviderField } from '../../types'

const props = defineProps<{
  provider: string
  modelValue: Record<string, any>
  mode: 'connection' | 'entity'
  entityDetails?: any
  type?: string
  hiddenFields?: string[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: Record<string, any>): void
}>()

const schema = ref<ProviderSchema | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const videoRef = ref<HTMLVideoElement | null>(null)

const { devices, currentStream, startPreview, stopPreview } = useDevices()

const deviceOptions = computed(() => [
  { value: '', label: 'Select a camera...' },
  ...devices.value.map(d => ({
    value: d.deviceId,
    label: d.label || `Camera ${d.deviceId.slice(0, 5)}`
  }))
])

const attributeOptions = computed(() => {
  if (!props.entityDetails?.attributes) return []
  return Object.keys(props.entityDetails.attributes).map(attr => ({
    value: attr,
    label: attr
  }))
})

const enumOptions = computed(() => {
  const opts = props.entityDetails?.attributes?.options
  if (!Array.isArray(opts)) return null
  const values = opts
    .map(o => String(o))
    .filter(o => o.length > 0)
  return values.length ? values : null
})

const stateSuggestions = computed(() => {
  const suggestions = new Set<string>()
  if (props.entityDetails) {
    const currentVal = props.modelValue.state_attribute 
      ? props.entityDetails.attributes?.[props.modelValue.state_attribute] 
      : props.entityDetails.state
    if (currentVal !== undefined && currentVal !== null) {
      suggestions.add(String(currentVal).toLowerCase())
    }
  }
  
  return Array.from(suggestions).sort()
})

const currentEntityValue = computed(() => {
  if (!props.entityDetails) return null
  const attr = props.modelValue.state_attribute
  let val = attr ? props.entityDetails.attributes?.[attr] : props.entityDetails.state
  
  if (val === undefined || val === null) return null
  
  return val
})

async function fetchSchema() {
  if (!props.provider) return
  loading.value = true
  error.value = null
  try {
    const response = await printersApi.providerSchema(props.provider)
    schema.value = response.data
    
    const fields = props.mode === 'connection' ? response.data.connection_fields : response.data.entity_fields
    const updates = { ...props.modelValue }
    let changed = false
    
    fields.forEach(f => {
      if (f.type === 'select' && f.options && f.options.length > 0 && updates[f.name] === undefined) {
        updates[f.name] = f.options[0].value
        changed = true
      }
    })
    
    if (changed) {
      emit('update:modelValue', updates)
    }
  } catch (e) {
    error.value = 'Failed to load configuration fields'
  } finally {
    loading.value = false
  }
}

onMounted(fetchSchema)
watch(() => props.provider, fetchSchema)

function updateField(name: string, value: any) {
  emit('update:modelValue', { ...props.modelValue, [name]: value })
}

function checkCondition(condition?: string): boolean {
  if (!condition) return true
  const match = condition.match(/^(\w+)\s*([=!]=)\s*['"]([^'"]+)['"]$/)
  if (!match) return true
  
  const [_, key, op, val] = match
  const currentVal = key === 'type' && props.type ? props.type : props.modelValue[key]
  
  if (op === '==') return currentVal === val
  if (op === '!=') return currentVal !== val
  
  return true
}

const visibleFields = computed(() => {
  if (!schema.value) return []
  const fields = props.mode === 'connection' ? schema.value.connection_fields : schema.value.entity_fields
  return fields.filter(f => {
    const isHidden = props.hiddenFields?.includes(f.name)
    const isHAStatusAttribute =
      props.provider === 'homeassistant' && props.type === 'status' && f.name === 'state_attribute'
    return !isHidden && !isHAStatusAttribute && checkCondition(f.condition)
  })
})

watch(() => props.modelValue.device_id, (newId) => {
  if (newId) {
    startPreview(newId)
  } else {
    stopPreview()
  }
})

watch(currentStream, async (stream) => {
  if (stream) {
    await nextTick()
    
    const el = Array.isArray(videoRef.value) ? videoRef.value[0] : videoRef.value
    
    if (el && typeof el.play === 'function') {
      el.srcObject = stream
      try {
        await el.play()
      } catch (e) {
        console.error('Failed to play video preview:', e)
      }
    } else {
      console.warn('Video element or play method not found', el)
    }
  }
})
</script>

<template>
  <div :class="$style.form">
    <div v-if="loading" :class="$style.loading">Loading configuration...</div>
    <div v-else-if="error" :class="$style.error">{{ error }}</div>
    <div v-else-if="schema">
      <div v-for="field in visibleFields" 
           :key="field.name" 
           class="form-field">
        <label :for="field.name">{{ field.label }}<span v-if="field.required" :class="$style.required">*</span></label>
        
        <!-- Enum Select for HA status mapping -->
        <Select
          v-if="field.name.endsWith('_state') && enumOptions"
          :id="field.name"
          :modelValue="modelValue[field.name] || ''"
          :options="enumOptions.map(v => ({ value: v, label: v }))"
          @update:modelValue="updateField(field.name, $event)"
          fullWidth
        />

        <!-- Standard Select -->
        <Select 
          v-else-if="field.type === 'select'"
          :id="field.name"
          :modelValue="modelValue[field.name]"
          :options="field.options || []"
          @update:modelValue="updateField(field.name, $event)"
          fullWidth
        />

        <!-- Combobox (Select + Text) -->
        <div v-else-if="field.type === 'combobox'" :class="$style.combobox">
          <Input 
            :id="field.name"
            :list="`${field.name}-list`"
            :modelValue="modelValue[field.name]"
            @update:modelValue="updateField(field.name, $event)"
            :placeholder="field.placeholder || `Enter or select ${field.label.toLowerCase()}...`"
            fullWidth
          />
          <datalist :id="`${field.name}-list`">
            <option 
              v-for="opt in (field.name.endsWith('_state') ? stateSuggestions : attributeOptions.map(o => o.value))" 
              :key="opt" 
              :value="opt"
            >
              {{ opt }}
            </option>
          </datalist>
          <p v-if="entityDetails" :class="$style.hint">
            Current value: <strong>{{ currentEntityValue }}</strong>
          </p>
        </div>

        <!-- Device Select for Webcams -->
        <div v-else-if="field.type === 'device_select'" :class="$style.devicePicker">
          <Select 
            :id="field.name"
            :modelValue="modelValue[field.name]"
            :options="deviceOptions"
            @update:modelValue="updateField(field.name, $event)"
            fullWidth
          />
          
          <div v-if="currentStream" :class="$style.preview">
            <video ref="videoRef" autoplay playsinline muted :class="$style.video"></video>
            <div :class="$style.previewBadge">Live Preview</div>
          </div>
        </div>

        <!-- Text/Password Inputs -->
        <div v-else :class="$style.inputWrapper">
          <Input 
            :id="field.name"
            :type="field.type === 'password' ? 'password' : 'text'"
            :modelValue="modelValue[field.name]"
            @update:modelValue="updateField(field.name, $event)"
            :placeholder="field.placeholder || `Enter ${field.label.toLowerCase()}...`"
            fullWidth
          />
          <p v-if="entityDetails && field.name.endsWith('_states')" :class="$style.hint">
            Tip: Current entity value is <strong>{{ currentEntityValue }}</strong>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<style module>
.form {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.required {
  color: var(--danger);
  margin-left: var(--space-1);
}

.hint {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  margin-top: var(--space-1);
}

.hint strong {
  color: var(--text-primary);
}

.loading, .error {
  padding: var(--space-8);
  text-align: center;
  color: var(--text-tertiary);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border: 1px dashed var(--border-default);
}

.error {
  color: var(--danger);
  border-color: var(--danger-200);
}

.devicePicker {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.preview {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  background-color: #000;
  border-radius: var(--radius-lg);
  overflow: hidden;
  border: 1px solid var(--border-subtle);
}

.video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.previewBadge {
  position: absolute;
  top: var(--space-3);
  left: var(--space-3);
  background-color: var(--primary);
  color: var(--primary-on);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
  text-transform: uppercase;
}
</style>

