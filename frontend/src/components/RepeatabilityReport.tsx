import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useMutation } from '@tanstack/react-query'
import { runRepeatabilityTest } from '../services/forensic'
import { getModelRegistry } from '../services/modelComparison'

export default function RepeatabilityReport() {
  const { id } = useParams()
  const [iterations, setIterations] = useState(10)
  const [modelName, setModelName] = useState('svm')

  const { data: registry } = useQuery({
    queryKey: ['model-registry'],
    queryFn: getModelRegistry,
  })

  const registryModels = registry?.models || {}
  const availableModels = Array.isArray(registryModels)
    ? registryModels.filter(m => m.status === 'completed').map(m => m.model_name)
    : Object.values(registryModels)
        .filter((m: any) => m.status === 'completed')
        .map((m: any) => m.model_name)

  const mutation = useMutation({
    mutationFn: () => runRepeatabilityTest(Number(id), modelName, iterations),
  })

  const result = mutation.data

  return (
    <div className="bg-white p-6 rounded shadow">
      <h2 className="text-xl font-bold mb-4">Repeatability Testing</h2>
      <p className="text-sm text-gray-600 mb-4">
        Run the same model on the same evidence multiple times to verify deterministic behavior.
      </p>
      <div className="flex gap-2 mb-4">
        <input className="border rounded p-2" type="number" value={iterations} onChange={e => setIterations(Number(e.target.value))} min={2} max={100} />
        <select className="border rounded p-2" value={modelName} onChange={e => setModelName(e.target.value)}>
          {availableModels.length > 0 ? (
            availableModels.map(name => (
              <option key={name} value={name}>{name}</option>
            ))
          ) : (
            <option value="svm">SVM</option>
          )}
        </select>
        <button onClick={() => mutation.mutate()} disabled={mutation.isPending} className="bg-blue-600 text-white px-4 py-2 rounded">
          {mutation.isPending ? 'Running...' : 'Run Test'}
        </button>
      </div>

      {result && (
        <div className="space-y-2">
          <div className="flex justify-between"><span>Prediction Consistency:</span><span className="font-bold">{result.prediction_consistency}%</span></div>
          <div className="flex justify-between"><span>Confidence Variance:</span><span className="font-bold">{result.confidence_variance.toFixed(2)}%</span></div>
          <div className="flex justify-between"><span>Explanation Consistency:</span><span className="font-bold">{result.explanation_consistency}%</span></div>
          <div className={`p-2 rounded ${result.pass_fail === 'PASS' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
            Result: {result.pass_fail}
          </div>
        </div>
      )}
    </div>
  )
}
