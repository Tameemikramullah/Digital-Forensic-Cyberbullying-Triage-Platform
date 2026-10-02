import { useQuery } from '@tanstack/react-query'
import { getEvidence } from '../services/evidence'
import { Link } from 'react-router-dom'
import { FileText, Clock, AlertTriangle, CheckCircle, FlaskConical, Activity, SearchX, GitCompare } from 'lucide-react'

export default function Dashboard() {
  const { data: evidence = [] } = useQuery({ queryKey: ['evidence'], queryFn: getEvidence })

  const total = evidence.length
  const pending = evidence.filter((e: any) => e.status === 'PENDING').length
  const triaged = evidence.filter((e: any) => e.status === 'TRIAGED').length
  const reviewed = evidence.filter((e: any) => e.status === 'REVIEWED').length

  const cards = [
    { label: 'Total Evidence', value: total, icon: FileText, color: 'bg-blue-500' },
    { label: 'Pending', value: pending, icon: Clock, color: 'bg-yellow-500' },
    { label: 'Triaged', value: triaged, icon: AlertTriangle, color: 'bg-orange-500' },
    { label: 'Reviewed', value: reviewed, icon: CheckCircle, color: 'bg-green-500' },
  ]

  const navCards = [
    { label: 'Threshold Calibration', desc: 'Threshold sweep study and justification', to: '/threshold-calibration', icon: FlaskConical, color: 'bg-purple-600' },
    { label: 'Operational Evaluation', desc: 'Recall, precision, workload reduction', to: '/operational-evaluation', icon: Activity, color: 'bg-teal-600' },
    { label: 'Error Analysis', desc: 'False positives, false negatives, ambiguous cases', to: '/error-analysis', icon: SearchX, color: 'bg-red-600' },
    { label: 'Model Comparison', desc: 'Compare SVM, BERT, CNN, Logistic, Naive Bayes', to: '/model-comparison', icon: GitCompare, color: 'bg-gray-700' },
  ]

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <Link to="/evidence/upload" className="bg-blue-600 text-white px-4 py-2 rounded">Upload Evidence</Link>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {cards.map(card => (
          <div key={card.label} className="bg-white p-4 rounded shadow">
            <div className={`${card.color} text-white p-2 rounded-full w-10 h-10 flex items-center justify-center mb-2`}>
              <card.icon size={20} />
            </div>
            <p className="text-gray-600 text-sm">{card.label}</p>
            <p className="text-2xl font-bold">{card.value}</p>
          </div>
        ))}
      </div>

      <div className="mt-8">
        <h2 className="text-xl font-bold mb-4">Analytics & Evaluation</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {navCards.map(card => (
            <Link key={card.to} to={card.to} className="bg-white p-4 rounded shadow hover:shadow-md transition-shadow">
              <div className={`${card.color} text-white p-2 rounded-full w-10 h-10 flex items-center justify-center mb-3`}>
                <card.icon size={20} />
              </div>
              <p className="font-bold">{card.label}</p>
              <p className="text-sm text-gray-600">{card.desc}</p>
            </Link>
          ))}
        </div>
      </div>

      <div className="mt-8">
        <Link to="/evidence" className="text-blue-600 hover:underline">View Evidence Queue →</Link>
      </div>
    </div>
  )
}
