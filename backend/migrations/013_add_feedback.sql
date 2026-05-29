-- Migration 013: Add feedback column to app_users

ALTER TABLE app_users
ADD COLUMN IF NOT EXISTS feedback TEXT;
