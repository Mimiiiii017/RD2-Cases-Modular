# Business logic layer
import json
from datetime import datetime
from fastapi import HTTPException
from repositories.cases import (
    upsert_cases, count_all, get_top_status, get_last_updated,
    get_avg_processing_days, get_by_month, get_by_day,
    get_pie_by_month, get_pie_by_day_filed,
    get_search_by_case_number, get_search_by_date,
    log_import_run, get_import_runs,
)

REQUIRED_KEYS = [
    "Case Number", "Service Center", "Case Type", "Case Status",
    "Title", "Application Filed Date", "Last Received Date",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_dt(value):
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(value).strip(), fmt)
        except ValueError:
            continue
    return None


# ── Import ────────────────────────────────────────────────────────────────────

def validate_and_clean(records: list[dict]) -> list[tuple]:
    """Validate, normalise, and deduplicate records. Returns list of tuples."""
    cleaned = {}
    for rec in records:
        missing = [k for k in REQUIRED_KEYS if k not in rec]
        if missing:
            raise ValueError(f"Missing keys: {missing}")

        last_received = parse_dt(rec.get("Last Received Date"))
        case_number   = str(rec.get("Case Number", "")).strip()

        if not case_number or last_received is None:
            continue

        row = (
            case_number,
            str(rec.get("Service Center", "")).strip(),
            str(rec.get("Case Type", "")).strip(),
            str(rec.get("Case Status", "")).strip().lower(),
            str(rec.get("Title", "")).strip(),
            parse_dt(rec.get("Application Filed Date")),
            last_received,
            datetime.utcnow(),
        )

        # Deduplicate: keep latest last_received_date per case number
        if case_number not in cleaned or last_received > cleaned[case_number][6]:
            cleaned[case_number] = row

    return list(cleaned.values())


def process_import(conn, raw_bytes: bytes, filename: str) -> dict:
    """Full import pipeline: parse JSON → validate → deduplicate → upsert → log."""
    from db import ensure_tables

    try:
        records = json.loads(raw_bytes)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")

    if not isinstance(records, list):
        raise ValueError("JSON must be an array of objects")

    rows_read = len(records)
    rows      = validate_and_clean(records)
    rows_kept = len(rows)

    ensure_tables(conn)
    upsert_cases(conn, rows)
    total_in_db = count_all(conn)

    log_import_run(
        conn, filename, rows_read, rows_kept,
        rows_read - rows_kept, total_in_db
    )

    return {
        "status":       "success",
        "filename":     filename,
        "rows_read":    rows_read,
        "rows_kept":    rows_kept,
        "rows_skipped": rows_read - rows_kept,
        "total_in_db":  total_in_db,
    }


# ── Stats ─────────────────────────────────────────────────────────────────────

def get_stats(conn) -> dict:
    total       = count_all(conn)
    top_status  = get_top_status(conn)
    last_import = get_last_updated(conn)
    avg         = get_avg_processing_days(conn)
    return {
        "total_cases":         total,
        "top_status":          top_status,
        "last_import":         last_import.isoformat() if last_import else None,
        "avg_processing_days": round(float(avg), 1) if avg else None,
    }


# ── Charts ────────────────────────────────────────────────────────────────────

def get_charts_by_month(conn) -> dict:
    rows = get_by_month(conn)
    data = {}
    for month, status, cnt in rows:
        data.setdefault(month, {})[status] = cnt
    return {"data": data}


def get_charts_by_day(conn, month: str) -> dict:
    rows = get_by_day(conn, month)
    data = {}
    for day, status, cnt in rows:
        data.setdefault(day, {})[status] = cnt
    return {"month": month, "data": data}


def get_pie_month(conn, month: str) -> dict:
    rows = get_pie_by_month(conn, month)
    return {"month": month, "data": [{"status": r[0], "count": r[1]} for r in rows]}


def get_pie_day_filed(conn, date: str) -> dict:
    rows = get_pie_by_day_filed(conn, date)
    return {"date": date, "data": [{"status": r[0], "count": r[1]} for r in rows]}


# ── Search ────────────────────────────────────────────────────────────────────

def search_cases(conn, case_number: str = None, date: str = None) -> dict:
    if case_number:
        rows = get_search_by_case_number(conn, case_number)
    else:
        rows = get_search_by_date(conn, date)

    for row in rows:
        for k, v in row.items():
            if hasattr(v, 'isoformat'):
                row[k] = v.isoformat()

    return {"results": rows, "count": len(rows)}


# ── Import runs ───────────────────────────────────────────────────────────────

def get_all_import_runs(conn) -> dict:
    runs = get_import_runs(conn)
    for run in runs:
        if run.get("imported_at"):
            run["imported_at"] = run["imported_at"].isoformat()
    return {"runs": runs, "count": len(runs)}