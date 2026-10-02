import { useQuery } from '@tanstack/react-query'
import { getThresholdCalibration } from '../services/thresholdCalibration'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts'

export default function ThresholdCalibration() {
  const { data, isLoading } = useQuery({
    queryKey: ['threshold-calibration'],
    queryFn: () => getThresholdCalibration(),
  })

  if (isLoading) return <div className="p-6">Loading calibration study...</div>
  if (!data || !data.results) return <div className="p-6 text-gray-600">{data?.message || 'No calibration data available.'}</div>

  const chartData = data.results.map((r: any) => ({
    threshold: r.threshold,
    recall: r.recall,
    precision: r.precision,
    workloadReduction: r.workload_reduction,
    missedEvidenceRate: r.missed_evidence_rate,
  }))

  const selectedThreshold = data.selected_threshold ?? 0.7
  const reliabilityData = (data.reliability_data || []).map((item: any) => ({
    ...item,
    perfect: item.bin_mid,
  }))

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-2">Threshold Calibration Study</h1>
      <p className="text-gray-600 mb-6">
        Model: <span className="font-bold">{data.model_name}</span> | Reviewed Evidence: <span className="font-bold">{data.total_reviewed}</span> | Actual Harmful: <span className="font-bold">{data.actual_harmful}</span>
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded shadow">
          <p className="text-sm text-gray-600">Selected Threshold</p>
          <p className="text-2xl font-bold">{selectedThreshold.toFixed(2)}</p>
        </div>
        <div className="bg-white p-4 rounded shadow">
          <p className="text-sm text-gray-600">Brier Score</p>
          <p className="text-2xl font-bold">{data.brier_score?.toFixed(4) ?? 'N/A'}</p>
          <p className="text-xs text-gray-500">Lower is better</p>
        </div>
        <div className="bg-white p-4 rounded shadow">
          <p className="text-sm text-gray-600">ECE</p>
          <p className="text-2xl font-bold">{data.ece?.toFixed(4) ?? 'N/A'}</p>
          <p className="text-xs text-gray-500">Expected Calibration Error</p>
        </div>
        <div className="bg-white p-4 rounded shadow">
          <p className="text-sm text-gray-600">Actual Harmful / Total</p>
          <p className="text-2xl font-bold">{data.actual_harmful} / {data.total_reviewed}</p>
        </div>
      </div>

      {reliabilityData.length > 0 && (
        <div className="bg-white p-6 rounded shadow mb-6">
          <h2 className="text-xl font-bold mb-4">Reliability Diagram</h2>
          <p className="text-sm text-gray-600 mb-4">
            This plot shows how well the model's predicted probabilities match observed frequencies. Perfect calibration follows the diagonal line.
          </p>
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={reliabilityData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="bin_mid" label={{ value: 'Mean Predicted Probability', position: 'insideBottom', offset: -10 }} />
              <YAxis domain={[0, 1]} label={{ value: 'Observed Frequency', angle: -90, position: 'insideLeft' }} />
              <Tooltip formatter={(value: any) => value.toFixed(4)} />
              <Legend />
              <Line type="monotone" dataKey="bin_accuracy" stroke="#10b981" name="Observed Accuracy" strokeWidth={2} />
              <Line type="monotone" dataKey="bin_confidence" stroke="#3b82f6" name="Mean Confidence" strokeWidth={2} />
              <Line type="monotone" dataKey="perfect" stroke="#9ca3af" name="Perfect Calibration" strokeWidth={1} strokeDasharray="5 5" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="bg-white p-6 rounded shadow mb-6 overflow-x-auto">
        <h2 className="text-xl font-bold mb-4">Calibration Table</h2>
        <table className="min-w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left">Threshold</th>
              <th className="px-4 py-2 text-left">Recall (%)</th>
              <th className="px-4 py-2 text-left">Precision (%)</th>
              <th className="px-4 py-2 text-left">Workload Reduction (%)</th>
              <th className="px-4 py-2 text-left">Missed Evidence Rate (%)</th>
              <th className="px-4 py-2 text-left">Flagged / Total</th>
              <th className="px-4 py-2 text-left">TP / FP / FN / TN</th>
            </tr>
          </thead>
          <tbody>
            {data.results.map((row: any) => (
              <tr key={row.threshold} className={`border-t ${row.threshold === selectedThreshold ? 'bg-blue-50' : ''}`}>
                <td className="px-4 py-2 font-mono font-bold">{row.threshold.toFixed(2)}</td>
                <td className="px-4 py-2">{row.recall.toFixed(1)}%</td>
                <td className="px-4 py-2">{row.precision.toFixed(1)}%</td>
                <td className="px-4 py-2">{row.workload_reduction.toFixed(1)}%</td>
                <td className="px-4 py-2">{row.missed_evidence_rate.toFixed(1)}%</td>
                <td className="px-4 py-2">{row.flagged_count} / {row.total_reviewed}</td>
                <td className="px-4 py-2 text-xs">
                  {row.true_positives} / {row.false_positives} / {row.false_negatives} / {row.true_negatives}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="bg-white p-6 rounded shadow mb-6">
        <h2 className="text-xl font-bold mb-4">Metrics by Threshold</h2>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="threshold" label={{ value: 'Threshold', position: 'insideBottom', offset: -10 }} />
            <YAxis domain={[0, 100]} label={{ value: 'Percentage (%)', angle: -90, position: 'insideLeft' }} />
            <Tooltip formatter={(value: any) => `${value.toFixed(1)}%`} />
            <Legend />
            <Bar dataKey="recall" fill="#10b981" name="Recall" />
            <Bar dataKey="precision" fill="#3b82f6" name="Precision" />
            <Bar dataKey="workloadReduction" fill="#f59e0b" name="Workload Reduction" />
            <Bar dataKey="missedEvidenceRate" fill="#ef4444" name="Missed Evidence Rate" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="bg-white p-6 rounded shadow">
        <h2 className="text-xl font-bold mb-4">Selected Threshold Justification</h2>
        <p className="text-sm text-gray-600 mb-2">
          The current triage threshold is <span className="font-bold">{selectedThreshold.toFixed(2)}</span>. This value was selected to balance recall, precision, workload reduction, and missed-evidence rate based on the calibration study above.
        </p>
        <p className="text-sm text-gray-600">
          At threshold {selectedThreshold.toFixed(2)}, the system achieves high precision while maintaining acceptable recall, ensuring that flagged evidence is highly likely to be harmful and reducing the overall review burden on human examiners.
        </p>
        <p className="text-sm text-gray-600 mt-2">
          Brier Score: <span className="font-bold">{data.brier_score?.toFixed(4) ?? 'N/A'}</span> (lower is better) | ECE: <span className="font-bold">{data.ece?.toFixed(4) ?? 'N/A'}</span>
        </p>
      </div>
    </div>
  )
}
