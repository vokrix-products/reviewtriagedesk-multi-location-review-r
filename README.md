# ReviewTriageDesk — Multi-Location Review Response Queue

ReviewTriageDesk is a review-response operations product for multi-location
businesses. It ingests review exports from many locations and sources (Google,
Yelp, and similar review platforms), normalizes them into a single triage queue,
and tracks each review through its response lifecycle: drafting, approval,
posting, escalation, and SLA compliance.

This repository contains the pure processing engine and its demo/test harness.
It does not make network calls; it turns raw upload bytes into normalized,
dashboard-ready records.

## Archetype

- **Type:** Review-response triage / queueing backend
- **Domain:** Reputation management, multi-location review operations
- **Inputs:** Review exports and queues as PDF, Excel (.xlsx), CSV/TSV/pipe text,
  or plain text
- **Output:** A flat `list[dict]` of records, one per review row
- **Storage-free:** No database and no external calls; pure transformation

## Files

| File | Purpose |
|---|---|
| `processor.py` | Core extraction engine. Defines `process_file(file_bytes: bytes) -> list[dict]`. Handles PDF, Excel, CSV, and plain text parsing; normalizes fields; extracts title, status, due_date, and details; deduplicates on `review_id`. |
| `run_demo.py` | Zero-argument demo using hardcoded CSV bytes. Calls `process_file`, asserts the result is a list, prints extracted records, exits 0. |
| `run_tests.py` | Lightweight `unittest` suite covering CSV parsing, record shape, allowed status, due-date top-level rule, and fallback text extraction. |
| `requirements.txt` | Runtime dependencies: openai, requests, pdfplumber, openpyxl. |

## Record shape

Every record returned by `process_file` is a dict with exactly these keys:

```python
{
    "title": str,          # reviewer / location / identifier label
    "status": str,         # one of ALLOWED_STATUSES (e.g. "draft_generated:good")
    "details": dict,       # all remaining normalized fields
    "due_date": str | None # ISO-8601 date or datetime, TOP-LEVEL only
}
```

### Status rules

- `status` is always one of the exact strings in `ALLOWED_STATUSES`.
- The value after the colon is severity (`info`, `warning`, `good`,
  `critical`). The whole string is the status.
- `response_status` / `review_status` values are mapped via
  `RESPONSE_STATUS_MAP`.
- Boolean/flag columns take precedence: `escalation_required`,
  `approval_required`, `sla_breached`, `sla_at_risk`.
- Unknown or missing statuses fall back to `new:info`.
- Unparseable input yields a `parse_error:critical` record.
- Duplicate `review_id` values yield `duplicate_row:warning`.

### Due-date rule

`due_date` must appear **only** at the top level of the record. It is extracted,
when present, from the first matching column of:

```
sla_due_at, due_date, response_due_at, deadline, due_at
```

These keys are then **removed from `details`**. `due_date` is `None` when no
date-bearing column exists.

### Deduplication

Rows are deduplicated on `review_id`. The first occurrence keeps its derived
status; later occurrences are returned with `duplicate_row:warning`.

## Supported input formats

Parsing is attempted in this order, first match wins:

1. **PDF** — text + tables via `pdfplumber`; tables become row dicts.
2. **Excel** — `.xlsx` sheets via `openpyxl`; first row is the header.
3. **Delimited text / plain text** — CSV/TSV/pipe via `csv.Sniffer`; falls back
   to one record per non-empty line with a `{"text": ...}` row.

## What the poller expects as input

The processor is designed to be called by a poller/worker that receives a raw
file upload and the dashboard that consumes normalized records.

- **Input to the poller:** raw file bytes (`bytes`) for a single review export
  or review queue file. Typical columns include `review_id`, `source_platform`,
  `reviewer_name`, `location_name`, `brand_name`, `review_body`, `review_date`,
  `sla_due_at`, `response_status`.
- **Call:** `process_file(file_bytes)` — pure, synchronous, no network, no disk.
- **Output to the dashboard:** `list[dict]` of records in the shape above.
  The dashboard upserts on `details["review_id"]`, uses `status` for queue
  lanes and severity, `due_date` for SLA countdowns, and `title` for the row
  label (reviewer or location).

## Requirements

```
openai
requests
pdfplumber
openpyxl
```

Install:

```bash
pip install -r requirements.txt
```

## Usage

```python
from processor import process_file

with open("review_export.csv", "rb") as f:
    file_bytes = f.read()

records = process_file(file_bytes)
for record in records:
    print(record["title"], record["status"], record["due_date"])
```

## Demo and tests

```bash
python3 run_demo.py
python3 run_tests.py
```

`run_demo.py` prints a summary of extracted records and exits 0.
`run_tests.py` runs the `unittest` suite and exits 0 on success.
Railway: reviewtriagedesk-multi-location-review-r
Cloudflare: reviewtriagedesk-multi-location-review-r.vokrix.co
