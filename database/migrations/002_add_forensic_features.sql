-- Migration: Add forensic triage and explainability tables
-- Run this in Supabase SQL Editor or via psql

-- Create explanations table
CREATE TABLE IF NOT EXISTS explanations (
    id SERIAL PRIMARY KEY,
    evidence_id INT NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) DEFAULT '1.0',
    explanation_method VARCHAR(50) NOT NULL,
    feature_name VARCHAR(255) NOT NULL,
    contribution FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (evidence_id) REFERENCES evidence(id) ON DELETE CASCADE
);

-- Create repeatability_tests table
CREATE TABLE IF NOT EXISTS repeatability_tests (
    id SERIAL PRIMARY KEY,
    evidence_id INT NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    iterations INT NOT NULL,
    prediction_consistency FLOAT NOT NULL,
    confidence_variance FLOAT NOT NULL,
    explanation_consistency FLOAT NOT NULL,
    pass_fail VARCHAR(20) NOT NULL,
    details_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (evidence_id) REFERENCES evidence(id) ON DELETE CASCADE
);

-- Create integrity_checks table
CREATE TABLE IF NOT EXISTS integrity_checks (
    id SERIAL PRIMARY KEY,
    evidence_id INT NOT NULL,
    original_hash VARCHAR(64) NOT NULL,
    current_hash VARCHAR(64) NOT NULL,
    match INT NOT NULL,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (evidence_id) REFERENCES evidence(id) ON DELETE CASCADE
);

-- Add integrity columns to evidence table
ALTER TABLE evidence
  ADD COLUMN IF NOT EXISTS integrity_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
  ADD COLUMN IF NOT EXISTS integrity_verified_at TIMESTAMP;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_explanations_evidence_id ON explanations(evidence_id);
CREATE INDEX IF NOT EXISTS idx_repeatability_tests_evidence_id ON repeatability_tests(evidence_id);
CREATE INDEX IF NOT EXISTS idx_integrity_checks_evidence_id ON integrity_checks(evidence_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_evidence_id ON audit_logs(evidence_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_examiner_reviews_evidence_id ON examiner_reviews(evidence_id);
CREATE INDEX IF NOT EXISTS idx_classification_results_evidence_id ON classification_results(evidence_id);
