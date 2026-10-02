import { useQuery } from '@tanstack/react-query'
import { getModelRegistry } from '../services/modelComparison'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { CheckCircle2, XCircle, Clock, Database } from 'lucide-react'

interface ModelRecord {
  model_name: string
  version: string
  status: string
  trained_at: string
  training_time_seconds: number
  train_samples: number
  test_samples: number
  evaluation?: {
    accuracy: number
    macro_f1: number
    weighted_f1: number
    per_class?: Record<string, any>
  }
  error?: string
}

export default function TrainingPerformance() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['model-registry'],
    queryFn: getModelRegistry,
  })

  if (isLoading) return <div className="p-6">Loading training performance...</div>
  if (error) return <div className="p-6 text-red-600">Failed to load training registry.</div>

  const registry = data || {}
  const modelsDict = registry.models || {}
  const models: ModelRecord[] = Array.isArray(modelsDict)
    ? modelsDict
    : Object.values(modelsDict)
  const completedModels = models.filter(m => m.status === 'completed' && m.evaluation)

  const chartData = completedModels.map(m => ({
    model: m.model_name,
    accuracy: m.evaluation!.accuracy * 100,
    macro_f1: m.evaluation!.macro_f1 * 100,
    weighted_f1: m.evaluation!.weighted_f1 * 100,
    training_time: m.training_time_seconds,
    train_samples: m.train_samples,
    test_samples: m.test_samples,
  }))

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-2">Training Performance</h1>
      <p className="text-gray-600 mb-6">
        Held-out test set metrics recorded during model training. These are distinct from operational metrics computed against examiner decisions.
      </p>

      {chartData.length > 0 && (
        <div className="bg-white p-6 rounded shadow mb-6">
          <h2 className="text-xl font-bold mb-4">Performance Metrics (Test Set)</h2>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="model" />
              <YAxis domain={[0, 100]} label={{ value: 'Percentage (%)', angle: -90, position: 'insideLeft' }} />
              <Tooltip formatter={(value: any) => `${value.toFixed(1)}%`} />
              <Legend />
              <Bar dataKey="accuracy" fill="#10b981" name="Accuracy" />
              <Bar dataKey="macro_f1" fill="#3b82f6" name="Macro F1" />
              <Bar dataKey="weighted_f1" fill="#f59e0b" name="Weighted F1" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="bg-white p-6 rounded shadow mb-6 overflow-x-auto">
        <h2 className="text-xl font-bold mb-4">Model Registry</h2>
        <table className="min-w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left">Model</th>
              <th className="px-4 py-2 text-left">Status</th>
              <th className="px-4 py-2 text-left">Version</th>
              <th className="px-4 py-2 text-left">Trained At</th>
              <th className="px-4 py-2 text-left">Train / Test Samples</th>
              <th className="px-4 py-2 text-left">Training Time</th>
              <th className="px-4 py-2 text-left">Accuracy</th>
              <th className="px-4 py-2 text-left">Macro F1</th>
              <th className="px-4 py-2 text-left">Weighted F1</th>
            </tr>
          </thead>
          <tbody>
            {models.map((model) => (
              <tr key={model.model_name} className="border-t">
                <td className="px-4 py-2 font-bold capitalize">{model.model_name}</td>
                <td className="px-4 py-2">
                  {model.status === 'completed' ? (
                    <span className="inline-flex items-center gap-1 text-green-700 font-bold">
                      <CheckCircle2 size={16} /> Completed
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-red-700 font-bold">
                      <XCircle size={16} /> Failed
                    </span>
                  )}
                </td>
                <td className="px-4 py-2">{model.version}</td>
                <td className="px-4 py-2 text-xs">{model.trained_at ? new Date(model.trained_at).toLocaleString() : 'N/A'}</td>
                <td className="px-4 py-2">
                  <span className="inline-flex items-center gap-1">
                    <Database size={14} /> {model.train_samples} / {model.test_samples}
                  </span>
                </td>
                <td className="px-4 py-2">
                  <span className="inline-flex items-center gap-1">
                     <Clock size={14} /> {model.training_time_seconds != null ? Number(model.training_time_seconds).toFixed(1) + 's' : 'N/A'}
                  </span>
                </td>
                <td className="px-4 py-2">
                  {model.evaluation ? `${(model.evaluation.accuracy * 100).toFixed(1)}%` : 'N/A'}
                </td>
                <td className="px-4 py-2">
                  {model.evaluation ? `${(model.evaluation.macro_f1 * 100).toFixed(1)}%` : 'N/A'}
                </td>
                <td className="px-4 py-2">
                  {model.evaluation ? `${(model.evaluation.weighted_f1 * 100).toFixed(1)}%` : 'N/A'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {models.some(m => m.status === 'failed') && (
        <div className="bg-red-50 border border-red-200 rounded p-4 mb-6">
          <h2 className="text-lg font-bold text-red-800 mb-2">Failed Models</h2>
          <div className="space-y-2">
            {models.filter(m => m.status === 'failed').map(model => (
              <div key={model.model_name} className="text-sm text-red-700">
                <span className="font-bold capitalize">{model.model_name}:</span> {model.error}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}