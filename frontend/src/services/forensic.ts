import { api } from './api'

export async function getExplanations(evidenceId: number) {
  const res = await api.get(`/integrity/evidence/${evidenceId}/explanations`)
  return res.data
}

export async function verifyIntegrity(evidenceId: number) {
  const res = await api.post(`/integrity/evidence/${evidenceId}/verify-integrity`)
  return res.data
}

export async function getIntegrityChecks(evidenceId: number) {
  const res = await api.get(`/integrity/evidence/${evidenceId}/integrity-checks`)
  return res.data
}

export async function runRepeatabilityTest(evidenceId: number, modelName = 'svm', iterations = 10) {
  const res = await api.post(`/repeatability/evidence/${evidenceId}/repeatability?model_name=${modelName}&iterations=${iterations}`)
  return res.data
}

export async function getReproducibilityReport() {
  const res = await api.get('/reproducibility/reproducibility-report')
  return res.data
}

export async function runReproducibilityTest(modelName = 'svm') {
  const res = await api.get(`/reproducibility/reproducibility-test?model_name=${modelName}`)
  return res.data
}

export async function getOperationalMetrics() {
  const res = await api.get('/operational/operational-metrics')
  return res.data
}

export async function getSimulatedCases(modelName = 'svm') {
  const res = await api.get(`/operational/simulated-cases?model_name=${modelName}`)
  return res.data
}

export async function verifyAuditChain(evidenceId: number) {
  const res = await api.get(`/audit/verify/${evidenceId}`)
  return res.data
}
