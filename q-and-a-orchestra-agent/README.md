# Q&A Orchestra Agent + Deep Scraping RECA

A production-grade meta-agent system for designing agent orchestras through conversational Q&A — plus a high-performance Alberta real estate agent scraper powered by RECA.

## 🎭 CodeBuddy Orchestra Framework

This project follows the **CodeBuddy Orchestra** framework with specialized personas:

- **Project Manager**: Planning and coordination
- **Architect**: System design and architecture  
- **Implementation Planner**: Code implementation strategy
- **Debugger**: Issue identification and resolution
- **Validator**: Code review and quality assurance

### Phase-to-Persona Mapping
- Phase 1 (CSV Export) → Debugger ✅
- Phase 2 (Email Testing) → Implementation Planner 🔄
- Phase 3 (Full Enrichment) → Implementation Planner ◐
- Phase 4 (Validation) → Validator ◐
- Phase 5 (Database) → Project Manager ◐
- Phase 6 (Production) → Architect ◐

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

- **Surface scrape** — ✅ Complete: 20,447 agents scraped and stored in JSON
- **Deep scrape** — ⚠️ Partial: RECA endpoint returns 404, need alternative approach
- **Email enrichment** — 🔄 In Progress: Architecture complete, implementation ready
- **CSV export** — ✅ Complete: Auto-path configuration implemented
- **Database ingestion** — ✅ Ready: Scripts and schema in place

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

# 4. Check path configuration
python scripts/check_paths.py

# 5. Export to CSV (auto-saves to Downloads)
python scripts/export_to_csv.py

# 6. Run email enrichment (when ready)
python scripts/enrich_emails.py

# 7. Ingest data into database
python scripts/db_ingest.py
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
├── scripts/               # Utility and processing scripts
│   ├── full_sweep.py      # Production A-Z sweep script
│   ├── enrich_emails.py   # Email enrichment engine
│   ├── export_to_csv.py   # CSV export with auto-path
│   ├── check_paths.py     # Path configuration utility
│   └── db_ingest.py       # Database ingestion
├── tests/
│   ├── test_integration.py
│   └── e2e_reca_scrape.py
├── docs/                  # Documentation
│   ├── email-enrichment-architecture.md
│   └── codebuddy-compliance.md
├── .codebuddy/            # CodeBuddy rules
│   └── rules.md           # Repository rules
└── data/                  # Scrape output (gitignored)
    ├── all_agents.json    # ✅ 20,447 agents scraped
    ├── all_agents.csv     # ✅ Generated on demand
    └── sweep_checkpoint.json
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | **Yes** | Google Gemini API key (primary LLM) |
| `ANTHROPIC_API_KEY` | No | Fallback LLM provider |
| `OPENAI_API_KEY` | No | Fallback LLM provider |
| `REDIS_URL` | No | Redis URL for message bus (default: `redis://localhost:6379`) |
| `DATABASE_URL` | No | PostgreSQL URL for data ingestion |

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

### Personas
- **Project Manager**: `Activating CodeBuddy Project Manager...` (Planning)
- **Architect**: `Activating CodeBuddy Architect...` (System Design)
- **Reviewer**: `Activating CodeBuddy Reviewer...` (Code Quality)
- **Tester**: `Activating CodeBuddy Tester...` (Verification)
- **Debugger**: `Activating CodeBuddy Debugger...` (Self-Healing)

### Features
- **Self-Healing Workflow**: Automatically fixes test failures.
- **Rules Engine**: Custom project rules in `.codebuddy/rules.md`.
- **City Normalization**: `scripts/normalize_data.py` ensures consistent data casing.

## Current Status

### ✅ Completed
- Surface scrape of all RECA agents (20,447 total)
- Email enrichment architecture designed
- Database schema and ingestion scripts ready
- Data validation and filtering utilities available
- CSV export with auto-path configuration
- CodeBuddy Orchestra framework fully integrated

### 🔄 In Progress
- Email enrichment implementation testing

### ❌ Issues
- RECA deep scrape endpoint returns 404 (need alternative approach)

## License

MIT License — see LICENSE file for details.