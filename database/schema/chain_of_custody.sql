CREATE TABLE IF NOT EXISTS chain_of_custody (
    id INT AUTO_INCREMENT PRIMARY KEY,
    evidence_id INT NOT NULL,
    action VARCHAR(100) NOT NULL,
    performed_by INT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (evidence_id) REFERENCES evidence(id) ON DELETE CASCADE,
    FOREIGN KEY (performed_by) REFERENCES users(id)
);
