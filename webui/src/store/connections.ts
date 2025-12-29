import { ref } from 'vue'
import { defineStore } from 'pinia'
import { connectionsApi } from '../services/api'
import { useCrudStore } from '../composables/useCrudStore'
import type { Connection, ConnectionCreate, ConnectionUpdate } from '../types'

export const useConnectionsStore = defineStore('connections', () => {
  const crud = useCrudStore<Connection, ConnectionCreate, ConnectionUpdate>(
    connectionsApi
  )

  const healthStatuses = ref<Record<string, 'healthy' | 'unhealthy' | 'unknown' | 'loading'>>({})

  async function fetchHealth(id: string) {
    healthStatuses.value[id] = 'loading'
    try {
      const response = await connectionsApi.health(id)
      healthStatuses.value[id] = response.data.healthy ? 'healthy' : 'unhealthy'
    } catch (e) {
      healthStatuses.value[id] = 'unhealthy'
    }
  }

  async function fetchAll() {
    await crud.fetchAll()
    crud.items.value.forEach(conn => {
      fetchHealth(conn.id)
    })
  }

  async function create(data: ConnectionCreate) {
    const conn = await crud.create(data)
    fetchHealth(conn.id)
    return conn
  }

  async function update(id: string, data: ConnectionUpdate) {
    const conn = await crud.update(id, data)
    fetchHealth(conn.id)
    return conn
  }

  return {
    connections: crud.items,
    loading: crud.loading,
    error: crud.error,
    healthStatuses,
    fetchAll,
    fetchHealth,
    create,
    update,
    remove: crud.remove
  }
})
