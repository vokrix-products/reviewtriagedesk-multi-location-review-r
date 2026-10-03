from processor import process_file


DEMO_CSV = (
    b"review_id,source_platform,reviewer_name,location_name,review_body,review_date,sla_due_at,response_status\n"
    b"r-101,Google,Alice Johnson,Downtown Cafe,Great coffee and friendly staff,2025-01-02,2025-01-03T18:00:00Z,draft_generated\n"
    b"r-102,Yelp,Bob Smith,Uptown Cafe,Slow service during lunch,2025-01-02,2025-01-03T18:00:00Z,new\n"
)


def main():
    results = process_file(DEMO_CSV)
    assert isinstance(results, list), "process_file must return a list"
    assert results, "demo should produce at least one record"

    print(f"Processed {len(results)} records")
    for record in results:
        print(
            f"- {record['title']} | {record['status']} | "
            f"due={record['due_date']} | details_keys={sorted(record['details'].keys())}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
