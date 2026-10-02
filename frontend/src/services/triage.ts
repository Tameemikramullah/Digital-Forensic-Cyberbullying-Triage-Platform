import { api } from './api'
import type { ExplanationResponse, EnsembleResponse } from '../types'

export async function triageEvidence(evidenceId: number, modelName = 'svm') {
  const res = await api.post(`/triage/${evidenceId}`, { model_name: modelName })
  return res.data as ExplanationResponse
}

export async function getTriageResult(evidenceId: number) {
  const res = await api.get(`/triage/${evidenceId}`)
  return res.data
}

export async function triageEnsemble(evidenceId: number, modelNames: string[] = ['svm', 'logistic', 'naive_bayes', 'cnn', 'bert']) {
  const res = await api.post(`/triage/ensemble/${evidenceId}`, { model_names: modelNames })
  return res.data as EnsembleResponse
}
