#!/usr/bin/env python3
"""
RECA Leads API - FastAPI service for accessing filtered lead data.

Endpoints:
- GET /leads - List leads with filters
- GET /leads/{drill_id} - Get single lead
- GET /leads/export - Export to CSV
- GET /leads/stats - Statistics dashboard
- GET /health - Health check

Usage:
    uvicorn api.leads_api:app --host 0.0.0.0 --port 8000
"""
import os
import csv
import io
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI(
    title="RECA Leads API",
    description="API for accessing Alberta real estate agent leads",
    version="1.0.0"
)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")


def get_db():
    """Get database connection."""
    if not DATABASE_URL:
        raise Exception("DATABASE_URL environment variable not set")
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


# Pydantic models
class Lead(BaseModel):
    drill_id: str
    first_name: str
    middle_name: Optional[str] = ""
    last_name: str
    full_name: str
    status: str
    brokerage: Optional[str] = ""
    city: Optional[str] = ""
    sector: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""
    quality_score: Optional[int] = 0
    scraped_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class LeadStats(BaseModel):
    total_leads: int
    with_email: int
    with_phone: int
    with_both: int
    avg_quality_score: float
    top_cities: List[dict]
    top_brokerages: List[dict]


# Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM agents")
        count = cur.fetchone()['count']
        conn.close()
        return {"status": "healthy", "agents_count": count}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.get("/leads", response_model=List[Lead])
async def list_leads(
    city: Optional[str] = Query(None, description="Filter by city"),
    status: Optional[str] = Query("Licensed", description="Filter by status"),
    min_quality: Optional[int] = Query(0, description="Minimum quality score"),
    has_email: Optional[bool] = Query(None, description="Filter by email presence"),
    has_phone: Optional[bool] = Query(None, description="Filter by phone presence"),
    brokerage: Optional[str] = Query(None, description="Filter by brokerage (partial match)"),
    limit: int = Query(100, le=1000, description="Max results to return"),
    offset: int = Query(0, description="Pagination offset")
):
    """
    List leads with filtering and pagination.
    
    Example:
        GET /leads?city=Calgary&min_quality=70&has_email=true&limit=50
    """
    conn = get_db()
    cur = conn.cursor()
    
    # Build query
    query = "SELECT * FROM agents WHERE 1=1"
    params = []
    
    if status:
        query += " AND status LIKE %s"
        params.append(f"%{status}%")
    
    if city:
        query += " AND city ILIKE %s"
        params.append(f"%{city}%")
    
    if min_quality > 0:
        query += " AND quality_score >= %s"
        params.append(min_quality)
    
    if has_email is not None:
        if has_email:
            query += " AND email IS NOT NULL AND email != ''"
        else:
            query += " AND (email IS NULL OR email = '')"
    
    if has_phone is not None:
        if has_phone:
            query += " AND phone IS NOT NULL AND phone != ''"
        else:
            query += " AND (phone IS NULL OR phone = '')"
    
    if brokerage:
        query += " AND brokerage ILIKE %s"
        params.append(f"%{brokerage}%")
    
    query += " ORDER BY quality_score DESC, last_name ASC"
    query += " LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    
    cur.execute(query, params)
    results = cur.fetchall()
    conn.close()
    
    return results


@app.get("/leads/{drill_id}", response_model=Lead)
async def get_lead(drill_id: str):
    """Get a single lead by drill_id."""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM agents WHERE drill_id = %s", (drill_id,))
    result = cur.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return result


@app.get("/leads/export")
async def export_leads(
    city: Optional[str] = Query(None),
    status: Optional[str] = Query("Licensed"),
    min_quality: Optional[int] = Query(0),
    format: str = Query("csv", description="Export format: csv or json")
):
    """
    Export leads to CSV or JSON.
    
    Example:
        GET /leads/export?city=Calgary&min_quality=70&format=csv
    """
    conn = get_db()
    cur = conn.cursor()
    
    # Build query (same logic as list_leads)
    query = "SELECT * FROM agents WHERE 1=1"
    params = []
    
    if status:
        query += " AND status LIKE %s"
        params.append(f"%{status}%")
    
    if city:
        query += " AND city ILIKE %s"
        params.append(f"%{city}%")
    
    if min_quality > 0:
        query += " AND quality_score >= %s"
        params.append(min_quality)
    
    query += " ORDER BY quality_score DESC, last_name ASC"
    
    cur.execute(query, params)
    results = cur.fetchall()
    conn.close()
    
    if format == "csv":
        # Generate CSV
        output = io.StringIO()
        if results:
            fieldnames = results[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for row in results:
                writer.writerow(row)
        
        csv_content = output.getvalue()
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=leads_export.csv"}
        )
    else:
        # Return JSON
        return results


@app.get("/leads/stats", response_model=LeadStats)
async def get_stats():
    """Get lead statistics dashboard."""
    conn = get_db()
    cur = conn.cursor()
    
    # Total leads
    cur.execute("SELECT COUNT(*) as count FROM agents WHERE status LIKE '%Licensed%'")
    total = cur.fetchone()['count']
    
    # Email stats
    cur.execute("SELECT COUNT(*) as count FROM agents WHERE email IS NOT NULL AND email != ''")
    with_email = cur.fetchone()['count']
    
    # Phone stats
    cur.execute("SELECT COUNT(*) as count FROM agents WHERE phone IS NOT NULL AND phone != ''")
    with_phone = cur.fetchone()['count']
    
    # Both
    cur.execute("""
        SELECT COUNT(*) as count FROM agents 
        WHERE email IS NOT NULL AND email != '' 
        AND phone IS NOT NULL AND phone != ''
    """)
    with_both = cur.fetchone()['count']
    
    # Avg quality
    cur.execute("SELECT AVG(quality_score) as avg FROM agents")
    avg_quality = cur.fetchone()['avg'] or 0
    
    # Top cities
    cur.execute("""
        SELECT city, COUNT(*) as count 
        FROM agents 
        WHERE city IS NOT NULL AND city != ''
        GROUP BY city 
        ORDER BY count DESC 
        LIMIT 10
    """)
    top_cities = [{"city": row['city'], "count": row['count']} for row in cur.fetchall()]
    
    # Top brokerages
    cur.execute("""
        SELECT brokerage, COUNT(*) as count 
        FROM agents 
        WHERE brokerage IS NOT NULL AND brokerage != ''
        GROUP BY brokerage 
        ORDER BY count DESC 
        LIMIT 10
    """)
    top_brokerages = [{"brokerage": row['brokerage'], "count": row['count']} for row in cur.fetchall()]
    
    conn.close()
    
    return LeadStats(
        total_leads=total,
        with_email=with_email,
        with_phone=with_phone,
        with_both=with_both,
        avg_quality_score=round(avg_quality, 1),
        top_cities=top_cities,
        top_brokerages=top_brokerages
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
