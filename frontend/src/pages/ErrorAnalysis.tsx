import { useQuery } from '@tanstack/react-query'
import { getErrorAnalysis } from '../services/errorAnalysis'
import { AlertTriangle, AlertCircle, HelpCircle, TrendingUp } from 'lucide-react'

interface ErrorItem {
  evidence_id: number
  source_platform: string
  content: string
  prediction: string
  confidence: number
  examiner_decision: string
  review_notes?: string
  model_name: string
  model_version: string
  threshold: number
  risk_level: string
}

interface Discussion {
  total_evaluated: number
  true_positives: number
  true_negatives: number
  false_positives_count: number
  false_negatives_count: number
  ambiguous_count: number
  error_rate: number
  false_positive_rate: number
  false_negative_rate: number
  category_counts?: Record<string, number>
  category_details?: Record<string, any[]>
}

function ErrorCard({ item, type }: { item: ErrorItem; type: 'fp' | 'fn' | 'amb' }) {
  const borderColor = type === 'fp' ? 'border-red-200' : type === 'fn' ? 'border-orange-200' : 'border-yellow-200'
  const bgColor = type === 'fp' ? 'bg-red-50' : type === 'fn' ? 'bg-orange-50' : 'bg-yellow-50'
  const title = type === 'fp' ? 'False Positive' : type === 'fn' ? 'False Negative' : 'Ambiguous Case'

  return (
    <div className={`border rounded p-4 ${borderColor} ${bgColor}`}>
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-bold text-sm">{title} — Evidence #{item.evidence_id}</h3>
        <span className="text-xs text-gray-600">{item.source_platform}</span>
      </div>
      <p className="text-sm mb-2 font-mono bg-white p-2 rounded border">{item.content}</p>
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div><strong>Prediction:</strong> {item.prediction}</div>
        <div><strong>Confidence:</strong> {(item.confidence * 100).toFixed(1)}%</div>
        <div><strong>Examiner Decision:</strong> {item.examiner_decision}</div>
        <div><strong>Risk Level:</strong> {item.risk_level}</div>
        <div><strong>Model:</strong> {item.model_name} v{item.model_version}</div>
        <div><strong>Threshold:</strong> {item.threshold}</div>
      </div>
      {item.review_notes && (
        <div className="mt-2 text-xs text-gray-700">
          <strong>Examiner Notes:</strong> {item.review_notes}
        </div>
      )}
    </div>
  )
}

export default function ErrorAnalysis() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['error-analysis'],
    queryFn: getErrorAnalysis,
  })

  if (isLoading) return <div className="p-6">Loading error analysis...</div>
  if (error) return <div className="p-6 text-red-600">Failed to load error analysis.</div>
  if (!data) return <div className="p-6">No error analysis data available.</div>

  const falsePositives: ErrorItem[] = data.false_positives || []
  const falseNegatives: ErrorItem[] = data.false_negatives || []
  const ambiguousCases: ErrorItem[] = data.ambiguous_cases || []
  const discussion: Discussion = data.discussion || {}
  const categoryCounts = discussion.category_counts || {}
  const categoryDetails = discussion.category_details || {}

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-2">Structured Error Analysis</h1>
      <p className="text-gray-600 mb-6">
        Systematic review of model mistakes to identify failure modes and improvement opportunities.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded shadow border border-red-100">
          <p className="text-sm text-gray-600">False Positives</p>
          <p className="text-2xl font-bold text-red-600">{falsePositives.length}</p>
        </div>
        <div className="bg-white p-4 rounded shadow border border-orange-100">
          <p className="text-sm text-gray-600">False Negatives</p>
          <p className="text-2xl font-bold text-orange-600">{falseNegatives.length}</p>
        </div>
        <div className="bg-white p-4 rounded shadow border border-yellow-100">
          <p className="text-sm text-gray-600">Ambiguous Cases</p>
          <p className="text-2xl font-bold text-yellow-600">{ambiguousCases.length}</p>
        </div>
        <div className="bg-white p-4 rounded shadow">
          <p className="text-sm text-gray-600">Error Rate</p>
          <p className="text-2xl font-bold">{discussion.error_rate?.toFixed(1) || 0}%</p>
        </div>
      </div>

      {(Object.keys(categoryCounts).length > 0) && (
        <div className="bg-white p-6 rounded shadow mb-6">
          <h2 className="text-xl font-bold mb-4">Forensic Error Taxonomy</h2>
          <p className="text-sm text-gray-600 mb-4">
            Errors are categorized into forensic failure modes based on examiner review notes and content analysis. Categories may overlap when multiple factors are present.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            {Object.entries(categoryCounts).map(([category, count]) => (
              <div key={category} className="border rounded p-3">
                <p className="text-xs text-gray-500 uppercase">{category.replace(/_/g, ' ')}</p>
                <p className="text-2xl font-bold">{count as number}</p>
              </div>
            ))}
          </div>
          <div className="space-y-4">
            {Object.entries(categoryDetails).map(([category, items]) => (
              <div key={category} className="border rounded p-4">
                <h3 className="font-bold mb-2">{category.replace(/_/g, ' ')}</h3>
                <p className="text-xs text-gray-600 mb-2">
                  {(categoryDetails[category] as any[]).length} case(s)
                </p>
                <div className="space-y-2">
                  {(items as any[]).slice(0, 5).map((item: any, i: number) => (
                    <div key={i} className="text-sm border-b pb-2">
                      <p className="font-mono text-xs bg-gray-100 p-1 rounded">Evidence #{item.evidence_id}</p>
                      <p className="text-xs text-gray-700 mt-1">{item.content}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        <span className="font-bold">Error:</span> {item.error_type} | <span className="font-bold">Prediction:</span> {item.prediction} | <span className="font-bold">Decision:</span> {item.examiner_decision}
                      </p>
                      {item.review_notes && (
                        <p className="text-xs text-gray-600 mt-1 italic">"{item.review_notes}"</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div className="bg-white p-6 rounded shadow">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2"><AlertTriangle className="text-red-500" size={20} /> False Positives</h2>
          <p className="text-sm text-gray-600 mb-4">
            Benign content incorrectly flagged as cyberbullying. These represent unnecessary review burden and potential false accusations.
          </p>
          <div className="space-y-4">
            {falsePositives.length === 0 && <p className="text-sm text-gray-500">No false positives recorded.</p>}
            {falsePositives.map(item => (
              <ErrorCard key={item.evidence_id} item={item} type="fp" />
            ))}
          </div>
        </div>

        <div className="bg-white p-6 rounded shadow">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2"><AlertCircle className="text-orange-500" size={20} /> False Negatives</h2>
          <p className="text-sm text-gray-600 mb-4">
            Cyberbullying content missed by the model. These are the most critical failures as harmful content goes unflagged.
          </p>
          <div className="space-y-4">
            {falseNegatives.length === 0 && <p className="text-sm text-gray-500">No false negatives recorded.</p>}
            {falseNegatives.map(item => (
              <ErrorCard key={item.evidence_id} item={item} type="fn" />
            ))}
          </div>
        </div>

        <div className="bg-white p-6 rounded shadow">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2"><HelpCircle className="text-yellow-500" size={20} /> Ambiguous Cases</h2>
          <p className="text-sm text-gray-600 mb-4">
            Low-confidence predictions or cases requiring additional review. These highlight content where the model is uncertain.
          </p>
          <div className="space-y-4">
            {ambiguousCases.length === 0 && <p className="text-sm text-gray-500">No ambiguous cases recorded.</p>}
            {ambiguousCases.map(item => (
              <ErrorCard key={item.evidence_id} item={item} type="amb" />
            ))}
          </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded shadow">
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2"><TrendingUp size={20} /> Discussion</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-bold mb-2">Summary Statistics</h3>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between"><span>Total Evaluated:</span><span className="font-bold">{discussion.total_evaluated || 0}</span></div>
              <div className="flex justify-between"><span>True Positives:</span><span className="font-bold">{discussion.true_positives || 0}</span></div>
              <div className="flex justify-between"><span>True Negatives:</span><span className="font-bold">{discussion.true_negatives || 0}</span></div>
              <div className="flex justify-between"><span>False Positive Rate:</span><span className="font-bold text-red-600">{discussion.false_positive_rate?.toFixed(1) || 0}%</span></div>
              <div className="flex justify-between"><span>False Negative Rate:</span><span className="font-bold text-orange-600">{discussion.false_negative_rate?.toFixed(1) || 0}%</span></div>
            </div>
          </div>
          <div>
            <h3 className="font-bold mb-2">Key Observations</h3>
            <ul className="text-sm text-gray-700 space-y-1 list-disc list-inside">
              <li>False positives often involve sarcasm, slang, or context-dependent language.</li>
              <li>False negatives may stem from subtle harassment, coded language, or implicit threats.</li>
              <li>Ambiguous cases highlight the importance of human-in-the-loop review for borderline content.</li>
              <li>Threshold calibration and feature engineering should target reducing false negatives while maintaining precision.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
