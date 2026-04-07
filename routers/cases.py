from fastapi import APIRouter, UploadFile, File, HTTPException
from db import get_conn
from services.cases import (
    process_import, get_stats,
    get_charts_by_month, get_charts_by_day,
    get_pie_month, get_pie_day_filed,
    search_cases, get_all_import_runs,
)

router = APIRouter()


# ── Health ────────────────────────────────────────────────────────────────────

@router.api_route("/health", methods=["GET", "HEAD"])
def health():
    try:
        conn = get_conn()
        conn.close()
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "db": str(e)}


# ── Import ────────────────────────────────────────────────────────────────────

@router.post("/import-json")
async def import_json(file: UploadFile = File(...)):
    content  = await file.read()
    filename = file.filename or "upload.json"

    try:
        conn = get_conn()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {e}")

    try:
        return process_import(conn, content, filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        conn.close()


# ── Dashboard API ─────────────────────────────────────────────────────────────

@router.get("/api/stats")
def api_stats():
    try:
        conn = get_conn()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
    try:
        return get_stats(conn)
    finally:
        conn.close()


@router.get("/api/charts/by-month")
def api_by_month():
    try:
        conn = get_conn()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
    try:
        return get_charts_by_month(conn)
    finally:
        conn.close()


@router.get("/api/charts/by-day")
def api_by_day(month: str):
    try:
        conn = get_conn()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
    try:
        return get_charts_by_day(conn, month)
    finally:
        conn.close()


@router.get("/api/charts/pie-month")
def api_pie_month(month: str):
    try:
        conn = get_conn()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
    try:
        return get_pie_month(conn, month)
    finally:
        conn.close()


@router.get("/api/charts/pie-day-filed")
def api_pie_day_filed(date: str):
    try:
        conn = get_conn()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
    try:
        return get_pie_day_filed(conn, date)
    finally:
        conn.close()


@router.get("/api/search")
def api_search(case_number: str = None, date: str = None):
    if not case_number and not date:
        raise HTTPException(status_code=400, detail="Provide case_number or date")
    try:
        conn = get_conn()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
    try:
        return search_cases(conn, case_number, date)
    finally:
        conn.close()


@router.get("/api/import-runs")
def api_import_runs():
    try:
        conn = get_conn()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
    try:
        return get_all_import_runs(conn)
    finally:
        conn.close()