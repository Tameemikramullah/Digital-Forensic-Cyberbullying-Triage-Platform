import { api } from './api'

export async function getAuditLogs(evidenceId: number) {
  const res = await api.get(`/audit/${evidenceId}`)
  return res.data
}

export async function getChainOfCustody(evidenceId: number) {
  const res = await api.get(`/audit/chain-of-custody/${evidenceId}`)
  return res.data
}
