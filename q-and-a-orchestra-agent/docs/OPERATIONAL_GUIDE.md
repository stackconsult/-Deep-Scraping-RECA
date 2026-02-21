# 🛠️ RECA Operational Guide

This guide details how to operate the **RECA Agent Orchestra** in a production environment.

## 🐳 Docker Stack Management

The entire system (Agent, Database, Redis, Ollama, Dashboard) runs in Docker containers.

### Starting the Stack
```bash
# Start in background
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Accessing Services
| Service | Internal URL | Host URL | Description |
|---------|--------------|----------|-------------|
| **API** | `http://orchestra-agent:8000` | `http://localhost:8000` | REST API / Swagger UI |
| **Dashboard** | `http://dashboard:8501` | `http://localhost:8501` | Data Enrichment UI |
| **Ollama** | `http://ollama:11434` | `http://localhost:11434` | Local LLM Inference |
| **Redis** | `redis:6379` | `localhost:6379` | Message Bus |
| **Postgres** | `postgres:5432` | `localhost:5432` | Persistent Storage |

---

## 🚀 Running the Enrichment Pipeline

We provide a master script to automate the **Enrichment -> Validation -> Ingestion** workflow.

### Usage
```bash
# Run on a sample of 50 agents
python scripts/run_pipeline.py --input data/all_agents.json --batch-size 10 --sample 50

# Run full production sweep (WARNING: Long running process)
python scripts/run_pipeline.py --input data/all_agents.json --batch-size 10
```

### Pipeline Stages
1.  **Enrichment** (`scripts/production_enrichment.py`):
    *   Reads source JSON.
    *   Uses Hybrid Agent (Scraper + LLM + Deep Research) to find emails.
    *   Saves progress to `data/all_agents_enriched.json`.
    *   *Resumable*: Automatically picks up where it left off.

2.  **Validation** (`scripts/validate_data.py`):
    *   Analyzes the enriched dataset.
    *   Checks for duplicates, missing emails, and validity.
    *   Outputs a quality report.

3.  **Ingestion** (`scripts/db_ingest.py`):
    *   Connects to PostgreSQL (`DATABASE_URL`).
    *   Upserts records into `agents` table.
    *   Preserves enrichment metadata (confidence, source, method).

---

## 🔍 Deep Research Agent

The system includes a fallback "Deep Research" capability for hard-to-find agents.

*   **Trigger**: Automatically runs when standard brokerage website scraping fails.
*   **Method**: Performs a DuckDuckGo search for the agent + brokerage, scrapes top results, and uses LLM to extract contact info.
*   **Configuration**: Enabled by default in `EnhancedHybridEmailAgent`. Can be toggled in `config`.

---

## 📊 Database Schema

The PostgreSQL database stores rich metadata for each lead.

**Key Columns:**
*   `drill_id`: Unique RECA identifier.
*   `email`: Primary email address found.
*   `email_source`: Source of the email (e.g., `brokerage_website`, `deep_research`).
*   `email_confidence`: Confidence score (0.0 - 1.0).
*   `validation_status`: `valid`, `unverified`, or `failed`.
*   `quality_score`: Overall lead quality score.

---

## 🛠️ Maintenance & Troubleshooting

**Resetting Data:**
```bash
# Clear docker volumes (WARNING: Deletes DB data)
docker-compose -f docker-compose.prod.yml down -v
```

**Updating Models:**
To pull a new Ollama model:
```bash
docker exec -it orchestra-ollama ollama pull llama3
```

**Logs:**
Application logs are structured JSON for easy parsing. Check `logs/` directory or container output.
