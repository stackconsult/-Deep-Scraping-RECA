# RECA Email Enrichment Architecture

## Overview
This document outlines the architecture for enriching RECA agent data with email addresses through alternative methods, following a non-destructive approach that builds alongside existing data without modifying it.

## Current Issue
The RECA deep scrape is failing because the endpoint `https://reports.myreca.ca/publicsearch.aspx` returns 404. We need alternative methods to obtain email addresses for the 18,832 agents we've already scraped.

## Architecture Components

### 1. Data Flow
```
RECA Surface Data (all_agents.json) 
    ↓
Email Enrichment Engine
    ↓
Enhanced Dataset (all_agents_enriched.json)
    ↓
Validation & Merge Layer
    ↓
Final Dataset (agents_final.json)
```

### 2. Email Enrichment Strategies

#### Strategy A: Alternative RECA Endpoints
- Search for new RECA public search URLs
- Monitor site structure changes
- Implement adaptive scraping logic

#### Strategy B: Brokerage Website Scraping
- Extract brokerage websites from agent data
- Scrape individual brokerage sites for agent emails
- Implement respectful scraping with delays

#### Strategy C: Professional Directory Cross-Reference
- Cross-reference with other professional directories
- Use name + city + brokerage as matching criteria
- Implement confidence scoring for matches

#### Strategy D: Email Pattern Generation
- Generate likely email patterns based on brokerage domains
- Common patterns: firstname@brokerage.com, first.last@brokerage.com
- Validate email existence without sending emails

### 3. Core Components

#### A. Email Enrichment Engine (`scripts/enrich_emails.py`)
- Reads existing agent data from `all_agents.json`
- Applies multiple enrichment strategies
- Scores confidence for each found email
- Saves enriched data with new email fields

#### B. Brokerage Site Scraper (`integrations/brokerage_scraper.py`)
- Identifies brokerage websites
- Extracts agent contact pages
- Implements polite scraping with rate limits
- Handles various site structures

#### C. Email Validator (`integrations/email_validator.py`)
- Validates email format and domain existence
- Checks MX records for email domains
- Implements syntax validation
- Flags suspicious or invalid emails

#### D. Checkpoint Manager (`utils/checkpoint.py`)
- Tracks enrichment progress
- Enables resume on interruption
- Stores success/failure statistics

### 4. Data Schema Enhancements

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
    "email_source": "brokerage_website",
    "email_confidence": 0.85,
    "enriched_at": "2026-02-20T15:37:00Z",
    "validation_status": "valid",
    "enrichment_method": "pattern_matching"
  }
}
```

### 5. Rate Limiting & Respectful Scraping

#### Rate Limits
- Brokerage sites: 1 request per 5 seconds
- Directory sites: 1 request per 2 seconds
- Implement delays between requests
- Respect robots.txt files

#### Polite Scraping Practices
- Identify scraper with proper User-Agent
- Provide contact information
- Don't overload servers
- Cache results to avoid repeat requests

### 6. Error Handling & Resilience

#### Retry Logic
- Exponential backoff: 2s, 4s, 8s, 16s
- Max retries: 3 per request
- Circuit breaker after 10 consecutive failures

#### Fallback Strategies
- If brokerage scraping fails, try email patterns
- If no email found, mark as "email_not_found"
- Never overwrite existing data

### 7. Email Pattern Generation

#### Common Patterns
1. `{first}@{domain}`
2. `{first}.{last}@{domain}`
3. `{firstinitial}{last}@{domain}`
4. `{first}{lastinitial}@{domain}`
5. `{first}.{lastinitial}@{domain}`

#### Domain Extraction
- Parse brokerage names to find domains
- Search for brokerage websites
- Extract domain from found websites

### 8. Confidence Scoring

#### Score Factors
- Source reliability (RECA = 1.0, brokerage = 0.8, pattern = 0.6)
- Email format validation
- Domain existence check
- Pattern match quality

#### Score Ranges
- 0.9-1.0: High confidence (direct source)
- 0.7-0.9: Medium confidence (brokerage site)
- 0.5-0.7: Low confidence (pattern generation)
- 0.0-0.5: Very low confidence (guesswork)

### 9. Implementation Phases

#### Phase 2.1: Infrastructure
1. Create enrichment engine framework
2. Implement checkpoint management
3. Set up logging and monitoring

#### Phase 2.2: Strategy Implementation
1. Implement brokerage website scraper
2. Create email pattern generator
3. Add email validation

#### Phase 2.3: Testing & Validation
1. Test on sample of 100 agents
2. Validate email accuracy
3. Optimize confidence scoring

#### Phase 2.4: Full Processing
1. Process all 18,832 agents
2. Generate enrichment report
3. Create final dataset

### 10. Monitoring & Reporting

#### Metrics to Track
- Email enrichment rate by strategy
- Confidence score distribution
- Processing speed (agents/minute)
- Success/failure rates

#### Reports
- Daily progress reports
- Final enrichment summary
- Email quality assessment
- Cost/benefit analysis

### 11. Legal & Ethical Considerations

#### Compliance
- Respect robots.txt
- Don't violate terms of service
- Consider privacy implications
- Provide opt-out mechanism

#### Best Practices
- Only collect publicly available emails
- Don't send verification emails
- Store data securely
- Be transparent about data collection

### 12. Next Steps
1. Create `scripts/enrich_emails.py` framework
2. Implement `integrations/brokerage_scraper.py`
3. Add email validation utilities
4. Create test suite with sample data
5. Run pilot on 100 agents