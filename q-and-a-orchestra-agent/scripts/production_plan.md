# RECA Lead Scraper - Production Implementation Plan

## Executive Summary
Transform existing 18,832 scraped agents into production-ready lead database with:
- Email extraction via deep scrape
- Enhanced phone number scraping
- Incremental update detection
- PostgreSQL database with API
- Cloud Run deployment for scheduled re-scraping

## Current State Analysis
- ✅ 18,832 agents scraped (surface data)
- ✅ 15,535 actively licensed agents (prime leads)
- ❌ 0 emails extracted (deep scrape pending)
- ✅ All agents have drill_id (deep scrape ready)
- ✅ Checkpoint/resume system working
- ✅ Deduplication implemented

## Implementation Phases

### Phase 1: Deep Scrape Email Extraction (2-6 hours runtime)
**Goal**: Extract emails for all 18,832 agents via drillthrough

**Tasks**:
1. Run deep scrape with monitoring: `python scripts/full_sweep.py --deep --resume`
2. Create parallel worker version for faster extraction
3. Add progress tracking dashboard
4. Implement graceful error handling

**Expected Output**: `all_agents_deep.json` with email field populated

**Risk**: Rate limiting (mitigated by delays), session expiration (handled by re-init)

---

### Phase 2: Enhanced Field Extraction
**Goal**: Extract phone numbers and other contact fields from detail pages

**Tasks**:
1. Analyze RECA drillthrough HTML for phone patterns
2. Enhance `perform_drillthrough()` to extract phone, license number, license dates
3. Add secondary email extraction (alternate patterns)
4. Test on sample of 100 agents first

**Expected Fields**:
- Phone (office/mobile if available)
- License number
- License effective/expiry dates
- Professional designations (if visible)

---

### Phase 3: Data Validation & Cleanup
**Goal**: Production-ready, clean lead database

**Tasks**:
1. Create `scripts/filter_leads.py`:
   - Remove "Not Licensed" status
   - Remove suspended/cancelled
   - Validate email format
   - Normalize city names (Calgary, CALGARY → Calgary)
   - Deduplicate by drill_id

2. Create `scripts/enrich_leads.py`:
   - Parse brokerage type (RE/MAX, Century 21, etc.)
   - Extract city region (Calgary SE, Edmonton North, etc.)
   - Add lead quality score based on completeness
   - Flag leads with no email/phone as "incomplete"

3. Run validation: `python scripts/validate_data.py --input data/all_agents_deep.json`

**Expected Output**: `leads_clean.json` with 15K+ quality leads

---

### Phase 4: Incremental Update System
**Goal**: Daily/weekly updates without full re-scrape

**Tasks**:
1. Create `scripts/incremental_scraper.py`:
   - Load existing agents from database
   - Query RECA for each agent by drill_id
   - Detect changes: status, brokerage, email, phone
   - Flag new agents (not in database)
   - Update only changed records

2. Add change detection:
   - Hash agent record fields
   - Compare with database hash
   - Log changes to audit table

3. Create `scripts/new_agent_detector.py`:
   - Run A-Z sweep with "recently added" filter if available
   - Compare against database to find truly new agents

**Expected Output**: Daily delta updates, change audit log

---

### Phase 5: Database Integration
**Goal**: PostgreSQL database with optimized schema and API

**Tasks**:
1. Enhanced database schema:
   ```sql
   CREATE TABLE agents (
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
       email VARCHAR(255),
       phone VARCHAR(50),
       license_number VARCHAR(100),
       license_effective DATE,
       license_expiry DATE,
       quality_score INT,
       data_hash VARCHAR(64),
       scraped_at TIMESTAMP DEFAULT NOW(),
       updated_at TIMESTAMP DEFAULT NOW(),
       last_verified TIMESTAMP
   );
   
   CREATE TABLE agent_changes (
       id SERIAL PRIMARY KEY,
       drill_id VARCHAR(255) REFERENCES agents(drill_id),
       field_name VARCHAR(100),
       old_value TEXT,
       new_value TEXT,
       changed_at TIMESTAMP DEFAULT NOW()
   );
   
   CREATE INDEX idx_agents_status ON agents(status);
   CREATE INDEX idx_agents_city ON agents(city);
   CREATE INDEX idx_agents_brokerage ON agents(brokerage);
   CREATE INDEX idx_agents_quality ON agents(quality_score);
   ```

2. Setup Neon/Supabase PostgreSQL:
   - Create database instance
   - Run migration scripts
   - Configure connection pooling

3. Ingest data: `python scripts/db_ingest.py --input data/leads_clean.json --create-table`

4. Create FastAPI for lead access:
   - GET /leads - List with filters (city, status, quality)
   - GET /leads/{id} - Get single lead
   - GET /leads/export - CSV export
   - GET /leads/stats - Statistics dashboard

**Expected Output**: Live API at https://reca-leads-api.example.com

---

### Phase 6: Production Deployment
**Goal**: Cloud Run service with scheduled scraping

**Tasks**:
1. Optimize `cloud_scraper.py`:
   - Add concurrent workers (ThreadPoolExecutor)
   - Implement graceful shutdown
   - Add comprehensive logging
   - Health check with metrics

2. Create `Dockerfile.production`:
   - Multi-stage build
   - Minimal runtime dependencies
   - Security hardening
   - Health checks

3. Deploy to Cloud Run:
   ```bash
   gcloud run deploy reca-scraper \
     --source . \
     --platform managed \
     --region us-central1 \
     --timeout 3600 \
     --memory 2Gi \
     --cpu 2 \
     --set-env-vars DATABASE_URL=$DATABASE_URL
   ```

4. Setup Cloud Scheduler:
   - Daily incremental: 6 AM MST
   - Weekly full sweep: Sunday 2 AM MST
   - POST to https://reca-scraper.run.app/scrape/incremental

5. Monitoring & Alerts:
   - Cloud Logging for errors
   - Uptime checks
   - Email alerts for failures
   - Slack webhook for completion notifications

**Expected Output**: Automated lead updates, zero manual intervention

---

## Success Metrics
- ✅ 15,000+ active licensed leads
- ✅ 70%+ email coverage
- ✅ 50%+ phone coverage (if available on RECA)
- ✅ < 1 hour incremental update time
- ✅ 99.9% scraper uptime
- ✅ Zero data loss on failure

## Timeline
- Phase 1: 2-6 hours (deep scrape runtime)
- Phase 2: 4-6 hours (phone extraction)
- Phase 3: 2-3 hours (validation/cleanup)
- Phase 4: 6-8 hours (incremental system)
- Phase 5: 4-6 hours (database + API)
- Phase 6: 4-6 hours (deployment)

**Total: 22-35 hours development + 2-6 hours runtime**

## Next Steps
1. Start deep scrape immediately (longest task)
2. While scraping, develop enhanced extractors
3. Setup database infrastructure
4. Build incremental updater
5. Deploy to production
6. Monitor first full cycle

---

*Generated: 2026-02-18*
