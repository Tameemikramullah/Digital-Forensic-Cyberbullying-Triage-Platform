import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getReproducibilityReport, runReproducibilityTest } from '../services/forensic'

export default function Reproducibility() {
  const [modelName, setModelName] = useState('svm')
  const [testResult, setTestResult] = useState<any>(null)
  const [isRunning, setIsRunning] = useState(false)

  const { data: envReport, isLoading: envLoading } = useQuery({
    queryKey: ['reproducibility-report'],
    queryFn: getReproducibilityReport,
  })

  const handleRunTest = async () => {
    setIsRunning(true)
    try {
      const result = await runReproducibilityTest(modelName)
      setTestResult(result)
    } catch (err) {
      alert('Reproducibility test failed')
    } finally {
      setIsRunning(false)
    }
  }

  const exportJSON = () => {
    const payload = {
      environment: envReport,
      test_execution: testResult,
      exported_at: new Date().toISOString(),
    }
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `reproducibility-${modelName}-${new Date().toISOString().replace(/[:.]/g, '-')}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-2">Reproducibility</h1>
      <p className="text-gray-600 mb-6">
        This page provides the environment manifest and a fixed reproducibility test suite. Run the same test in a second environment and compare the JSON output to verify reproducibility.
      </p>

      <div className="bg-white p-6 rounded shadow mb-6">
        <h2 className="text-xl font-bold mb-4">Environment Manifest</h2>
        {envLoading ? (
          <p>Loading environment report...</p>
        ) : envReport ? (
          <div className="space-y-2 text-sm">
            <p><strong>Python:</strong> {envReport.python_version}</p>
            <p><strong>OS:</strong> {envReport.os}</p>
            <p><strong>Implementation:</strong> {envReport.python_implementation}</p>
            <p><strong>Machine:</strong> {envReport.machine}</p>
            <p><strong>Processor:</strong> {envReport.processor}</p>
            <p><strong>FastAPI:</strong> {envReport.framework_versions?.fastapi}</p>
            <p><strong>SQLAlchemy:</strong> {envReport.framework_versions?.sqlalchemy}</p>
            <p><strong>scikit-learn:</strong> {envReport.framework_versions?.scikit_learn}</p>
          </div>
        ) : (
          <p>No environment data available.</p>
        )}
      </div>

      <div className="bg-white p-6 rounded shadow mb-6">
        <h2 className="text-xl font-bold mb-4">Reproducibility Test Suite</h2>
        <p className="text-sm text-gray-600 mb-4">
          Execute the fixed test suite on the selected model. Export the result and compare it with an identical run in another environment.
        </p>
        <div className="flex gap-2 mb-4">
          <select className="border rounded p-2" value={modelName} onChange={e => setModelName(e.target.value)}>
            <option value="svm">SVM</option>
            <option value="logistic">Logistic</option>
            <option value="naive_bayes">Naive Bayes</option>
          </select>
          <button onClick={handleRunTest} disabled={isRunning} className="bg-blue-600 text-white px-4 py-2 rounded">
            {isRunning ? 'Running...' : 'Run Test'}
          </button>
          {testResult && (
            <button onClick={exportJSON} className="bg-gray-600 text-white px-4 py-2 rounded">
              Export JSON
            </button>
          )}
        </div>

        {testResult && (
          <div className="space-y-4">
            <div className="flex gap-4">
              <div className="bg-gray-50 p-3 rounded border">
                <p className="text-sm text-gray-600">Total Cases</p>
                <p className="text-xl font-bold">{testResult.total_cases}</p>
              </div>
              <div className="bg-gray-50 p-3 rounded border">
                <p className="text-sm text-gray-600">Passed</p>
                <p className="text-xl font-bold text-green-700">{testResult.passed_cases}</p>
              </div>
              <div className="bg-gray-50 p-3 rounded border">
                <p className="text-sm text-gray-600">Failed</p>
                <p className="text-xl font-bold text-red-700">{testResult.failed_cases_count}</p>
              </div>
              <div className="bg-gray-50 p-3 rounded border">
                <p className="text-sm text-gray-600">Overall</p>
                <p className={`text-xl font-bold ${testResult.all_passed ? 'text-green-700' : 'text-red-700'}`}>
                  {testResult.all_passed ? 'PASS' : 'FAIL'}
                </p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left">ID</th>
                    <th className="px-4 py-2 text-left">Input</th>
                    <th className="px-4 py-2 text-left">Prediction</th>
                    <th className="px-4 py-2 text-left">Confidence</th>
                    <th className="px-4 py-2 text-left">Expected</th>
                    <th className="px-4 py-2 text-left">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {testResult.results?.map((row: any) => (
                    <tr key={row.id} className="border-t">
                      <td className="px-4 py-2 font-mono text-xs">{row.id}</td>
                      <td className="px-4 py-2 text-xs max-w-xs truncate">{row.input}</td>
                      <td className="px-4 py-2 font-bold">{row.prediction}</td>
                      <td className="px-4 py-2">{(row.confidence * 100).toFixed(1)}%</td>
                      <td className="px-4 py-2">{row.expected_prediction}</td>
                      <td className="px-4 py-2">
                        {row.passed ? (
                          <span className="text-green-700 font-bold">PASS</span>
                        ) : (
                          <span className="text-red-700 font-bold">FAIL</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {testResult.failed_details?.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded p-4">
                <h3 className="font-bold text-red-800 mb-2">Failed Cases</h3>
                {testResult.failed_details.map((detail: any, i: number) => (
                  <p key={i} className="text-sm text-red-700">
                    {detail.id}: expected {detail.expected}, got {detail.actual}
                  </p>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
