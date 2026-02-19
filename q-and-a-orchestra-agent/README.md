# Q&A Orchestra Agent + Deep Scraping RECA

A production-grade meta-agent system for designing agent orchestras through conversational Q&A — plus a high-performance Alberta real estate agent scraper powered by RECA.

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
- **Deep scrape** — Drills into each agent's detail page to extract email addresses
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

# 3. Run integration tests
pytest tests/test_integration.py -v

# 4. Run a single-name E2E scrape
python tests/e2e_reca_scrape.py

# 5. Run the full A-Z sweep (surface only)
python scripts/full_sweep.py

# 6. Run with deep scrape (email extraction)
python scripts/full_sweep.py --deep

# 7. Resume an interrupted sweep
python scripts/full_sweep.py --deep --resume

# 8. Scrape specific letters only
python scripts/full_sweep.py --letters A B C --deep
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
│   └── full_sweep.py      # Production A-Z sweep script
├── tests/
│   ├── test_integration.py
│   └── e2e_reca_scrape.py
└── data/                  # Scrape output (gitignored)
    ├── reca_agents.json
    ├── reca_agents.csv
    └── sweep_checkpoint.json
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

## License

MIT License — see LICENSE file for details.
