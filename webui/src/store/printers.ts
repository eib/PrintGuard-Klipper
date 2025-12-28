import { defineStore } from 'pinia'
import { ref } from 'vue'
import { printersApi, notificationsApi } from '../services/api'
import { getPushEndpoint } from '../services/notifications'
import type { Printer, PrinterCreate, PrinterUpdate } from '../types'

export const usePrintersStore = defineStore('printers', () => {
  const printers = ref<Printer[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const endpoint = await getPushEndpoint()
      const response = await printersApi.list(endpoint || undefined)
      printers.value = response.data
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Failed to fetch printers'
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  async function create(data: PrinterCreate) {
    const response = await printersApi.create(data)
    printers.value.push(response.data)
    return response.data
  }

  async function update(id: string, data: PrinterUpdate) {
    const response = await printersApi.update(id, data)
    const index = printers.value.findIndex(p => p.id === id)
    if (index !== -1) {
      printers.value[index] = response.data
    }
    return response.data
  }

  async function remove(id: string) {
    await printersApi.delete(id)
    printers.value = printers.value.filter(p => p.id !== id)
  }

  async function sendCommand(id: string, cmd: string) {
    await printersApi.command(id, cmd)
    // Refresh the printer status
    const endpoint = await getPushEndpoint()
    const response = await printersApi.get(id, endpoint || undefined)
    const index = printers.value.findIndex(p => p.id === id)
    if (index !== -1) {
      printers.value[index] = response.data
    }
  }

  async function toggleNotifications(id: string, enabled: boolean) {
    const endpoint = await getPushEndpoint()
    await notificationsApi.togglePrinter(id, enabled, endpoint || undefined)
    const index = printers.value.findIndex(p => p.id === id)
    if (index !== -1) {
      printers.value[index].notifications_enabled = enabled
    }
  }

  async function toggleInference(id: string, action: 'start' | 'stop') {
    await printersApi.inferenceCommand(id, action)
    const index = printers.value.findIndex(p => p.id === id)
    if (index !== -1) {
      printers.value[index].inference_paused = action === 'stop'
    }
  }

  return {
    printers,
    loading,
    error,
    fetchAll,
    create,
    update,
    remove,
    sendCommand,
    toggleNotifications,
    toggleInference
  }
})

