-- Evidence-file preservation and tamper-evident log/custody chain support.
-- Apply this migration before deploying a database created by earlier scripts.

ALTER TABLE evidence ADD COLUMN IF NOT EXISTS original_file_path VARCHAR(1024);
ALTER TABLE evidence ADD COLUMN IF NOT EXISTS original_filesize INTEGER;

ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS previous_hash VARCHAR(64);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS entry_hash VARCHAR(64);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entry_hash ON audit_logs(entry_hash);

ALTER TABLE chain_of_custody ADD COLUMN IF NOT EXISTS previous_hash VARCHAR(64);
ALTER TABLE chain_of_custody ADD COLUMN IF NOT EXISTS entry_hash VARCHAR(64);
CREATE INDEX IF NOT EXISTS idx_chain_of_custody_entry_hash ON chain_of_custody(entry_hash);
