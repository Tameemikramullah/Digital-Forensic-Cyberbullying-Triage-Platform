import { api } from './api'

export async function exportEvidence(evidenceId: number, format: 'json' | 'pdf' = 'json') {
  const res = await api.get(`/export/evidence/${evidenceId}/export?format=${format}`)
  return res.data
}
