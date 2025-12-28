import { defineStore } from 'pinia'
import { ref } from 'vue'
import { componentsApi } from '../services/api'
import { useCrudStore } from '../composables/useCrudStore'
import type { Component, ComponentCreate, ComponentUpdate } from '../types'

export const useComponentsStore = defineStore('components', () => {
  const crud = useCrudStore<Component, ComponentCreate, ComponentUpdate>(
    componentsApi
  )
  const componentRegistry = ref<Record<string, Component>>({})
  const filters = ref<any>({})

  async function fetchAll(newFilters?: any, replace = false) {
    if (newFilters) {
      filters.value = replace ? { ...newFilters } : { ...filters.value, ...newFilters }
    } else if (replace) {
      filters.value = {}
    }
    
    await crud.fetchAll(filters.value)
    
    crud.items.value.forEach(comp => {
      componentRegistry.value[comp.id] = comp
    })
  }

  async function create(data: ComponentCreate) {
    const result = await crud.create(data)
    componentRegistry.value[result.id] = result
    return result
  }

  async function update(id: string, data: ComponentUpdate) {
    const result = await crud.update(id, data)
    componentRegistry.value[id] = result
    return result
  }

  async function remove(id: string, force = false) {
    await componentsApi.delete(id, force)
    crud.items.value = crud.items.value.filter(c => c.id !== id)
    delete componentRegistry.value[id]
  }

  return {
    components: crud.items,
    componentRegistry,
    loading: crud.loading,
    filters,
    error: crud.error,
    fetchAll,
    create,
    update,
    remove
  }
})
