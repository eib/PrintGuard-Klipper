<script setup lang="ts">
import HealthBadge from '../shared/HealthBadge.vue'
import IconButton from '../ui/IconButton.vue'
import Badge from '../ui/Badge.vue'
import { Eye, Trash2 } from 'lucide-vue-next'
import type { Component } from '../../types'

defineProps<{
  components: Component[]
}>()

const emit = defineEmits<{
  (e: 'delete', component: Component): void
  (e: 'preview', component: Component): void
}>()
</script>

<template>
  <div :class="$style.tableWrapper">
    <div class="table-container">
      <table class="base-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Type</th>
            <th>Provider</th>
            <th>Connection</th>
            <th>Health</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="comp in components" :key="comp.id">
            <td data-label="Name" :class="$style.name">{{ comp.name }}</td>
            <td data-label="Type">
              <Badge :variant="comp.type === 'camera' ? 'primary' : comp.type === 'control' ? 'success' : 'warning'" size="sm">
                {{ comp.type }}
              </Badge>
            </td>
            <td data-label="Provider">
              <span :class="$style.providerBadge">{{ comp.provider }}</span>
            </td>
            <td data-label="Connection">
              <span v-if="comp.connection" :class="$style.connectionName">{{ comp.connection.name }}</span>
              <span v-else :class="$style.standalone">Standalone</span>
            </td>
            <td data-label="Health">
              <HealthBadge status="healthy" />
            </td>
            <td data-label="Actions">
              <div class="table-actions">
                <IconButton
                  v-if="comp.type === 'camera'"
                  variant="ghost"
                  size="sm"
                  title="Live Preview"
                  @click="emit('preview', comp)"
                >
                  <Eye />
                </IconButton>
                <IconButton
                  variant="danger"
                  size="sm"
                  title="Delete"
                  @click="emit('delete', comp)"
                >
                  <Trash2 />
                </IconButton>
              </div>
            </td>
          </tr>
          <tr v-if="components.length === 0">
            <td colspan="6" class="table-empty">No components found matching filters.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style module>
.name {
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

.providerBadge {
  font-size: var(--font-size-xs);
  background-color: var(--bg-tertiary);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-md);
  text-transform: uppercase;
  font-weight: var(--font-weight-semibold);
  letter-spacing: var(--letter-spacing-wide);
  color: var(--text-secondary);
}

.connectionName {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
}

.standalone {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  font-style: italic;
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
    min-width: 0; /* Prevent overflow */
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

  .base-table td :global(.table-actions) {
    justify-content: flex-end;
    width: 100%;
    max-width: 100%;
  }

  .name {
    font-size: var(--font-size-lg);
    border-bottom-width: 2px !important;
    max-width: 100% !important;
  }
}
</style>
