from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import hashlib
import io
import json
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4
import pandas as pd
from rapidfuzz import fuzz, process

# ─────────────────────────────────────────────
# App setup
# ─────────────────────────────────────────────
app = FastAPI(
    title="Kisna Excel Merger API",
    description="Upload 5 Excel files to get the Final Merged & Summary Excel.",
    version="1.0.0",
)

# Allow any frontend origin to call this API (tighten in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    init_db()
    global JOB_STORE
    JOB_STORE = _load_jobs_from_db()


DB_PATH = Path(__file__).resolve().parent / "job_store.db"
JOB_STORE: list[dict] = []


def _connect_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _connect_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            job_code TEXT,
            file_name TEXT,
            date TEXT,
            time_utc TEXT,
            file_size TEXT,
            file_type TEXT,
            status TEXT,
            operator TEXT,
            records_count TEXT,
            sha256_seal TEXT,
            source_files TEXT,
            preview_rows TEXT,
            sheet_data TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    columns = {row[1] for row in conn.execute("PRAGMA table_info(jobs)")}
    if "metrics" not in columns:
        conn.execute("ALTER TABLE jobs ADD COLUMN metrics TEXT")
    if "sheet_data" not in columns:
        conn.execute("ALTER TABLE jobs ADD COLUMN sheet_data TEXT")
    conn.commit()
    conn.close()


def _persist_job(job: dict, sheet_data: dict[str, list[dict]]) -> None:
    conn = _connect_db()
    conn.execute(
        """
        INSERT OR REPLACE INTO jobs (
            id, job_code, file_name, date, time_utc, file_size, file_type,
            status, operator, records_count, sha256_seal, source_files, preview_rows, metrics, sheet_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job["id"],
            job["jobCode"],
            job["fileName"],
            job["date"],
            job["timeUTC"],
            job["fileSize"],
            job["fileType"],
            job["status"],
            job["operator"],
            job["recordsCount"],
            job["sha256Seal"],
            json.dumps(job.get("sourceFiles", [])),
            json.dumps(job.get("previewRows", [])),
            json.dumps(job.get("metrics") or {}),
            json.dumps(sheet_data),
        ),
    )
    conn.commit()
    conn.close()


def _load_sheet_data(job_id: str) -> dict[str, list[dict]]:
    conn = _connect_db()
    row = conn.execute("SELECT sheet_data FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    if not row or not row["sheet_data"]:
        return {}
    return json.loads(row["sheet_data"])


def _workbook_bytes_from_sheets(sheet_data: dict[str, list[dict]]) -> bytes:
    if not sheet_data:
        raise HTTPException(
            status_code=409,
            detail="The full workbook data is unavailable for this job. Reprocess the source files to enable workbook downloads.",
        )

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, rows in sheet_data.items():
            dataframe = pd.DataFrame.from_records(rows)
            dataframe.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    output.seek(0)
    return output.getvalue()


def _load_jobs_from_db() -> list[dict]:
    conn = _connect_db()
    rows = conn.execute(
        """
        SELECT id, job_code, file_name, date, time_utc, file_size, file_type,
               status, operator, records_count, sha256_seal, source_files, preview_rows, metrics
        FROM jobs
        ORDER BY created_at DESC
        """
    ).fetchall()
    conn.close()

    jobs: list[dict] = []
    for row in rows:
        source_files = json.loads(row["source_files"] or "[]") if row["source_files"] else []
        preview_rows = json.loads(row["preview_rows"] or "[]") if row["preview_rows"] else []
        metrics = json.loads(row["metrics"] or "{}") if row["metrics"] else {}
        jobs.append(
            {
                "id": row["id"],
                "jobCode": row["job_code"],
                "fileName": row["file_name"],
                "date": row["date"],
                "timeUTC": row["time_utc"],
                "fileSize": row["file_size"],
                "fileType": row["file_type"],
                "status": row["status"],
                "operator": row["operator"],
                "recordsCount": row["records_count"],
                "sha256Seal": row["sha256_seal"],
                "sourceFiles": source_files,
                "previewRows": preview_rows,
                "metrics": metrics,
            }
        )
    return jobs


init_db()
JOB_STORE = _load_jobs_from_db()


def _job_from_payload(file_name: str, records_count: int, status: str, source_files: list[str], output_bytes: bytes | None = None):
    now = datetime.now(timezone.utc)
    seal = hashlib.sha256((output_bytes or b"")).hexdigest()[:24] if output_bytes else "job-seal-not-available"
    return {
        "id": str(uuid4()),
        "jobCode": f"#SP-{now.strftime('%Y%m%d-%H%M%S')}",
        "fileName": file_name,
        "date": now.strftime("%Y-%m-%d"),
        "timeUTC": now.strftime("%H:%M:%S"),
        "fileSize": "7.2 MB",
        "fileType": "xlsx",
        "status": status,
        "operator": "Kisna Ops",
        "recordsCount": f"{records_count:,}",
        "sha256Seal": seal,
        "sourceFiles": source_files,
    }

# ─────────────────────────────────────────────
# Filename validation
# ─────────────────────────────────────────────
EXPECTED_KEYWORDS = {
    "branded_file":    "branded",
    "rm_file":         "rm",
    "master_file":     "master",
    "sale_file":       "sale",
    "receivable_file": "receivable",
}

FINAL_OUTPUT_COLUMNS = [
    "Priority",
    "particulars",
    "vch type",
    "vch no.",
    "date",
    "debit",
    "credit",
    "emr id",
    "jso order no",
    "source",
    "region",
    "zone",
    "part",
    "state",
    "ba code",
    "territory",
    "city",
    "type",
    "status",
    "kisna/siva",
    "party name",
    "nsm",
    "zone head",
    "receivable_credit",
    "outstanding",
    "advance_payment",
]


def must_be_xlsx(filename: str, field_name: str) -> None:
    """Reject anything that is not an .xlsx file."""
    if not filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=400,
            detail=f"'{field_name}' must be an .xlsx file (got: '{filename}').",
        )


def validate_filename(field_name: str, filename: str) -> None:
    """Raise HTTP 400 if the uploaded filename does not match the expected keyword."""
    keyword = EXPECTED_KEYWORDS[field_name]
    if keyword not in filename.lower():
        raise HTTPException(
            status_code=400,
            detail=(
                f"Wrong file uploaded for '{field_name}'. "
                f"Filename must contain '{keyword}' (got: '{filename}'). "
                "Please upload the correct file."
            ),
        )


# ─────────────────────────────────────────────
# Core processing  (100% identical to new3.py)
# ─────────────────────────────────────────────
def _preview_rows_from_workbook(workbook_bytes: bytes, limit: int = 200) -> list[dict]:
    """Extract a lightweight preview set from the merged workbook for spreadsheet rendering."""
    try:
        preview_df = pd.read_excel(io.BytesIO(workbook_bytes), sheet_name="Final Merged")
    except Exception:
        return []

    rows = preview_df.head(limit).to_dict(orient="records")
    normalized: list[dict] = []
    for row in rows:
        clean_row = {}
        for key, value in row.items():
            if pd.isna(value):
                clean_row[str(key)] = None
            elif isinstance(value, pd.Timestamp):
                clean_row[str(key)] = value.isoformat()
            else:
                clean_row[str(key)] = value
        normalized.append(clean_row)
    return normalized


def _records_from_dataframe(dataframe: pd.DataFrame) -> list[dict]:
    records = []
    for row in dataframe.to_dict(orient="records"):
        clean_row = {}
        for key, value in row.items():
            if pd.isna(value):
                clean_row[str(key)] = None
            elif isinstance(value, pd.Timestamp):
                clean_row[str(key)] = value.isoformat()
            elif hasattr(value, "item"):
                clean_row[str(key)] = value.item()
            else:
                clean_row[str(key)] = value
        records.append(clean_row)
    return records


def process_files(
    branded_bytes: bytes,
    rm_bytes: bytes,
    master_bytes: bytes,
    sale_bytes: bytes,
    receivable_bytes: bytes,
) -> dict[str, object]:

    # Step 1: Read Branded & RM Job (header at row 9)
    branded_book = pd.read_excel(io.BytesIO(branded_bytes), sheet_name=None, header=8)
    rm_book = pd.read_excel(io.BytesIO(rm_bytes), sheet_name=None, header=8)
    branded_sheet_count = len(branded_book)
    rm_sheet_count = len(rm_book)
    branded_all = pd.concat(branded_book, ignore_index=True) if branded_book else pd.DataFrame()
    rm_all = pd.concat(rm_book, ignore_index=True) if rm_book else pd.DataFrame()

    # Cleanup
    branded_all.columns = [col.strip().lower() for col in branded_all.columns]
    rm_all.columns = [col.strip().lower() for col in rm_all.columns]

    # Normalize EMR columns
    if "emr" in branded_all.columns and "emr id" not in branded_all.columns:
        branded_all.rename(columns={"emr": "emr id"}, inplace=True)
    if "emr" in rm_all.columns and "emr id" not in rm_all.columns:
        rm_all.rename(columns={"emr": "emr id"}, inplace=True)

    # Remove "Total" rows
    branded_all = branded_all[
        ~branded_all["particulars"].astype(str).str.lower().str.contains("total", na=False)
    ]
    rm_all = rm_all[
        ~rm_all["particulars"].astype(str).str.lower().str.contains("total", na=False)
    ]

    # Branded: find JSO Order Number column
    jso_col = None
    for col in branded_all.columns:
        if "jso order number" in col or "jso no" in col:
            jso_col = col
            break

    if not jso_col:
        raise HTTPException(
            status_code=422,
            detail="Branded Excel must have a 'JSO Order Number' or 'JSO No' column.",
        )

    branded_data = branded_all[
        ["particulars", "vch type", "vch no.", "date", "debit", "credit", "emr id", jso_col]
    ].copy()
    branded_data.rename(columns={jso_col: "jso order no"}, inplace=True)

    rm_data = rm_all[
        ["particulars", "vch type", "vch no.", "date", "debit", "credit", "emr id"]
    ].copy()

    # Read master and tally sheets
    # Strip trailing whitespace from sheet name to be safe
    master_xl = pd.ExcelFile(io.BytesIO(master_bytes))
    master_sheet = next(
        (s for s in master_xl.sheet_names if s.strip() == "Kisna Force Master Details"),
        None,
    )
    if master_sheet is None:
        raise HTTPException(
            status_code=422,
            detail=f"Master Excel must contain a sheet named 'Kisna Force Master Details'. Found: {master_xl.sheet_names}",
        )
    master_df = master_xl.parse(master_sheet, header=0)
    tally_df = pd.read_excel(
        io.BytesIO(master_bytes), sheet_name="Tally Ledger Name", header=0
    )
    master_df.columns = master_df.columns.str.lower().str.strip()
    tally_df.columns = tally_df.columns.str.lower().str.strip()

    tally_df["company"] = tally_df["company"].astype(str).str.strip().str.lower()
    tally_df["code"] = tally_df["code"].astype(str).str.strip().str.upper()
    if "emr id" in master_df.columns:
        master_df["emr id"] = master_df["emr id"].astype(str).str.strip().str.upper()

    # Map EMR if missing (branded & rm)
    particular_to_code = dict(zip(tally_df["company"], tally_df["code"]))
    patched_emr = 0
    for df in [branded_data, rm_data]:
        missing_emr = df["emr id"].isna()
        df["emr id"] = df["emr id"].fillna(
            df["particulars"].astype(str).str.strip().str.lower().map(particular_to_code)
        )
        patched_emr += int((missing_emr & df["emr id"].notna()).sum())
        df["emr id"] = df["emr id"].astype(str).str.strip().str.upper()

    # Source tagging
    branded_data["source"] = "branded"
    rm_data["source"] = "rm"
    combined = pd.concat([branded_data, rm_data], ignore_index=True)

    # Merge with master data (attributes)
    master_cols_keep = [
        "emr id", "region", "zone", "part", "state", "ba code",
        "territory", "city", "type", "status", "kisna/siva",
        "party name", "nsm", "zone head",
    ]
    final_rows = combined.merge(
        master_df[master_cols_keep].drop_duplicates("emr id"),
        on="emr id",
        how="left",
    )

    # Sales file (only for RM matching to fetch JSO)
    sale_sheet_count = len(pd.ExcelFile(io.BytesIO(sale_bytes)).sheet_names)
    sale_df = pd.read_excel(io.BytesIO(sale_bytes), header=0)
    sale_df.columns = sale_df.columns.str.lower()
    sale_df.rename(columns={
        "doc. date": "date",
        "doc. no.": "vch no.",
        "account code": "emr id",
        "account name": "party name",
        "sr code": "ba code",
        "ref. code": "state",
    }, inplace=True)
    if "emr id" in sale_df.columns:
        sale_df["emr id"] = sale_df["emr id"].astype(str).str.strip().str.upper()

    # Ensure sale_df has a 'jso order no' column (may be named differently)
    jso_sale_col = next(
        (c for c in sale_df.columns if "jso" in c and ("order" in c or "no" in c)), None
    )
    if jso_sale_col and jso_sale_col != "jso order no":
        sale_df.rename(columns={jso_sale_col: "jso order no"}, inplace=True)
    if "jso order no" not in sale_df.columns:
        sale_df["jso order no"] = pd.NA

    # Dates
    final_rows["date"] = pd.to_datetime(final_rows["date"], errors="coerce")
    sale_df["date"] = pd.to_datetime(sale_df["date"], errors="coerce")

    # Only RM part merge with Sale invoice for JSO
    rm_only = final_rows[final_rows["source"] == "rm"].merge(
        sale_df[["date", "vch no.", "emr id", "party name", "ba code", "state", "jso order no"]],
        on=["date", "vch no.", "emr id", "party name", "ba code", "state"],
        how="left",
        suffixes=("", "_sale"),
    )
    jso_missing = rm_only["jso order no"].isna()
    rm_only["jso order no"] = rm_only["jso order no"].combine_first(rm_only["jso order no_sale"])
    patched_jso = int((jso_missing & rm_only["jso order no"].notna()).sum())
    rm_only.drop(columns=["jso order no_sale"], inplace=True)

    branded_only = final_rows[final_rows["source"] == "branded"]
    final_rows = pd.concat([branded_only, rm_only], ignore_index=True)

    # Ensure numeric
    for col in ["debit", "credit"]:
        final_rows[col] = pd.to_numeric(final_rows[col], errors="coerce").fillna(0)

    # Priority Column
    priority_ii_ids = {
        "MPCCD", "MPGJ2", "TNPJ", "UPAH", "UPBPAKS", "UPHG", "UPHK", "UPJP",
        "UPMHJ", "UPPLP", "UPPLR", "UPUBJH1", "UPUDJB", "UPUHKJHP", "UPURJL",
        "UPUSDJBW", "UPUTRSJ",
    }
    final_rows["Priority"] = final_rows["emr id"].apply(
        lambda x: "II" if str(x).strip().upper() in priority_ii_ids else "I"
    )

    # Receivable processing
    receivable_sheet_count = len(pd.ExcelFile(io.BytesIO(receivable_bytes)).sheet_names)
    receivable_df = pd.read_excel(io.BytesIO(receivable_bytes), header=0)
    receivable_df.columns = receivable_df.columns.str.lower()

    def fuzzy_match(name, choices, threshold=85):
        if pd.isna(name):
            return None
        match, score, _ = process.extractOne(name, choices, scorer=fuzz.token_sort_ratio)
        return match if score >= threshold else None

    receivable_df["matched_company"] = receivable_df["particulars"].apply(
        lambda x: fuzzy_match(str(x).lower(), tally_df["company"].unique())
    )
    receivable_df = receivable_df.merge(
        tally_df[["company", "code"]],
        left_on="matched_company",
        right_on="company",
        how="left",
    )
    receivable_df["emr id"] = receivable_df["code"].str.upper()
    receivable_df["credit"] = pd.to_numeric(receivable_df["credit"], errors="coerce").fillna(0)

    # Ledger totals per EMR
    emr_ledger = final_rows.groupby("emr id", as_index=False).agg(
        debit=("debit", "sum"),
        credit=("credit", "sum"),
    )
    # Receivable per EMR
    emr_recv = receivable_df.groupby("emr id", as_index=False).agg(
        receivable_credit=("credit", "sum")
    )

    emr_bal = emr_ledger.merge(emr_recv, on="emr id", how="left").fillna({"receivable_credit": 0})
    emr_bal["outstanding"] = (emr_bal["debit"] - emr_bal["credit"]) - emr_bal["receivable_credit"]
    emr_bal["advance_payment"] = emr_bal["outstanding"].apply(lambda x: abs(x) if x < 0 else 0)
    emr_bal["outstanding"] = emr_bal["outstanding"].apply(lambda x: x if x > 0 else 0)

    # Merge balances back to rows
    final_rows = final_rows.merge(
        emr_bal[["emr id", "receivable_credit", "outstanding", "advance_payment"]],
        on="emr id",
        how="left",
    ).fillna({"receivable_credit": 0, "outstanding": 0, "advance_payment": 0})

    # Monthly Sheets — compute month BEFORE reordering columns so 'month' stays available
    final_rows["month"] = final_rows["date"].dt.to_period("M").astype(str)
    monthly_groups = {
        m: d.drop(columns=["month"])
        for m, d in final_rows.groupby("month")
        if m != "NaT"
    }
    year_summary = (
        final_rows.assign(year=final_rows["date"].dt.year)
        .dropna(subset=["year"])
        .assign(year=lambda dataframe: dataframe["year"].astype(int))
        .groupby("year", as_index=False)
        .agg(
            records=("emr id", "size"),
            debit=("debit", "sum"),
            credit=("credit", "sum"),
            receivable_credit=("receivable_credit", "sum"),
            outstanding=("outstanding", "sum"),
            advance_payment=("advance_payment", "sum"),
        )
    )

    # Summaries (only from emr_bal_attr)
    master_unique = master_df[["emr id", "region", "zone", "party name"]].drop_duplicates("emr id")
    emr_bal_attr = emr_bal.merge(master_unique, on="emr id", how="left")

    summary_zone = emr_bal_attr.groupby("zone", dropna=False)[
        ["debit", "receivable_credit", "outstanding", "advance_payment"]
    ].sum().reset_index()

    summary_region = emr_bal_attr.groupby("region", dropna=False)[
        ["debit", "receivable_credit", "outstanding", "advance_payment"]
    ].sum().reset_index()

    summary_company = emr_bal_attr.groupby("party name", dropna=False)[
        ["debit", "receivable_credit", "outstanding", "advance_payment"]
    ].sum().reset_index()

    summary_emr = emr_bal_attr[
        ["emr id", "debit", "receivable_credit", "outstanding", "advance_payment"]
    ].copy()

    # Align final data with the authoritative workbook schema provided by the client
    # NOTE: 'month' is a temporary helper column; exclude it from FINAL_OUTPUT_COLUMNS reorder
    missing_columns = [c for c in FINAL_OUTPUT_COLUMNS if c not in final_rows.columns]
    for col in missing_columns:
        final_rows[col] = ""
    final_rows_output = final_rows[FINAL_OUTPUT_COLUMNS]  # no 'month' col here — already excluded

    # Build output Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        final_rows_output.to_excel(writer, sheet_name="Final Merged", index=False)
        summary_zone.to_excel(writer, sheet_name="Zone Summary", index=False)
        summary_region.to_excel(writer, sheet_name="Region Summary", index=False)
        summary_company.to_excel(writer, sheet_name="Company Summary", index=False)
        summary_emr.to_excel(writer, sheet_name="EMR Summary", index=False)
        year_summary.to_excel(writer, sheet_name="Year Summary", index=False)
        for month, df_month in monthly_groups.items():
            safe_name = month.replace("-", "_")
            df_month.to_excel(writer, sheet_name=safe_name, index=False)
    output.seek(0)
    workbook_sheets = {
        "Final Merged": final_rows_output,
        "Zone Summary": summary_zone,
        "Region Summary": summary_region,
        "Company Summary": summary_company,
        "EMR Summary": summary_emr,
        "Year Summary": year_summary,
        **{
            month.replace("-", "_"): dataframe
            for month, dataframe in monthly_groups.items()
        },
    }
    sheet_data = {
        sheet_name: _records_from_dataframe(dataframe)
        for sheet_name, dataframe in workbook_sheets.items()
    }
    preview_rows = _preview_rows_from_workbook(output.getvalue())
    duplicate_keys = [column for column in ["vch no.", "date", "emr id"] if column in final_rows.columns]
    duplicate_rows = int(final_rows.duplicated(duplicate_keys, keep=False).sum()) if duplicate_keys else 0
    regions = []
    if "region" in final_rows.columns:
        regions = sorted({
            str(value).strip()
            for value in final_rows["region"].dropna().tolist()
            if str(value).strip() and str(value).strip().lower() != "nan"
        })
    master_sheet_count = len(master_xl.sheet_names)
    return {
        "workbook": output,
        "preview_rows": preview_rows,
        "sheet_data": sheet_data,
        "stats": {
            "sheetCount": branded_sheet_count + rm_sheet_count + master_sheet_count + sale_sheet_count + receivable_sheet_count,
            "recordCount": int(len(final_rows)),
            "duplicateRows": duplicate_rows,
            "patchedRows": patched_emr + patched_jso,
            "regionCount": len(regions),
            "regions": regions,
        },
    }


# ─────────────────────────────────────────────
# API Endpoints
# ─────────────────────────────────────────────
def _parse_record_count(value) -> int:
    try:
        return int(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return 0


def _preview_metrics(job: dict) -> dict:
    rows = job.get("previewRows") or []
    keys = []
    regions = set()
    patched = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        keys.append((row.get("vch no."), row.get("date"), row.get("emr id")))
        region = str(row.get("region") or "").strip()
        if region and region.lower() != "nan":
            regions.add(region)
        if str(row.get("source") or "").lower() == "rm" and row.get("jso order no"):
            patched += 1
    counts: dict = {}
    for key in keys:
        counts[key] = counts.get(key, 0) + 1
    duplicate_keys = {key for key, count in counts.items() if count > 1 and key[0]}
    duplicate_rows = sum(1 for key in keys if key in duplicate_keys)
    return {
        "recordCount": len(rows),
        "duplicateRows": duplicate_rows,
        "patchedRows": patched,
        "regionCount": len(regions),
        "regions": sorted(regions),
    }


def _resolved_metrics(job: dict) -> dict:
    stored = job.get("metrics") if isinstance(job.get("metrics"), dict) else {}
    source_files = [str(name) for name in (job.get("sourceFiles") or [])]
    xlsx_count = sum(1 for name in source_files if name.lower().endswith(".xlsx"))
    xls_count = sum(1 for name in source_files if name.lower().endswith(".xls") and not name.lower().endswith(".xlsx"))
    preview = _preview_metrics(job)
    regions = stored.get("regions") or preview["regions"]
    return {
        "fileCount": int(stored.get("fileCount") or len(source_files) or 0),
        "sheetCount": int(stored.get("sheetCount") or 0),
        "xlsxCount": int(stored.get("xlsxCount") if stored.get("xlsxCount") is not None else xlsx_count),
        "xlsCount": int(stored.get("xlsCount") if stored.get("xlsCount") is not None else xls_count),
        "recordCount": int(stored.get("recordCount") or _parse_record_count(job.get("recordsCount")) or preview["recordCount"]),
        "duplicateRows": int(stored.get("duplicateRows") if stored.get("duplicateRows") is not None else preview["duplicateRows"]),
        "patchedRows": int(stored.get("patchedRows") if stored.get("patchedRows") is not None else preview["patchedRows"]),
        "regionCount": int(stored.get("regionCount") if stored.get("regionCount") is not None else len(regions)),
        "regions": regions,
        "durationSeconds": stored.get("durationSeconds"),
    }


def _percent_change(current: float, previous: float) -> float:
    if previous <= 0:
        return 0.0
    return round(((current - previous) / previous) * 100, 1)


def _job_timestamp(job: dict):
    try:
        return datetime.strptime(f"{job.get('date')} {job.get('timeUTC') or '00:00:00'}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def _aggregate_kpis(jobs: list[dict]) -> dict:
    now = datetime.now(timezone.utc)
    week = timedelta(days=7)
    this_week = []
    last_week = []
    for job in jobs:
        stamp = _job_timestamp(job)
        if stamp is None:
            continue
        if now - week <= stamp <= now:
            this_week.append(job)
        elif now - (week * 2) <= stamp < now - week:
            last_week.append(job)

    def totals(selected: list[dict]) -> dict:
        rolled = {
            "files": 0,
            "sheets": 0,
            "xlsx": 0,
            "xls": 0,
            "records": 0,
            "duplicates": 0,
            "patched": 0,
            "duration_sum": 0.0,
            "duration_count": 0,
            "regions": set(),
        }
        for job in selected:
            metrics = _resolved_metrics(job)
            rolled["files"] += metrics["fileCount"]
            rolled["sheets"] += metrics["sheetCount"]
            rolled["xlsx"] += metrics["xlsxCount"]
            rolled["xls"] += metrics["xlsCount"]
            rolled["records"] += metrics["recordCount"]
            rolled["duplicates"] += metrics["duplicateRows"]
            rolled["patched"] += metrics["patchedRows"]
            if metrics["durationSeconds"] is not None:
                rolled["duration_sum"] += float(metrics["durationSeconds"])
                rolled["duration_count"] += 1
            rolled["regions"].update(metrics["regions"] or [])
        return rolled

    all_jobs = totals(jobs)
    current = totals(this_week)
    previous = totals(last_week)
    total_merges = len(jobs)
    successful = sum(1 for job in jobs if job.get("status") == "OK")
    flagged = sum(1 for job in jobs if job.get("status") != "OK")
    avg_run = (all_jobs["duration_sum"] / all_jobs["duration_count"]) if all_jobs["duration_count"] else 42.0
    saved_seconds = max(0.0, total_merges * (18 * 60 - avg_run))
    current_saved = max(0.0, len(this_week) * (18 * 60 - avg_run))
    previous_saved = max(0.0, len(last_week) * (18 * 60 - avg_run))
    success_rate = (successful / total_merges * 100) if total_merges else 0.0
    dupe_pct = (all_jobs["duplicates"] / all_jobs["records"] * 100) if all_jobs["records"] else 0.0
    patched_pct = (all_jobs["patched"] / all_jobs["records"] * 100) if all_jobs["records"] else 0.0
    row_quality = ((all_jobs["records"] - all_jobs["duplicates"]) / all_jobs["records"] * 100) if all_jobs["records"] else success_rate
    quality = row_quality * 0.7 + success_rate * 0.3 if all_jobs["records"] else success_rate
    last_success = (
        sum(1 for job in last_week if job.get("status") == "OK") / len(last_week) * 100
        if last_week else 0.0
    )
    this_success = (
        sum(1 for job in this_week if job.get("status") == "OK") / len(this_week) * 100
        if this_week else 0.0
    )
    sparkline = []
    today = now.date()
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        sparkline.append(sum(1 for job in jobs if (_job_timestamp(job) or now).date() == day))
    return {
        "totalMerges": total_merges,
        "mergeTrendPct": _percent_change(len(this_week), len(last_week)),
        "jobsThisWeek": len(this_week),
        "sparkline": sparkline,
        "filesProcessed": all_jobs["files"],
        "filesTrendPct": _percent_change(current["files"], previous["files"]),
        "avgSheetsPerFile": round(all_jobs["sheets"] / all_jobs["files"], 1) if all_jobs["sheets"] and all_jobs["files"] else None,
        "xlsxCount": all_jobs["xlsx"],
        "xlsCount": all_jobs["xls"],
        "regionCount": len(all_jobs["regions"]),
        "hoursSaved": round(saved_seconds / 3600, 1),
        "timeTrendPct": _percent_change(current_saved, previous_saved),
        "laborSaved": round((saved_seconds / 3600) * 37),
        "avgRunSeconds": round(avg_run, 1),
        "qualityScore": round(quality, 1),
        "qualityTrendPct": _percent_change(this_success, last_success),
        "dupePct": round(dupe_pct, 1),
        "patchedPct": round(patched_pct, 1),
        "deterministicValid": total_merges > 0 and flagged == 0 and dupe_pct < 1,
    }


@app.get("/dashboard/summary", summary="Return KPI summary for the dashboard")
def dashboard_summary():
    total_jobs = len(JOB_STORE)
    ok_jobs = sum(1 for job in JOB_STORE if job["status"] == "OK")
    flagged_jobs = sum(1 for job in JOB_STORE if job["status"] == "ACTION_NEEDED")
    record_count = sum(_parse_record_count(job.get("recordsCount")) for job in JOB_STORE)
    return {
        "totalJobs": total_jobs,
        "successfulJobs": ok_jobs,
        "flaggedJobs": flagged_jobs,
        "recordsProcessed": record_count,
        "recentFiles": JOB_STORE[:5],
        "kpis": _aggregate_kpis(JOB_STORE),
    }


@app.get("/jobs", summary="List recent merge jobs")
def list_jobs():
    return JOB_STORE


@app.get("/jobs/{job_id}", summary="Fetch a single merge job")
def get_job(job_id: str):
    for job in JOB_STORE:
        if job["id"] == job_id:
            return job
    raise HTTPException(status_code=404, detail="Job not found")


@app.get("/jobs/{job_id}/rows", summary="Fetch merged workbook preview rows for the spreadsheet viewer")
def get_job_rows(job_id: str):
    job = get_job(job_id)
    preview_rows = job.get("previewRows", [])
    return {
        "rows": preview_rows,
        "count": len(preview_rows),
    }


@app.get("/jobs/{job_id}/sheets", summary="Fetch all worksheets for the spreadsheet viewer")
def get_job_sheets(job_id: str):
    get_job(job_id)
    return {"sheets": _load_sheet_data(job_id)}


@app.get("/jobs/{job_id}/download", summary="Download the generated merged workbook")
def download_job(job_id: str):
    job = get_job(job_id)
    workbook_bytes = _workbook_bytes_from_sheets(_load_sheet_data(job_id))
    filename = Path(job["fileName"]).name
    if not filename.lower().endswith(".xlsx"):
        filename = f"{filename}.xlsx"
    return StreamingResponse(
        io.BytesIO(workbook_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@app.post(
    "/process",
    summary="Upload 5 Excel files and download the merged output Excel",
    response_description="Final_Merged_Monthly_Summary.xlsx",
)
async def process_excel(
    branded_file: UploadFile = File(..., description="Branded Apr Excel (.xlsx)"),
    rm_file: UploadFile = File(..., description="RM Job Excel (.xlsx)"),
    master_file: UploadFile = File(..., description="Master Data Excel (.xlsx)"),
    sale_file: UploadFile = File(..., description="Sale Invoice Excel (.xlsx)"),
    receivable_file: UploadFile = File(..., description="Trade Receivable Excel (.xlsx)"),
):
    # Validate every uploaded file
    for field_name, upload in [
        ("branded_file",    branded_file),
        ("rm_file",         rm_file),
        ("master_file",     master_file),
        ("sale_file",       sale_file),
        ("receivable_file", receivable_file),
    ]:
        must_be_xlsx(upload.filename, field_name)
        validate_filename(field_name, upload.filename)

    # Read bytes from each file
    try:
        branded_bytes    = await branded_file.read()
        rm_bytes         = await rm_file.read()
        master_bytes     = await master_file.read()
        sale_bytes       = await sale_file.read()
        receivable_bytes = await receivable_file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded files: {exc}")

    # Run processing
    try:
        started = time.perf_counter()
        processed = process_files(
            branded_bytes, rm_bytes, master_bytes, sale_bytes, receivable_bytes
        )
        duration_seconds = round(time.perf_counter() - started, 1)
        output = processed["workbook"]
        preview_rows = processed["preview_rows"]
        output_bytes = output.getvalue()
        stats = processed.get("stats") or {}
    except HTTPException:
        raise  # re-raise our own validation errors as-is
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Processing failed: {exc}")

    job = _job_from_payload(
        file_name="Final_Merged_Monthly_Summary.xlsx",
        records_count=int(stats.get("recordCount") or len(preview_rows)),
        status="OK",
        source_files=[
            branded_file.filename,
            rm_file.filename,
            master_file.filename,
            sale_file.filename,
            receivable_file.filename,
        ],
        output_bytes=output_bytes,
    )
    source_names = [
        branded_file.filename or "",
        rm_file.filename or "",
        master_file.filename or "",
        sale_file.filename or "",
        receivable_file.filename or "",
    ]
    job["previewRows"] = preview_rows
    job["metrics"] = {
        **stats,
        "fileCount": len(source_names),
        "xlsxCount": sum(1 for name in source_names if name.lower().endswith(".xlsx")),
        "xlsCount": sum(1 for name in source_names if name.lower().endswith(".xls") and not name.lower().endswith(".xlsx")),
        "durationSeconds": duration_seconds,
    }
    JOB_STORE.insert(0, job)
    _persist_job(job, processed.get("sheet_data") or {})

    # Stream the Excel back to the frontend
    return StreamingResponse(
        io.BytesIO(output_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="Final_Merged_Monthly_Summary.xlsx"',
            "X-Job-Id": job["id"],
            "Access-Control-Expose-Headers": "X-Job-Id, Content-Disposition",
        },
    )


@app.get("/", summary="Health check")
def root():
    return {"status": "ok", "message": "Kisna Excel Merger API is running."}
