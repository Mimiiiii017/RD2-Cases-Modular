from pydantic import BaseModel
from typing import Optional


class HealthResponse(BaseModel):
    status: str
    db: str


class ImportResult(BaseModel):
    status: str
    filename: str
    rows_read: int
    rows_kept: int
    rows_skipped: int
    total_in_db: int


class StatsResponse(BaseModel):
    total_cases: int
    top_status: str
    last_import: Optional[str]
    avg_processing_days: Optional[float]


class ByMonthResponse(BaseModel):
    data: dict


class ByDayResponse(BaseModel):
    month: str
    data: dict


class PieItem(BaseModel):
    status: str
    count: int


class PieMonthResponse(BaseModel):
    month: str
    data: list[PieItem]


class PieDayFiledResponse(BaseModel):
    date: str
    data: list[PieItem]


class CaseRecord(BaseModel):
    case_number: str
    service_center: Optional[str]
    case_type: Optional[str]
    case_status: Optional[str]
    title: Optional[str]
    application_filed_date: Optional[str]
    last_received_date: Optional[str]
    updated_at: Optional[str]


class SearchResponse(BaseModel):
    results: list[CaseRecord]
    count: int


class ImportRun(BaseModel):
    id: int
    filename: Optional[str]
    imported_at: Optional[str]
    rows_read: int
    rows_kept: int
    rows_skipped: int
    total_in_db: int


class ImportRunsResponse(BaseModel):
    runs: list[ImportRun]
    count: int
