import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getEvidenceById } from '../services/evidence'
import { triageEvidence, triageEnsemble } from '../services/triage'
import { createReview } from '../services/reviews'
import { getAuditLogs } from '../services/audit'
import { getExplanations, verifyIntegrity, verifyAuditChain } from '../services/forensic'
import { useState } from 'react'
import { Hash, FileText, CheckCircle, Download, Shield, Zap, FlaskConical } from 'lucide-react'
import ForensicTimeline from '../components/ForensicTimeline'
import RepeatabilityReport from '../components/RepeatabilityReport'

export default function EvidenceDetails() {
  const { id } = useParams()
  const { data: evidence, isLoading, error } = useQuery({ queryKey: ['evidence', id], queryFn: () => getEvidenceById(Number(id)) })
  const [triage, setTriage] = useState<any>(null)
  const [ensembleResult, setEnsembleResult] = useState<any>(null)
  const [explanations, setExplanations] = useState<any[]>([])
  const [integrity, setIntegrity] = useState<any>(null)
  const [reviewDecision, setReviewDecision] = useState('')
  const [reviewNotes, setReviewNotes] = useState('')
  const [reviewSuccess, setReviewSuccess] = useState(false)
  const [auditLogs, setAuditLogs] = useState<any[]>([])
  const [auditVerification, setAuditVerification] = useState<any>(null)
  const [isAuditLoading, setIsAuditLoading] = useState(false)
  const [isTriageLoading, setIsTriageLoading] = useState(false)
  const [isEnsembleLoading, setIsEnsembleLoading] = useState(false)

  const handleTriage = async () => {
    setIsTriageLoading(true)
    try {
      const result = await triageEvidence(Number(id))
      setTriage(result)
      setEnsembleResult(null)
      const logs = await getAuditLogs(Number(id))
      setAuditLogs(logs)
      const exps = await getExplanations(Number(id))
      setExplanations(exps)
    } catch (err) {
      alert('Triage failed')
    } finally {
      setIsTriageLoading(false)
    }
  }

  const handleEnsembleTriage = async () => {
    setIsEnsembleLoading(true)
    try {
      const result = await triageEnsemble(Number(id))
      setEnsembleResult(result)
      setTriage(null)
      const logs = await getAuditLogs(Number(id))
      setAuditLogs(logs)
      const exps = await getExplanations(Number(id))
      setExplanations(exps)
    } catch (err) {
      alert('Ensemble triage failed')
    } finally {
      setIsEnsembleLoading(false)
    }
  }

  const handleVerifyIntegrity = async () => {
    try {
      const result = await verifyIntegrity(Number(id))
      setIntegrity(result)
    } catch (err) {
      alert('Integrity verification failed')
    }
  }

  const handleVerifyAuditChain = async () => {
    setIsAuditLoading(true)
    try {
      const result = await verifyAuditChain(Number(id))
      setAuditVerification(result)
    } catch (err) {
      alert('Audit chain verification failed')
    } finally {
      setIsAuditLoading(false)
    }
  }

  const handleReview = async () => {
    if (!reviewDecision) return
    try {
      await createReview(Number(id), { decision: reviewDecision, notes: reviewNotes })
      setReviewSuccess(true)
      setReviewDecision('')
      setReviewNotes('')
    } catch (err) {
      alert('Review failed')
    }
  }

  const exportJSON = () => {
    const data = {
      evidence,
      triage,
      ensembleResult,
      explanations,
      integrity,
      audit_logs: auditLogs,
      exported_at: new Date().toISOString(),
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `evidence-${id}-export.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (isLoading) return <div className="p-6">Loading...</div>
  if (error) return <div className="p-6 text-red-600">Failed to load evidence. You may need to log in again.</div>
  if (!evidence) return <div className="p-6">Evidence not found</div>

  const riskLevel = triage?.risk_level || ensembleResult?.risk_level
  const riskColor = riskLevel === 'HIGH' ? 'text-red-600 bg-red-50 border-red-200' : riskLevel === 'MEDIUM' ? 'text-yellow-600 bg-yellow-50 border-yellow-200' : 'text-green-600 bg-green-50 border-green-200'

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Evidence #{evidence.id}</h1>
        <div className="flex gap-2">
          <button onClick={exportJSON} className="bg-gray-600 text-white px-4 py-2 rounded flex items-center gap-2">
            <Download size={16} /> Export JSON
          </button>
          <Link to={`/reports`} className="bg-gray-600 text-white px-4 py-2 rounded">Reports</Link>
          <Link to={`/audit/${evidence.id}`} className="bg-gray-600 text-white px-4 py-2 rounded">Audit Logs</Link>
          <Link to={`/review/${evidence.id}`} className="bg-blue-600 text-white px-4 py-2 rounded">Review</Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded shadow">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2"><FileText size={20} /> Evidence Information</h2>
          <p className="mb-2"><strong>Platform:</strong> {evidence.source_platform}</p>
          <p className="mb-2"><strong>Post ID:</strong> {evidence.source_post_id}</p>
          <p className="mb-2"><strong>Status:</strong> {evidence.status}</p>
          <p className="mb-2"><strong>Date:</strong> {new Date(evidence.acquisition_date).toLocaleString()}</p>
        </div>

        <div className="bg-white p-6 rounded shadow">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2"><Hash size={20} /> SHA-256 Hash</h2>
          <p className="break-all font-mono text-sm">{evidence.evidence_hash}</p>
          <button onClick={handleVerifyIntegrity} className="mt-2 bg-gray-600 text-white px-3 py-1 rounded text-sm flex items-center gap-1">
            <Shield size={14} /> Verify Integrity
          </button>
          {integrity && (
            <div className={`mt-2 p-2 rounded ${integrity.match ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
              {integrity.match ? '✓ VERIFIED' : '⚠ HASH MISMATCH'}
              <p className="text-xs">Checked: {integrity.checked_at}</p>
            </div>
          )}
        </div>
      </div>

      <div className="mt-6 bg-white p-6 rounded shadow">
        <h2 className="text-xl font-bold mb-4">Content</h2>
        <p className="whitespace-pre-wrap">{evidence.content}</p>
      </div>

      {evidence.evidence_metadata && (
        <div className="mt-6 bg-white p-6 rounded shadow">
          <h2 className="text-xl font-bold mb-4">Metadata</h2>
          <p className="mb-2"><strong>Author:</strong> {evidence.evidence_metadata.author_name}</p>
          <p className="mb-2"><strong>Source URL:</strong> {evidence.evidence_metadata.source_url}</p>
          <p className="mb-2"><strong>Filename:</strong> {evidence.evidence_metadata.filename}</p>
        </div>
      )}

      <div className="mt-6 flex gap-3">
        <button onClick={handleTriage} disabled={isTriageLoading || isEnsembleLoading} className="bg-green-600 text-white px-4 py-2 rounded flex items-center gap-2 disabled:bg-gray-400">
          <Zap size={16} /> {isTriageLoading ? 'Running...' : 'Run Quick Triage'}
        </button>
        <button onClick={handleEnsembleTriage} disabled={isTriageLoading || isEnsembleLoading} className="bg-blue-600 text-white px-4 py-2 rounded flex items-center gap-2 disabled:bg-gray-400">
          <FlaskConical size={16} /> {isEnsembleLoading ? 'Running...' : 'Run Full Triage'}
        </button>
      </div>

      {triage && (
        <div className="mt-6 bg-white p-6 rounded shadow">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2"><Zap size={20} /> Quick Triage Result</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div><p className="text-sm text-gray-600">Model</p><p className="font-bold">{triage.model_name || 'SVM'}</p></div>
            <div><p className="text-sm text-gray-600">Version</p><p className="font-bold">{triage.model_version}</p></div>
            <div><p className="text-sm text-gray-600">Threshold</p><p className="font-bold">{triage.threshold}</p></div>
            <div><p className="text-sm text-gray-600">Processing Time</p><p className="font-bold">{triage.processing_time_ms}ms</p></div>
            <div><p className="text-sm text-gray-600">Explanation Method</p><p className="font-bold">{triage.explanation_method}</p></div>
            <div><p className="text-sm text-gray-600">Risk Level</p><p className={`font-bold ${riskColor}`}>{triage.risk_level}</p></div>
            <div className="col-span-2"><p className="text-sm text-gray-600">Preprocessing</p><p className="text-sm">{triage.preprocessing_steps}</p></div>
          </div>
        </div>
      )}

      {ensembleResult && (
        <div className="mt-6 bg-white p-6 rounded shadow">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2"><FlaskConical size={20} /> Full Triage Result (Ensemble)</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div><p className="text-sm text-gray-600">Prediction</p><p className="font-bold">{ensembleResult.prediction}</p></div>
            <div><p className="text-sm text-gray-600">Confidence</p><p className="font-bold">{(ensembleResult.confidence * 100).toFixed(1)}%</p></div>
            <div><p className="text-sm text-gray-600">Risk Level</p><p className={`font-bold ${ensembleResult.risk_level === 'HIGH' ? 'text-red-600' : ensembleResult.risk_level === 'MEDIUM' ? 'text-yellow-600' : 'text-green-600'}`}>{ensembleResult.risk_level}</p></div>
            <div><p className="text-sm text-gray-600">Threshold</p><p className="font-bold">{ensembleResult.threshold}</p></div>
            <div><p className="text-sm text-gray-600">Processing Time</p><p className="font-bold">{ensembleResult.processing_time_ms}ms</p></div>
            <div><p className="text-sm text-gray-600">Explanation Method</p><p className="font-bold">{ensembleResult.explanation_method}</p></div>
            <div className="col-span-2"><p className="text-sm text-gray-600">Preprocessing</p><p className="text-sm">{ensembleResult.preprocessing_steps}</p></div>
          </div>

          {ensembleResult.requires_further_review && (
            <div className="bg-yellow-50 border border-yellow-200 rounded p-4 mb-4">
              <p className="font-bold text-yellow-800">Requires Further Review</p>
              <p className="text-sm text-yellow-700">This evidence has been flagged for human examiner review.</p>
            </div>
          )}

          <h3 className="font-bold mb-2">Model Votes</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
            {ensembleResult.votes?.map((vote: any) => (
              <div key={vote.model_name} className="border rounded p-3">
                <p className="text-xs text-gray-500 uppercase">{vote.model_name}</p>
                <p className="font-bold">{vote.prediction}</p>
                <p className="text-sm">{(vote.confidence * 100).toFixed(1)}%</p>
              </div>
            ))}
          </div>

          {ensembleResult.model_agreement && (
            <div className="bg-gray-50 border rounded p-3 mb-4">
              <p className="text-sm"><strong>Agreement:</strong> {ensembleResult.model_agreement.agreement}</p>
              <p className="text-sm"><strong>Confidence Spread:</strong> {(ensembleResult.model_agreement.confidence_spread * 100).toFixed(1)}%</p>
              <p className="text-sm"><strong>Disagreement Levels:</strong> {ensembleResult.model_agreement.disagreement_levels}</p>
              {ensembleResult.model_agreement.forced_review && (
                <p className="text-sm text-red-700 font-bold">Forced review due to model disagreement</p>
              )}
            </div>
          )}
        </div>
      )}

      {(triage || ensembleResult) && (
        <div className="mt-6 bg-white p-6 rounded shadow">
          <h2 className="text-xl font-bold mb-4">Triage Result</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="border rounded p-4">
              <p className="text-sm text-gray-600">Prediction</p>
              <p className="text-2xl font-bold">{triage?.prediction || ensembleResult?.prediction}</p>
            </div>
            <div className="border rounded p-4">
              <p className="text-sm text-gray-600">Confidence</p>
              <p className="text-2xl font-bold">{((triage?.confidence || ensembleResult?.confidence) * 100).toFixed(1)}%</p>
            </div>
            <div className={`border rounded p-4 ${riskColor}`}>
              <p className="text-sm">Risk Level</p>
              <p className="text-2xl font-bold">{triage?.risk_level || ensembleResult?.risk_level}</p>
            </div>
          </div>

          {(triage?.requires_further_review || ensembleResult?.requires_further_review) && (
            <div className="bg-yellow-50 border border-yellow-200 rounded p-4 mb-6">
              <p className="font-bold text-yellow-800">Requires Further Review</p>
              <p className="text-sm text-yellow-700">This evidence has been flagged for human examiner review.</p>
            </div>
          )}

          <div className="border-t pt-6">
            <h3 className="font-bold mb-4">Examiner Decision</h3>
            {!reviewSuccess ? (
              <div className="space-y-4">
                <div>
                  <label className="block mb-2 text-sm font-bold">Decision</label>
                  <div className="flex gap-2">
                    <button type="button" onClick={() => setReviewDecision('CONFIRMED')} className={`px-4 py-2 rounded border ${reviewDecision === 'CONFIRMED' ? 'bg-green-600 text-white border-green-600' : 'bg-white hover:bg-green-50'}`}>Confirm</button>
                    <button type="button" onClick={() => setReviewDecision('REJECTED')} className={`px-4 py-2 rounded border ${reviewDecision === 'REJECTED' ? 'bg-red-600 text-white border-red-600' : 'bg-white hover:bg-red-50'}`}>Reject</button>
                    <button type="button" onClick={() => setReviewDecision('NEEDS_MORE_REVIEW')} className={`px-4 py-2 rounded border ${reviewDecision === 'NEEDS_MORE_REVIEW' ? 'bg-yellow-600 text-white border-yellow-600' : 'bg-white hover:bg-yellow-50'}`}>Escalate</button>
                  </div>
                </div>
                <div>
                  <label className="block mb-2 text-sm font-bold">Notes</label>
                  <textarea className="w-full p-2 border rounded" rows={3} value={reviewNotes} onChange={e => setReviewNotes(e.target.value)} placeholder="Examiner notes..." />
                </div>
                <button onClick={handleReview} disabled={!reviewDecision} className="bg-blue-600 text-white px-4 py-2 rounded disabled:bg-gray-400">Submit Review</button>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-green-700">
                <CheckCircle size={20} />
                <span>Review submitted successfully.</span>
              </div>
            )}
          </div>
        </div>
      )}

      {explanations.length > 0 && (triage || ensembleResult) && (
        <div className="mt-6 bg-white p-6 rounded shadow">
          <h2 className="text-xl font-bold mb-4">Why Was This Flagged?</h2>
          <div className="space-y-2">
            {explanations.map((exp: any) => (
              <div key={exp.id} className="flex justify-between items-center border-b pb-2">
                <span className="font-mono bg-gray-100 px-2 py-1 rounded">{exp.feature_name}</span>
                <span className="text-sm text-gray-700">Contribution: {exp.contribution.toFixed(4)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {(triage || ensembleResult) && (
        <div className="mt-6">
          <RepeatabilityReport />
        </div>
      )}

      {auditLogs.length > 0 && (
        <div className="mt-6 bg-white p-6 rounded shadow">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">Audit Timeline</h2>
            <button onClick={handleVerifyAuditChain} disabled={isAuditLoading} className="bg-gray-600 text-white px-3 py-1 rounded text-sm flex items-center gap-1">
              <Shield size={14} /> {isAuditLoading ? 'Verifying...' : 'Verify Chain'}
            </button>
          </div>
          {auditVerification && (
            <div className={`mb-4 p-3 rounded border ${auditVerification.overall_valid ? 'bg-green-50 border-green-200 text-green-700' : 'bg-red-50 border-red-200 text-red-700'}`}>
              <p className="font-bold">{auditVerification.overall_valid ? 'Chain Valid' : 'Chain Tampered'}</p>
              <p className="text-xs">Audit logs checked: {auditVerification.audit_chain.logs_checked} | Custody records checked: {auditVerification.custody_chain.records_checked}</p>
              {auditVerification.audit_chain.errors.length > 0 && (
                <ul className="text-xs mt-1 list-disc list-inside">
                  {auditVerification.audit_chain.errors.map((e: string, i: number) => <li key={i}>{e}</li>)}
                </ul>
              )}
              {auditVerification.custody_chain.errors.length > 0 && (
                <ul className="text-xs mt-1 list-disc list-inside">
                  {auditVerification.custody_chain.errors.map((e: string, i: number) => <li key={i}>{e}</li>)}
                </ul>
              )}
            </div>
          )}
          <ForensicTimeline events={auditLogs} />
        </div>
      )}
    </div>
  )
}
