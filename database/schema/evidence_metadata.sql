CREATE TABLE IF NOT EXISTS evidence_metadata (
    id INT AUTO_INCREMENT PRIMARY KEY,
    evidence_id INT NOT NULL,
    author_name VARCHAR(255),
    source_url VARCHAR(1024),
    original_timestamp TIMESTAMP NULL,
    filename VARCHAR(255),
    filesize INT,
    FOREIGN KEY (evidence_id) REFERENCES evidence(id) ON DELETE CASCADE
);
