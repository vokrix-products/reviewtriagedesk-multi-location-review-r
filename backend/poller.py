"""ReviewTriageDesk poller - polls Supabase jobs for pending process_upload jobs."""

import datetime
import json
import os
import time
import traceback

import requests

import processor

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
PRODUCT_ID = os.environ.get("PRODUCT_ID", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

REST_URL = f"{SUPABASE_URL}/rest/v1"

SB_HEADERS = {
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    "apikey": SUPABASE_SERVICE_KEY,
}


def download_file(bucket, file_path):
    if file_path.startswith(bucket + "/"):
        file_path = file_path[len(bucket) + 1:]
    url = f"{SUPABASE_URL}/storage/v1/object/{bucket}/{file_path}"
    resp = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "apikey": SUPABASE_SERVICE_KEY,
        },
    )
    resp.raise_for_status()
    return resp.content


def upload_file(bucket, file_path, data, content_type="application/octet-stream"):
    url = f"{SUPABASE_URL}/storage/v1/object/{bucket}/{file_path}"
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "apikey": SUPABASE_SERVICE_KEY,
            "Content-Type": content_type,
            "x-upsert": "true",
        },
        data=data,
    )
    resp.raise_for_status()
    return resp


def fetch_pending_jobs():
    url = (
        f"{REST_URL}/jobs?status=eq.pending"
        f"&job_type=eq.process_upload"
        f"&product_id=eq.{PRODUCT_ID}"
        f"&select=*&order=created_at.asc&limit=10"
    )
    resp = requests.get(url, headers=SB_HEADERS)
    resp.raise_for_status()
    return resp.json()


def claim_job(job_id):
    url = f"{REST_URL}/jobs?id=eq.{job_id}&status=eq.pending"
    resp = requests.patch(
        url,
        headers={
            **SB_HEADERS,
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        },
        json={"status": "processing"},
    )
    resp.raise_for_status()
    return resp.json()


def insert_record(record, customer_id, source_file_path):
    resp = requests.post(
        REST_URL + "/records",
        headers={
            **SB_HEADERS,
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
        json={
            "product_id": PRODUCT_ID,
            "customer_id": customer_id,
            "title": record["title"],
            "status": record["status"],
            "details": record["details"],
            "source_file_path": source_file_path,
            "due_date": record.get("due_date"),
        },
    )
    resp.raise_for_status()
    return resp


def update_job(job_id, payload):
    url = f"{REST_URL}/jobs?id=eq.{job_id}"
    resp = requests.patch(
        url,
        headers={
            **SB_HEADERS,
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
        json=payload,
    )
    resp.raise_for_status()
    return resp


def insert_notification(customer_id, title, body, notif_type):
    try:
        requests.post(
            REST_URL + "/notifications",
            headers={
                **SB_HEADERS,
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            json={
                "product_id": PRODUCT_ID,
                "customer_id": customer_id,
                "title": title,
                "body": body,
                "type": notif_type,
                "read": False,
            },
        )
    except Exception:
        traceback.print_exc()


def process_job(job):
    job_id = job.get("id")
    customer_id = job.get("customer_id")
    input_file_path = job.get("input_file_path")
    output_prefix = job.get("output_file_path") or "results"

    claimed = claim_job(job_id)
    if not claimed:
        return

    try:
        file_bytes = download_file("uploads", input_file_path)

        records = processor.process_file(file_bytes)

        for record in records:
            insert_record(record, customer_id, input_file_path)

        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        result_path = f"{output_prefix}/{job_id}_{timestamp}.json"
        payload = json.dumps(records, indent=2, default=str).encode("utf-8")
        upload_file("results", result_path, payload, content_type="application/json")

        update_job(
            job_id,
            {
                "status": "completed",
                "output_file_path": f"results/{result_path}",
                "result_summary": {
                    "records_created": len(records),
                    "source_file_path": input_file_path,
                },
                "completed_at": datetime.datetime.utcnow().isoformat() + "Z",
            },
        )

        insert_notification(
            customer_id,
            "Processing complete",
            "Your upload has been processed successfully.",
            "success",
        )

    except Exception as exc:
        traceback.print_exc()
        try:
            update_job(
                job_id,
                {
                    "status": "failed",
                    "result_summary": {"error": str(exc)},
                    "completed_at": datetime.datetime.utcnow().isoformat() + "Z",
                },
            )
        except Exception:
            traceback.print_exc()

        insert_notification(
            customer_id,
            "Processing failed",
            "There was an error processing your upload.",
            "error",
        )


def poll():
    while True:
        try:
            jobs = fetch_pending_jobs()
            for job in jobs:
                try:
                    process_job(job)
                except Exception:
                    traceback.print_exc()
        except Exception:
            traceback.print_exc()

        time.sleep(60)


if __name__ == "__main__":
    print("Poller started")
    poll()
