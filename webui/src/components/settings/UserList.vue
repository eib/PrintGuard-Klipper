<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminApi } from '../../services/api'
import Button from '../ui/Button.vue'
import Input from '../ui/Input.vue'
import Badge from '../ui/Badge.vue'
import MultiSelect from '../ui/MultiSelect.vue'
import { AVAILABLE_SCOPES } from '../../types/scopes'
import type { User } from '../../types'

const users = ref<User[]>([])
const loading = ref(false)
const showAdd = ref(false)
const newUser = ref({ username: '', password: '', scopes: ['printer:read', 'rtc:stream'] })

const scopeOptions = AVAILABLE_SCOPES.map(s => ({ value: s, label: s }))

async function fetchUsers() {
  loading.value = true
  try {
    const response = await adminApi.listUsers()
    users.value = response.data
  } finally {
    loading.value = false
  }
}

async function handleAdd() {
  try {
    await adminApi.createUser({
      ...newUser.value,
      scopes: newUser.value.scopes.join(' ')
    })
    showAdd.value = false
    newUser.value = { username: '', password: '', scopes: ['printer:read', 'rtc:stream'] }
    fetchUsers()
  } catch (e) {
    alert('Failed to add user')
  }
}

async function handleDelete(username: string) {
  if (!confirm(`Delete user ${username}?`)) return
  try {
    await adminApi.deleteUser(username)
    fetchUsers()
  } catch (e) {
    alert('Failed to delete user')
  }
}

onMounted(fetchUsers)
</script>

<template>
  <div :class="$style.section">
    <div :class="$style.header">
      <h3>Users</h3>
      <Button variant="ghost" size="sm" @click="showAdd = !showAdd">
        {{ showAdd ? 'Cancel' : '+ Add User' }}
      </Button>
    </div>

    <div v-if="showAdd" :class="$style.addCard">
      <form @submit.prevent="handleAdd" :class="$style.form">
        <Input v-model="newUser.username" placeholder="Username" required />
        <Input v-model="newUser.password" type="password" placeholder="Password" required />
        <MultiSelect
          v-model="newUser.scopes"
          :options="scopeOptions"
          placeholder="Select Scopes"
        />
        <Button type="submit" variant="primary">Create User</Button>
      </form>
    </div>

    <div :class="$style.tableWrapper">
      <div class="table-container">
        <table class="base-table">
          <thead>
            <tr>
              <th>Username</th>
              <th>Scopes</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.username">
              <td data-label="Username"><strong>{{ user.username }}</strong></td>
              <td data-label="Scopes">
                <div :class="$style.scopes">
                  <Badge v-for="s in user.scopes.split(' ')" :key="s" variant="neutral" size="sm">{{ s }}</Badge>
                </div>
              </td>
              <td data-label="Actions">
                <Button variant="danger" size="sm" @click="handleDelete(user.username)">Delete</Button>
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

.addCard {
  background-color: var(--card-bg);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  box-shadow: var(--shadow-sm);
}

.form {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr auto;
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
}

@media (max-width: 480px) {
  .addCard {
    padding: var(--space-4);
  }

  .form {
    gap: var(--space-2);
  }
}
</style>

