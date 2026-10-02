import { useQuery } from '@tanstack/react-query'
import { getModelComparison } from '../services/modelComparison'
import { CheckCircle2, AlertTriangle } from 'lucide-react'

interface ModelRow {
  model: string
  f1: number | null
  runtime: string
  explainability: string
  selected: boolean
  avg_runtime_ms?: number
  error?: string
  warning?: string | null
}

export default function ModelComparison() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['model-comparison'],
    queryFn: getModelComparison,
  })

  if (isLoading) return <div className="p-6">Loading model comparison...</div>
  if (error) return <div className="p-6 text-red-600">Failed to load model comparison.</div>
  if (!data || !data.models) return <div className="p-6">No comparison data available.</div>

  const rows: ModelRow[] = data.models || []
  const warnings: string[] = data.warnings || []
  const meta = data.meta || {}

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-2">Inter-Model Comparison</h1>
      <p className="text-gray-600 mb-6">
        Operational comparison against examiner decisions. This F1 score is distinct from the held-out multiclass Macro-F1 recorded during model training.
      </p>

      {warnings.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded p-4 mb-6">
          <h2 className="text-lg font-bold text-yellow-800 flex items-center gap-2 mb-2">
            <AlertTriangle size={20} /> Evaluation Warnings
          </h2>
          <ul className="list-disc list-inside text-sm text-yellow-700 space-y-1">
            {warnings.map((warning, idx) => (
              <li key={idx}>{warning}</li>
            ))}
          </ul>
          {meta.total_reviewed_pairs !== undefined && (
            <p className="text-xs text-yellow-600 mt-2">
              Reviewed evidence pairs used for this comparison: {meta.total_reviewed_pairs}
            </p>
          )}
        </div>
      )}

      <div className="bg-white p-6 rounded shadow mb-6 overflow-x-auto">
        <h2 className="text-xl font-bold mb-4">Comparison Table</h2>
        <table className="min-w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left">Model</th>
              <th className="px-4 py-2 text-left">Operational F1 (%)</th>
              <th className="px-4 py-2 text-left">Runtime</th>
              <th className="px-4 py-2 text-left">Explainability</th>
              <th className="px-4 py-2 text-left">Selected</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.model} className={`border-t ${row.selected ? 'bg-green-50' : ''}`}>
                <td className="px-4 py-2 font-bold capitalize">{row.model}</td>
                <td className="px-4 py-2">
                  {row.f1 !== null && row.f1 !== undefined ? `${row.f1.toFixed(1)}%` : (
                    <span className="text-red-600" title={row.error}>{row.error || 'N/A'}</span>
                  )}
                  {row.warning && (
                    <p className="text-xs text-orange-600 mt-1 flex items-center gap-1">
                      <AlertTriangle size={12} /> {row.warning}
                    </p>
                  )}
                </td>
                <td className="px-4 py-2">
                  {row.runtime}
                  {row.avg_runtime_ms !== undefined && (
                    <span className="text-xs text-gray-500 block">{row.avg_runtime_ms.toFixed(1)} ms/example</span>
                  )}
                </td>
                <td className="px-4 py-2">{row.explainability}</td>
                <td className="px-4 py-2">
                  {row.selected ? (
                    <span className="inline-flex items-center gap-1 text-green-700 font-bold">
                      <CheckCircle2 size={16} /> Yes
                    </span>
                  ) : (
                    <span className="text-gray-500">No</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="bg-white p-6 rounded shadow">
        <h2 className="text-xl font-bold mb-4">Justification</h2>
        <p className="text-sm text-gray-700">{data.justification}</p>
      </div>
    </div>
  )
}
