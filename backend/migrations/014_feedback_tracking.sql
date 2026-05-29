ALTER TABLE app_users ADD COLUMN IF NOT EXISTS feedback_status VARCHAR(50) DEFAULT 'Open';
ALTER TABLE app_users ADD COLUMN IF NOT EXISTS feedback_dev_comments TEXT;
