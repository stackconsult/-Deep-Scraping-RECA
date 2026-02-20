# DataBreach.com Email Enrichment Architecture

## Overview
This document outlines the architecture for enriching RECA agent data with email addresses from DataBreach.com, following a non-destructive approach that builds alongside existing data without modifying it.

## Architecture Components

### 1. Data Flow
```
RECA Surface Data (all_agents.json) 
    ↓
DataBreach.com API Client
    ↓
Email Enrichment Processor
    ↓
Enhanced Dataset (all_agents_enriched.json)
    ↓
Validation & Merge Layer
    ↓
Final Dataset (agents_final.json)
```

### 2. Core Components

#### A. DataBreach API Client (`integrations/databreach_client.py`)
- Handles authentication with DataBreach.com API
- Implements rate limiting (100 requests/minute recommended)
- Provides retry logic with exponential backoff
- Caches results to minimize API calls

#### B. Email Enrichment Processor (`scripts/enrich_emails_databreach.py`)
- Reads existing agent data from `all_agents.json`
- Extracts key identifiers: name, city, brokerage
- Queries DataBreach.com API for email matches
- Applies confidence scoring based on match quality
- Saves enriched data with new email fields

#### C. Checkpoint Manager (`utils/checkpoint.py`)
- Tracks enrichment progress
- Enables resume on interruption
- Stores API usage statistics

### 3. Data Schema Enhancements

#### Original Agent Record
```json
{
  "name": "John Smith",
  "first_name": "John",
  "last_name": "Smith",
  "brokerage": "ABC Realty",
  "city": "Calgary",
  "status": "Licensed",
  "drill_id": "302iT2R0x123"
}
```

#### Enhanced Record (Non-Destructive)
```json
{
  // Original fields unchanged
  "name": "John Smith",
  "first_name": "John",
  "last_name": "Smith",
  "brokerage": "ABC Realty",
  "city": "Calgary",
  "status": "Licensed",
  "drill_id": "302iT2R0x123",
  
  // New enrichment fields
  "enrichment": {
    "email": "john@abcrealty.ca",
    "email_source": "databreach",
    "email_confidence": 0.85,
    "enriched_at": "2026-02-20T15:37:00Z",
    "api_match_details": {
      "match_type": "name+brokerage+city",
      "databreach_id": "1234567"
    }
  }
}
```

### 4. Rate Limiting Strategy

#### API Limits
- DataBreach.com: 100 requests/minute (adjust based on plan)
- Implement token bucket algorithm
- Track usage in checkpoint file

#### Batching Approach
```python
# Process in batches to respect limits
BATCH_SIZE = 50
RATE_LIMIT_DELAY = 30  # seconds between batches
```

### 5. Error Handling & Resilience

#### Retry Logic
- Exponential backoff: 1s, 2s, 4s, 8s, 16s
- Max retries: 5 per request
- Circuit breaker after 10 consecutive failures

#### Fallback Strategies
- If exact name+brokerage match fails, try name+city
- If no match found, mark as "email_not_found"
- Never overwrite existing data

### 6. Caching Strategy

#### Local Cache
- Cache successful API responses for 24 hours
- Use SHA256 hash of search parameters as cache key
- Implement cache cleanup on startup

#### Cache Structure
```
cache/
├── databreach/
│   ├── {hash1}.json
│   ├── {hash2}.json
│   └── metadata.json
```

### 7. Monitoring & Observability

#### Metrics to Track
- API request count and rate
- Success/failure rate
- Email match rate by confidence level
- Processing speed (agents/minute)

#### Logging
- Structured JSON logs
- Log levels: DEBUG, INFO, WARN, ERROR
- Separate log files for API calls

### 8. Security Considerations

#### API Key Management
- Store API key in environment variables
- Never commit API keys to repository
- Implement key rotation capability

#### Data Privacy
- Only query with necessary PII
- Store only results, not search queries
- Implement data retention policy

### 9. Implementation Phases

#### Phase 2.1: Core Infrastructure
1. Create DataBreach API client
2. Implement rate limiting and retry logic
3. Set up caching layer

#### Phase 2.2: Enrichment Engine
1. Build enrichment processor
2. Implement confidence scoring
3. Add checkpoint management

#### Phase 2.3: Testing & Validation
1. Create test dataset (100 agents)
2. Run enrichment on test data
3. Validate email quality

#### Phase 2.4: Full Processing
1. Process all 18,832 agents
2. Monitor API usage and costs
3. Generate enrichment report

### 10. Cost Estimation

#### API Costs
- DataBreach.com: $0.10 per lookup (example)
- Total lookups: 18,832 agents
- Estimated cost: $1,883.20

#### Optimization Opportunities
- Batch queries where possible
- Cache results to avoid duplicate lookups
- Prioritize high-value agents first

### 11. Next Steps
1. Create `integrations/databreach_client.py`
2. Implement `scripts/enrich_emails_databreach.py`
3. Set up environment configuration
4. Create test suite
5. Run pilot on 100 agents