import { useQuery } from '@tanstack/react-query'
import { getModelEvaluation } from '../services/modelEvaluation'
import { Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { FlaskConical, Activity, SearchX, GitCompare } from 'lucide-react'

const COLORS = ['#10b981', '#ef4444', '#f59e0b', '#3b82f6']

const relatedTools = [
  { to: '/threshold-calibration', label: 'Threshold Calibration', desc: 'Sweep thresholds and justify selection', icon: FlaskConical, color: 'bg-purple-600' },
  { to: '/operational-evaluation', label: 'Operational Evaluation', desc: 'Recall, precision, workload reduction', icon: Activity, color: 'bg-teal-600' },
  { to: '/error-analysis', label: 'Error Analysis', desc: 'False positives, false negatives, ambiguous cases', icon: SearchX, color: 'bg-red-600' },
  { to: '/model-comparison', label: 'Model Comparison', desc: 'Compare SVM, BERT, CNN, Logistic, Naive Bayes', icon: GitCompare, color: 'bg-gray-700' },
]

export default function ModelPerformanceDashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['model-evaluation'],
    queryFn: () => getModelEvaluation(),
  })

  if (isLoading) return <div className="p-6">Loading model evaluation...</div>
  if (error) return <div className="p-6 text-red-600">Failed to load evaluation data.</div>
  if (!data || data.total_evaluated === 0) return <div className="p-6">No evaluated evidence available. Run triage and submit examiner reviews to see metrics.</div>

  const cm = data.confusion_matrix || {}
  const pieData = [
    { name: 'True Positive', value: cm.tp || 0 },
    { name: 'False Positive', value: cm.fp || 0 },
    { name: 'False Negative', value: cm.fn || 0 },
    { name: 'True Negative', value: cm.tn || 0 },
  ]

  const barData = [
    { name: 'Accuracy', value: data.accuracy },
    { name: 'Precision', value: data.precision },
    { name: 'Recall', value: data.recall },
    { name: 'F1', value: data.f1 },
    { name: 'ROC AUC', value: data.roc_auc },
    { name: 'FPR', value: data.false_positive_rate },
    { name: 'FNR', value: data.false_negative_rate },
  ]

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-2">ML Model Performance Dashboard</h1>
      <p className="text-gray-600 mb-6">
        Model: <span className="font-bold">{data.model_name}</span> | Evaluated Evidence: <span className="font-bold">{data.total_evaluated}</span>
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded shadow">
          <p className="text-sm text-gray-600">Accuracy</p>
          <p className="text-2xl font-bold">{data.accuracy.toFixed(1)}%</p>
        </div>
        <div className="bg-white p-4 rounded shadow">
          <p className="text-sm text-gray-600">Precision</p>
          <p className="text-2xl font-bold">{data.precision.toFixed(1)}%</p>
        </div>
        <div className="bg-white p-4 rounded shadow">
          <p className="text-sm text-gray-600">Recall</p>
          <p className="text-2xl font-bold">{data.recall.toFixed(1)}%</p>
        </div>
        <div className="bg-white p-4 rounded shadow">
          <p className="text-sm text-gray-600">F1 Score</p>
          <p className="text-2xl font-bold">{data.f1.toFixed(1)}%</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="bg-white p-6 rounded shadow">
          <h2 className="text-xl font-bold mb-4">Performance Metrics</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis domain={[0, 100]} />
              <Tooltip formatter={(value: any) => `${value.toFixed(1)}%`} />
              <Legend />
              <Bar dataKey="value" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white p-6 rounded shadow">
          <h2 className="text-xl font-bold mb-4">Confusion Matrix</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
              {pieData.map((_entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
            <div>TP: {cm.tp}</div>
            <div>FP: {cm.fp}</div>
            <div>FN: {cm.fn}</div>
            <div>TN: {cm.tn}</div>
          </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded shadow mb-6">
        <h2 className="text-xl font-bold mb-4">Error Rates</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-600">False Positive Rate</p>
            <p className="text-2xl font-bold text-red-600">{data.false_positive_rate.toFixed(1)}%</p>
            <p className="text-xs text-gray-500">Benign evidence incorrectly flagged as harmful</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">False Negative Rate</p>
            <p className="text-2xl font-bold text-orange-600">{data.false_negative_rate.toFixed(1)}%</p>
            <p className="text-xs text-gray-500">Harmful evidence missed by the model</p>
          </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded shadow">
        <h2 className="text-xl font-bold mb-4">Related Analysis</h2>
        <p className="text-sm text-gray-600 mb-4">Drill down from model performance into deeper forensic analysis.</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {relatedTools.map(tool => (
            <Link key={tool.to} to={tool.to} className="border rounded p-4 hover:shadow-md transition-shadow">
              <div className={`${tool.color} text-white p-2 rounded-full w-10 h-10 flex items-center justify-center mb-3`}>
                <tool.icon size={20} />
              </div>
              <p className="font-bold">{tool.label}</p>
              <p className="text-sm text-gray-600">{tool.desc}</p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
