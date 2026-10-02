-- Migration: Add forensic triage metadata fields
-- Run this in Supabase SQL Editor or via psql

-- Add new columns to classification_results
ALTER TABLE classification_results
  ADD COLUMN IF NOT EXISTS model_version VARCHAR(50) DEFAULT '1.0',
  ADD COLUMN IF NOT EXISTS threshold FLOAT DEFAULT 0.7,
  ADD COLUMN IF NOT EXISTS processing_time_ms INT,
  ADD COLUMN IF NOT EXISTS preprocessing_steps TEXT,
  ADD COLUMN IF NOT EXISTS explanation_method VARCHAR(50),
  ADD COLUMN IF NOT EXISTS risk_level VARCHAR(20);

-- Update audit_logs to use actor/event_type/event_details
ALTER TABLE audit_logs
  RENAME COLUMN action TO event_type;

ALTER TABLE audit_logs
  RENAME COLUMN performed_by TO actor;

ALTER TABLE audit_logs
  RENAME COLUMN details_json TO event_details;

-- Update examiner_reviews to use decision/examiner_id
ALTER TABLE examiner_reviews
  RENAME COLUMN reviewer_id TO examiner_id;

ALTER TABLE examiner_reviews
  RENAME COLUMN reviewer_decision TO decision;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_audit_logs_evidence_id ON audit_logs(evidence_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_examiner_reviews_evidence_id ON examiner_reviews(evidence_id);
CREATE INDEX IF NOT EXISTS idx_classification_results_evidence_id ON classification_results(evidence_id);
