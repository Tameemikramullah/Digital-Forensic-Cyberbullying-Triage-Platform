import { api } from './api'

export async function getModelEvaluation(modelName?: string) {
  const params = modelName ? `?model_name=${encodeURIComponent(modelName)}` : ''
  const res = await api.get(`/model-evaluation/evaluation${params}`)
  return res.data
}
