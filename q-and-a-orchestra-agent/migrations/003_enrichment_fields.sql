-- Migration: Add Enrichment Metadata Columns
-- Adds fields to store detailed results from the Enhanced Hybrid Email Agent

-- Add enrichment metadata columns
ALTER TABLE agents ADD COLUMN IF NOT EXISTS email_source VARCHAR(50);
ALTER TABLE agents ADD COLUMN IF NOT EXISTS enrichment_method VARCHAR(50);
ALTER TABLE agents ADD COLUMN IF NOT EXISTS validation_status VARCHAR(50);
ALTER TABLE agents ADD COLUMN IF NOT EXISTS email_confidence FLOAT DEFAULT 0.0;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS last_enriched_at TIMESTAMP;

-- Create index on verification status for quick filtering of valid leads
CREATE INDEX IF NOT EXISTS idx_agents_validation_status ON agents(validation_status);
CREATE INDEX IF NOT EXISTS idx_agents_email_confidence ON agents(email_confidence DESC);

-- Update stats view to include enrichment metrics
DROP VIEW IF EXISTS agent_stats;
CREATE OR REPLACE VIEW agent_stats AS
SELECT
    COUNT(*) as total_agents,
    COUNT(CASE WHEN status LIKE '%Licensed%' THEN 1 END) as licensed_count,
    COUNT(CASE WHEN email IS NOT NULL AND email != '' THEN 1 END) as with_email,
    COUNT(CASE WHEN email_source = 'brokerage_website' THEN 1 END) as from_website,
    COUNT(CASE WHEN email_source = 'pattern_generation' THEN 1 END) as from_pattern,
    COUNT(CASE WHEN validation_status = 'valid' THEN 1 END) as validated_emails,
    ROUND(AVG(quality_score)::numeric, 1) as avg_quality_score,
    ROUND(AVG(CASE WHEN email_confidence > 0 THEN email_confidence ELSE NULL END)::numeric, 2) as avg_confidence,
    MAX(updated_at) as last_update,
    MAX(last_enriched_at) as last_enrichment
FROM agents;
