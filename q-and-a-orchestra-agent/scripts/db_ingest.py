#!/usr/bin/env python3
"""
Database Ingestion Script — load scraped RECA agents into Postgres/Neon.

Usage:
    export DATABASE_URL="postgresql://user:pass@host/dbname?sslmode=require"
    python scripts/db_ingest.py [--input reca_agents.json] [--create-table]

Requires:  pip install psycopg2-binary  (or asyncpg)
"""
import argparse
import json
import os
import sys
from pathlib import Path

try:
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError:
    psycopg2 = None


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS agents (
    id              SERIAL PRIMARY KEY,
    drill_id        VARCHAR(255) UNIQUE NOT NULL,
    first_name      VARCHAR(255),
    middle_name     VARCHAR(255),
    last_name       VARCHAR(255),
    full_name       VARCHAR(512),
    status          VARCHAR(100),
    brokerage       VARCHAR(512),
    city            VARCHAR(255),
    sector          VARCHAR(255),
    aka             VARCHAR(255),
    email           VARCHAR(255),
    phone           VARCHAR(50),
    quality_score   INTEGER DEFAULT 0,
    scraped_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agents_drill_id ON agents(drill_id);
CREATE INDEX IF NOT EXISTS idx_agents_last_name ON agents(last_name);
CREATE INDEX IF NOT EXISTS idx_agents_city ON agents(city);
CREATE INDEX IF NOT EXISTS idx_agents_quality_score ON agents(quality_score DESC);
"""

UPSERT_SQL = """
INSERT INTO agents (drill_id, first_name, middle_name, last_name, full_name,
                    status, brokerage, city, sector, aka, email, phone, quality_score, updated_at,
                    email_source, enrichment_method, validation_status, email_confidence, last_enriched_at)
VALUES %s
ON CONFLICT (drill_id) DO UPDATE SET
    first_name    = EXCLUDED.first_name,
    middle_name   = EXCLUDED.middle_name,
    last_name     = EXCLUDED.last_name,
    full_name     = EXCLUDED.full_name,
    status        = EXCLUDED.status,
    brokerage     = EXCLUDED.brokerage,
    city          = EXCLUDED.city,
    sector        = EXCLUDED.sector,
    aka           = EXCLUDED.aka,
    email         = EXCLUDED.email,
    phone         = EXCLUDED.phone,
    quality_score = EXCLUDED.quality_score,
    email_source      = EXCLUDED.email_source,
    enrichment_method = EXCLUDED.enrichment_method,
    validation_status = EXCLUDED.validation_status,
    email_confidence  = EXCLUDED.email_confidence,
    last_enriched_at  = EXCLUDED.last_enriched_at,
    updated_at    = NOW();
"""


def load_agents(path: str) -> list:
    with open(path) as f:
        return json.load(f)


def ingest(agents: list, database_url: str, create_table: bool = False):
    """Connect to Postgres and upsert agents."""
    if psycopg2 is None:
        print("❌  psycopg2 not installed.  pip install psycopg2-binary")
        sys.exit(1)

    conn = psycopg2.connect(database_url)
    cur = conn.cursor()

    if create_table:
        print("  Creating table...")
        cur.execute(CREATE_TABLE_SQL)
        conn.commit()

    # Prepare rows
    rows = []
    for a in agents:
        drill_id = a.get("drill_id", "")
        if not drill_id:
            continue  # Skip agents without drill_id

        # Extract enrichment metadata
        meta = a.get("enrichment_metadata", {})
        enrichment_status = a.get("enrichment_status")
        
        # Determine validation status
        validation_status = None
        if meta:
            if meta.get("validated_emails"):
                validation_status = "valid"
            elif enrichment_status == "failed":
                validation_status = "failed"
            elif enrichment_status == "success":
                validation_status = "unverified"

        # Determine last enriched timestamp
        last_enriched = "NOW()" if meta else None

        rows.append((
            drill_id,
            a.get("first_name", ""),
            a.get("middle_name", ""),
            a.get("last_name", ""),
            a.get("name", ""),
            a.get("status", ""),
            a.get("brokerage", ""),
            a.get("city", ""),
            a.get("sector", ""),
            a.get("aka", ""),
            a.get("email", ""),
            a.get("phone", ""),
            a.get("quality_score", 0),
            "NOW()", # updated_at
            meta.get("website") or meta.get("source_url") or "", # email_source
            meta.get("extraction_method") or meta.get("method") or "", # enrichment_method
            validation_status,
            meta.get("confidence", 0.0),
            last_enriched
        ))

    if not rows:
        print("  ⚠️  No agents with drill_id to ingest.")
        return

    # Use execute_values for efficient bulk insert
    # We need to handle the NOW() specially
    # Template must match the number of columns in VALUES
    # (drill_id, first, middle, last, full, status, brok, city, sec, aka, email, phone, qual, updated, source, method, val, conf, enriched)
    # The last_enriched_at can be NULL, so we pass it as %s
    # The updated_at is always NOW()
    
    # We have 19 params in VALUES list
    # param 14 is updated_at -> we pass "NOW()" string, but psycopg2 might escape it if we use %s.
    # Better to use DEFAULT or explicit string in SQL?
    # execute_values handles lists of tuples.
    # If we pass "NOW()" string to %s, it becomes 'NOW()'.
    # We should use a template that puts NOW() directly in SQL for updated_at.
    
    # 14th item is updated_at.
    # 19th item is last_enriched_at.
    
    # Let's adjust rows to NOT include updated_at string, and put NOW() in template.
    # Rows will have 18 items.
    
    rows_clean = []
    for r in rows:
        # r has 19 items.
        # r[13] is updated_at ("NOW()")
        # r[18] is last_enriched ("NOW()" or None)
        
        # We need to handle last_enriched carefully. If it is "NOW()", we want SQL NOW().
        # But execute_values binds variables.
        # Strategy: Pass None for last_enriched if not enriched.
        # For 'NOW()', we can't easily mix distinct SQL functions in bulk values unless we use a unified value.
        # Simplification: pass datetime.now() from python for timestamps to avoid SQL template complexity?
        # Or just use %s and pass None. For "NOW()", we can replace it in the template?
        # No, template applies to all rows.
        
        # Hack: Pass CURRENT_TIMESTAMP via python datetime
        from datetime import datetime
        now = datetime.now()
        
        last_enriched_val = now if r[18] else None
        
        # Construct row without the string "NOW()" placeholders
        new_row = (
            r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11], r[12],
            # skip r[13] (updated_at)
            r[14], r[15], r[16], r[17],
            last_enriched_val
        )
        rows_clean.append(new_row)

    # Template: 19 columns total in INSERT
    # We pass 18 values in row.
    # updated_at is at position 14 (1-based) -> index 13
    # VALUES (%s, %s, ..., %s, NOW(), %s, %s, %s, %s, %s)
    
    template = "(" + ",".join(["%s"] * 13) + ", NOW(), " + ",".join(["%s"] * 5) + ")"
    
    execute_values(cur, UPSERT_SQL, rows_clean, template=template, page_size=500)
    conn.commit()

    inserted = cur.rowcount
    print(f"  ✅  Upserted {len(rows_clean)} agents ({inserted} rows affected)")

    cur.close()
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Ingest RECA agents into Postgres")
    parser.add_argument("--input", "-i", default="reca_agents.json",
                        help="Path to scraped agents JSON")
    parser.add_argument("--create-table", action="store_true",
                        help="Create the agents table if it doesn't exist")
    args = parser.parse_args()

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌  DATABASE_URL environment variable not set.")
        print("   export DATABASE_URL='postgresql://user:pass@host/db?sslmode=require'")
        sys.exit(1)

    path = Path(args.input)
    if not path.exists():
        print(f"❌  File not found: {args.input}")
        sys.exit(1)

    agents = load_agents(str(path))
    print(f"  Loaded {len(agents)} agents from {path}")

    ingest(agents, database_url, create_table=args.create_table)


if __name__ == "__main__":
    main()
