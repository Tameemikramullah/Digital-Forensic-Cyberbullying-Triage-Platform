CREATE TABLE IF NOT EXISTS evidence (
    id INT AUTO_INCREMENT PRIMARY KEY,
    evidence_hash CHAR(64) UNIQUE NOT NULL,
    source_platform VARCHAR(100) NOT NULL,
    source_post_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    acquisition_date TIMESTAMP NOT NULL,
    uploaded_by INT NOT NULL,
    status ENUM('PENDING', 'TRIAGED', 'REVIEWED', 'CLOSED') NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (uploaded_by) REFERENCES users(id)
);
