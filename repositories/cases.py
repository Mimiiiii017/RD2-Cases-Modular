# Data access layer
from psycopg2.extras import execute_values


# ── Cases ─────────────────────────────────────────────────────────────────────

def upsert_cases(conn, rows: list[tuple]):
    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO public.case_latest
                (case_number, service_center, case_type, case_status,
                 title, application_filed_date, last_received_date, updated_at)
            VALUES %s
            ON CONFLICT (case_number) DO UPDATE SET
                service_center         = EXCLUDED.service_center,
                case_type              = EXCLUDED.case_type,
                case_status            = EXCLUDED.case_status,
                title                  = EXCLUDED.title,
                application_filed_date = EXCLUDED.application_filed_date,
                last_received_date     = EXCLUDED.last_received_date,
                updated_at             = EXCLUDED.updated_at;
        """, rows)
    conn.commit()


def count_all(conn) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM public.case_latest")
        return cur.fetchone()[0]


def get_top_status(conn) -> str:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT case_status FROM public.case_latest
            GROUP BY case_status ORDER BY COUNT(*) DESC LIMIT 1
        """)
        row = cur.fetchone()
        return row[0] if row else "N/A"


def get_last_updated(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT MAX(updated_at) FROM public.case_latest")
        return cur.fetchone()[0]


def get_avg_processing_days(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT AVG(EXTRACT(EPOCH FROM (last_received_date - application_filed_date)) / 86400)
            FROM public.case_latest
            WHERE application_filed_date IS NOT NULL
            AND last_received_date IS NOT NULL
        """)
        return cur.fetchone()[0]


def get_by_month(conn) -> list:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT TO_CHAR(application_filed_date, 'YYYY-MM') AS month,
                   case_status, COUNT(*) AS cnt
            FROM public.case_latest
            WHERE application_filed_date IS NOT NULL
            GROUP BY month, case_status
            ORDER BY month ASC, cnt DESC
        """)
        return cur.fetchall()


def get_by_day(conn, month: str) -> list:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT TO_CHAR(application_filed_date, 'YYYY-MM-DD') AS day,
                   case_status, COUNT(*) AS cnt
            FROM public.case_latest
            WHERE TO_CHAR(application_filed_date, 'YYYY-MM') = %s
            GROUP BY day, case_status
            ORDER BY day ASC
        """, (month,))
        return cur.fetchall()


def get_pie_by_month(conn, month: str) -> list:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT case_status, COUNT(*) AS cnt
            FROM public.case_latest
            WHERE TO_CHAR(application_filed_date, 'YYYY-MM') = %s
            GROUP BY case_status ORDER BY cnt DESC
        """, (month,))
        return cur.fetchall()


def get_pie_by_day_filed(conn, date: str) -> list:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT case_status, COUNT(*) AS cnt
            FROM public.case_latest
            WHERE DATE(application_filed_date) = %s
            GROUP BY case_status ORDER BY cnt DESC
        """, (date,))
        return cur.fetchall()


def get_search_by_case_number(conn, case_number: str) -> list:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT case_number, service_center, case_type, case_status,
                   title, application_filed_date, last_received_date, updated_at
            FROM public.case_latest
            WHERE UPPER(case_number) = UPPER(%s)
        """, (case_number.strip(),))
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]


def get_search_by_date(conn, date: str) -> list:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT case_number, service_center, case_type, case_status,
                   title, application_filed_date, last_received_date, updated_at
            FROM public.case_latest
            WHERE DATE(application_filed_date) = %s
            ORDER BY application_filed_date DESC
        """, (date,))
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]


# ── Import runs ───────────────────────────────────────────────────────────────

def log_import_run(conn, filename: str, rows_read: int, rows_kept: int,
                   rows_skipped: int, total_in_db: int):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO public.import_runs
                (filename, rows_read, rows_kept, rows_skipped, total_in_db)
            VALUES (%s, %s, %s, %s, %s)
        """, (filename, rows_read, rows_kept, rows_skipped, total_in_db))
    conn.commit()


def get_import_runs(conn) -> list:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, filename, imported_at, rows_read, rows_kept,
                   rows_skipped, total_in_db
            FROM public.import_runs
            ORDER BY imported_at DESC
            LIMIT 50
        """)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]