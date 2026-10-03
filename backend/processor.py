import csv
import datetime
import io
import json
import re
from typing import Any, Dict, List, Optional

import openpyxl
import pdfplumber


# Exact status strings allowed by the ReviewTriageDesk dashboard.
# The colon-separated suffix is severity, but the whole string is the status.
ALLOWED_STATUSES = {
    "new:info",
    "unread:warning",
    "unresponded:critical",
    "draft_pending:info",
    "draft_generated:good",
    "needs_approval:warning",
    "approved:good",
    "posted:good",
    "skipped:info",
    "snoozed:info",
    "reopened:warning",
    "archived:info",
    "failed_post:critical",
    "flagged:warning",
    "sensitive:critical",
    "legal_hold:critical",
    "refund_risk:critical",
    "safety_risk:critical",
    "health_risk:critical",
    "discrimination_risk:critical",
    "churn_risk:warning",
    "escalation_required:critical",
    "approval_required:warning",
    "auto_post_eligible:good",
    "auto_post_blocked:warning",
    "sla_ok:good",
    "sla_at_risk:warning",
    "sla_breached:critical",
    "sla_paused_business_hours:info",
    "unassigned:warning",
    "assigned:good",
    "escalated:critical",
    "awaiting_approval:warning",
    "approved_by_hq:good",
    "approved_by_region:good",
    "approved_by_location:good",
    "matched:good",
    "ambiguous:warning",
    "misrouted:critical",
    "missing_location:critical",
    "duplicate:info",
    "source_unmapped:warning",
    "connected:good",
    "token_expired:warning",
    "sync_error:critical",
    "source_disconnected:critical",
    "no_review_access:critical",
    "pending_authorization:warning",
    "brand_voice_missing:warning",
    "location_voice_missing:warning",
    "template_missing:warning",
    "policy_conflict:critical",
    "compliance_review:warning",
    "missing:critical",
    "expired:critical",
    "valid:good",
    "parse_error:critical",
    "duplicate_row:warning",
}

DEFAULT_STATUS = "new:info"
PARSE_ERROR_STATUS = "parse_error:critical"
DUPLICATE_STATUS = "duplicate_row:warning"

RESPONSE_STATUS_MAP = {
    "new": "new:info",
    "unread": "unread:warning",
    "unresponded": "unresponded:critical",
    "draft_pending": "draft_pending:info",
    "draft_generated": "draft_generated:good",
    "needs_approval": "needs_approval:warning",
    "approved": "approved:good",
    "posted": "posted:good",
    "skipped": "skipped:info",
    "snoozed": "snoozed:info",
    "reopened": "reopened:warning",
    "archived": "archived:info",
    "failed_post": "failed_post:critical",
    "escalation_required": "escalation_required:critical",
    "approval_required": "approval_required:warning",
    "sla_ok": "sla_ok:good",
    "sla_breached": "sla_breached:critical",
    "sla_at_risk": "sla_at_risk:warning",
    "unassigned": "unassigned:warning",
    "assigned": "assigned:good",
    "escalated": "escalated:critical",
    "awaiting_approval": "awaiting_approval:warning",
    "approved_by_hq": "approved_by_hq:good",
    "approved_by_region": "approved_by_region:good",
    "approved_by_location": "approved_by_location:good",
    "matched": "matched:good",
    "ambiguous": "ambiguous:warning",
    "misrouted": "misrouted:critical",
    "missing_location": "missing_location:critical",
    "source_unmapped": "source_unmapped:warning",
    "flag": "flagged:warning",
    "sensitive": "sensitive:critical",
    "legal_hold": "legal_hold:critical",
    "refund_risk": "refund_risk:critical",
    "safety_risk": "safety_risk:critical",
    "health_risk": "health_risk:critical",
    "discrimination_risk": "discrimination_risk:critical",
    "sla_paused_business_hours": "sla_paused_business_hours:info",
    "connected": "connected:good",
    "token_expired": "token_expired:warning",
    "sync_error": "sync_error:critical",
    "source_disconnected": "source_disconnected:critical",
    "no_review_access": "no_review_access:critical",
    "pending_authorization": "pending_authorization:warning",
    "brand_voice_missing": "brand_voice_missing:warning",
    "location_voice_missing": "location_voice_missing:warning",
    "template_missing": "template_missing:warning",
    "policy_conflict": "policy_conflict:critical",
    "compliance_review": "compliance_review:warning",
    "missing": "missing:critical",
    "expired": "expired:critical",
    "valid": "valid:good",
    "parse_error": "parse_error:critical",
    "duplicate_row": "duplicate_row:warning",
}

TITLE_KEYS = [
    "reviewer_name",
    "customer_name",
    "employee_name",
    "vendor_name",
    "contract_party",
    "patient_name",
    "location_name",
    "brand_name",
    "source_review_url",
    "review_id",
    "supplier",
    "product",
]

DUE_DATE_KEYS = [
    "sla_due_at",
    "due_date",
    "response_due_at",
    "deadline",
    "due_at",
]

TRUE_VALUES = {"true", "yes", "1", "y", "t", "x", "checked"}


def normalize_key(key: str) -> str:
    key = str(key).strip()
    key = re.sub(r"[^0-9a-zA-Z]+", "_", key.lower())
    key = re.sub(r"_+", "_", key).strip("_")
    if not key:
        key = "column"
    if key[0].isdigit():
        key = "col_" + key
    return key


def stringify_value(value: Any) -> Any:
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    if isinstance(value, datetime.date):
        return value.isoformat()
    if isinstance(value, datetime.time):
        return value.isoformat()
    if isinstance(value, (dict, list)):
        return json.dumps(value, default=str)
    return value


def safe_status(value: str) -> str:
    if not isinstance(value, str):
        return DEFAULT_STATUS
    if value in ALLOWED_STATUSES:
        return value
    return DEFAULT_STATUS


def extract_title(row: Dict[str, Any]) -> str:
    for key in TITLE_KEYS:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()

    excluded = {
        "review_body",
        "review_title",
        "body",
        "internal_notes",
        "audit_log_json",
        "error",
    }
    for key, value in row.items():
        if key in excluded:
            continue
        if value is not None and str(value).strip():
            return str(value).strip()

    return "Unnamed Record"


def extract_due_date(row: Dict[str, Any]) -> Optional[str]:
    for key in DUE_DATE_KEYS:
        value = row.get(key)
        if value is None:
            continue
        text = str(value).strip()
        match = re.search(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?",
            text,
        )
        if match:
            return match.group(0)
        match = re.search(r"\d{4}-\d{2}-\d{2}", text)
        if match:
            return match.group(0)
    return None


def _is_true(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in TRUE_VALUES


def _derive_status(row: Dict[str, Any]) -> str:
    if _is_true(row.get("escalation_required")) or str(
        row.get("escalation_required", "")
    ).strip().lower() in {"escalated", "escalation_required"}:
        return "escalation_required:critical"

    if _is_true(row.get("approval_required")) or str(
        row.get("approval_required", "")
    ).strip().lower() in {"approval", "approval_required"}:
        return "approval_required:warning"

    if _is_true(row.get("sla_breached")) or str(
        row.get("sla_breached", "")
    ).strip().lower() in {"breached"}:
        return "sla_breached:critical"

    if _is_true(row.get("sla_at_risk")) or str(
        row.get("sla_at_risk", "")
    ).strip().lower() in {"at_risk"}:
        return "sla_at_risk:warning"

    response_status = (
        row.get("response_status", None) or row.get("review_status", None)
    )
    if response_status is not None:
        mapped = RESPONSE_STATUS_MAP.get(str(response_status).strip().lower())
        if mapped:
            return mapped

    return DEFAULT_STATUS


def _parse_delimited_text(text: str) -> List[Dict[str, Any]]:
    text = text.strip()
    if not text:
        return []

    try:
        sample = text[:8192]
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
        has_header = csv.Sniffer().has_header(sample)
        if has_header:
            reader = csv.DictReader(io.StringIO(text), dialect=dialect)
            rows = []
            for row in reader:
                cleaned = {k: v for k, v in row.items() if k is not None}
                rows.append(cleaned)
            if rows:
                return rows

        reader = csv.reader(io.StringIO(text), dialect=dialect)
        matrix = list(reader)
        if matrix:
            first = matrix[0]
            headers = [f"column_{i+1}" for i in range(len(first))]
            rows = []
            for row in matrix:
                padded = list(row) + [""] * (len(headers) - len(row))
                rows.append(dict(zip(headers, padded)))
            return rows
    except Exception:
        pass

    return [{"text": line.strip()} for line in text.splitlines() if line.strip()]


def _parse_pdf(file_bytes: bytes) -> List[Dict[str, Any]]:
    extracted_tables: List[Dict[str, Any]] = []
    text_parts: List[str] = []

    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                if text.strip():
                    text_parts.append(text)

                tables = page.extract_tables() or []
                for table in tables:
                    if not table or len(table) < 2:
                        continue

                    headers: List[str] = []
                    for i, cell in enumerate(table[0]):
                        headers.append(
                            str(cell).strip() if cell is not None else f"column_{i+1}"
                        )

                    for r in table[1:]:
                        if not any(c is not None and str(c).strip() for c in r):
                            continue
                        row: Dict[str, Any] = {}
                        for i, cell in enumerate(r):
                            if i >= len(headers):
                                break
                            row[headers[i]] = (
                                str(cell).strip() if cell is not None else ""
                            )
                        extracted_tables.append(row)
    except Exception:
        return []

    if extracted_tables:
        return extracted_tables

    return _parse_delimited_text("\n".join(text_parts))


def _parse_excel(file_bytes: bytes) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
    try:
        for ws in wb.worksheets:
            data = list(ws.iter_rows(values_only=True))
            if not data:
                continue

            headers: List[str] = []
            for i, cell in enumerate(data[0]):
                headers.append(str(cell).strip() if cell is not None else f"column_{i+1}")

            for r in data[1:]:
                if not any(c is not None and str(c).strip() for c in r):
                    continue

                row: Dict[str, Any] = {}
                for i, cell in enumerate(r):
                    if i >= len(headers):
                        break
                    if cell is not None and str(cell).strip():
                        row[headers[i]] = stringify_value(cell)
                if row:
                    rows.append(row)
    finally:
        wb.close()

    return rows


def _fallback_parse(file_bytes: bytes) -> List[Dict[str, Any]]:
    text = file_bytes.decode("utf-8", errors="ignore")
    return _parse_delimited_text(text)


def rows_to_records(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    records = []
    seen = set()

    for row in rows:
        if not isinstance(row, dict):
            continue

        cleaned: Dict[str, Any] = {}
        for key, value in row.items():
            if key is None:
                continue
            cleaned[normalize_key(str(key))] = stringify_value(value)

        if not any(str(value).strip() for value in cleaned.values() if value is not None):
            continue

        title = extract_title(cleaned)
        due_date = extract_due_date(cleaned)

        review_id = cleaned.get("review_id")
        status = _derive_status(cleaned)

        if review_id is not None and str(review_id).strip():
            rid = str(review_id).strip()
            if rid in seen:
                status = DUPLICATE_STATUS
            else:
                seen.add(rid)

        # due_date must be top-level only, never inside details.
        details: Dict[str, Any] = {}
        for key, value in cleaned.items():
            if key in {"due_date", "sla_due_at", "response_due_at", "deadline", "due_at"}:
                continue
            details[key] = value

        records.append(
            {
                "title": title,
                "status": safe_status(status),
                "details": details,
                "due_date": due_date,
            }
        )

    return records


def process_file(file_bytes: bytes) -> list[dict]:
    if not isinstance(file_bytes, bytes):
        return [
            {
                "title": "Parse Error",
                "status": PARSE_ERROR_STATUS,
                "details": {"error": "file_bytes must be bytes"},
                "due_date": None,
            }
        ]

    rows: List[Dict[str, Any]] = []

    try:
        rows = _parse_pdf(file_bytes)
    except Exception:
        rows = []

    if not rows:
        try:
            rows = _parse_excel(file_bytes)
        except Exception:
            rows = []

    if not rows:
        try:
            rows = _fallback_parse(file_bytes)
        except Exception:
            rows = []

    if not rows:
        return [
            {
                "title": "Empty Document",
                "status": PARSE_ERROR_STATUS,
                "details": {"error": "No parsable content found"},
                "due_date": None,
            }
        ]

    records = rows_to_records(rows)
    if not records:
        return [
            {
                "title": "Empty Document",
                "status": PARSE_ERROR_STATUS,
                "details": {"error": "No records extracted"},
                "due_date": None,
            }
        ]

    return records


def extract_text(file_bytes):
    try:
        import pdfplumber
        import io
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            text = ""
            for p in pdf.pages:
                text = text + (p.extract_text() or "") + "\n"
            if text.strip():
                return text
    except Exception:
        pass
    try:
        return file_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return ""

