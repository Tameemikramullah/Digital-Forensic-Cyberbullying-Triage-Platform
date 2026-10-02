CREATE TABLE IF NOT EXISTS classification_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    evidence_id INT NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) DEFAULT '1.0',
    prediction VARCHAR(50) NOT NULL,
    confidence_score FLOAT NOT NULL,
    risk_level VARCHAR(20),
    threshold FLOAT DEFAULT 0.7,
    processing_time_ms INT,
    preprocessing_steps TEXT,
    explanation_method VARCHAR(50),
    explanation_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (evidence_id) REFERENCES evidence(id) ON DELETE CASCADE
);
