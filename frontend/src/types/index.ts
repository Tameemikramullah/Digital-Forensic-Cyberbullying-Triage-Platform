export interface User {
  id: number
  email: string
  role: 'ADMIN' | 'INVESTIGATOR' | 'REVIEWER'
  created_at: string
}

export interface Evidence {
  id: number
  evidence_hash: string
  source_platform: string
  source_post_id: string
  content: string
  acquisition_date: string
  uploaded_by: number
  status: 'PENDING' | 'TRIAGED' | 'REVIEWED' | 'CLOSED'
  created_at: string
  original_file_path?: string
  original_filesize?: number
  metadata?: EvidenceMetadata
  classification_results?: ClassificationResult[]
  examiner_reviews?: ExaminerReview[]
  audit_logs?: AuditLog[]
  chain_of_custody?: ChainOfCustody[]
}

export interface EvidenceMetadata {
  id: number
  evidence_id: number
  author_name?: string
  source_url?: string
  original_timestamp?: string
  filename?: string
  filesize?: number
}

export interface ClassificationResult {
  id: number
  evidence_id: number
  model_name: string
  prediction: string
  confidence_score: number
  explanation_summary?: string
  created_at: string
}

export interface ExaminerReview {
  id: number
  evidence_id: number
  reviewer_id: number
  reviewer_decision: string
  notes?: string
  reviewed_at: string
}

export interface AuditLog {
  id: number
  evidence_id: number
  action: string
  performed_by: number
  details_json?: string
  timestamp: string
}

export interface ChainOfCustody {
  id: number
  evidence_id: number
  action: string
  performed_by: number
  timestamp: string
}

export interface ExplanationResponse {
  prediction: string
  confidence: number
  risk_level: string
  requires_further_review: boolean
  model_version: string
  threshold: number
  processing_time_ms?: number
  preprocessing_steps?: string
  explanation_method?: string
  top_features: { term: string; impact: number }[]
  model_agreement?: {
    agreement: string
    confidence_spread: number
    disagreement_levels: number
    unique_predictions: string[]
    forced_review?: boolean
  }
}

export interface Explanation {
  id: number
  evidence_id: number
  model_name: string
  model_version: string
  explanation_method: string
  feature_name: string
  contribution: number
  created_at: string
}

export interface ModelVote {
  model_name: string
  prediction: string
  confidence: number
}

export interface EnsembleResponse {
  evidence_id: number
  prediction: string
  confidence: number
  risk_level: string
  requires_further_review: boolean
  threshold: number
  processing_time_ms?: number
  preprocessing_steps?: string
  explanation_method?: string
  explanation_summary: string
  top_features: { term: string; impact: number }[]
  votes: ModelVote[]
  model_agreement: {
    agreement: string
    confidence_spread: number
    disagreement_levels: number
    unique_predictions: string[]
    forced_review?: boolean
  }
}

export interface IntegrityCheck {
  id: number
  evidence_id: number
  original_hash: string
  current_hash: string
  match: boolean
  checked_at: string
}

export interface RepeatabilityTest {
  id: number
  evidence_id: number
  model_name: string
  iterations: number
  prediction_consistency: number
  confidence_variance: number
  explanation_consistency: number
  pass_fail: string
  details: any
  created_at: string
}

export interface OperationalMetrics {
  total_evidence: number
  triaged: number
  reviewed: number
  harmful: number
  benign: number
  flagged: number
  confirmed: number
  rejected: number
  escalated: number
  recall: number
  precision: number
  false_positive_rate: number
  false_negative_rate: number
  workload_reduction: number
  triage_reduction: number
}
