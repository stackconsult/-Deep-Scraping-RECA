-- Enhanced RECA Leads Database Schema
-- Migration: Add quality_score, data_hash, and change tracking

-- Drop existing table if upgrading (backup first!)
-- DROP TABLE IF EXISTS agent_changes CASCADE;
-- DROP TABLE IF EXISTS agents CASCADE;

-- Main agents table
CREATE TABLE IF NOT EXISTS agents (
    id SERIAL PRIMARY KEY,
    drill_id VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(255),
    middle_name VARCHAR(255),
    last_name VARCHAR(255),
    full_name VARCHAR(512),
    status VARCHAR(100),
    brokerage VARCHAR(512),
    city VARCHAR(255),
    sector VARCHAR(255),
    aka VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    quality_score INTEGER DEFAULT 0,
    data_hash VARCHAR(64),
    scraped_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_verified TIMESTAMP
);

-- Change tracking table
CREATE TABLE IF NOT EXISTS agent_changes (
    id SERIAL PRIMARY KEY,
    drill_id VARCHAR(255) REFERENCES agents(drill_id) ON DELETE CASCADE,
    field_name VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    changed_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_agents_drill_id ON agents(drill_id);
CREATE INDEX IF NOT EXISTS idx_agents_last_name ON agents(last_name);
CREATE INDEX IF NOT EXISTS idx_agents_city ON agents(city);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_brokerage ON agents(brokerage);
CREATE INDEX IF NOT EXISTS idx_agents_quality_score ON agents(quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_agents_email ON agents(email) WHERE email IS NOT NULL AND email != '';
CREATE INDEX IF NOT EXISTS idx_agents_phone ON agents(phone) WHERE phone IS NOT NULL AND phone != '';

CREATE INDEX IF NOT EXISTS idx_changes_drill_id ON agent_changes(drill_id);
CREATE INDEX IF NOT EXISTS idx_changes_changed_at ON agent_changes(changed_at DESC);

-- Add quality_score to existing table if upgrading
-- ALTER TABLE agents ADD COLUMN IF NOT EXISTS quality_score INTEGER DEFAULT 0;
-- ALTER TABLE agents ADD COLUMN IF NOT EXISTS data_hash VARCHAR(64);
-- ALTER TABLE agents ADD COLUMN IF NOT EXISTS last_verified TIMESTAMP;

-- Update existing records to calculate quality score
-- UPDATE agents SET quality_score = (
--     (CASE WHEN email IS NOT NULL AND email != '' THEN 40 ELSE 0 END) +
--     (CASE WHEN phone IS NOT NULL AND phone != '' THEN 30 ELSE 0 END) +
--     (CASE WHEN brokerage IS NOT NULL AND brokerage != '' THEN 20 ELSE 0 END) +
--     (CASE WHEN city IS NOT NULL AND city != '' THEN 10 ELSE 0 END)
-- ) WHERE quality_score = 0;

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for auto-updating updated_at
DROP TRIGGER IF EXISTS update_agents_updated_at ON agents;
CREATE TRIGGER update_agents_updated_at
    BEFORE UPDATE ON agents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- View for licensed agents only
CREATE OR REPLACE VIEW licensed_agents AS
SELECT * FROM agents
WHERE status LIKE '%Licensed%'
  AND status NOT LIKE '%suspend%'
  AND status NOT LIKE '%cancel%'
  AND status NOT LIKE '%withdrawal%';

-- View for high-quality leads (score >= 70)
CREATE OR REPLACE VIEW high_quality_leads AS
SELECT * FROM licensed_agents
WHERE quality_score >= 70;

-- Stats view
CREATE OR REPLACE VIEW agent_stats AS
SELECT
    COUNT(*) as total_agents,
    COUNT(CASE WHEN status LIKE '%Licensed%' THEN 1 END) as licensed_count,
    COUNT(CASE WHEN email IS NOT NULL AND email != '' THEN 1 END) as with_email,
    COUNT(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 END) as with_phone,
    COUNT(CASE WHEN email IS NOT NULL AND email != '' AND phone IS NOT NULL AND phone != '' THEN 1 END) as with_both,
    ROUND(AVG(quality_score)::numeric, 1) as avg_quality_score,
    MAX(updated_at) as last_update
FROM agents;

-- Grant permissions (adjust user as needed)
-- GRANT SELECT, INSERT, UPDATE ON agents TO your_app_user;
-- GRANT SELECT, INSERT ON agent_changes TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE agents_id_seq TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE agent_changes_id_seq TO your_app_user;

-- Verify schema
SELECT 'Schema created successfully!' as status;
SELECT * FROM agent_stats;
