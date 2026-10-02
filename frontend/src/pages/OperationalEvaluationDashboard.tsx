import { useQuery } from '@tanstack/react-query'
import { getEvidence } from '../services/evidence'
import { getOperationalMetrics, getSimulatedCases } from '../services/forensic'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { useState } from 'react'

export default function OperationalEvaluationDashboard() {
  const [modelName, setModelName] = useState('svm')
  const { data: evidence = [] } = useQuery({ queryKey: ['evidence'], queryFn: getEvidence })
  const { data: liveMetrics } = useQuery({ queryKey: ['operational-metrics'], queryFn: getOperationalMetrics })
  const { data: simulated, isLoading: simLoading } = useQuery({
    queryKey: ['simulated-cases', modelName],
    queryFn: () => getSimulatedCases(modelName),
  })

  const total = evidence.length
  const triaged = evidence.filter((e: any) => e.status === 'TRIAGED' || e.status === 'REVIEWED' || e.status === 'CLOSED')
  const reviewed = evidence.filter((e: any) => e.status === 'REVIEWED' || e.status === 'CLOSED')

  const confirmed = reviewed.filter((e: any) => e.examiner_reviews?.some((r: any) => r.decision === 'CONFIRMED')).length
  const rejected = reviewed.filter((e: any) => e.examiner_reviews?.some((r: any) => r.decision === 'REJECTED')).length
  const escalated = reviewed.filter((e: any) => e.examiner_reviews?.some((r: any) => r.decision === 'NEEDS_MORE_REVIEW')).length

  const harmful = evidence.filter((e: any) => e.classification_results?.some((c: any) => c.prediction && c.prediction !== 'not_cyberbullying')).length
  const benign = total - harmful
  const flagged = harmful

  const tp = confirmed
  const fp = rejected
  const fn = escalated
  const tn = benign - fp > 0 ? benign - fp : 0

  const recall = (tp + fn) > 0 ? (tp / (tp + fn)) * 100 : 0
  const precision = (tp + fp) > 0 ? (tp / (tp + fp)) * 100 : 0
  const fpr = (fp + tn) > 0 ? (fp / (fp + tn)) * 100 : 0
  const fnr = (tp + fn) > 0 ? (fn / (tp + fn)) * 100 : 0
  const workloadReduction = total > 0 ? ((total - flagged) / total) * 100 : 0
  const triageReduction = total > 0 ? ((total - triaged.length) / total) * 100 : 0

  const liveChartData = [
    { name: 'Recall', value: liveMetrics?.recall || recall },
    { name: 'Precision', value: liveMetrics?.precision || precision },
    { name: 'FPR', value: liveMetrics?.false_positive_rate || fpr },
    { name: 'FNR', value: liveMetrics?.false_negative_rate || fnr },
    { name: 'Workload Reduction', value: liveMetrics?.workload_reduction || workloadReduction },
    { name: 'Triage Reduction', value: liveMetrics?.triage_reduction || triageReduction },
  ]

  const simChartData = simulated ? [
    { name: 'Accuracy', value: simulated.accuracy },
    { name: 'Recall', value: simulated.recall },
    { name: 'Precision', value: simulated.precision },
    { name: 'F1', value: simulated.f1_score },
    { name: 'FPR', value: simulated.false_positive_rate },
    { name: 'FNR', value: simulated.false_negative_rate },
  ] : []

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Operational Evaluation Dashboard</h1>

      <div className="bg-white p-6 rounded shadow mb-6">
        <h2 className="text-xl font-bold mb-4">Live Operational Metrics</h2>
        <p className="text-sm text-gray-600 mb-4">
          Metrics computed from examiner-reviewed evidence in the database. These reflect real operational performance but require sufficient reviewed cases to be statistically reliable.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-white p-4 rounded shadow border">
            <p className="text-sm text-gray-600">Total Evidence</p>
            <p className="text-2xl font-bold">{total}</p>
          </div>
          <div className="bg-white p-4 rounded shadow border">
            <p className="text-sm text-gray-600">Triaged / Reviewed</p>
            <p className="text-2xl font-bold">{triaged.length} / {reviewed.length}</p>
          </div>
          <div className="bg-white p-4 rounded shadow border">
            <p className="text-sm text-gray-600">Harmful / Benign</p>
            <p className="text-2xl font-bold">{harmful} / {benign}</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded shadow">
            <h3 className="text-lg font-bold mb-4">Metrics</h3>
            <div className="space-y-2">
              <div className="flex justify-between"><span>Recall:</span><span className="font-bold">{((liveMetrics?.recall || recall).toFixed(1))}%</span></div>
              <div className="flex justify-between"><span>Precision:</span><span className="font-bold">{((liveMetrics?.precision || precision).toFixed(1))}%</span></div>
              <div className="flex justify-between"><span>False Positive Rate:</span><span className="font-bold">{((liveMetrics?.false_positive_rate || fpr).toFixed(1))}%</span></div>
              <div className="flex justify-between"><span>False Negative Rate:</span><span className="font-bold">{((liveMetrics?.false_negative_rate || fnr).toFixed(1))}%</span></div>
              <div className="flex justify-between"><span>Workload Reduction:</span><span className="font-bold">{((liveMetrics?.workload_reduction || workloadReduction).toFixed(1))}%</span></div>
              <div className="flex justify-between"><span>Triage Reduction:</span><span className="font-bold">{((liveMetrics?.triage_reduction || triageReduction).toFixed(1))}%</span></div>
            </div>
          </div>
          <div className="bg-white p-6 rounded shadow">
            <h3 className="text-lg font-bold mb-4">Visualization</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={liveChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis domain={[0, 100]} />
                <Tooltip formatter={(value: any) => `${value.toFixed(1)}%`} />
                <Bar dataKey="value" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded shadow mb-6">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h2 className="text-xl font-bold">Simulated Case Study</h2>
            <p className="text-sm text-gray-600">
              Controlled evaluation using a fixed set of {simulated?.total_cases || 0} cases with known ground truth labels. This provides credible operational metrics independent of real examiner reviews.
            </p>
          </div>
          <select className="border rounded p-2" value={modelName} onChange={e => setModelName(e.target.value)}>
            <option value="svm">SVM</option>
            <option value="logistic">Logistic</option>
            <option value="naive_bayes">Naive Bayes</option>
          </select>
        </div>

        {simLoading ? (
          <p>Loading simulated case results...</p>
        ) : simulated ? (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-gray-50 p-3 rounded border">
                <p className="text-sm text-gray-600">Total Cases</p>
                <p className="text-xl font-bold">{simulated.total_cases}</p>
              </div>
              <div className="bg-gray-50 p-3 rounded border">
                <p className="text-sm text-gray-600">Correct / Incorrect</p>
                <p className="text-xl font-bold">{simulated.correct} / {simulated.incorrect}</p>
              </div>
              <div className="bg-gray-50 p-3 rounded border">
                <p className="text-sm text-gray-600">Accuracy</p>
                <p className="text-xl font-bold">{simulated.accuracy.toFixed(1)}%</p>
              </div>
              <div className="bg-gray-50 p-3 rounded border">
                <p className="text-sm text-gray-600">F1 Score</p>
                <p className="text-xl font-bold">{simulated.f1_score.toFixed(1)}%</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div className="bg-white p-6 rounded shadow">
                <h3 className="text-lg font-bold mb-4">Simulated Metrics</h3>
                <div className="space-y-2">
                  <div className="flex justify-between"><span>Recall:</span><span className="font-bold">{simulated.recall.toFixed(1)}%</span></div>
                  <div className="flex justify-between"><span>Precision:</span><span className="font-bold">{simulated.precision.toFixed(1)}%</span></div>
                  <div className="flex justify-between"><span>False Positive Rate:</span><span className="font-bold">{simulated.false_positive_rate.toFixed(1)}%</span></div>
                  <div className="flex justify-between"><span>False Negative Rate:</span><span className="font-bold">{simulated.false_negative_rate.toFixed(1)}%</span></div>
                </div>
              </div>
              <div className="bg-white p-6 rounded shadow">
                <h3 className="text-lg font-bold mb-4">Visualization</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={simChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis domain={[0, 100]} />
                    <Tooltip formatter={(value: any) => `${value.toFixed(1)}%`} />
                    <Bar dataKey="value" fill="#10b981" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="bg-white p-6 rounded shadow overflow-x-auto">
              <h3 className="text-lg font-bold mb-4">Case Results</h3>
              <table className="min-w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left">ID</th>
                    <th className="px-4 py-2 text-left">Category</th>
                    <th className="px-4 py-2 text-left">Content</th>
                    <th className="px-4 py-2 text-left">Ground Truth</th>
                    <th className="px-4 py-2 text-left">Prediction</th>
                    <th className="px-4 py-2 text-left">Confidence</th>
                    <th className="px-4 py-2 text-left">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {simulated.results?.map((row: any) => (
                    <tr key={row.id} className={`border-t ${row.correct ? '' : 'bg-red-50'}`}>
                      <td className="px-4 py-2 font-mono text-xs">{row.id}</td>
                      <td className="px-4 py-2 text-xs">{row.category}</td>
                      <td className="px-4 py-2 text-xs max-w-xs truncate">{row.content}</td>
                      <td className="px-4 py-2">{row.ground_truth}</td>
                      <td className="px-4 py-2 font-bold">{row.prediction}</td>
                      <td className="px-4 py-2">{(row.confidence * 100).toFixed(1)}%</td>
                      <td className="px-4 py-2">
                        {row.correct ? (
                          <span className="text-green-700 font-bold">CORRECT</span>
                        ) : (
                          <span className="text-red-700 font-bold">INCORRECT</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        ) : (
          <p>No simulated case data available.</p>
        )}
      </div>
    </div>
  )
}
