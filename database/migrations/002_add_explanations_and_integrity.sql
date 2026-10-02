-- Migration: Add forensic triage tables and columns
-- Run in Supabase SQL Editor or psql

-- New tables
CREATE TABLE IF NOT EXISTS explanations (
    id SERIAL PRIMARY KEY,
    evidence_id INT NOT NULL REFERENCES evidence(id) ON DELETE CASCADE,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) DEFAULT '1.0',
    explanation_method VARCHAR(50) NOT NULL,
    feature_name VARCHAR(255) NOT NULL,
    contribution FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS repeatability_tests (
    id SERIAL PRIMARY KEY,
    evidence_id INT NOT NULL REFERENCES evidence(id) ON DELETE CASCADE,
    model_name VARCHAR(100) NOT NULL,
    iterations INT NOT NULL,
    prediction_consistency FLOAT NOT NULL,
    confidence_variance FLOAT NOT NULL,
    explanation_consistency FLOAT NOT NULL,
    pass_fail VARCHAR(20) NOT NULL,
    details_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS integrity_checks (
    id SERIAL PRIMARY KEY,
    evidence_id INT NOT NULL REFERENCES evidence(id) ON DELETE CASCADE,
    original_hash VARCHAR(64) NOT NULL,
    current_hash VARCHAR(64) NOT NULL,
    match INT NOT NULL,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add integrity columns to evidence
ALTER TABLE evidence ADD COLUMN IF NOT EXISTS integrity_status VARCHAR(20) DEFAULT 'UNVERIFIED';
ALTER TABLE evidence ADD COLUMN IF NOT EXISTS integrity_verified_at TIMESTAMP NULL;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_explanations_evidence_id ON explanations(evidence_id);
CREATE INDEX IF NOT EXISTS idx_repeatability_tests_evidence_id ON repeatability_tests(evidence_id);
CREATE INDEX IF NOT EXISTS idx_integrity_checks_evidence_id ON integrity_checks(evidence_id);
