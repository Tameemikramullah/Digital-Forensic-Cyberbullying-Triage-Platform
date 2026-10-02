import { api } from './api'

export async function getThresholdCalibration(modelName = 'svm') {
  const res = await api.get(`/threshold-calibration/calibration?model_name=${modelName}`)
  return res.data
}
