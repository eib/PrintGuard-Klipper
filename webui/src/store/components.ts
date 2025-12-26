import { defineStore } from 'pinia'
import { ref } from 'vue'
import { componentsApi } from '../services/api'
import type { Component, ComponentCreate, ComponentUpdate } from '../types'

export const useComponentsStore = defineStore('components', () => {
  const components = ref<Component[]>([])
  const componentRegistry = ref<Record<string, Component>>({})
  const loading = ref(false)
  const error = ref<string | null>(null)
  const filters = ref<any>({})

  async function fetchAll(newFilters?: any, replace = false) {
    if (newFilters) {
      if (replace) {
        filters.value = { ...newFilters }
      } else {
        filters.value = { ...filters.value, ...newFilters }
      }
    } else if (replace) {
      filters.value = {}
    }

    loading.value = true
    error.value = null
    try {
      const response = await componentsApi.list(filters.value)
      components.value = response.data

      response.data.forEach(comp => {
        componentRegistry.value[comp.id] = comp
      })
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Failed to fetch components'
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  async function create(data: ComponentCreate) {
    const response = await componentsApi.create(data)
    components.value.push(response.data)
    componentRegistry.value[response.data.id] = response.data
    return response.data
  }

  async function update(id: string, data: ComponentUpdate) {
    const response = await componentsApi.update(id, data)
    const index = components.value.findIndex(c => c.id === id)
    if (index !== -1) {
      components.value[index] = response.data
    }
    componentRegistry.value[id] = response.data
    return response.data
  }

  async function remove(id: string, force = false) {
    await componentsApi.delete(id, force)
    components.value = components.value.filter(c => c.id !== id)
    delete componentRegistry.value[id]
  }

  return {
    components,
    componentRegistry,
    loading,
    filters,
    error,
    fetchAll,
    create,
    update,
    remove
  }
})

