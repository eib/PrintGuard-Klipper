import { defineStore } from 'pinia'
import { connectionsApi } from '../services/api'
import { useCrudStore } from '../composables/useCrudStore'
import type { Connection, ConnectionCreate, ConnectionUpdate } from '../types'

export const useConnectionsStore = defineStore('connections', () => {
  const crud = useCrudStore<Connection, ConnectionCreate, ConnectionUpdate>(
    connectionsApi
  )

  return {
    connections: crud.items,
    loading: crud.loading,
    error: crud.error,
    fetchAll: crud.fetchAll,
    create: crud.create,
    update: crud.update,
    remove: crud.remove
  }
})
