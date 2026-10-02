import { api } from './api'

export async function getErrorAnalysis() {
  const res = await api.get('/error-analysis/error-analysis')
  return res.data
}
