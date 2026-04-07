from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from db import get_conn
from services.cases import (
    process_import, get_stats,
    get_charts_by_month, get_charts_by_day,
    get_pie_month, get_pie_day_filed,
    search_cases, get_all_import_runs,
)

router = APIRouter()

UPLOAD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Caseflow – Import</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {
    --ink: #111827; --muted: #6b7280; --sand: #f7f3ea;
    --teal: #0f766e; --teal-dark: #0b5f58;
    --card: #fffdf8; --line: rgba(17,24,39,0.12);
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Space Grotesk', sans-serif;
    background: radial-gradient(1200px 800px at 10% -20%, #fff2c9 0%, transparent 60%),
                radial-gradient(900px 600px at 95% 0%, #cfeee8 0%, transparent 55%),
                var(--sand);
    min-height: 100vh; color: var(--ink);
  }
  header {
    background: rgba(255,253,248,0.9); border-bottom: 1px solid var(--line);
    padding: 0 32px; height: 62px; display: flex; align-items: center;
    justify-content: space-between; backdrop-filter: blur(8px);
  }
  .brand-name { font-size: 16px; font-weight: 600; }
  .logout {
    font-size: 12px; color: var(--teal); text-decoration: none;
    padding: 7px 14px; border: 1px solid rgba(15,118,110,0.3); border-radius: 999px;
    font-family: 'IBM Plex Mono', monospace; letter-spacing: 0.06em; transition: all 0.15s;
  }
  .logout:hover { border-color: var(--teal); color: var(--teal-dark); }
  .page { max-width: 720px; margin: 48px auto; padding: 0 24px; }
  h2 { font-size: 22px; font-weight: 600; margin-bottom: 6px; }
  .sub { font-size: 14px; color: var(--muted); margin-bottom: 28px; }
  .card {
    background: var(--card); border: 1px solid var(--line); border-radius: 18px;
    padding: 32px; box-shadow: 0 16px 28px rgba(17,24,39,0.12);
    animation: rise 0.45s ease-out; margin-bottom: 24px;
  }
  .card-title { font-size: 15px; font-weight: 600; margin-bottom: 16px; }
  .drop-zone {
    border: 2px dashed rgba(17,24,39,0.22); border-radius: 14px;
    padding: 52px 24px; text-align: center; cursor: pointer; transition: all 0.2s;
    background: linear-gradient(135deg, #fff7e8 0%, #fef3e2 45%, #e7f6f2 100%);
  }
  .drop-zone:hover, .drop-zone.drag-over {
    border-color: var(--teal); box-shadow: 0 12px 20px rgba(15,118,110,0.2);
    transform: translateY(-1px);
  }
  .upload-icon {
    width: 46px; height: 46px; background: rgba(15,118,110,0.12);
    border-radius: 12px; display: flex; align-items: center; justify-content: center;
    margin: 0 auto 16px;
  }
  .upload-icon svg { width: 22px; height: 22px; color: var(--teal); }
  .drop-zone h3 { font-size: 16px; font-weight: 600; margin-bottom: 6px; }
  .drop-zone p  { font-size: 13px; color: var(--muted); }
  .drop-zone p span { color: var(--teal); cursor: pointer; }
  #fileInput { display: none; }
  .selected-file {
    display: none; align-items: center; gap: 10px; margin-top: 16px;
    background: #fff; border: 1px solid var(--line); border-radius: 12px; padding: 12px 14px;
  }
  .selected-file.visible { display: flex; }
  .file-name { font-size: 13px; font-weight: 600; flex: 1; }
  .file-size { font-size: 12px; color: var(--muted); }
  .remove { background: none; border: none; cursor: pointer; color: var(--muted); font-size: 18px; padding: 0 4px; }
  .remove:hover { color: #ef4444; }
  .import-btn {
    width: 100%; margin-top: 16px; padding: 12px;
    background: linear-gradient(135deg, var(--teal) 0%, #14b8a6 100%);
    color: white; border: none; border-radius: 12px;
    font-size: 14px; font-weight: 600; font-family: 'Space Grotesk', sans-serif;
    cursor: pointer; transition: transform 0.12s, box-shadow 0.2s;
    display: flex; align-items: center; justify-content: center; gap: 8px;
  }
  .import-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 12px 20px rgba(15,118,110,0.25); }
  .import-btn:disabled { opacity: 0.5; cursor: not-allowed; }
  .result { display: none; margin-top: 20px; padding: 16px 20px; border-radius: 12px; font-size: 14px; }
  .result.success { display: block; background: #ecfdf5; border: 1px solid #a7f3d0; color: #065f46; }
  .result.error   { display: block; background: #fff1f2; border: 1px solid #fecdd3; color: #9f1239; }
  .result strong  { display: block; font-weight: 600; margin-bottom: 6px; }
  .stats { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 12px; }
  .stat { background: #fff; border: 1px solid rgba(15,118,110,0.15); border-radius: 10px; padding: 12px 14px; }
  .stat-val { font-size: 22px; font-weight: 700; }
  .stat-lbl { font-size: 11px; color: var(--muted); margin-top: 2px; }
  .runs-table { width: 100%; border-collapse: collapse; font-size: 13px; }
  .runs-table th {
    text-align: left; padding: 8px 12px; font-size: 11px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted);
    border-bottom: 1px solid var(--line);
  }
  .runs-table td { padding: 10px 12px; border-bottom: 1px solid rgba(17,24,39,0.06); }
  .runs-table tr:last-child td { border-bottom: none; }
  .spinner {
    width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3);
    border-top-color: white; border-radius: 50%;
    animation: spin 0.7s linear infinite; display: none;
  }
  .spinner.visible { display: block; }
  @keyframes spin { to { transform: rotate(360deg); } }
  @keyframes rise { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
  @media (max-width: 640px) { .stats { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<header>
  <span class="brand-name">Caseflow</span>
  <a href="/logout" class="logout">Sign out</a>
</header>
<div class="page">
  <h2>Import Cases</h2>
  <p class="sub">Upload a JSON file to import cases into the database.</p>
  <div class="card">
    <div class="card-title">Upload JSON Dataset</div>
    <div class="drop-zone" id="dropZone" onclick="document.getElementById('fileInput').click()">
      <div class="upload-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round"
                d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"/>
        </svg>
      </div>
      <h3>Drop your JSON file here</h3>
      <p>or <span>browse to upload</span></p>
    </div>
    <input type="file" id="fileInput" accept=".json" onchange="handleFile(this.files[0])">
    <div class="selected-file" id="selectedFile">
      <span class="file-name" id="fileName">–</span>
      <span class="file-size" id="fileSize">–</span>
      <button class="remove" onclick="clearFile()">×</button>
    </div>
    <button class="import-btn" id="importBtn" disabled onclick="runImport()">
      <div class="spinner" id="spinner"></div>
      <span id="btnLabel">Import to Database</span>
    </button>
    <div class="result" id="result"></div>
  </div>
  <div class="card">
    <div class="card-title">Import History</div>
    <div id="runsContainer">
      <p style="font-size:13px;color:var(--muted)">Loading…</p>
    </div>
  </div>
</div>
<script>
  let selectedFile = null;

  function handleFile(f) {
    if (!f) return;
    selectedFile = f;
    document.getElementById('fileName').textContent = f.name;
    document.getElementById('fileSize').textContent = (f.size/1024).toFixed(1) + ' KB';
    document.getElementById('selectedFile').classList.add('visible');
    document.getElementById('importBtn').disabled = false;
    document.getElementById('result').className = 'result';
  }

  function clearFile() {
    selectedFile = null;
    document.getElementById('fileInput').value = '';
    document.getElementById('selectedFile').classList.remove('visible');
    document.getElementById('importBtn').disabled = true;
  }

  const dz = document.getElementById('dropZone');
  dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('drag-over'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('drag-over'));
  dz.addEventListener('drop', e => { e.preventDefault(); dz.classList.remove('drag-over'); handleFile(e.dataTransfer.files[0]); });

  async function runImport() {
    if (!selectedFile) return;
    const btn = document.getElementById('importBtn');
    const spinner = document.getElementById('spinner');
    const label = document.getElementById('btnLabel');
    const result = document.getElementById('result');
    btn.disabled = true; spinner.classList.add('visible'); label.textContent = 'Importing…';
    result.className = 'result';
    const form = new FormData();
    form.append('file', selectedFile);
    try {
      const res = await fetch('/import-json', { method: 'POST', body: form });
      const d = await res.json();
      if (res.ok) {
        result.className = 'result success';
        result.innerHTML = `
          <strong>✓ Import successful</strong>
          <div class="stats">
            <div class="stat"><div class="stat-val">${d.rows_read.toLocaleString()}</div><div class="stat-lbl">Rows read</div></div>
            <div class="stat"><div class="stat-val">${d.rows_kept.toLocaleString()}</div><div class="stat-lbl">Rows imported</div></div>
            <div class="stat"><div class="stat-val">${d.rows_skipped.toLocaleString()}</div><div class="stat-lbl">Rows skipped</div></div>
            <div class="stat"><div class="stat-val">${d.total_in_db.toLocaleString()}</div><div class="stat-lbl">Total in database</div></div>
          </div>`;
        loadRuns();
      } else {
        result.className = 'result error';
        result.innerHTML = `<strong>Import failed</strong>${d.detail || 'Unknown error'}`;
      }
    } catch(e) {
      result.className = 'result error';
      result.innerHTML = `<strong>Error</strong>Could not reach the server.`;
    } finally {
      btn.disabled = false; spinner.classList.remove('visible'); label.textContent = 'Import to Database';
    }
  }

  async function loadRuns() {
    try {
      const res = await fetch('/api/import-runs');
      const d = await res.json();
      const el = document.getElementById('runsContainer');
      if (!d.runs.length) { el.innerHTML = '<p style="font-size:13px;color:var(--muted)">No imports yet.</p>'; return; }
      el.innerHTML = `
        <table class="runs-table">
          <thead><tr>
            <th>#</th><th>Filename</th><th>Imported At</th>
            <th>Read</th><th>Kept</th><th>Skipped</th><th>Total in DB</th>
          </tr></thead>
          <tbody>${d.runs.map(r => `
            <tr>
              <td>${r.id}</td><td>${r.filename}</td>
              <td>${new Date(r.imported_at).toLocaleString()}</td>
              <td>${r.rows_read}</td><td>${r.rows_kept}</td>
              <td>${r.rows_skipped}</td><td>${r.total_in_db}</td>
            </tr>`).join('')}
          </tbody>
        </table>`;
    } catch {}
  }

  loadRuns();
</script>
</body>
</html>
"""


# ── Pages ─────────────────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
def root():
    return RedirectResponse(url="/upload")


@router.get("/upload", response_class=HTMLResponse)
def upload_page():
    return HTMLResponse(UPLOAD_HTML)


@router.get("/logout")
def logout():
    return RedirectResponse(url="/upload")


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