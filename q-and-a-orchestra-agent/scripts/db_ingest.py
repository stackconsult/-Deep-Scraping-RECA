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
    drill_id        VARCHAR(255) UNIQUE,
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
    scraped_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agents_drill_id ON agents(drill_id);
CREATE INDEX IF NOT EXISTS idx_agents_last_name ON agents(last_name);
CREATE INDEX IF NOT EXISTS idx_agents_city ON agents(city);
"""

UPSERT_SQL = """
INSERT INTO agents (drill_id, first_name, middle_name, last_name, full_name,
                    status, brokerage, city, sector, aka, email, phone, updated_at)
VALUES %s
ON CONFLICT (drill_id) DO UPDATE SET
    first_name  = EXCLUDED.first_name,
    middle_name = EXCLUDED.middle_name,
    last_name   = EXCLUDED.last_name,
    full_name   = EXCLUDED.full_name,
    status      = EXCLUDED.status,
    brokerage   = EXCLUDED.brokerage,
    city        = EXCLUDED.city,
    sector      = EXCLUDED.sector,
    aka         = EXCLUDED.aka,
    email       = EXCLUDED.email,
    phone       = EXCLUDED.phone,
    updated_at  = NOW();
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
            "NOW()",
        ))

    if not rows:
        print("  ⚠️  No agents with drill_id to ingest.")
        return

    # Use execute_values for efficient bulk insert
    # We need to handle the NOW() specially
    template = "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())"
    rows_clean = [r[:-1] for r in rows]  # Remove the NOW() placeholder

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
