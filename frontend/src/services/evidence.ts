import { api } from './api'

export async function uploadEvidence(formData: FormData) {
  const res = await api.post('/evidence/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

export async function bulkUploadEvidence(items: Array<{ source_platform: string; source_post_id: string; content: string; acquisition_date: string; metadata?: { author_name?: string; source_url?: string } }>) {
  const res = await api.post('/evidence/bulk-upload', { items })
  return res.data
}

export async function getEvidence() {
  const res = await api.get('/evidence')
  return res.data
}

export async function getEvidenceById(id: number) {
  const res = await api.get(`/evidence/${id}`)
  return res.data
}

export async function deleteEvidence(id: number) {
  return api.delete(`/evidence/${id}`)
}
