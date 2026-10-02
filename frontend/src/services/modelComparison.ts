import { api } from './api'

export async function getModelComparison() {
  const res = await api.get('/model-comparison/model-comparison')
  return res.data
}

export async function getModelRegistry() {
  const res = await api.get('/model-comparison/registry')
  return res.data
}
