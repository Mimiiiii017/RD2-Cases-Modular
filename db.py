import psycopg2
import os
from dotenv import load_dotenv

load_dotenv(override=True)


def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "casesdb"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )


def ensure_tables(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS public.case_latest (
                case_number            TEXT PRIMARY KEY,
                service_center         TEXT,
                case_type              TEXT,
                case_status            TEXT,
                title                  TEXT,
                application_filed_date TIMESTAMP,
                last_received_date     TIMESTAMP,
                updated_at             TIMESTAMP DEFAULT NOW()
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS public.import_runs (
                id           SERIAL PRIMARY KEY,
                filename     TEXT,
                imported_at  TIMESTAMP DEFAULT NOW(),
                rows_read    INTEGER,
                rows_kept    INTEGER,
                rows_skipped INTEGER,
                total_in_db  INTEGER
            );
        """)
        conn.commit()