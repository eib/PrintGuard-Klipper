<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminApi } from '../../services/api'
import Button from '../ui/Button.vue'
import Input from '../ui/Input.vue'
import Badge from '../ui/Badge.vue'
import MultiSelect from '../ui/MultiSelect.vue'
import { AVAILABLE_SCOPES } from '../../types/scopes'
import type { M2MApplication } from '../../types'

const apps = ref<M2MApplication[]>([])
const loading = ref(false)
const showAdd = ref(false)
const newApp = ref({ name: '', scopes: ['printer:read', 'rtc:stream'] })
const lastCreated = ref<any>(null)

const scopeOptions = AVAILABLE_SCOPES.map(s => ({ value: s, label: s }))

async function fetchApps() {
  loading.value = true
  try {
    const response = await adminApi.listM2M()
    apps.value = response.data
  } finally {
    loading.value = false
  }
}

async function handleAdd() {
  try {
    const response = await adminApi.createM2M({
      ...newApp.value,
      scopes: newApp.value.scopes.join(' ')
    })
    lastCreated.value = response.data
    showAdd.value = false
    newApp.value = { name: '', scopes: ['printer:read', 'rtc:stream'] }
    fetchApps()
  } catch (e) {
    alert('Failed to add M2M app')
  }
}

async function handleDelete(clientId: string) {
  if (!confirm(`Delete M2M application ${clientId}?`)) return
  try {
    await adminApi.deleteM2M(clientId)
    fetchApps()
  } catch (e) {
    alert('Failed to delete M2M app')
  }
}

onMounted(fetchApps)
</script>

<template>
  <div :class="$style.section">
    <div :class="$style.header">
      <h3>M2M Applications</h3>
      <Button variant="ghost" size="sm" @click="showAdd = !showAdd">
        {{ showAdd ? 'Cancel' : '+ New M2M App' }}
      </Button>
    </div>

    <div v-if="lastCreated" :class="$style.secretAlert">
      <h4>⚠️ Save your client secret!</h4>
      <p>It will not be shown again.</p>
      <div :class="$style.secretBox">
        <div><strong>Client ID:</strong> <code>{{ lastCreated.client_id }}</code></div>
        <div><strong>Client Secret:</strong> <code>{{ lastCreated.client_secret }}</code></div>
      </div>
      <Button variant="ghost" size="sm" :class="$style.dismiss" @click="lastCreated = null">Dismiss</Button>
    </div>

    <div v-if="showAdd" :class="$style.addCard">
      <form @submit.prevent="handleAdd" :class="$style.form">
        <Input v-model="newApp.name" placeholder="App Name (e.g. Home Assistant)" required />
        <MultiSelect
          v-model="newApp.scopes"
          :options="scopeOptions"
          placeholder="Select Scopes"
        />
        <Button type="submit" variant="primary">Create Application</Button>
      </form>
    </div>

    <div :class="$style.tableWrapper">
      <div class="table-container">
        <table class="base-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Client ID</th>
              <th>Scopes</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="app in apps" :key="app.client_id">
              <td data-label="Name"><strong>{{ app.name }}</strong></td>
              <td data-label="Client ID"><code>{{ app.client_id }}</code></td>
              <td data-label="Scopes">
                <div :class="$style.scopes">
                  <Badge v-for="s in app.scopes.split(' ')" :key="s" variant="neutral" size="sm">{{ s }}</Badge>
                </div>
              </td>
              <td data-label="Actions">
                <Button variant="danger" size="sm" @click="handleDelete(app.client_id)">Delete</Button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style module>
.section {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.secretAlert {
  background-color: var(--warning-bg);
  border: 1px solid var(--warning-200);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.secretAlert h4 {
  color: var(--warning);
}

.secretBox {
  background-color: var(--bg-secondary);
  padding: var(--space-4);
  border-radius: var(--radius-lg);
  font-family: monospace;
  font-size: var(--font-size-sm);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  border: 1px solid var(--border-subtle);
}

.secretBox code {
  color: var(--text-primary);
  font-weight: var(--font-weight-bold);
}

.dismiss {
  align-self: flex-end;
  color: var(--warning);
}

.addCard {
  background-color: var(--card-bg);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  box-shadow: var(--shadow-sm);
}

.form {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: var(--space-4);
  align-items: flex-end;
}

.scopes {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-1);
}

.tableWrapper {
  width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

/* ============================================
   Mobile Responsive Styles
   ============================================ */

@media (max-width: 768px) {
  .header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-3);
  }

  .secretAlert {
    padding: var(--space-4);
  }

  .secretBox {
    font-size: var(--font-size-xs);
  }

  .addCard {
    padding: var(--space-4);
  }

  .form {
    grid-template-columns: 1fr;
    gap: var(--space-3);
  }

  .tableWrapper {
    border: none;
    border-radius: 0;
    overflow-x: visible;
  }

  .table-container {
    background-color: transparent;
    border: none;
    overflow: visible;
  }

  .base-table, 
  .base-table thead, 
  .base-table tbody, 
  .base-table th, 
  .base-table td, 
  .base-table tr {
    display: block;
    width: 100%;
  }

  .base-table thead {
    display: none;
  }

  .base-table tr {
    background-color: var(--card-bg);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-xl);
    margin-bottom: var(--space-4);
    padding: var(--space-2) var(--space-4);
    box-shadow: var(--shadow-sm);
    width: 100%;
    box-sizing: border-box;
  }

  .base-table td {
    display: flex;
    justify-content: space-between;
    align-items: center;
    text-align: right;
    padding: var(--space-3) 0;
    border-bottom: 1px solid var(--border-subtle);
    gap: var(--space-3);
    min-width: 0;
  }

  .base-table td:last-child {
    border-bottom: none;
  }

  .base-table td::before {
    content: attr(data-label);
    font-weight: var(--font-weight-bold);
    color: var(--text-tertiary);
    text-transform: uppercase;
    font-size: var(--font-size-xs);
    letter-spacing: var(--letter-spacing-wide);
    flex-shrink: 0;
  }

  .base-table td > * {
    max-width: 65%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex-shrink: 1;
  }

  .base-table td code {
    word-break: break-all;
    max-width: 100%;
    text-align: right;
    white-space: normal;
  }
}

@media (max-width: 480px) {
  .secretAlert {
    padding: var(--space-3);
  }

  .addCard {
    padding: var(--space-3);
  }

  .form {
    gap: var(--space-2);
  }
}
</style>

