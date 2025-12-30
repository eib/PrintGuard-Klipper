import { ref, type Ref } from 'vue'

interface CrudApi<T, C, U> {
  list: (params?: any) => Promise<{ data: T[] }>
  create: (data: C) => Promise<{ data: T }>
  update?: (id: string, data: U) => Promise<{ data: T }>
  delete: (id: string, ...args: any[]) => Promise<any>
}

export function useCrudStore<T extends { id: string }, C, U>(
  api: CrudApi<T, C, U>
) {
  const items = ref<T[]>([]) as Ref<T[]>
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchAll(params?: any) {
    loading.value = true
    error.value = null
    try {
      const response = await api.list(params)
      items.value = response.data
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Failed to fetch'
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  async function create(data: C): Promise<T> {
    const response = await api.create(data)
    items.value.push(response.data)
    return response.data
  }

  async function update(id: string, data: U): Promise<T> {
    if (!api.update) throw new Error('Update not implemented for this resource')
    const response = await api.update(id, data)
    const index = items.value.findIndex(item => item.id === id)
    if (index !== -1) {
      items.value[index] = response.data
    }
    return response.data
  }

  async function remove(id: string, ...args: any[]) {
    await api.delete(id, ...args)
    items.value = items.value.filter(item => item.id !== id)
  }

  return {
    items,
    loading,
    error,
    fetchAll,
    create,
    update,
    remove
  }
}

