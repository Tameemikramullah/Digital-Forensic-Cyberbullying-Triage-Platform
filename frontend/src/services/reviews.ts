import { api } from './api'

export async function createReview(evidenceId: number, data: { decision: string; notes?: string }) {
  const res = await api.post(`/reviews?evidence_id=${evidenceId}`, data)
  return res.data
}

export async function getReviews(evidenceId: number) {
  const res = await api.get(`/reviews/${evidenceId}`)
  return res.data
}
