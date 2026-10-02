CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    evidence_id INT NOT NULL,
    actor VARCHAR(255) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (evidence_id) REFERENCES evidence(id) ON DELETE CASCADE
);
