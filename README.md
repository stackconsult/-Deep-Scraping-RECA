# Q&A Orchestra Agent + Deep Scraping RECA

A production-grade meta-agent system for designing agent orchestras through conversational Q&A — plus a high-performance Alberta real estate agent scraper powered by RECA.

## 📊 Current Build Status

### ✅ Completed Components
- **Surface Scrape**: Complete (18,832 agents found)
- **Database Schema**: Built (`migrations/002_enhanced_schema.sql`)
- **Ingestion Script**: Built (`scripts/db_ingest.py`)
- **Incremental Scraper**: Built (`scripts/incremental_scraper.py`)
- **Cloud Scraper**: Built (`scripts/cloud_scraper.py`)

### ⚠️ In Progress / Issues Identified
- **Deep Scrape**: Complete but flawed - 0% extraction rate for both phones and emails
- **Progress**: 13,500/18,832 agents processed (71.7%)
- **Issue**: The `perform_drillthrough` function in `integrations/reca_scraper_logic.py` is failing to extract contact information

### 🎯 Active Checklist (CodeBuddy Orchestra)

#### Phase 1: Fix RECA Phone Extraction (Persona: Debugger) - IN PROGRESS
- [ ] Debug and fix phone extraction logic in `reca_scraper_logic.py`
- [ ] Test extraction on sample agents
- [ ] Resume deep scrape with fixed logic

#### Phase 2: Architect Email Enrichment (Persona: Architect) - PENDING
- [ ] Design DataBreach.com integration architecture
- [ ] Plan rate-limiting and caching strategy
- [ ] Define data flow for third-party enrichment

#### Phase 3: Implement Email Enrichment (Persona: Implementation Planner) - PENDING
- [ ] Build `scripts/enrich_emails_databreach.py`
- [ ] Implement checkpointing for enrichment process
- [ ] Process existing JSON data non-destructively

#### Phase 4: Data Validation & Merge (Persona: Validator) - PENDING
- [ ] Clean and merge RECA phone data with DataBreach email data
- [ ] Validate data integrity and deduplication

#### Phase 5: Database Ingestion (Persona: Project Manager) - PENDING
- [ ] Ingest enhanced dataset into PostgreSQL
- [ ] Verify API endpoints serve data correctly

#### Phase 6: Productionization (Persona: Architect) - PENDING
- [ ] Update Docker/Deployment configs
- [ ] Deploy enhanced system

---

## Overview

### Agent Orchestra

Five specialized agents collaborate to help users design production-grade agent orchestras:

1. **Repository Analysis Agent** — Reads and understands architecture patterns from repos
2. **Requirements Extraction Agent** — Conducts conversational Q&A to extract user requirements
3. **Architecture Designer Agent** — Applies patterns to design custom agent orchestras
4. **Implementation Planner Agent** — Generates phased implementation plans with cost estimates
5. **Validator Agent** — Reviews designs against best practices and safety mechanisms

### RECA Scraper

A full-scale scraper for the Alberta Real Estate Council Association (RECA) agent directory:

- **Surface scrape** — Iterates A–Z + two-letter prefixes (702 queries) to find all licensed agents
- **Deep scrape** — Drills into each agent's detail page to extract email addresses and phone numbers
- **Checkpoint/resume** — Saves progress to JSON so interrupted scrapes can resume
- **Deduplication** — Merges results by `drill_id` for unique records
- **Export** — Outputs to both JSON and CSV formats

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+ with FastAPI |
| LLM | **Google Gemini** (primary) via `google-genai` SDK |
| Message Bus | Redis for event-driven communication |
| Database | Postgres on Neon for conversation history |
| Observability | Prometheus + Grafana |
| Scraping | `requests` + RECA ViewerControl POST-based scraper |

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env — set GOOGLE_API_KEY (required)

# 2.5 Setup Development Environment (Fixes Git extensions)
# If you encounter issues with Git extensions or pre-commit hooks:
./scripts/setup_dev.sh
# Note: If this fails, run `brew install git-lfs` manually and try again.

# 3. Run integration tests
pytest tests/test_integration.py -v

# 4. Run a single-name E2E scrape
python tests/e2e_reca_scrape.py

# 5. Run the full A-Z sweep (surface only)
python scripts/full_sweep.py

# 6. Run with deep scrape (email & phone extraction)
python scripts/full_sweep.py --deep

# 7. Resume an interrupted sweep
python scripts/full_sweep.py --deep --resume

# 8. Scrape specific letters only
python scripts/full_sweep.py --letters A B C --deep

# 9. Run Async Scraper (Redis required)
# Start Redis
redis-server

# Start Worker
python scripts/scraper_worker.py

# Queue jobs via Agent or QueueManager
# (See agents/reca_scraper_agent.py for usage)
```

## Architecture

```
q-and-a-orchestra-agent/
├── agents/                # Specialized agent implementations
│   └── reca_scraper_agent.py
├── config/                # Model routing & policy configuration
│   ├── models.yaml        # Gemini model definitions
│   └── policies.yaml      # Model selection policies
├── core/                  # Model router, telemetry, introspection
│   └── model_router.py    # Routes to Gemini/Anthropic/OpenAI
├── integrations/          # External service integrations
│   └── reca_scraper_logic.py  # RECA HTTP scraper engine
├── orchestrator/          # Message bus, router, context management
├── providers/             # LLM provider clients
│   └── google_client.py   # Gemini API client
├── schemas/               # Pydantic data models
├── scripts/
│   ├── full_sweep.py      # Production A-Z sweep script
│   ├── db_ingest.py       # Database ingestion script
│   └── incremental_scraper.py
├── tests/
│   ├── test_integration.py
│   └── e2e_reca_scrape.py
└── data/                  # Scrape output (gitignored)
    ├── all_agents.json
    ├── all_agents_deep.json
    └── deep_checkpoint.json
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | **Yes** | Google Gemini API key (primary LLM) |
| `ANTHROPIC_API_KEY` | No | Fallback LLM provider |
| `OPENAI_API_KEY` | No | Fallback LLM provider |
| `REDIS_URL` | No | Redis URL for message bus (default: `redis://localhost:6379`) |

## Development

```bash
# Run tests
pytest tests/ -v

# Format code
black .

# Lint
flake8 .

# Type check
mypy .
```

## CodeBuddy Integration

This project includes **CodeBuddy** autonomous agent capabilities.

### Active Personas
- **Project Manager**: Planning and task management (`task.md`)
- **Architect**: System design and architecture decisions
- **Debugger**: Self-healing and issue resolution (currently active on phone extraction)
- **Reviewer**: Code quality and best practices
- **Tester**: Verification and testing
- **Implementation Planner**: Detailed implementation planning

### Features
- **Self-Healing Workflow**: Automatically fixes test failures
- **Rules Engine**: Custom project rules in `.codebuddy/rules.md`
- **Non-Destructive Enhancement**: Builds alongside existing architecture without breaking changes

## Data Processing Pipeline

### Current State
1. **Surface Scrape** ✅ - Collected 18,832 agents
2. **Deep Scrape** ⚠️ - Processing complete but extraction failed (0% rate)
3. **Email Enrichment** 🔄 - Planned via DataBreach.com integration
4. **Data Validation** ⏳ - Pending
5. **Database Ingestion** ⏳ - Pending

### Next Steps
The immediate priority is fixing the phone/email extraction in `integrations/reca_scraper_logic.py`. Once resolved, we will implement the DataBreach.com email enrichment as a separate, non-destructive process.

## License

MIT License — see LICENSE file for details.
